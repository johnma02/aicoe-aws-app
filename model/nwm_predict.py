#!/usr/bin/env python
# coding: utf-8
import datetime as dt
import warnings
from copy import deepcopy
import numpy as np
from joblib import load
from joblib import dump
import glob
import pandas as pd
import xarray as xr
import xgboost as xgb
import datetime
import time
import re
import os
import pip
import boto3
print(__doc__)
# importing necessary libraries

warnings.filterwarnings("ignore")

# pip install xgboost==1.6.0

# physical parameters
geo_vars = [
    'Lat',
    'Lon',
    'albedo12m',
    'greenfrac',
    'hgt_m',
    'landusef',
    'lu_index',
    'slopecat',
    'snoalb',
    'soilcbot',
    'soilctop',
    'soiltemp'
]

# accumulated variables on a daily scale
acc_vars = [
    'SWFORC',
    'LWFORC',
    'FSA',
    'FIRA',
    'IRB',
    'QQSFC ',
    'QQSUB',
    'SHG',
    'QSNOW',
    'RAINRATE'
]

# average varialbes on a dily scale
avg_vars = [
    'TGB',
    'T2MVM',
    'Q2MV',
    'SOIL_M1',
    'SOIL_M2',
    'SOIL_M3',
    'SOIL_M4',
    'SOIL_T1',
    'SOIL_T2',
    'SOIL_T3',
    'SOIL_T4',
    'SOIL_W1',
    'SOIL_W2',
    'SOIL_W3',
    'SOIL_W4',
    'SOILICE',
    'SOILSATM',
    'ZWATTABLRT',
    'SNEQV',
    'EMISS',
    'SFCHEADSUBRTM',
    'SFHD'
]

# calculate daily values from the accumulated ones
diff_vars = ['ACCPRCP', 'ACSNOM', 'QBDRYRT', 'QSNOW']

# variables
land_vars = [
    'SWFORC', 'LWFORC', 'ACCPRCP', 'EMISS', 'FSA', 'FIRA', 'HFX', 'LH', 'EDIR', 'ETRAN', 'ZWT', 'WA',
    'RAINRATE', 'WT', 'TR', 'IRG', 'SHG', 'EVG', 'SAG', 'IRB', 'SHB', 'EVB', 'TRAD', 'TG', 'TGV', 'TGB', 'T2MVM',
    'Q2MV', 'Q2MB', 'ZSNSO_SN', 'SNICE', 'SNLIQ', 'SOIL_T1', 'SNOW_T', 'SNOWH', 'SNEQV', 'QSNOW',
    'ISNOW', 'FSNO', 'ACSNOW', 'ACSNOM', 'CM', 'CH', 'CHV', 'CHB', 'CHLEAF', 'CHUC', 'CHV2', 'CHB2',
    'RTMASS', 'STMASS', 'WOOD', 'NEE', 'GPP', 'ACCET', 'SOILICE', 'SOILSATM', 'SNOWT_AVG', 'SOIL_T2',
    'SOIL_T3', 'SOIL_T4', 'SOIL_WM_1', 'SOIL_WM_2', 'SOIL_WM_3', 'SOIL_WM_4'
]

runoff_vars = [
    'QBDRYRT',
    'SOIL_MM_1',
    'SOIL_MM_2',
    'SOIL_MM_3',
    'SOIL_MM_4',
    'SFCHEADSUBRTM',
    'SFHD',
    'ZWATTABLRT',
    'QQSFC ',
    'qqsub_acc'
]


def save_data_to_netCDF(inputs, predict_results):
    # save Xarray to NetCDF
    predict_results.time.attrs['unit'] = 'Time days'
    # print(predict_results)
    c = predict_results.transpose('time', 'y', 'x')
    # save xarray to netCDF
    c.to_netcdf(inputs)


def extract_date(file_path: str):
    file_name = file_path.split('/')[-1]
    match = re.search("(\d{8})", file_name)
    date_str = match.group(1)
    return pd.to_datetime(date_str, format='%Y%m%d')


