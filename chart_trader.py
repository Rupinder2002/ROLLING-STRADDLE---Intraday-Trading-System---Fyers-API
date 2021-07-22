import sys, time, os
from datetime import datetime
import dill as pickle
import trade_model
import fyers_auth, symbol_model, order_shooter
import playsound
import logging, config
import numpy as np

mainfolder = config.mainfolder
trd_date = datetime.today().strftime('%d_%m_%Y')
LOG_FORMAT = "%(levelname)s %(asctime)s %(name)s - %(message)s"
logging.basicConfig(filename='{}/log/trade_day_{}.log'.format(mainfolder, trd_date),
                    level = logging.DEBUG,
                    format= LOG_FORMAT,
                    filemode = 'a')
logger = logging.getLogger(__name__)
# Silence other loggers
for log_name, log_obj in logging.Logger.manager.loggerDict.items():
     if log_name != __name__:
          log_obj.disabled = True

can_lows = []
can_highs = []

def set_low_highs(tf, new_low, new_high):
    global can_lows
    global can_highs
    can_lows = []
    can_highs = []
    for _ in range(tf):
        can_lows.append(new_low)
        can_highs.append(new_high)

def is_candle_tf(trt, tf):
    trt1 = trt.split(':')
    tr2 = ((int(trt1[0]) * 60) + int(trt1[1]))/tf
    if tr2.is_integer():
        return True
    return False

tick_round = lambda x: round(0.05*round(x/0.05), 2)

def read_pickle():
    readfile = open('{}/temp/trade_obj.obj'.format(mainfolder),'rb')
    trade_obj = pickle.load(readfile)
    readfile.close()
    return trade_obj

def update_pickle(trade_obj):
    writefile = open('{}/temp/trade_obj.obj'.format(mainfolder),'wb')
    pickle.dump(trade_obj,writefile)
    writefile.close()
    return trade_obj

def fetch_positions(trade_detail):
    try:
        ret_positions =[]
        fyers, access_token = fyers_auth.fetch_fyers_token()
        open_response = fyers.positions(token=access_token) # Access positions
        positions = open_response['data']['netPositions']
        for position in positions:
            symbol = position['symbol']
            if symbol[4:9] == trade_detail['instrument']: #checks if NIFTY option positions
                ret_positions.append(position)
            elif symbol[4:13] == trade_detail['instrument']: #checks if BANKNIFTY option positions
                ret_positions.append(position)
        return ret_positions
    except:
        print("Glitch fetching positions")
        logger.warning("Glitch fetching positions")
        return fetch_positions(trade_detail)

def fetch_orders(trade_detail):
    try:
        ret_orders = []
        fyers, access_token = fyers_auth.fetch_fyers_token()
        response = fyers.orders(token = access_token)
        orders = response['data']['orderBook'] #Access order book
        for order in orders:
            symbol = order['symbol']
            if symbol[4:9] == trade_detail['instrument']: #checks if NIFTY option orders
                ret_orders.append(order)
            elif symbol[4:13] == trade_detail['instrument']: #checks if BANKNIFTY option orders
                ret_orders.append(order)
        return ret_orders
    except:
        print("Glitch fetching orders")
        logger.warning("Glitch fetching orders")
        return fetch_orders(trade_detail)

