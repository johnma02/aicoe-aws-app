import boto3
import subprocess

"""
payload = {
    "day": yyyymmdd
    "day_suffix": int
}

`day` is a datestring specifying the date of the predictions
`day_suffix` is an integer representing ...
0: present day
1: one day after present day ...
etc.

`day_suffix` is appended to the output png's file name.
"""


def lambda_handler(event, context):
    s3 = boto3.client('s3')

    s3.download_file('aicoe-runoff-risk-outputs',
                     event["day"]+"-preds.nc", "/tmp/"+event["day"]+"-preds.nc")

    # Convert NetCDF to GeoTIFF
    input_file = "/tmp/"+event["day"]+"-preds.nc"
    variable_name = "risk_all"

    subdataset = f"NETCDF:\"{input_file}\":{variable_name}"

    subprocess.run(["./generate_projection.sh"] + [subdataset])

    print("Posting projection to S3:")

    s3 = boto3.resource('s3')
    data_put = open("/tmp/output_contour.png", 'rb')
    s3.Bucket(
        'aicoe-runoff-risk-projections').put_object(Key="day"+str(event["day_suffix"])+".png", Body=data_put)

    data_put.close()

    print("Successfully posted projection to S3")
