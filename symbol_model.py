import pandas as pd
import datetime as dt
from datetime import datetime
from pandas.core.indexes.base import Index
from pynse import *
import config, logging
nse = Nse()
# nse.clear_data()

mainfolder = config.mainfolder
trd_date = datetime.today().strftime('%d_%m_%Y')
LOG_FORMAT = "%(levelname)s %(asctime)s %(name)s- %(message)s"
logging.basicConfig(filename='{}/log/trade_day_{}.log'.format(mainfolder, trd_date),
                    level = logging.DEBUG,
                    format= LOG_FORMAT,
                    filemode = 'a')
logger = logging.getLogger(__name__)

class Symbol:
    def __init__(self, trade_detail, strike, opt):
        self.inst = trade_detail['instrument']
        self.exp = trade_detail['weekly_expiry']
        self.strike = strike
        self.opt = opt
    def get_symbol(self):
        symbol_file = '{}/temp/fyers_symbols.csv'.format(mainfolder)
        df3 = pd.read_csv(symbol_file)
        ex_dt = datetime.strptime(self.exp, '%d_%m_%Y').strftime('%y %b %d')
        nome = self.inst + ' ' + ex_dt + ' ' + str(self.strike) + ' ' + self.opt
        row = df3.loc[(df3['name']==nome)]
        symbol = row['symbol'].to_list()
        return symbol[0]
    def get_lotsize(self):
        symbol_file = '{}/temp/fyers_symbols.csv'.format(mainfolder)
        df3 = pd.read_csv(symbol_file)
        ex_dt = datetime.strptime(self.exp, '%d_%m_%Y').strftime('%y %b %d')
        nome = self.inst + ' ' + ex_dt + ' ' + str(self.strike) + ' ' + self.opt
        row = df3.loc[(df3['name']==nome)]
        lot_size = row['lot_size'].to_list()
        return lot_size[0]

def findotm_buys(trade_detail, option_type):
    ins = trade_detail['instrument']
    exp = trade_detail['weekly_expiry']
    expiry = datetime.strptime(exp, "%d_%m_%Y").date()
    BB_NF = {0:(1.8,2.6), 1:(1.5,2.2), 2:(1.25,1.8), 3:(1,1.2), 4:(1.7,2.4)} #optimum nifty otm buy price range(min, max) by days
    BB_BN = {0:(6,9), 1:(4.5,6.5), 2:(3.5,5), 3:(1.3,2), 4:(10,15)} #optimum banknifty otm buy price range(min, max) by days
    now = dt.datetime.today()
    wk_day = now.weekday()
    if ins == 'NIFTY':
        BB = BB_NF[wk_day]
    elif ins == 'BANKNIFTY':
        BB = BB_BN[wk_day]
    df = nse.option_chain(ins, expiry)
    ltp = get_fno_ltp(trade_detail, 'IDX', None)
    wk_day = now.weekday() #0-Mon to 6-sun
    if option_type == 'CE':
        otmce = ltp
        for i in range(len(df)):
            if (df.iloc[i]['CE.lastPrice'] >= BB[0]) and (df.iloc[i]['CE.lastPrice'] <= BB[1]):
                otmce = max(df.iloc[i]['strikePrice'], otmce)
            continue
        otmce_sym = Symbol(trade_detail, otmce, 'CE')
        otmce_symbol = otmce_sym.get_symbol()
        option_lotsize = otmce_sym.get_lotsize()
        fotm_CE_buy = {'name' : otmce_symbol, 'lot_size': option_lotsize}
        return fotm_CE_buy
    elif option_type == 'PE':
        otmpe = ltp
        for i in range(len(df)):
            if (df.iloc[i]['PE.lastPrice'] <= BB[1]) and (df.iloc[i]['PE.lastPrice'] >= BB[0]):
                otmpe = min(df.iloc[i]['strikePrice'], otmpe)
            continue
        otmpe_sym = Symbol(trade_detail, otmpe, 'PE')
        otmpe_symbol = otmpe_sym.get_symbol()
        option_lotsize = otmpe_sym.get_lotsize()
        fotm_PE_buy = {'name' : otmpe_symbol, 'lot_size': option_lotsize}
        return fotm_PE_buy

def get_fno_ltp(trade_detail, fno_type, strike): #fno_types are #CE, PE & IDX for index
    ins = trade_detail['instrument']
    exp = trade_detail['weekly_expiry']
    expiry = datetime.strptime(exp, "%d_%m_%Y").date()
    try:
        if fno_type == 'CE':
            quote = nse.get_quote(ins,Segment.OPT,expiry,OptionType.CE, strike)
            ltp = quote['lastPrice']
        elif fno_type == 'PE':
            quote = nse.get_quote(ins,Segment.OPT,expiry,OptionType.PE, strike)
            ltp = quote['lastPrice']
        elif fno_type == 'IDX':
            if ins == 'NIFTY':
                quote = nse.get_indices(IndexSymbol.Nifty50)
                pnts = quote['last'].to_list()
                ltp = pnts[0]
            elif ins == 'BANKNIFTY':
                quote = nse.get_indices(IndexSymbol.NiftyBank)
                pnts = quote['last'].to_list()
                ltp = pnts[0]
        return ltp
    except:
        logger.error("Glitch fetching FNO ltp")
        return 0