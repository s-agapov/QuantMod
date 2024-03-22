from equityDataClass import equityClass

class systemMarketClass(object):
    def __init__(self):
        self.systemName = ""
        self.symbol = ""
        self.tradesList =list()
        self.equity = equityClass
        self.avgWin = 0
        self.avgLoss = 0
        self.avgTrade = 0
        self.profitLoss = 0
        self.numTrades = 0
        self.maxxDD = 0
        self.clsTrdDD = 0
        self.perWins = 0
    def setSysMarkInfo(self,sysName,symbol,trades,equity):
        self.systemName = sysName
        self.symbol = symbol
        self.tradesList = list(trades)
        self.equity = equity
        temp1 = 0
        temp2 = 0
        temp3 = 0
        temp4 = 0
        temp5 = 0
        temp6 = 0
        temp7 = 0
        temp8 = 0
        temp9 = 0
        temp10 = 0
        numTrades = 0
        for i in range(0,len(self.equity.dailyEquityVal)):
            temp5 = self.equity.dailyEquityVal[i]
            temp6 = max(temp6,temp5)
            temp7 = max(temp7,temp6-temp5)
            self.maxxDD = temp7
        for i in range(0,len(self.tradesList)):
            temp8 += self.tradesList[i].tradeProfit
            temp9 = max(temp9,temp8)
            temp10= max(temp10,temp9-temp8)
            self.clsTrdDD = temp10
            if self.tradesList[i].entryOrExit == 1:
                numTrades += 1
            if self.tradesList[i].tradeProfit >= 0:
                temp1 += self.tradesList[i].tradeProfit
                temp2 += 1
            if self.tradesList[i].tradeProfit < 0:
                temp3 += self.tradesList[i].tradeProfit
                temp4 += 1
        if temp2 != 0: self.avgWin = temp1/temp2
        if temp4 != 0: self.avgLoss = temp3/temp4
        if numTrades != 0: self.avgTrade = temp5/numTrades
        self.numTrades =numTrades
        self.profitLoss = temp5
        if numTrades != 0: self.perWins = temp2 / numTrades
        
                
        
        
        
        
