import orders_model, chart_trader
import logging
from datetime import datetime
import sys, config

mainfolder = config.mainfolder
trd_date = datetime.today().strftime('%d_%m_%Y')
LOG_FORMAT = "%(levelname)s %(asctime)s %(name)s - %(message)s"
logging.basicConfig(filename='{}/log/trade_day_{}.log'.format(mainfolder, trd_date),
                    level = logging.DEBUG,
                    format= LOG_FORMAT,
                    filemode = 'a')
logger = logging.getLogger(__name__)

def exit_position(id, fyers, access_token):  
    exit_pos = orders_model.exit_position(id)
    jsondata = exit_pos.getJsonStructure()
    response = fyers.exit_positions(token=access_token, data = jsondata)
    logger.info(f'Exited Positon : {response}')

def convert_hedge_to_MARGIN(trade_detail, fyers, access_token):  #Use for EOD
    """[Converts existing carry forward hedges to Margin by End of Day to use for next day]

    Args:
        trade_detail ([calss obj]): trade_obj attributes to get the information on instrument (NIFTY/BANKNIFTY)
        fyers ([object]): [fyers api object for using any api command]
        access_token ([string]): [access token for login]
    """
    positions = chart_trader.fetch_positions(trade_detail)
    hedge_positions = [(position['symbol'], position['side'], position['buyQty']) for position in positions if position['side'] == 1 and\
                         position['productType'] == 'INTRADAY' and position['segment'] == 'D']
    for pos in hedge_positions:
        conv_pos = orders_model.convert_hedge(pos[0], pos[1], pos[2], 'INTRADAY', 'MARGIN')
        jsondata = conv_pos.getJsonStructure()
        response = fyers.convert_position(token=access_token, data = jsondata)
        logger.info(f'Hedge positons Converted to Margin: {response}')
        continue

def convert_hedge_to_INTRADAY(trade_detail, fyers, access_token): #Use for SOD
    """[Converts existing carry forward hedges from MArgin to Intraday for margin beefits by Start of the Day]

    Args:
        trade_detail ([calss obj]): trade_obj attributes to get the information on instrument (NIFTY/BANKNIFTY)
        fyers ([object]): [fyers api object for using any api command]
        access_token ([string]): [access token for login]
    """
    positions = chart_trader.fetch_positions(trade_detail)
    hedge_positions = [(position['symbol'], position['side'], position['buyQty']) for position in positions if position['side'] == 1 and\
                         position['productType'] == 'MARGIN' and position['segment'] == 'D']
    for pos in hedge_positions:
        conv_pos = orders_model.convert_hedge(pos[0], pos[1], pos[2],'MARGIN', 'INTRADAY')
        jsondata = conv_pos.getJsonStructure()
        response = fyers.convert_position(token=access_token, data = jsondata)
        logger.info(f'Hedge positons Converted to Intraday: {response}')
        continue

def cancel_pending_order(symbol, fyers, access_token):
    response = fyers.orders(token = access_token)
    orders = response['data']['orderBook']
    actv_order = [order for order in orders if order['status'] == 6 \
        and order['productType'] =='INTRADAY' and order['symbol'] == symbol] #position['symbol']]
    for order in actv_order:
        cancel_order = orders_model.cancel_order(order['id'])
        jsondata = cancel_order.getJsonStructure()
        response = fyers.delete_orders(token=access_token, data = jsondata)
        logger.info(f'cancelled order for exit position: {response}')

def cancel_all_pending_orders(trade_detail, fyers, access_token):
    orders = chart_trader.fetch_orders(trade_detail)
    actv_orders = [order['id'] for order in orders if order['status'] == 6 ]
    for id in actv_orders:
        cancel_order = orders_model.cancel_order(id)
        jsondata = cancel_order.getJsonStructure()
        response = fyers.delete_orders(token=access_token, data = jsondata)
        logger.info(f'cancelled order for eod: {response}')
        continue

