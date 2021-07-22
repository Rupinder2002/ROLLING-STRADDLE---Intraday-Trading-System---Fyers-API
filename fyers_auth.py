import json
from datetime import datetime
import pandas as pd
from fyers_api import fyersModel, accessToken
import sys
import requests
import csv
import re
import logging, config

mainfolder = config.mainfolder
trd_date = datetime.today().strftime('%d_%m_%Y')
LOG_FORMAT = "%(levelname)s %(asctime)s %(name)s - %(message)s"
logging.basicConfig(filename='{}/log/trade_day_{}.log'.format(mainfolder, trd_date),
                    level = logging.DEBUG,
                    format= LOG_FORMAT,
                    filemode = 'a')
logger = logging.getLogger(__name__)

df3 = pd.DataFrame()
symbol_file = '{}/temp/fyers_symbols.csv'.format(mainfolder)
url = 'http://public.fyers.in/sym_details/NSE_FO.csv'
columns = ['instrument', 'name', 'A', 'lot_size', 'tick', 'B', 'C', 'date', 'time', 'symbol', 'D', 'E', 'num', 'symbol_name']
df = pd.read_csv(url, names =columns, header=None)
nms = ['BANKNIFTY', 'NIFTY']
df3 = df[df['symbol_name'].isin(nms)]
df3.to_csv(symbol_file)

def get_token(app_id, app_secret, fyers_id, password, pan_dob):
    appSession = accessToken.SessionModel(app_id, app_secret)
    response = appSession.auth()
    if response["code"] != 200:
        return response
        # sys.exit()

    auth_code = response["data"]["authorization_code"]

    appSession.set_token(auth_code)

    generateTokenUrl = appSession.generate_token()
    # webbrowser.open(generateTokenUrl, new=1)
    headers = {
        "accept": "*/*",
        "accept-language": "en-IN,en-US;q=0.9,en;q=0.8",
        "content-type": "application/json; charset=UTF-8",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "referrer": generateTokenUrl
    }
    payload = {"fyers_id": fyers_id, "password": password,
               "pan_dob": pan_dob, "appId": app_id, "create_cookie": False}
    result = requests.post("https://api.fyers.in/api/v1/token",
                           headers=headers, json=payload, allow_redirects=True)
    if result.status_code != 200:
        logger.warning('error occurred status code :: ', result.status_code)
        return
    # print(result.json())
    result_url = result.json()["Url"]
    token_re = re.search(r'access_token=(.*?)&', result_url, re.I)
    if token_re:
        return token_re.group(1)
    return "error"

def fyers_login():
    try:
        user = json.loads(open('{}/config/userinfo.json'.format(mainfolder), 'r').read().strip())
        # NOTE Contents of userinfo.json
        access_token = get_token(app_id=user['fyers_app_id'], app_secret=user['fyers_app_secret'],
                                fyers_id=user['fyers_id'], password=user['fyers_password'], pan_dob=user['fyers_pan_or_dob'])
        try:
            fyers = fyersModel.FyersModel()
            fyers.positions(token=access_token)
            with open('{}/temp/access_token.txt'.format(mainfolder), 'w') as wr1:
                wr = csv.writer(wr1)
                wr.writerow([access_token])
            logger.info("Fyers Login Successfull")
            print("Fyers Login Successfull")
        except:
            logger.critical("Error logging into Fyers")
            sys.exit("Login Failed for Fyers")
    except:
        logger.critical("Error logging into Fyers")
        sys.exit("Login Failed for Fyers")

def fetch_fyers_token():
    # access_token = open('{}/temp/access_token.txt'.format(mainfolder), 'r').read().strip()
    access_token = open('{}/temp/access_token.txt'.format(config.access_token_loc), 'r').read().strip()
    fyers = fyersModel.FyersModel()
    return fyers, access_token
