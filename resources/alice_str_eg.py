from alice_blue import *
import time , datetime
import traceback
import math

# user=''
# pwd=''
# secret='' #app secret
# app=''  # app Id
# twofa =''
# access_token = AliceBlue.login_and_get_access_token(username=user, password=pwd, \
#  twoFA=twofa,api_secret=secret,app_id=app)
# alice = AliceBlue(username=username, password=password, access_token=access_token, \
#     master_contracts_to_download=['NSE','NFO'])

username = ''
password = ''
api_secret = ''
twoFA = ''


alice  =None
socket_opened = False
indexLtp = None
strangle = True

def login():
    global alice
    access_token = AliceBlue.login_and_get_access_token(username=username, password=password,\
        twoFA=twoFA,  api_secret=api_secret)
    # alice = AliceBlue(username=username, password=password, access_token=access_token)
    alice = AliceBlue(username=username, password=password, access_token=access_token, \
        master_contracts_to_download=['NSE','NFO'])
    
    def event_handler_quote_update(message):
        try:
            print(message)
            global indexLtp
            indexLtp = message['ltp']
        except Exception as e:
            traceback.print_exc()

    def open_callback():
        global socket_opened
        socket_opened = True

    alice.start_websocket(subscribe_callback=event_handler_quote_update,
                        socket_open_callback=open_callback,
                        run_in_background=True)
    while(socket_opened==False):
        pass
    alice.subscribe(alice.get_instrument_by_symbol('NSE', 'Nifty Bank'), LiveFeedType.MARKET_DATA) 
    time.sleep(5)
    
def place_order (transaction_type,symbol):
    qty = int(symbol.lot_size)
    res= alice.place_order(transaction_type = TransactionType.Sell,
                     instrument = symbol,
                     quantity = qty,
                     order_type = OrderType.Market,
                     product_type = ProductType.Delivery,
                     price = 0.0,
                     trigger_price = None,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
    print(res)


if __name__ == '__main__':
    login()
    time.sleep(10)
    ATMStrike = math.ceil(indexLtp/100)*100
    print(f'ATMStrike : {ATMStrike}')
    awayFromATM = 0
    if strangle:
        awayFromATM = 300
    
    ce_strike = alice.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date=datetime.date(2021, 6, 24), is_fut=False, strike=ATMStrike + awayFromATM, is_CE = True)
    pe_strike = alice.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date=datetime.date(2021, 6, 24), is_fut=False, strike=ATMStrike - awayFromATM, is_CE = False)

    print(ce_strike, pe_strike)

    # place_order(TransactionType.Sell,ce_strike )
    # place_order(TransactionType.Sell,pe_strike )
