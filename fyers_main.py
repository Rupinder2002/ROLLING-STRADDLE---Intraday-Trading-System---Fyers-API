import json, os
import pandas as pd
import orders_model
from fyers_api import fyersModel
import order_shooter, chart_trader, symbol_model, orders_model, fyers_auth
import time

fyers = None
def test():
    return('its me working!')
fyers_auth.fyers_login()

def main():
    global fyers
    access_token = open('D:/ProjectT/Quickey/Rolling_SIR/temp/access_token.txt', 'r').read().strip()
    fyers = fyersModel.FyersModel()
#     ############################### Place Orders ######################
#     test_order = orders_model.place_orders()
#     test_order.setSymbol('NSE:SBIN-EQ')
#     test_order.setqty(1)
#     test_order.setside(1)
#     test_order.setType(1)
#     test_order.setlimitPrice(400)
#     jsondata = test_order.getJsonStructure()
#     print(jsondata)
#     response = fyers.place_orders(token=access_token, data = jsondata)
#     print(response)
    ################################ Modify Orders #######################
    # test2_order = orders_model.update_orders('52106188001')
    # test2_order.upd_limitPrice(117)
    # test2_order.upd_stopPrice(128.5)
    # jsondata = test2_order.getJsonStructure()
    # response = fyers.update_orders(token=access_token, data = jsondata)
    # print(response)
    ################################ CANCEL ORDER #########################
    # test3_order = orders_model.cancel_order('52106178668')
    # jsondata = test3_order.getJsonStructure()
    # response = fyers.delete_orders(token=access_token, data = jsondata) 
    #######################################################################
    # response = fyers.positions(token=access_token) # Access positions
    # positions = response['data']['netPositions']
    # print(positions)
    # for position in positions:
    #     if position['netQty'] == 0:
    #         print(f"{position['symbol']} : Closed Position")
    #         continue
    #     exit_pos = orders_model.exit_position(position['id'])
    #     jsondata = exit_pos.getJsonStructure()
    #     response = fyers.exit_positions(token=access_token, data = jsondata)
    #     print (response)
    #########################################################################
    # response = fyers.orders(token = access_token)
    # print(response)
    # orders = response['data']['orderBook']
    # actv_orders = [(order['symbol'], order['id']) for order in orders if order['status'] == 1 \
    #     and order['productType'] =='INTRADAY']
    # print(actv_orders)

    # for order in actv_orders:
    #     symbol = order[0]
    #     if symbol[4:9] == 'NIFTY':
    #         test3_order = orders_model.cancel_order(order[1])
    #         jsondata = test3_order.getJsonStructure()
    #         print(jsondata)
    #     elif symbol[4:13] == 'BANKNIFTY':
    #         test3_order = orders_model.cancel_order(order[1])
    #         jsondata = test3_order.getJsonStructure()
    #         print(jsondata)
    #########################################################
#     t1 = time.process_time()
#     response = fyers.positions(token=access_token) # Access positions
#     positions = response['data']['netPositions']
#     hedge_CE_qty =[]
#     hedge_PE_qty =[]
#     pos_PE_qty =[]
#     pos_CE_qty=[]
#     print(positions)
#     for position in positions:
#         symbol = position['symbol']
#         if symbol[-2:] == 'CE' and position['side'] == 1 and position['netQty'] > 0:
#             hedge_CE_qty.append(position['buyQty'])
#         elif symbol[-2:] == 'PE' and position['side'] == 1 and position['netQty'] > 0:
#             hedge_PE_qty.append(position['buyQty'])
#         elif symbol[-2:] == 'CE' and position['side'] == -1 and position['netQty'] < 0:
#             pos_CE_qty.append(position['sellQty'])
#         elif symbol[-2:] == 'PE' and position['side'] == -1 and position['netQty'] < 0:
#             pos_PE_qty.append(position['sellQty'])
#         continue 
#     print(hedge_CE_qty,hedge_PE_qty,pos_PE_qty, pos_CE_qty)
    
#     if sum(hedge_CE_qty) > sum(pos_CE_qty):
#         qty_tobuy = sum(hedge_CE_qty) - sum(pos_CE_qty)
#         print(f"buy hedge for CE {qty_tobuy}")
#     if sum(hedge_PE_qty) > sum(pos_PE_qty):
#         qty_tobuy = sum(hedge_PE_qty) - sum(pos_PE_qty)
#         print(f"buy hedge for PE {qty_tobuy}")
        
#     t2 = time.process_time()

#     print(f'Took {t2-t1} Seconds')

    response = fyers.positions(token=access_token) # Access positions
    positions = response['data']['netPositions']
    # print(positions)
    actv_positions_ids = [position['id'] for position in positions if abs(position['netQty']) == 0 \
            and position['productType'] !='INTRADAY']
    print(actv_positions_ids)
    # for position in positions:
    #     if position['netQty'] == 0:
    #         print(f"{position['symbol']} : Closed Position")
    #         continue
    #     exit_pos = orders_model.exit_position(position['id'])
    #     jsondata = exit_pos.getJsonStructure()
    #     response = fyers.exit_positions(token=access_token, data = jsondata)
    #     print (response)

if __name__ == '__main__':
    main()