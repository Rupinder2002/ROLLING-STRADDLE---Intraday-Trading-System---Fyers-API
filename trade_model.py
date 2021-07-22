from datetime import datetime
import json
import NFO_expiry_calc
import config

#Change your inputs here for setting up the strategy.
# NOTE!!!!
# NIFTY / BANKNIFTY only
# No. of Lots
# Starting time of the strategy
# Closing time of the strategy, closes all the open positions.
# max_loss should max_loss per leg * lots taken * unit straddle range(50-NIFTY / 100-BANKNIFTY)
# trail_perc in percentage, trails this much percentage of the LTP of the option anytime
# for Nifty 50,100,150 (order of 50) for BN 100,200 (order of 100)
mainfolder = config.mainfolder
setup = json.loads(open('{}/config/strat_setup.json'.format(mainfolder), 'r').read().strip())

class Trade_Inputs:
    
    def __init__(self):
        self.weekly_expiry = NFO_expiry_calc.getNearestWeeklyExpiryDate().strftime('%d_%m_%Y') #will be set automatically 
        self.trd_date = datetime.today().strftime('%d_%m_%Y') #will set current date automatically
        self.instrument = setup['instrument']
        self.lots = setup['lots']
        self.start_time = setup['start_time']
        self.end_time = setup['end_time']
        self.max_loss = setup['max_loss']
        self.trail_perc = setup['trail_perc']
        self.timeframe = setup['timeframe']
        self.trd_action = None #will be set automatically
        self.strdl_range = setup['strdl_range']
        self.straddle_strike = 0 #will be set automatically
        self.cross_low = 0 #will be set automatically
        self.cross_high = 0 #will be set automatically
        self.prev_strike = 0 #will be set automatically
        self.prev2_strike = 0 #will be set automatically
        self.prev3_strike = 0 #will be set automatically

    def set_trd_action(self, trd_action):
        self.trd_action = trd_action
        
    def set_straddle_strike(self, straddle_strike):
        self.straddle_strike = int(straddle_strike)
        self.cross_low = int(self.straddle_strike) - int(self.strdl_range)
        self.cross_high = int(self.straddle_strike) + int(self.strdl_range)
        
    def set_cross_low(self, cross_low):
        self.cross_low = float(cross_low)
    
    def set_cross_high(self, cross_high):
        self.cross_high = float(cross_high)

    def set_strike_history(self, prev_strike, prev2_strike, prev3_strike):
        self.prev_strike = prev_strike
        self.prev2_strike = prev2_strike
        self.prev3_strike = prev3_strike

    def remove_trail_position(self, name):
        for i in range(len(self.trail_positions)):
            if self.trail_positions[i]['symbol'] == name:
                del self.trail_positions[i]
                break

    def get_trade_setting(self):
        return json.loads(json.dumps(self.__dict__))

    def get_trade_time(self):
        start = datetime.today().strftime('%Y-%m-%d') +' '+ self.start_time
        end = datetime.today().strftime('%Y-%m-%d') +' '+ self.end_time
        start_time = datetime.strptime(start, '%Y-%m-%d %H:%M')
        end_time = datetime.strptime(end, '%Y-%m-%d %H:%M')
        trade_time = {'start' : start_time, 'end' : end_time}
        return trade_time

    @staticmethod
    def define_strike(strdl_range, start_price):
        return int(strdl_range * round(float(start_price)/strdl_range))