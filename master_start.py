from datetime import datetime
import order_shooter, chart_trader
import trade_model, fyers_auth, symbol_model
import time, sys
import logging, config

mainfolder = config.mainfolder
trd_date = datetime.today().strftime('%d_%m_%Y')
LOG_FORMAT = "%(levelname)s %(asctime)s %(name)s - %(message)s"
logging.basicConfig(filename='{}/log/trade_day_{}.log'.format(mainfolder, trd_date),
                    level = logging.DEBUG,
                    format= LOG_FORMAT,
                    filemode = 'a')
logger = logging.getLogger(__name__)

def take_hedge(trade_obj, fyers, access_token):
    trade_detail = trade_obj.get_trade_setting()
    fotm_buy = []
    otm_CE = symbol_model.findotm_buys(trade_detail, 'CE')
    fotm_buy.append(otm_CE)
    otm_PE = symbol_model.findotm_buys(trade_detail, 'PE')
    fotm_buy.append(otm_PE)
    for i in range(len(fotm_buy)):
        opt_name = fotm_buy[i]['name']
        opt_qty = trade_detail['lots'] * fotm_buy[i]['lot_size']
        order_id = order_shooter.market_buy_order(opt_name, opt_qty, fyers, access_token)
        print("Hedge Taken")
        logger.info(f"Hedge order placed : {order_id}")
    return trade_obj

def opening_straddle(trade_obj, fyers, access_token):
    trade_detail = trade_obj.get_trade_setting()
    strdl_range = trade_detail['strdl_range']
    fno_type = 'IDX' #CE, PE & IDX for index
    start_price = symbol_model.get_fno_ltp(trade_detail, fno_type, None) #get index current price
    start_strike = trade_model.Trade_Inputs.define_strike(strdl_range, start_price)
    atmpe_sym = symbol_model.Symbol(trade_detail, start_strike, 'PE')
    atmce_sym = symbol_model.Symbol(trade_detail, start_strike, 'CE')
    atmpe_symbol = atmpe_sym.get_symbol()
    lotsize = atmpe_sym.get_lotsize() 
    atmce_symbol = atmce_sym.get_symbol()
    opt_qty = trade_detail['lots'] * lotsize
    order_input = [(atmpe_symbol, opt_qty),(atmce_symbol, opt_qty)]
    order_ids=[]
    for inpu in order_input:
        order_id = order_shooter.market_sell_order(inpu[0], inpu[1], fyers, access_token)
        order_ids.append(order_id)
        print(f"Placed order for new Straddle: {order_id}")
        continue
    time.sleep(4)
    placing_Straddle_SLM(trade_detail, order_ids, opt_qty, fyers, access_token)
    trade_obj.set_straddle_strike(start_strike)
    trade_obj.set_trd_action('active')
    return trade_obj

def placing_Straddle_SLM(trade_detail, order_ids, opt_qty, fyers, access_token):
    resp = fyers.tradebook(token = access_token)
    trades = resp['data']['tradeBook']
    for order in order_ids:
        try:
            ord_info = [{'symbol' : trade['symbol'],'trd_prc' : trade['tradePrice']} for trade in trades if trade['orderNumber'] == order\
                        and trade['transactionType'] == 'SELL']
            sell_prc = ord_info[0]['trd_prc'] + (trade_detail['max_loss'] / opt_qty)
            sell_price = chart_trader.tick_round(sell_prc)
            slm_id = order_shooter.place_SLM_for_sell(ord_info[0]['symbol'], opt_qty, sell_price, fyers, access_token)
            print(f"Placed SLM for new straddle {slm_id}")
            continue
        except IndexError as ie:
            logger.warning(f"SLM placement for straddle failed!! {ie}")
            retry = input("SLM placement for straddle failed Do you want to retry ? y/n: ")
            if retry == 'y':
                return placing_Straddle_SLM(trade_detail, order_ids, opt_qty, fyers, access_token)
            else:
                sys.exit("SLM placement for straddle failed, check the connectivity")
    return 'ok'

def opening_trades(trade_obj):
    trade_time = trade_obj.get_trade_time()
    start_time = trade_time['start']
    fyers, access_token = fyers_auth.fetch_fyers_token()
    # trade_obj = take_hedge(trade_obj, fyers, access_token)
    # while True:
    #     if start_time <= datetime.now():
    #         relay_trade_obj = opening_straddle(trade_obj, fyers, access_token)
    #         return relay_trade_obj
    #     logger.info(f"waiting for {start_time} to place order")
    #     time.sleep(1)
    #     continue
    ###################################################### carry forward hedging
    now = datetime.today()
    wk_day = now.weekday()
    if wk_day == 0 or wk_day == 4: #should be 0(monday), 4(friday)
        trade_obj = take_hedge(trade_obj, fyers, access_token)
        pass
    else: #Assumes there is a hedge already taken and converts them from Margin to Intraday to start.
        trade_detail = trade_obj.get_trade_setting()
        order_shooter.convert_hedge_to_INTRADAY(trade_detail, fyers, access_token)
        logger.info("converting existing hedge to intraday")
    while True:
        if start_time <= datetime.now():
            relay_trade_obj = opening_straddle(trade_obj, fyers, access_token)
            return relay_trade_obj
        logger.info(f"waiting for {start_time} to place order")
        time.sleep(1)
        continue