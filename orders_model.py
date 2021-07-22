import json

class place_orders:

    def __init__(self):
        self.symbol = None
        self.qty = 0 #lot size multiplied by no. of lots
        self.type = 1 #1:Limit order, 2:Market Order, 3: SLM, 4:SLL
        self.side = 1 #1: Buy, -1: Sell
        self.productType = 'INTRADAY' #CNC, INTRADAY, CO, BO
        self.limitPrice = 0
        self.stopPrice = 0
        self.disclosedQty = 0
        self.validity = 'DAY'
        self.offlineOrder = "False" #True Only for AMO orders
        self.stoploss = 0
        self.takeProfit = 0

    def setSymbol (self, symbol):
        self.symbol = symbol
    
    def setlimitPrice (self, limitPrice):
        self.limitPrice = limitPrice

    def setqty (self, qty):
        self.qty = qty

    def setside (self, side):
        self.side = side

    def setproductType (self, productType):
        self.productType = productType

    def setType(self, type):
        self.type = type

    def setstopPrice(self, stopPrice):
        self.stopPrice = stopPrice

    def setStopLoss(self, stopLoss):
        self.stopLoss = stopLoss

    def setTakeProfit(self, takeProfit):
        self.takeProfit = takeProfit

    def getJsonStructure(self):
        return json.loads(json.dumps(self.__dict__))

class update_orders:
    def __init__(self, id):
        self.id = id
        self.qty = 0
        self.type = 3
        self.limitPrice = 0
        self.stopPrice = 0
    
    def upd_limitPrice (self, limitPrice):
        self.limitPrice = limitPrice

    def upd_qty (self, qty):
        self.qty = qty

    def upd_Type(self, type):
        self.type = type
    
    def upd_stopPrice(self, stopPrice):
        self.stopPrice = stopPrice

    def getJsonStructure(self):
        return json.loads(json.dumps(self.__dict__))

class cancel_order:

    def __init__(self, id):
        self.id = id

    def getJsonStructure(self):
        return json.loads(json.dumps(self.__dict__))

class exit_position:

    def __init__(self, id):
        self.id = id

    def getJsonStructure(self):
        return json.loads(json.dumps(self.__dict__))


class convert_hedge:
    def __init__(self, symbol, side, qty, from_pt, to_pt):
        self.symbol = symbol
        self.positionSide = side
        self.convertQty = qty
        self.convertFrom = from_pt
        self.convertTo = to_pt

    def getJsonStructure(self):
        return json.loads(json.dumps(self.__dict__))

