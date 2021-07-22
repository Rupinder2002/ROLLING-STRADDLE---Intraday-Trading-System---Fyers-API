import datetime, time
from datetime import datetime
from pendulum import date
import json
from alice_blue import *
import pandas as pd
from time import localtime, strftime
import threading
import fyers_auth, trade_model, master_start, chart_trader
import csv, json
import playsound
import logging, config

mainfolder = config.mainfolder
trd_date = datetime.today().strftime('%d_%m_%Y')
LOG_FORMAT = "%(levelname)s %(asctime)s %(name)s- %(message)s"
logging.basicConfig(filename='{}/log/trade_day_{}.log'.format(mainfolder, trd_date),
                    level = logging.DEBUG,
                    format= LOG_FORMAT,
                    filemode = 'a')
logger = logging.getLogger(__name__)

logger.info(f"Start Time : {datetime.today()}")
logger.info(80*"=")
playsound.playsound('{}/notify/day_start.wav'.format(mainfolder), True)
trade_obj = trade_model.Trade_Inputs()
trade_obj = chart_trader.update_pickle(trade_obj)
trade_detail = trade_obj.get_trade_setting()
ins = trade_detail['instrument']
print(f"STARTING ROLLING STRADDLE FOR {ins}")
print(f"Start Time : {datetime.today()}")
if  ins == 'NIFTY':
    scrip = 'Nifty 50' #['NIFTY JUN FUT', 'BANKNIFTY JUN FUT']#['Nifty 50', 'Nifty Bank'] #['CRUDEOIL JUN FUT', 'SILVERMIC JUN FUT']
elif ins == 'BANKNIFTY':
    scrip = 'Nifty Bank'
excng = 'NSE' # NFO, NSE, MCX
socket_opened = False
df = pd.DataFrame()
timeframe = 60 # in seconds, 60 for 1min candle DO NOT CHANGE

def event_handler_quote_update(message):
    global df
    timestamp = datetime.fromtimestamp(message['exchange_time_stamp'])
    ltp = message['ltp']
    instrument = message['instrument'].symbol
    exchange = message['instrument'].exchange
    df = df.append({'symbol': instrument, 'timestamp': timestamp, 'ltp':ltp, 'exchange' : exchange}, ignore_index=True)
    
def open_callback():
    global socket_opened
    socket_opened = True
    print("Data Feed Socket Opened")
 
def alice_login():
    try:
        user = json.loads(open('{}/config/userinfo.json'.format(mainfolder), 'r').read().strip())
        access_token = AliceBlue.login_and_get_access_token(username = user['alice_username'], password = user['alice_password'],\
            twoFA = user['alice_twoFA'],  api_secret = user['alice_api_secret'])
        alice = AliceBlue(username = user['alice_username'], password = user['alice_password'], access_token = access_token, \
            master_contracts_to_download= [excng])
        alice.start_websocket(subscribe_callback=event_handler_quote_update,
                            socket_open_callback=open_callback,
                            run_in_background=True)
        while(socket_opened==False):
            pass
        
        alice.subscribe(alice.get_instrument_by_symbol(excng, scrip), LiveFeedType.COMPACT)
        logger.info("Aliceblue Login successfull")
        print("Aliceblue Login successfull")
        return alice
    except:
        logger.error("Error Logging into Aliceblue, Retrying")
        return alice_login()

def createOHLC():
    start = time.time()
    global df
    copydf = df.copy(deep=True).drop_duplicates()
    df = pd.DataFrame()
    getOHLC_df(copydf)
    interval = timeframe - (time.time() - start)
    threading.Timer(interval, createOHLC).start()

def getOHLC_df(df):
    try:
        df = df.sort_values('timestamp')
        timestamp = df['timestamp'].iloc[0].round(freq='1min') #change Frequency according to the timeframe given
        minute = timestamp.strftime('%H:%M')
        sym = df['symbol'].to_list()
        symbol = sym[0]
        openp = df['ltp'].iloc[0]
        closep = df['ltp'].iloc[-1]
        highp = df['ltp'].max()
        lowp = df['ltp'].min()
        exchange = df['exchange'].iloc[0]
        df_live = {'symbol':symbol,
            'exchange':exchange,
            'timestamp':timestamp,
            'minute':minute,
            'open':openp,
            'high':highp,
            'low':lowp,
            'close':closep}
        with open('{}/data/{}_data_{}.csv'.format(mainfolder, ins, trd_date), 'a', newline='') as file:
            fieldnames = ['symbol', 'exchange', 'timestamp', 'minute', 'open', 'high', 'low', 'close']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writerow({'symbol': symbol, 'exchange':exchange, 'timestamp': timestamp, 'minute' : minute,
                'open': openp, 'high': highp, 'low': lowp, 'close': closep})
        chart_trader.candle_watch(df_live)
    except KeyError as e:
        print("Error occured in the flow")
        logger.warning(f"Data Feed Error(Key Error): {e}")

if __name__ == '__main__':
    alice_login()
    fyers_auth.fyers_login()
    trade_obj = master_start.opening_trades(trade_obj)
    chart_trader.update_pickle(trade_obj)
    #########################use when stopping and resuming from middle, only during testing
    # trade_obj.set_straddle_strike(15950)
    # trade_obj = chart_trader.update_pickle(trade_obj)
    # trade_detail = trade_obj.get_trade_setting()
    # print(trade_detail)
    ##############################
    interval = timeframe - datetime.now().second
    time.sleep(interval)
    createOHLC()