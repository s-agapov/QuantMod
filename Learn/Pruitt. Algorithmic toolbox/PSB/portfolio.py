from systemMarket import systemMarketClass

class portfolioClass(object):
    def __init__(self):
        self.portfolioName = ""
        self.systemMarkets = list()
        self.portEquityDate = list()
        self.portEquityVal = list()
        self.portclsTrdEquity = list()
        self.portDailyEquityVal = list()
        self.portPeakEquity = 0
        self.portMinEquity = 0
        self.portMaxDD = 0
        tempEqu = 0
        cumEqu = 0
        maxEqu = -999999999
        minEqu = 999999999
        maxDD = 0
    
    def setPortfolioInfo(self,name,systemMarket):
        self.portfolioName = name
        self.systemMarkets = list(systemMarket)
        masterDateList = list()
        monthList = list()
        monthEquity = list()
        combinedEquity = list()
        self.portPeakEquity = -999999999999
        self.portMinEquity = -999999999999

        fileName1 = self.systemMarkets[0].systemName + "-Composite.txt"
        target1 = open(fileName1,"w")
        begDate = 99999999
        endDate = 0
        for i in range(0,len(self.systemMarkets)):
            if(self.systemMarkets[i].equity.equityDate[0] < begDate):
                begDate = self.systemMarkets[i].equity.equityDate[0]
            if(self.systemMarkets[i].equity.equityDate[-1] > endDate):
               endDate = self.systemMarkets[i].equity.equityDate[-1]
            
        for i in range(0,len(self.systemMarkets)):
            masterDateList += self.systemMarkets[i].equity.equityDate
            sysName = self.systemMarkets[i].systemName
            market = self.systemMarkets[i].symbol
            avgWin = self.systemMarkets[i].avgWin
            sysMark =self.systemMarkets[i]
            avgLoss = sysMark.avgLoss
            totProf = sysMark.profitLoss
            totTrades = sysMark.numTrades
            maxD = sysMark.maxxDD
            clsTrdDD = sysMark.clsTrdDD
            perWins = sysMark.perWins
            tempStr =''
            if len(sysName) < 15 :
                for j in range(0,15 - len(sysName)):
                    sysName = sysName + ' '                   
            if len(sysName) > 15: sysName = sysName[0:12]+'...'            
            if i == 0:
                print('SysName         Market TotProfit  MaxDD ClsTrdDD AvgWin AvgLoss PerWins TotTrades')
                print('---------------------------------------------------------------------------------')
                lineOutPut = 'Testing from : ' + str(begDate) + ' to: ' + str(endDate) + '\n'
                target1.write(lineOutPut)
                lineOutPut = '---------------------------------------------------------------------------------\n'
                target1.write(lineOutPut)
                lineOutPut = 'SysName         Market TotProfit  MaxDD ClsTrdDD AvgWin AvgLoss PerWins TotTrades\n'
                target1.write(lineOutPut)
            print('%s %-6s %9d %6d  %6d  %5d   %5d    %3.2f      %4d' % (sysName,market,totProf,maxD,clsTrdDD,avgWin,avgLoss,perWins,totTrades))
            target1.write('%s %-6s %9d %6d  %6d  %5d   %5d    %3.2f      %4d\n' % (sysName,market,totProf,maxD,clsTrdDD,avgWin,avgLoss,perWins,totTrades))
        print('---------------------------------------------------------------------------------')
        lineOutPut = '---------------------------------------------------------------------------------\n'
        target1.write(lineOutPut)
        masterDateList = removeDuplicates(masterDateList)
        masterDateList = sorted(masterDateList)
        self.portEquityDate = masterDateList
        monthList = createMonthList(masterDateList)
        pEquityTuple = list()
        numDaysInMList = len(masterDateList)
        for i in range(0,len(masterDateList)):
            cumuVal = 0
            for j in range(0,len(self.systemMarkets)):
                skipDay = 0
                try:
                    idx = self.systemMarkets[j].equity.equityDate.index(masterDateList[i])
                except ValueError:
                    skipDay = 1
                    marketDayCumu = 0
                    skipDate = masterDateList[i]
                    skipMkt = self.systemMarkets[j].symbol
                    numDaysInEquityStream = len(self.systemMarkets[j].equity.dailyEquityVal)
                    marketBeginDate = self.systemMarkets[j].equity.equityDate[0]
                    if (masterDateList[i] > marketBeginDate and i < numDaysInEquityStream):                        
                        marketDayCumu = self.systemMarkets[j].equity.dailyEquityVal[i-1]
                    else:
                        if masterDateList[i] < marketBeginDate:
                            marketDayCumu = 0
                        else:
                            marketDayCumu = self.systemMarkets[j].equity.dailyEquityVal[-1]
                    pEquityTuple += ((i,j,marketDayCumu),)
                    cumuVal += marketDayCumu
                if skipDay == 0:
                    marketDayCumu = self.systemMarkets[j].equity.dailyEquityVal[idx]
                    pEquityTuple += ((i,j,marketDayCumu),)
                    cumuVal += self.systemMarkets[j].equity.dailyEquityVal[idx]
            combinedEquity.append(cumuVal)
            self.portEquityVal.append(cumuVal)
            if cumuVal > self.portPeakEquity: self.portPeakEquity = cumuVal
            self.portMinEquity = max(self.portMinEquity,self.portPeakEquity - cumuVal)
            self.portMaxDD = self.portMinEquity
        tempStr = tempStr + '   '
        print('Totals              %12d %6d' % (self.portEquityVal[-1],self.portMaxDD))
        lineOutPut = 'Totals             '
        target1.write('%-s %12d %6d\n' % (lineOutPut,self.portEquityVal[-1],self.portMaxDD))
        print('-------------------------------------------------------------------')
        lineOutPut = '-------------------------------------------------------------------\n'
        target1.write(lineOutPut)

