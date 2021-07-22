# import symbol_model
# import trade_model
# import pandas as pd
# import NFO_expiry_calc
# import chart_trader
# import time
# from pandas.tseries.offsets import DateOffset

# trade_obj = trade_model.Trade_Inputs()
# trade_detail = trade_obj.get_trade_setting()
# print(trade_detail['instrument'])
# strike = None
# fno_type = 'IDX' #CE, PE & IDX for index

# LTP = symbol_model.get_fno_ltp(trade_detail, fno_type, strike)
# print(LTP)

# df =pd.read_csv('D:/ProjectT/Quickey/Rolling_SIR/temp/fyers_symbols.csv')

# symbol2 = Symbol(inst, exp, strike, opt)
# result = symbol2.get_symbol()
# result2 = symbol2.get_lotsize()

# if not result: #.empty:
#     print("Symbol not avilable")
# else:
#     print(result, result2)

# trade_obj = chart_trader.read_pickle()
# # trade_obj = trade_model.Trade_Inputs()
# # trade_obj.set_straddle_strike(15550)
# trade_obj.set_straddle_strike(15800)
# trade_obj = chart_trader.update_pickle(trade_obj)
# trade_detail = trade_obj.get_trade_setting()
# print(trade_detail)
# trade_obj.add_to_trail_SL('NSE:BANKNIFTY2170135200PE', 25, 35200 , 'PE')
# trade_obj = chart_trader.update_pickle(trade_obj)
#########################################
# df_live = pd.read_csv('D:/ProjectT/Quickey/Rolling_SIR/data/NIFTY_data_23_06_2021.csv')
# df_live['open'] = pd.to_numeric(df_live['open'], errors='coerce')
# df_live['high'] = pd.to_numeric(df_live['high'], errors='coerce')
# df_live['low'] = pd.to_numeric(df_live['low'], errors='coerce')
# df_live['close'] = pd.to_numeric(df_live['close'], errors='coerce')
# df_live['timestamp'] = pd.to_datetime(df_live['timestamp'], errors='coerce')

# def get_data(filename):
#     try:
#         data = pd.read_csv(filename, sep=",", header=None)
#     except:
#         return None
#     data.columns = ["instrument", "timestamp", "minute", "open", "high", "low", "close", "volume"]
#     if data["minute"][0]=="09:08" or data["minute"][0]=="09:09":
#         data = data.iloc[1:]
#     data['open'] = pd.to_numeric(data['open'], errors='coerce')
#     data['high'] = pd.to_numeric(data['high'], errors='coerce')
#     data['low'] = pd.to_numeric(data['low'], errors='coerce')
#     data['close'] = pd.to_numeric(data['close'], errors='coerce')
#     data["timestamp"] = data["timestamp"].map(str) + " " + data["minute"].map(str)
#     data["timestamp"] = data["timestamp"].str.replace(r':', '').astype(str)
#     data['timestamp'] = pd.to_datetime(data['timestamp'], format='%Y%m%d %H%M', errors='coerce')
#     data["timestamp"] = data["timestamp"] + DateOffset(minutes=-1)
#     data = data.drop(columns = ['instrument'])
#     return data

# filename = 'D:/ProjectT/Quickey/Rolling_SIR/data/NIFTY.csv'
# df_live = get_data(filename)
# df_live = pd.read_csv('D:/ProjectT/Quickey/Rolling_SIR/data/NIFTY_data_24_06_2021.csv')
# df_live['open'] = pd.to_numeric(df_live['open'], errors='coerce')
# df_live['high'] = pd.to_numeric(df_live['high'], errors='coerce')
# df_live['low'] = pd.to_numeric(df_live['low'], errors='coerce')
# df_live['close'] = pd.to_numeric(df_live['close'], errors='coerce')
# df_live['timestamp'] = pd.to_datetime(df_live['timestamp'], errors='coerce')

# for i in range(len(df_live)):
#     chart_trader.candle_watch(df_live.iloc[i])
    # time.sleep(1)