def candle_watch(df_live):   
    global can_lows
    global can_highs
    trade_obj = read_pickle()
    trade_detail = trade_obj.get_trade_setting()
    tf = trade_detail['timeframe']
    new_low = df_live['low']
    new_high = df_live['high']
    if not can_highs and not can_lows:
        set_low_highs(tf, new_low, new_high)
    del can_lows[0]
    del can_highs[0]
    can_lows.append(new_low)
    can_highs.append(new_high)
    trade_time = trade_obj.get_trade_time()
    if df_live['timestamp'] >= trade_time['end']:
        square_off_all(trade_obj, df_live['close'], df_live['minute'])
    elif min(can_lows) < trade_detail['cross_low']:
        low_tim = df_live['minute'] #for simulation
        if isinstance(trade_detail['cross_low'], float): #Roll Down
            logger.info(f"Breaking prev recorded low @ {low_tim}")
            prev3_strike = trade_detail['prev2_strike'] #set prev3
            prev2_strike = trade_detail['prev_strike'] #set prev2
            prev_strike = trade_detail['straddle_strike'] #set prev
            new_strike = trade_model.Trade_Inputs.define_strike(trade_detail['strdl_range'], df_live['close'])
            trade_obj.set_straddle_strike(new_strike)
            trade_obj.set_trd_action('rolldown')
            trade_obj.set_strike_history(prev_strike, prev2_strike, prev3_strike)
            logger.info(f"Rolling down the straddle to {new_strike}; Range: {trade_detail['strdl_range']}; 1min crossed dwn @ {df_live['minute']}")
            print(f"Rolling down the straddle to {new_strike}; Range: {trade_detail['strdl_range']}; 1min crossed dwn @ {df_live['minute']}")
            set_low_highs(tf, new_low, new_high)
            trade_obj = update_pickle(trade_obj)
            trade_obj = bro_trader(trade_obj)
            pass
        elif is_candle_tf(str(df_live['minute']), tf):
            now_low = min(can_lows)
            low_tim = df_live['minute']
            prev_low = trade_detail['cross_low']
            trade_obj.set_cross_low(now_low)
            update_pickle(trade_obj)
            logger.info(f'Went below @ {low_tim} crossing {prev_low} and made new {tf}min low {now_low}')
            print(f'Went below @ {low_tim} crossing {prev_low} and made new {tf}min low {now_low}')
            pass
    elif max(can_highs) > trade_detail['cross_high']:
        high_tim = df_live['minute']
        if isinstance(trade_detail['cross_high'], float): #Roll UP
            logger.info(f'Breaking prev recorded high @ {high_tim}')
            prev3_strike = trade_detail['prev2_strike']
            prev2_strike = trade_detail['prev_strike']
            prev_strike = trade_detail['straddle_strike']
            new_strike = trade_model.Trade_Inputs.define_strike(trade_detail['strdl_range'], df_live['close'])
            trade_obj.set_straddle_strike(new_strike)
            trade_obj.set_trd_action('rollup')
            trade_obj.set_strike_history(prev_strike, prev2_strike, prev3_strike)
            logger.info(f"Rolling up the straddle to {new_strike}; Range: {trade_detail['strdl_range']}; 1min crossed up @ {df_live['minute']}")
            print(f"Rolling up the straddle to {new_strike}; Range: {trade_detail['strdl_range']}; 1min crossed up @ {df_live['minute']}")
            set_low_highs(tf, new_low, new_high)
            trade_obj = update_pickle(trade_obj)
            trade_obj = bro_trader(trade_obj)
            pass
        elif is_candle_tf(df_live['minute'], tf):
            now_high = max(can_highs)
            high_tim = df_live['minute']
            prev_high = trade_detail['cross_high']
            trade_obj.set_cross_high(now_high)
            update_pickle(trade_obj)
            logger.info(f'Went above @ {high_tim} crossing {prev_high} and made new {tf}min high {now_high}')
            print(f'Went above @ {high_tim} crossing {prev_high} and made new {tf}min high {now_high}')
            pass
    fyers, access_token = fyers_auth.fetch_fyers_token()
    try:
        total_positions = fetch_positions(trade_detail)
        SLM_handler(trade_obj, total_positions, fyers, access_token)
        TPnL = sum([position['realized_profit'] for position in total_positions]) + sum([position['unrealized_profit'] for position in total_positions])
        if TPnL < (trade_detail['max_loss'] * (-3)):
            print(f"Oops Exceeded Maximum Loss for the Day, stopping for the day @ {df_live['minute']}")
            logger.info(f"Oops Exceeded Maximum Loss for the Day, stopping for the day @ {df_live['minute']}")
            square_off_all(trade_obj, df_live['close'], df_live['minute'])
        print(f"Last Checked candle: {df_live['minute']}; TPnL : {TPnL}")
    except:
        print(f"Last Checked candle: {df_live['minute']} with some error")
    return "OK"

