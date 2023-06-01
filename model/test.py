from lambda_function import *

payload = {
    'start_year': 2008,
    'start_month': 2,
    'start_day': 1,
    'end_year': 2008,
    'end_month': 2,
    'end_day': 1,
}

lambda_handler(payload, "foo")

