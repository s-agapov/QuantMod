from tradeClass import tradeInfo

class exitPosition(object):
    def __init__(self,myExitPrice,myExitDate,tempName,myCurShare,mp,commissions,tradeName,entryPrice,entryQuant,numShares,myBPV,cumuProfit):
        self.myExitPrice = myExitPrice
        self.myExitDate = myExitDate
        self.tempName = tempName
        self.myCurShare = myCurShare
        self.mp = mp
        self.commissions = commissions
        self.tradeName = tradeName
        self.entryPrice = entryPrice
        self.entryQuant = entryQuant
        self.numShares = numShares
        self.myBPV = myBPV
        self.cumuProfit = cumuProfit
        

    def exitTrade(self):
        if self.mp < 0:
            trades = tradeInfo('liqShort',self.myExitDate,self.tempName,self.myExitPrice,self.myCurShares,0)
            profit = trades.calcTradeProfit('liqShort',self.mp,self.entryPrice,self.myExitPrice,self.entryQuant,self.myCurShares) * self.myBPV
            profit = profit - myCurShares *commission
            trades.tradeProfit = profit
            cumuProfit += profit
            trades.cumuProfit = cumuProfit
        if self.mp > 0:
            trades = tradeInfo('liqLong',myExitDate,tempName,myExitPrice,myCurShares,0)
            profit = trades.calcTradeProfit('liqLong',mp,entryPrice,myExitPrice,entryQuant,myCurShares) * myBPV
            profit = profit - myCurShares * commission 
            trades.tradeProfit = profit
            cumuProfit += profit
            trades.cumuProfit = cumuProfit
        curShares = 0
        for remShares in range(0,len(entryQuant)):
            curShares += entryQuant[remShares]
        return (profit,trades,curShares)