def market_sell_order(symbol, qty, fyers, access_token):
    sell_order = orders_model.place_orders()
    sell_order.setSymbol(symbol)
    sell_order.setqty(qty)
    sell_order.setside(-1)
    sell_order.setType(2)
    jsondata = sell_order.getJsonStructure()
    response = fyers.place_orders(token=access_token, data = jsondata)
    if response['code'] != 200:
        print(f"Market Sell Order Failed: {response['message']}")
        logger.info(f"Market Sell Order Failed : {response['message']}")
    elif response['code'] == 500:
        print(f"HTTP 500 while placing Mkt Sell Ord: {response['message']}")
        logger.info(f"HTTP 500 while placing Mkt Sell Ord: {response['message']}")
        retry = input("Do you want to retry ? y/n: ")
        if retry == 'y':
            return market_sell_order(symbol, qty, fyers, access_token)
        else:
            sys.exit("Stopping due to order fail!")
    try:
        order_id = response['data']['id']
    except:
        order_id = None
    logger.info(f"Placed market sell order : {response['message']}")
    return order_id

def market_buy_order(symbol, qty, fyers, access_token):
    sell_order = orders_model.place_orders()
    sell_order.setSymbol(symbol)
    sell_order.setqty(qty)
    sell_order.setside(1)
    sell_order.setType(2)
    jsondata = sell_order.getJsonStructure()
    response = fyers.place_orders(token=access_token, data = jsondata)
    if response['code'] == 500:
        print(f"HTTP 500 while placing Mkt Buy Ord: {response['message']}")
        logger.info(f"HTTP 500 while placing Mkt Buy Ord: {response['message']}")
        retry = input("Do you want to retry ? y/n: ")
        if retry == 'y':
            return market_buy_order(symbol, qty, fyers, access_token)
        else:
            sys.exit("Stopping due to order fail!")
    elif response['code'] != 200:
        print(f"Market Buy Order Failed: {response['message']}")
        logger.info(f"Market Buy Order Failed : {response['message']}")
    try:
        order_id = response['data']['id']
    except:
        order_id = None
    logger.info(f"Placed market buy order : {response['message']}")
    return order_id

def place_SLM_for_sell(symbol, qty, stop_price, fyers, access_token):
    SLM_order = orders_model.place_orders()
    SLM_order.setSymbol(symbol)
    SLM_order.setqty(qty)
    SLM_order.setside(1)
    SLM_order.setType(3)
    SLM_order.setstopPrice(stop_price)
    jsondata = SLM_order.getJsonStructure()
    response = fyers.place_orders(token=access_token, data = jsondata)
    if response['code'] == 500:
        print(f"HTTP 500 while placing SLM : {response['message']}")
        logger.info(f"HTTP 500 while placing SLM: {response['message']}")
        retry = input("Do you want to retry ? y/n: ")
        if retry == 'y':
            return place_SLM_for_sell(symbol, qty, stop_price, fyers, access_token)
        else:
            sys.exit("Stopping due to order fail!")
    elif response['code'] != 200:
        print(f"SLM for sell Order Failed: {response['message']}")
        logger.info(f"SLM for sell Order Failed : {response['message']}")
    try:
        order_id = response['data']['id']
    except:
        order_id = None
    logger.info(f"Placed SLM for sellorder : {response['message']}")
    return order_id

def place_SLM_for_buy(symbol, qty, stop_price, fyers, access_token):
    SLM_order = orders_model.place_orders()
    SLM_order.setSymbol(symbol)
    SLM_order.setqty(qty)
    SLM_order.setside(-1)
    SLM_order.setType(3)
    SLM_order.setstopPrice(stop_price)
    jsondata = SLM_order.getJsonStructure()
    response = fyers.place_orders(token=access_token, data = jsondata)
    logger.info(f'Placed SLM for buy order : {response}')
    if response['code'] == 500:
        print(f"HTTP 500 while placing SLM : {response['message']}")
        logger.info(f"HTTP 500 while placing SLM: {response['message']}")
        retry = input("Do you want to retry ? y/n: ")
        if retry == 'y':
            return place_SLM_for_buy(symbol, qty, stop_price, fyers, access_token)
        else:
            sys.exit("Stopping due to order fail!")
    elif response['code'] != 200:
        print(f"SLM for buy Order Failed: {response['message']}")
        logger.info(f"SLM for sell Order Failed : {response['message']}")
    try:
        order_id = response['data']['id']
    except:
        order_id = None
    logger.info(f"Placed SLM for buyorder : {response['message']}")
    return order_id

def update_SLM__sell_price(id, qty, upd_price, fyers, access_token):
    SLM_modify = orders_model.update_orders(id)
    SLM_modify.upd_stopPrice(upd_price)
    SLM_modify.upd_qty(qty)
    jsondata = SLM_modify.getJsonStructure()
    response = fyers.update_orders(token=access_token, data = jsondata)
    logger.info(f'Placed update order : {response}')