def bro_trader(trade_obj):
    trade_detail = trade_obj.get_trade_setting()
    fyers, access_token = fyers_auth.fetch_fyers_token()
    positions = fetch_positions(trade_detail)  # Access positions
    actv_short_positions = [position for position in positions if position['netQty'] < 0 \
            and position['productType'] =='INTRADAY' and position['segment'] == 'D']
    if trade_detail['trd_action'] =='squareoff':
        now = datetime.today() #Enable if hedge position conversion is required.
        wk_day = now.weekday()
        if wk_day == 3 or wk_day == 4:
            all_positions = [position for position in positions if abs(position['netQty']) > 0 and position['segment'] == 'D']
            sorted_posi = sorted(all_positions, key=lambda all_pos: all_pos['side'])
            for position in sorted_posi:
                order_shooter.exit_position(position['id'], fyers, access_token)
                continue
            pass
        else:
            for position in actv_short_positions:
                order_shooter.exit_position(position['id'], fyers, access_token)
                continue
            # order_shooter.convert_hedge_to_MARGIN(trade_detail, fyers, access_token)
            pass
        order_shooter.cancel_all_pending_orders(trade_detail, fyers, access_token)
        trade_obj.set_trd_action('eodclosed')
        trade_obj = update_pickle(trade_obj)
        return trade_obj
    else:
        new_strike = trade_detail['straddle_strike']
        prev_strike = trade_detail['prev_strike']
        # prev2_strike = trade_detail['prev2_strike']
        prev3_strike = trade_detail['prev3_strike']
        prev_PE_obj = symbol_model.Symbol(trade_detail, prev_strike, 'PE')
        prev_PE = prev_PE_obj.get_symbol()
        prev_CE_obj = symbol_model.Symbol(trade_detail, prev_strike, 'CE')
        prev_CE = prev_CE_obj.get_symbol()
        lotsize = prev_CE_obj.get_lotsize()
        for position in actv_short_positions: #updating the existing positions.
            if trade_detail['trd_action'] == 'rollup':
                if position['symbol'] == prev_CE:
                    try:
                        order_shooter.cancel_pending_order(position['symbol'], fyers, access_token)
                        order_shooter.exit_position(position['id'], fyers, access_token)
                    except:
                        logger.warning("No open previous CE position to exit")
                        pass
                elif position['symbol'] == prev_PE: #Taking hedge for naked PE position
                    new_qty = lotsize * trade_detail['lots']
                    # Hedge_checker(trade_detail, 'PE', new_qty, fyers, access_token)
                    pass
                if prev3_strike !=0 and new_strike != prev3_strike:
                    prev3_PE_obj = symbol_model.Symbol(trade_detail, prev3_strike, 'PE')
                    prev3_PE = prev3_PE_obj.get_symbol()
                    if position['symbol'] == prev3_PE:
                        try:
                            order_shooter.cancel_pending_order(position['symbol'], fyers, access_token)
                            order_shooter.exit_position(position['id'], fyers, access_token)
                        except:
                            pass
                else:
                    pass
            elif trade_detail['trd_action'] == 'rolldown':
                if position['symbol'] == prev_PE:
                    try:
                        order_shooter.cancel_pending_order(position['symbol'], fyers, access_token)
                        order_shooter.exit_position(position['id'], fyers, access_token)
                    except:
                        logger.warning("No open previous PE position to exit")
                        pass
                elif position['symbol'] == prev_CE: #Taking hedge for naked PE position
                    new_qty = lotsize * trade_detail['lots']
                    # Hedge_checker(trade_detail, 'CE', new_qty, fyers, access_token)
                    pass
                if prev3_strike != 0 and new_strike != prev3_strike:
                    prev3_CE_obj = symbol_model.Symbol(trade_detail, prev3_strike, 'CE')
                    prev3_CE = prev3_CE_obj.get_symbol()
                    if position['symbol'] == prev3_CE:
                        try:
                            order_shooter.cancel_pending_order(position['symbol'], fyers, access_token)
                            order_shooter.exit_position(position['id'], fyers, access_token)
                        except:
                            pass
                else:
                    pass
            continue
        opt_qty = trade_detail['lots'] * lotsize
        open_positions = [position['symbol'] for position in actv_short_positions]
        new_PE_obj = symbol_model.Symbol(trade_detail, new_strike, 'PE')
        new_PE = new_PE_obj.get_symbol()
        new_CE_obj = symbol_model.Symbol(trade_detail, new_strike, 'CE')
        new_CE = new_CE_obj.get_symbol()
        order_ids = []
        if new_PE not in open_positions:
            order_id = order_shooter.market_sell_order(new_PE, opt_qty, fyers, access_token)
            order_ids.append(order_id)
            print(f"Placed rollover straddle PE order; {order_id}")
            logger.info(f"Placed rollover straddle PE order; {order_id}")
            pass
        else:
            orders = fetch_orders(trade_detail)
            sl_price = [order for order in orders if order['symbol']== new_PE and order['type']==3 and order['status']==6]
            ltp = symbol_model.get_fno_ltp(trade_detail, 'PE', new_strike)
            sell_prc = ltp + (trade_detail['max_loss'] / opt_qty)
            update_SL = tick_round(sell_prc)
            order_shooter.update_SLM__sell_price(sl_price[0]['id'], opt_qty, update_SL, fyers, access_token)
            logger.info(f"Modified max loss for existing PE pair; {new_PE}")
            pass
        if new_CE not in open_positions:
            order_id = order_shooter.market_sell_order(new_CE, opt_qty, fyers, access_token)
            order_ids.append(order_id)
            print(f"Placed rollover straddle CE order; {order_id}")
            logger.info(f"Placed rollover straddle CE order; {order_id}")
            pass
        else:
            orders = fetch_orders(trade_detail)
            sl_price = [order for order in orders if order['symbol']== new_PE and order['type']==3 and order['status']==6]
            ltp = symbol_model.get_fno_ltp(trade_detail, 'CE', new_strike)
            sell_prc = ltp + (trade_detail['max_loss'] / opt_qty)
            update_SL = tick_round(sell_prc)
            order_shooter.update_SLM__sell_price(sl_price[0]['id'], opt_qty, update_SL, fyers, access_token)
            logger.info(f"Modified max loss for existing CE pair; {new_CE}")
            pass
        time.sleep(2)
        try:
            resp = fyers.tradebook(token = access_token)
            trades = resp['data']['tradeBook']
            for order in order_ids:
                ord_info = [{'symbol' : trade['symbol'],'trd_prc' : trade['tradePrice']} for trade in trades if trade['orderNumber'] == order\
                            and trade['transactionType'] == 'SELL']
                sell_prc = ord_info[0]['trd_prc'] + (trade_detail['max_loss'] / opt_qty)
                sell_price = tick_round(sell_prc)
                slm_id = order_shooter.place_SLM_for_sell(ord_info[0]['symbol'], opt_qty, sell_price, fyers, access_token)
                print(f"placed SLM for rollover {slm_id}")
                continue
        except:
            print("Something went wrong while placing SLMs for new straddle")
            pass
        trade_obj.set_trd_action('active')
        trade_obj = update_pickle(trade_obj)
        playsound.playsound('{}/notify/rollover.wav'.format(mainfolder), True)
        return trade_obj

