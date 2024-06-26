
class tradeInfo(object):
    def __init__(self,tradeOrder,tradeDate,tradeName,tradePrice,quant,entryOrExit):
        self.tradeOrder = tradeOrder
        self.tradeDate = tradeDate
        self.tradeName = tradeName
        self.tradePrice = tradePrice
        self.quant = quant
        self.tradeProfit = 0
        self.cumuProfit = 0
        self.entryOrExit = entryOrExit
#        print("populating info: ",self.tradeName,' ',self.tradePrice)
        
    def calcTradeProfit(self,order,curPos,entryPrice,exitPrice,entryQuant,numShares):
        profit = 0
        totEntryQuant = 0
        tempNumShares = numShares
        numEntriesLookBack = 0
        for numEntries in range(0,len(entryPrice)):
##            totEntryQuant += entryQuant[numEntries]
            if tempNumShares >= entryQuant[numEntries]:
                tempNumShares -= entryQuant[numEntries]
                numEntriesLookBack += 1
        if tempNumShares > 0 : numEntriesLookBack += 1
        tempNumShares = numShares
        for numEntries in range(0,numEntriesLookBack):
            if numEntries < 0:
                numEntries = 1
            if entryQuant[numEntries] < tempNumShares:
                peelAmt = entryQuant[numEntries]
                tempNumShares = tempNumShares - peelAmt
            if entryQuant[numEntries] >= tempNumShares:
                peelAmt = tempNumShares               
            if order == 'buy':
                if curPos < 0:
                    profit = profit + (entryPrice[numEntries] - exitPrice) * peelAmt 
            elif order == 'sell':
                if curPos > 0:               
                    profit = profit + (exitPrice - entryPrice[numEntries]) * peelAmt
            elif order == 'liqLong':
                if curPos > 0:
                    profit = profit + (exitPrice - entryPrice[numEntries]) * peelAmt
            elif order == 'liqShort':
                if curPos < 0:
                    profit = profit + (entryPrice[numEntries] - exitPrice) * peelAmt
            if entryQuant[numEntries] == peelAmt :
                entryPrice.pop(numEntries)
                entryQuant.pop(numEntries)
            elif entryQuant[numEntries] > peelAmt:
                entryQuant[numEntries] = entryQuant[numEntries] - peelAmt
        return profit

    def printTrade(self):
 #       print(repr(self.tradeDate).rjust(8),' ',repr(self.tradeName).ljust(10),' ',repr(self.quant).rjust(2),
 #             ' ',repr(self.tradePrice).rjust(8),' ',repr(self.tradeProfit).rjust(6))
          print( '%8.0f %10s %2.0d %8.5f %10.2f %10.2f' % (self.tradeDate, self.tradeName, self.quant,self.tradePrice,self.tradeProfit,self.cumuProfit))
 #        print( '%8.0f %2d' % (self.tradeDate,self.quant))