##        print("Combined Equity: ",self.portEquityVal[-1])
##        lineOutPut = "Combined Equity: "
##        target1.write('%s %7.3f\n' %(lineOutPut,self.portEquityVal[-1]))                  
##        print("Combined MaxDD: ",self.portMaxDD)
##        lineOutPut = "Combined MaxDD: "
##        target1.write('%s %7.3f\n' %(lineOutPut,self.portMaxDD))
        print("Combined Monthly Return")
        print("Date         Profit Cum.Profit")
        lineOutPut = "Combined Monthly Return\n"
        target1.write(lineOutPut) 
        lineOutPut = "Date         Profit Cum.Profit\n"
        target1.write(lineOutPut)
        print('-------------------------------------------------------------------')
        lineOutPut = '-------------------------------------------------------------------\n'
        target1.write(lineOutPut)

                          
        for j in range(0,len(monthList)):
            idx = masterDateList.index(monthList[j])
            if j == 0:
                monthEquity.append(combinedEquity[idx])
                prevCombinedDailyEquity = monthEquity[-1]
            else:
                combinedDailyEquity = combinedEquity[idx]
                monthEquity.append(combinedDailyEquity -  prevCombinedDailyEquity)
                prevCombinedDailyEquity = combinedDailyEquity
            print('%8d %10.0f %10.0f ' % (monthList[j],monthEquity[j],combinedEquity[idx]))
            target1.write('%8d %10.0f %10.0f\n' % (monthList[j],monthEquity[j],combinedEquity[idx]))
        target1.close()
def removeDuplicates(li):
    my_set = set()
    res = []
    for e in li:
        if e not in my_set:
            res.append(e)
            my_set.add(e)
    return res
                  
def createMonthList(li):
    myMonthList = list()
    for i in range(0,len(li)):        
        if i != 0:
            tempa = int(li[i]/100)
            pMonth = int(li[i-1]/100) % 100  
            month = int(li[i]/100) % 100
            if pMonth != month:
                myMonthList.append(li[i-1])
            if i == len(li)-1:
                myMonthList.append(li[i])
    return myMonthList