def Hedge_checker(trade_detail, opt_type, new_qty, fyers, access_token):
    positions = fetch_positions(trade_detail)
    hedge_CE_qty = []
    hedge_PE_qty = []
    pos_PE_qty = []
    pos_CE_qty = []
    for position in positions:
        symbol = position['symbol']
        if symbol[-2:] == 'CE' and position['side'] == 1 and position['netQty'] > 0:
            hedge_CE_qty.append(abs(position['netQty']))
        elif symbol[-2:] == 'PE' and position['side'] == 1 and position['netQty'] > 0:
            hedge_PE_qty.append(abs(position['netQty']))
        elif symbol[-2:] == 'CE' and position['side'] == -1 and position['netQty'] < 0:
            pos_CE_qty.append(abs(position['netQty']))
        elif symbol[-2:] == 'PE' and position['side'] == -1 and position['netQty'] < 0:
            pos_PE_qty.append(abs(position['netQty']))
        continue
    if opt_type == 'CE':
        if sum(hedge_CE_qty) < (sum(pos_CE_qty) + new_qty):
            otm_CE = symbol_model.findotm_buys(trade_detail, 'CE')
            req_qty = sum(pos_CE_qty) + new_qty - sum(hedge_CE_qty)
            order_id = order_shooter.market_buy_order(otm_CE['name'], req_qty, fyers, access_token)
            print("Hedge for Naked CE leg Taken")
            logger.info(f"Naked CE Hedge order placed : {order_id}")
        else:
            print("hedge not required for CE")
            return None
    if opt_type == 'PE':
        if sum(hedge_PE_qty) < (sum(pos_PE_qty) + new_qty):
            otm_PE = symbol_model.findotm_buys(trade_detail, 'PE')
            req_qty = sum(pos_PE_qty) + new_qty - sum(hedge_PE_qty)
            order_id = order_shooter.market_buy_order(otm_PE['name'], req_qty, fyers, access_token)
            print("Hedge for Naked PE leg Taken")
            logger.info(f"Naked PE Hedge order placed : {order_id}")
        else:
            print("hedge not required for PE")
            return None