def get_daily_values(land_output, runoff_output, variables, inf_land_var, inf_runoff_var):
    new_data_sets = {}

    # Concatenate the datasets along the time dimension
    inland = [x for x in land_output if 'RT' not in x]
    inroute = [x for x in runoff_output if 'RT' in x]

    # Fetch dates from s3
    s3 = boto3.client('s3')
    for fetch in inland:
        s3.download_file('aicoe-runoff-risk-variables', fetch, fetch)

    for fetch in inroute:
        s3.download_file('aicoe-runoff-risk-variables', fetch, fetch)

    ds_list1 = [xr.open_dataset(file) for file in inland]
    ncland = xr.concat(ds_list1, dim='time')
    time_vals = [extract_date(file) for file in inland]
    ncland['time'] = xr.DataArray(time_vals, dims='time')

    ds_list2 = [xr.open_dataset(file) for file in inroute]
    ncroute = xr.concat(ds_list2, dim='time')
    time_vals = [extract_date(file) for file in inroute]
    ncroute['time'] = xr.DataArray(time_vals, dims='time')

    soil_layers = [0, 1, 2, 3]
    for layer in soil_layers:
        new_var = ncroute['SOIL_MM'].sel(soil_layers_stag=layer)
        new_var = new_var.rename('SOIL_MM_' + str(layer + 1))
        ncroute = xr.merge([ncroute, new_var])

    for layer in soil_layers:
        new_var = ncland['SOIL_WM'].sel(soil_layers_stag=layer)
        new_var = new_var.rename('SOIL_WM_' + str(layer + 1))
        if 'y_2' in new_var.dims:
            new_var = new_var.rename({'y_2': 'y'})
        ncland = xr.merge([ncland, new_var])

    new_data_sets = xr.Dataset()

    rain_rate = np.array(ncland['RAINRATE'].values)

    for var in variables:

        ############################
        ###### Scenario 1 ##########
        if var in inf_land_var:
            subset = ncland[var]
            if var == 'RAINRATE':
                subset = ncland[var] * 3600

            if var == 'QSNOW':
                subset = ncland[var] * 3600

            if np.argwhere(np.isnan(subset.values)).any():
                print('%s has NaN values.' % var)

            else:
                subset = ncland[var]

        elif var in inf_runoff_var:
            subset = ncroute[var]

            if np.argwhere(np.isnan(subset.values)).any():
                print('%s has NaN values.' % var)

        else:
            print('%s not found in either ncland or ncroute.' % var)

        new_data_sets = xr.merge([subset, new_data_sets], join="override")
    print(new_data_sets)

    rain_rate_2 = np.array(ncland['RAINRATE'].values)

    print("rain_rate == rain_rate_2: ", np.allclose(rain_rate, rain_rate_2))

    if np.isclose(rain_rate, rain_rate_2, rtol=1e-9, atol=1e-9).all():
        print("The two arrays are equal.")
    else:
        print("The two arrays are not equal.")
    return new_data_sets


# Get the hourly values of influential variables from Model Inputs
def get_daily_values_from_nwm(land_output, runoff_output, variables):
    # Land/routing file
    # Split influential variables into the land and runoff variables
    inf_land_var = []
    inf_runoff_var = []

    for var in variables:
        if var in land_vars:
            inf_land_var.append(var)
        elif var in runoff_vars:
            inf_runoff_var.append(var)
        elif var.lower() in {'zwattablrt', 'sfhd', 'qqsfc_acc', 'qqsub_acc'}:
            inf_runoff_var.append(var)
        else:
            print(
                'Influential variable: {0:s} is not included in model output'.format(var))
            exit()

    # Get daily values of influential variables
    daily_values = get_daily_values(
        land_output, runoff_output, variables, inf_land_var, inf_runoff_var)

    return daily_values


def predict_runoff(file_path, datasets, variables):
    # check if all variables are in datasets
    datasets_df = datasets.to_dataframe()
    colnames = datasets_df.columns.to_list()

    # print(datasets_df[variables[::-1]])

    if not all(col in colnames for col in variables):
        print('not all variables appear in the data set')
        exit()

    # load the classification model - predict occurrence and its probabilty of the daily EOF runoff
    occ_mod_name = file_path + "clas.joblib.dat"

    cv_occ_mod = load(occ_mod_name)
    # print(cv_occ_mod)

    # data for occurrence prediction
    val_c_xv = datasets_df[variables[::-1]]

    # print(val_c_xv)
    # print(np.where(val_c_xv.values > 0))
    # print(val_c_xv.values[570][0])

    # predict the occurrence of the EOF events (0 or 1) using the trained XGBoost classification trees
    val_c_yv_ev = cv_occ_mod.predict(val_c_xv)

    # predict the occurrence probability of the EOF events [0-1] (the probability is the values of the 1st column)
    val_c_yv_mod = cv_occ_mod.predict_proba(val_c_xv)[:, 1]
    # val_c_yv_mod = cv_occ_mod.predict_proba(val_c_xv)

    # load the regression model - predict runoff magnitude
    reg_mod_name = file_path + 'reg.joblib.dat'
    cv_reg_mod = load(reg_mod_name)

    # data for magnitude prediction of daily EOF events; Note that the same data is the same as the one used for the occurrence prediction
    val_m_xv = datasets_df[variables[::-1]]
    # print(val_m_xv)

    # predict runoff magnitude using the trained XGBoost regression trees
    val_m_yv_mod = cv_reg_mod.predict(val_m_xv)

    # Event: 0/1 for runoff occurrence; PROB: [0, 1] for occurence probability; RUNOFF: >=0 for the magnitudes of runoff

    # get the order of dimensions in the datasets object
    order = list(datasets.dims.keys())

    # determine the shape of each variable based on the order of dimensions
    event_shape = [datasets.dims[dim] for dim in order]
    prob_shape = [datasets.dims[dim] for dim in order]
    mag_shape = [datasets.dims[dim] for dim in order]

    # reshape the variables based on the order of dimensions
    runoff_event = xr.DataArray(
        data=val_c_yv_ev.reshape(event_shape),
        dims=order, coords=datasets.coords, name='EVENT')

    runoff_prob = xr.DataArray(
        data=val_c_yv_mod.reshape(prob_shape),
        dims=order, coords=datasets.coords, name='PROB')

    runoff_mag = xr.DataArray(
        data=val_m_yv_mod.reshape(mag_shape),
        dims=order, coords=datasets.coords, name='RUNOFF')

    # save the results
    res_runoff = xr.merge(
        [runoff_event, runoff_mag, runoff_prob], join="override")
    # print(res_runoff)

    # res_runoff.rename_vars({'rainrate':'ACCPRCP', 'sfhd':'SFCHEADSUBRT'})
    return res_runoff
