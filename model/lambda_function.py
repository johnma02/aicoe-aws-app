from nwm_predict import *
import netCDF4 as nc
import boto3

"""
payload structure:
payload = {
    'start_year': 2008,
    'start_month': 2,
    'start_day': 1,
    'end_year': 2008,
    'end_month': 2,
    'end_day': 1,
}
"""


def lambda_handler(event, context):
    start = time.time()

    print('Predicting the risk level of daily EOF runoffs:')

    current_path = os.getcwd()

    # read the hourly value from the netcdf file for n days in a row

    start_year, start_month, start_day = int(event['start_year']), int(
        event['start_month']), int(event['start_day'])

    end_year, end_month, end_day = int(event['end_year']), int(
        event['end_month']), int(event['end_day'])

    # Set the data directory path
    data_path = "data"

    # For now, assume we are only working in one day intervals
    start_date = datetime.date(start_year, start_month, start_day)
    end_date = datetime.date(end_year, end_month, end_day)

    land_output = [
        f"{data_path}/{date.strftime('%Y%m%d')}.LDASOUT_DOMAIN1.nc" for date in
        (start_date + datetime.timedelta(days=x)
         for x in range((end_date - start_date).days + 1))
    ]

    runoff_output = [
        f"{data_path}/{date.strftime('%Y%m%d')}.RTOUT_DOMAIN1.nc" for date in
        (start_date + datetime.timedelta(days=x)
         for x in range((end_date - start_date).days + 1))
    ]

    """
    Variables in daily Land file
    dict_keys(['ACSNOM', 'EMISSM', 'FIRA', 'FSA', 'IRB', 'LWFORC', 'Q2MVM', 'QSNOW', 'QSNOWM', 'RAINRATE', 'SOILICEM',
    'SOILSAT', 'SOILSATM', 'SOIL_TM', 'SOIL_WM', 'SWFORC', 'T2MVM', 'TGBM', 'crs', 'time', 'x', 'y'])

    Variables in daily runoff file
    dict_keys(['QBDRYRT', 'QBDRYRT_2', 'QSTRMVOLRT', 'SFCHEADSUBRTM', 'SOIL_MM', 'ZWATTABLRTM', 'crs', 'qqsfc_acc', 'qqsub_acc', 'time', 'x', 'y'])

    Variables in selected_variables_by_cluster.nc
    dict_keys(['time', 'x', 'y', 'ACSNOM', 'QSNOW', 'ACCPRCP'])

    Change TGV to T2MVM, and remove SHG
    """

    # influential variables for each cluster
    influential_vars = {
        # 'RAINRATE', 'SFHD', 'ACSNOM', 'SOILSAT'
        1: ['RAINRATE', 'SFCHEADSUBRTM', 'ACSNOM', 'SOILSATM'],
        2: ['RAINRATE', 'ACSNOM', 'SOILSATM', 'T2MVM'],
        3: ['RAINRATE', 'SOIL_WM_1', 'SOIL_MM_3', 'ACSNOM', 'SFCHEADSUBRTM'],
        4: ['RAINRATE', 'SOIL_WM_1', 'FIRA', 'SFCHEADSUBRTM', 'SOIL_MM_4', 'ACSNOM'],
        5: ['RAINRATE', 'ACSNOM', 'SFCHEADSUBRTM', 'T2MVM', 'SOILSATM', 'qqsub_acc', 'FIRA']
    }

    # runoff prediction for each cluster

    file_path = current_path + '/trained_clusters/'

    for i in range(1, 6):

        # get the influential variables
        # get() Method return the value for the given key if present in the dictionary.

        x = influential_vars.get(i)

        # Deep copy is a process in which the copying process occurs recursively.

        y = deepcopy(x)
        y.reverse()
        variables = y

        # get the hourly model output from WRF-Hydro model runs
        daily_values = get_daily_values_from_nwm(
            land_output, runoff_output, variables)

        # Step 2: load the statistical models and make predictions
        # provide the path to both event and runoff prediction models
        # (saved as a classification model, clas.joblib.dat and a regression model, reg.joblib.dat)

        mod_files = file_path + 'cluster' + str(i) + '/'

        # predictions of occurrence and the associated probability of EOF runoff using prediction classification models, and
        # predictions of its magnitudes using the regression model

        predict_results = predict_runoff(mod_files, daily_values, variables)

        predict = np.array(predict_results.variables['EVENT'])
        # save daily prediction results (event, probability and magnitude) into NetCDF format
        inputs = current_path + '/preds/p' + str(i) + '.nc'
        save_data_to_netCDF(inputs, predict_results)

    # Extract the predictions of event, probability, and magnitude for each cluster
    event_predictions = {}
    magnitude_predictions = {}
    probability_predictions = {}

    # Path to prediction results
    prediction_path = current_path + '/preds/'
    # Path to cluster definition
    cluster_file_path = current_path + '/trained_clusters/cluster_definition_1km.nc'

    # Iterate through clusters
    for cluster_number in range(1, 6):
        # Predictions (event, probability, and magnitude) for each cluster
        prediction_file = prediction_path + 'p' + str(cluster_number) + '.nc'
        predictions = xr.open_dataset(prediction_file)

        # Cluster definition
        cluster_definition = xr.open_dataset(cluster_file_path)

        # Event prediction
        event_values = np.fliplr(predictions.EVENT.values)

        # Probability prediction
        probability_values = np.fliplr(predictions.PROB.values)

        # Magnitude prediction
        magnitude_values = np.fliplr(predictions.RUNOFF.values)

        # Assign "1" to a specific cluster for each iteration
        cluster_values = cluster_definition.Cluster.values
        cluster_values[cluster_values != cluster_number] = np.nan
        cluster_values[cluster_values == cluster_number] = 1
        cluster_values_new_dim = cluster_values

        # Extract the prediction from a given cluster
        # re_cluster_values acts as a filter to mask out the values not in a given cluster
        batch_size, num_rows, num_cols = event_values.shape
        re_cluster_values = np.repeat(
            cluster_values_new_dim[np.newaxis, :, :], batch_size, axis=0)

        multi_event = np.multiply(event_values, re_cluster_values)
        multi_magnitude = np.multiply(magnitude_values, re_cluster_values)
        multi_probability = np.multiply(probability_values, re_cluster_values)

        # Assign predictions to different variables
        event_predictions[cluster_number] = multi_event
        magnitude_predictions[cluster_number] = multi_magnitude
        probability_predictions[cluster_number] = multi_probability

    # Assign model predictions to event, probability, and magnitude
    # Starting from cluster 1
    event = event_predictions.get(1)
    probability = probability_predictions.get(1)
    magnitude = magnitude_predictions.get(1)

    # Continue with clusters 2 to 5
    for cluster_num in range(2, 6):
        cluster_event = event_predictions.get(cluster_num)
        is_nan_event = np.isnan(event)
        event[is_nan_event] = cluster_event[is_nan_event]

        cluster_probability = probability_predictions.get(cluster_num)
        is_nan_probability = np.isnan(probability)
        probability[is_nan_probability] = cluster_probability[is_nan_probability]

        cluster_magnitude = magnitude_predictions.get(cluster_num)
        is_nan_magnitude = np.isnan(magnitude)
        magnitude[is_nan_magnitude] = cluster_magnitude[is_nan_magnitude]

    event_copy = deepcopy(event)
    probability_copy = deepcopy(probability)
    magnitude_copy = deepcopy(magnitude)

    # open an existing NetCDF template
    pd = xr.open_dataset(current_path + '/preds/p4.nc')

    pd.EVENT.values = event_copy
    pd.RUNOFF.values = probability_copy
    pd.PROB.values = magnitude_copy

    # ef = pd.transpose('time', 'y', 'x')
    ef = pd
    ef.to_netcdf(current_path + '/preds/pF.nc')

    end = time.time()

    print("Time: {0:.4f}s".format(end - start))

    # Risk level prediction based on the occurrence probability and magnitudes of daily runoff event using the risk level metrics

    start = time.time()

    print('Predicting risk level of daily EOF runoff based on the pre-defined risk matrix:')

    current_path = os.getcwd()

    # step 1: read the prediction for a given time period (10-day in our case)
    input_directory = current_path + '/preds/'

    # read the saved final output file with this name
    file_path = input_directory + 'pF.nc'
    x = xr.open_dataset(file_path)

    # read the magnitudes of daily EOF runoff
    y = x.RUNOFF.values
    y_map = y

    conditions = [
        y < 0.1,
        (y >= 0.1) & (y <= 0.45),
        (y > 0.45) & (y <= 2.4),
        (y > 2.4) & (y <= 11.6),
        y > 11.6
    ]

    choices = [0, 1, 2, 3, 4]
    y_map = np.select(conditions, choices, default=y_map)

    risk_levels = np.full((1, 1601, 2001), np.nan)
    # Convert the occurrence probability and categorical magnitude of runoff into risk levels (4 levels) using the risk-level metrics
    for index, values in np.ndenumerate(x.PROB.values):
        i, j, k = index
        magnitude = y_map[i, j, k]

        if values > 0.75:
            if magnitude <= 1:
                risk_levels[i, j, k] = 1
            elif magnitude == 2 or magnitude == 3:
                risk_levels[i, j, k] = 2
            else:
                risk_levels[i, j, k] = 3
        elif 0.75 >= values > 0.5:
            if magnitude <= 1:
                risk_levels[i, j, k] = 1
            else:
                risk_levels[i, j, k] = 2
        elif 0.5 >= values > 0.25:
            if magnitude <= 1:
                risk_levels[i, j, k] = 1
            else:
                risk_levels[i, j, k] = 2
        else:
            if magnitude <= 1:
                risk_levels[i, j, k] = 0
            else:
                risk_levels[i, j, k] = 1

    # Copy 10-day risk level prediction to a new variable, risk_levels_copy
    risk_levels_copy = deepcopy(risk_levels)

    # min, med and max risk level for each grid (1km x 1km) over a given period
    median_risk_levels = np.empty((1, 1601, 2001)) * np.nan
    min_risk_levels = np.empty((1, 1601, 2001)) * np.nan
    max_risk_levels = np.empty((1, 1601, 2001)) * np.nan

    num_periods, num_rows, num_cols = risk_levels_copy.shape

    for index, values in np.ndenumerate(risk_levels_copy[0]):
        i, j = index
        risk_levels_list = []
        for k in range(num_periods):
            risk_levels_list.append(risk_levels_copy[k, i, j])

        median_value = np.median(risk_levels_list)
        min_value = np.min(risk_levels_list)
        max_value = np.max(risk_levels_list)

        median_risk_levels[:, i, j] = median_value
        min_risk_levels[:, i, j] = min_value
        max_risk_levels[:, i, j] = max_value

    # Load the variable file produced from separate code for variables
    # Where does selected_variables_by_cluster.nc come from?
    selected_variables = xr.open_dataset(input_directory + 'p1.nc')

    # Save the min, med, max of risk level, qsnow, acsnom and accprcp.
    data_save = xr.Dataset(
        data_vars=dict(
            risk_min=(["time", "lat", "lon"], min_risk_levels),
            risk_max=(["time", "lat", "lon"], max_risk_levels),
            risk_median=(["time", "lat", "lon"], median_risk_levels),
            risk_all=(["time", "lat", "lon"], risk_levels_copy),
        ),
        coords=dict(
            lat=(["lat"], selected_variables.y.values[::-1],  # flip around the longitundinal axis
                 {'units': 'crs [m]'}),
            lon=(["lon"], selected_variables.x.values, {'units': 'crs [m]'}),
        ),
        attrs=dict(description="Risk Level"),
    )

    # save the file
    data_save.to_netcdf(input_directory + 'preds.nc')

    end = time.time()
    print("Time: {0:.4f}s".format(end - start))

    print("Posting predictions to S3:")

    s3 = boto3.resource('s3')
    data_put = open(input_directory+'preds.nc', 'rb')

    s3.Bucket(
        'aicoe-runoff-risk-outputs').put_object(Key=start_date.strftime('%Y%m%d')+"-preds.nc", Body=data_put)

    data_put.close()

    print("Successfully posted predictions to S3")