def SLM_updater(orders, symbol, trade_detail, opt, strike, qty, fyers, access_token):
    sl_price = [order for order in orders if order['symbol']== symbol and order['type']==3 and order['status']==6]
    ltp = symbol_model.get_fno_ltp(trade_detail, opt, strike)
    if ltp > 0:
        x = trade_detail['trail_perc']/10
        new_sl = ltp * (1 + (x-1)/np.sqrt(ltp))
        upd_sl = min(sl_price[0]['stopPrice'], new_sl)
        update_SL = tick_round(upd_sl)
        if update_SL != sl_price[0]['stopPrice']:
            order_shooter.update_SLM__sell_price(sl_price[0]['id'], qty, update_SL, fyers, access_token)
    else:
        pass

def SLM_handler(trade_obj, total_positions, fyers, access_token):
    try:
        trade_detail = trade_obj.get_trade_setting()
        active_positions = [position for position in total_positions if abs(position['netQty']) > 0 \
            and position['productType'] =='INTRADAY' and position['segment'] == 'D' and position['side'] == -1]
        orders = fetch_orders(trade_detail)
        alone = []
        for position in active_positions:
            symbol = position['symbol']
            strike = int(symbol[-7:-2])
            opt = symbol[-2:]
            qty = abs(position['netQty'])
            if strike != trade_detail['straddle_strike']:
                SLM_updater(orders, symbol, trade_detail, opt, strike, qty, fyers, access_token)
            else:
                strike_opt = (position['symbol'], opt, strike, qty)
                alone.append(strike_opt)
            continue
        if len(alone) == 1:
            SLM_updater(orders, alone[0][0], trade_detail, alone[0][1], alone[0][2], alone[0][3], fyers, access_token)
        else:
            pass
        return 'ok'
    except:
        logger.warning("Trail SL Fail")
        return None

def square_off_all(trade_obj, close, minu):
    trade_obj.set_trd_action('squareoff')
    trade_obj = update_pickle(trade_obj)
    trade_obj = bro_trader(trade_obj)
    trade_detail = trade_obj.get_trade_setting()
    print(f"All Orders sent to close at {close} @ {minu}")
    logger.info(f"All Orders sent to close at {close} @ {minu}")
    closed_positions = fetch_positions(trade_detail)  # Access positions
    PnL = sum([position['realized_profit'] for position in closed_positions])
    if PnL > 0:
        logger.info(f"Had a nice day Trading we made Rs{PnL}/- Profit Today in {trade_detail['instrument']}")
        print(f"Had a nice day Trading we made Rs{PnL}/- Profit Today in {trade_detail['instrument']}")
        playsound.playsound('{}/notify/profit_day_end.wav'.format(mainfolder), True)
        pass
    elif PnL < 0:
        logger.info(f"Had a rough day Trading we made Rs{abs(PnL)}/- Loss Today in {trade_detail['instrument']}")
        print(f"Had a rough day Trading we made Rs{abs(PnL)}/- Loss Today in {trade_detail['instrument']}")
        playsound.playsound('{}/notify/loss_day_end.wav'.format(mainfolder), True)
        pass
    os.remove('{}/temp/trade_obj.obj'.format(mainfolder)) #disable for post market analysis
    logger.info(80*"=")
    sys.exit("Bye! Bye! see you Next Trading day")