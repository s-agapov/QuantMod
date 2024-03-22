'''/////////////////////////////////////////////////////////////////////////////////
 System Tester.py - programmed by George Pruitt www.georgepruitt.com
 Copyright 2016 by George Pruitt
 Feel free to distribute and improve upon - just include this banner
 Version 1.4 scroll down about half way to get to your system coding section
///////////////////////////////////////////////////////////////////////////////////'''

#--------------------------------------------------------------------------------
#Import Section - inlcude functions, classes, variabels
#from external modules
#--------------------------------------------------------------------------------
import csv
import tkinter as tk
import os.path
from getData import getData
from dataLists import myDate,myTime,myOpen,myHigh,myLow,myClose
from tradeClass import tradeInfo
from equityDataClass import equityClass
from trade import trade
from systemMarket import systemMarketClass
from portfolio import portfolioClass
from indicators import highest,lowest,rsiClass,stochClass,sAverage,bollingerBands
from systemAnalytics import calcSystemResults
from tkinter.filedialog import askopenfilenames
#--------------------------------------------------------------------------------
  #End of Import Section
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
  #Helper Functions local to this module
#--------------------------------------------------------------------------------
def getDataAtribs(dClass):
   return(dClass.bigPtVal,dClass.symbol,dClass.minMove)
def getDataLists(dClass):
   return(dClass.date,dClass.open,dClass.high,dClass.low,dClass.close)
def roundToNearestTick(price,upOrDown,tickValue):
    temp1 = price - int(price)
    temp2 = int(temp1 / tickValue)
    temp3 = temp1 -(tickValue*temp2)
    if upOrDown == 1:
        temp4 = tickValue - temp3
        temp5 = temp1 + temp4
    if upOrDown == -1:
        temp4 = temp1 - temp3
        temp5 = temp4
    return(int(price) + temp5)

def calcTodaysOTE(mp,myClose,entryPrice,entryQuant,myBPV):
    todaysOTE = 0
    for entries in range(0,len(entryPrice)):
        if mp >= 1:
            todaysOTE += (myClose - entryPrice[entries])*myBPV*entryQuant[entries]
        if mp <= -1:
           todaysOTE += (entryPrice[entries] - myClose)*myBPV*entryQuant[entries]
    return(todaysOTE)

def exitPos(myExitPrice,myExitDate,tempName,myCurShares):
    global mp,commission
    global tradeName,entryPrice,entryQuant,exitPrice,numShares,myBPV,cumuProfit
    if mp < 0:
        trades = tradeInfo('liqShort',myExitDate,tempName,myExitPrice,myCurShares,0)
        profit = trades.calcTradeProfit('liqShort',mp,entryPrice,myExitPrice,entryQuant,myCurShares) * myBPV
        profit = profit - myCurShares *commission
        trades.tradeProfit = profit
        cumuProfit += profit
        trades.cumuProfit = cumuProfit
    if mp > 0:
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
#--------------------------------------------------------------------------------
  #End of functions
#--------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
  #Lists and variables are defined and initialized here
#---------------------------------------------------------------------------------
alist, blist, clist, dlist, elist = ([] for i in range(5))
marketPosition,listOfTrades,trueRanges,ranges = ([] for i in range(4))
dataClassList,systemMarketList,equityDataList = ([] for i in range(3))
entryPrice,fileList,entryPrice,entryQuant,exitQuant = ([] for i in range(5))
#exitPrice = list()
currentPrice = 0
totComms = 0
barsSinceEntry = 0
numRuns = 0
myBPV = 0
allowPyr = 0
curShares = 0

#---------------------------------------------------------------------------------
  #End of Lists and Variables
#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
  #Get the raw data and its associated attributes [pointvalue,symbol,tickvalue]
  #Read a csv file that has at least D,O,H,L,C - V and OpInt are optional
  #Set up a portfolio of multiple markets
#---------------------------------------------------------------------------------

dataClassList = getData()
numMarkets = len(dataClassList)
portfolio = portfolioClass()

#---------------------------------------------------------------------------------
# SET COMMISSION, NUMBER OF BARS TO BACK TEST, AND RAMP UP FOR INDICATORS
#---------------------------------------------------------------------------------

commission = 100 # deducted on a round turn basis
numBarsToGoBack = 3000 # number of bars from the end of data
rampUp = 100 # need this minimum of bars to calculate indicators
sysName = 'DMACross'


#////////  DO NOT CHANGE BELOW /////////////////////////////////////////////////
for marketCnt in range(0,numMarkets):
    listOfTrades[:] = []
    marketPosition[:] = []
    entryPrice[:] = []
    entryQuant[:] = []
    exitQuant[:] = []
    trueRanges[:] = []
    myBPV,myComName,myMinMove = getDataAtribs(dataClassList[marketCnt])
    myDate,myOpen,myHigh,myLow,myClose = getDataLists(dataClassList[marketCnt])
    for i in range(0,len(myDate)):
        marketPosition.append(0)
        ranges.append(myHigh[i] - myLow[i])
        if i == 0:
            trueRanges.append(ranges[i])
        if i > 0:
            trueRanges.append(max(myClose[i-1],myHigh[i]) - min(myClose[i-1],myLow[i]))
    systemMarket = systemMarketClass()
    equity = equityClass()
    equItm = 0
    totProfit =0
    maxPositionL = 0
    maxPositionS = 0
    cumuProfit = 0
    curShares = 0
    numShares = 0
    marketPosition.append(0)
    if len(myDate) < numBarsToGoBack: numBarsToGoBack = len(myDate)
    if numBarsToGoBack < rampUp: break
#////////  DO NOT CHANGE ABOVE /////////////////////////////////////////////////

#---------------------------------------------------------------------------------
#Instantiate Indicator Classes
#---------------------------------------------------------------------------------
    rsiStudy = rsiClass()
    stochStudy = stochClass()
#---------------------------------------------------------------------------------
    for i in range(len(myDate) - numBarsToGoBack,len(myDate)):
        equItm += 1
        tempDate = myDate[i]
        todaysCTE = todaysOTE = todaysEquity = 0
        marketPosition[i] = marketPosition[i-1]
        mp = marketPosition[i]
#        buyLevel,shortLevel,exitLevel = bollingerBands(myDate,myClose,60,2,i,1)
        prevAvg1 = sAverage(myClose,19,i,1)
        prevAvg2 = sAverage(myClose,39,i,1)
        avg1 = sAverage(myClose,19,i,0)
        avg2 = sAverage(myClose,39,i,0)
        atrVal = sAverage(trueRanges,10,i,0)
#        rsiVal = rsiStudy.calcRsi(myClose,10,i,0)
        stopAmt = 2000/myBPV
        profAmt = 3000/myBPV
#        print(myDate[i],"rsi ",rsiVal," atrVal ",atrVal*myBPV," ",myBPV)
#        fastKVal,fastDVal,slowDVal = stochStudy.calcStochastic(3,9,9,myHigh,myLow,myClose,i,1)

#        if (mp > 0 and maxPositionL < 3) : maxPositionL = mp
#        if (mp < 0 and maxPositionS < 3) : maxPositionS = mp


 #Long Entry Logic
        if (mp != 1) and avg1 > avg2 and prevAvg1 < prevAvg2:
            profit = 0
            price = myClose[i]
            if mp <= -1:
                profit,trades,curShares = exitPos(price,myDate[i],"RevShrtLiq",curShares)
                listOfTrades.append(trades)
                mp = 0
                todaysCTE = profit
            tradeName = "DMA Buy"
            mp += 1
            marketPosition[i] = mp
            numShares = 1
            entryPrice.append(price)
            entryQuant.append(numShares)
            curShares = curShares + numShares
            trades = tradeInfo('buy',myDate[i],tradeName,entryPrice[-1],numShares,1)
            barsSinceEntry = 1
            totProfit += profit
            listOfTrades.append(trades)
 #Long Exit - Loss
        if mp >= 1 and myClose[i] < entryPrice[-1] - stopAmt and barsSinceEntry > 1:
            price = myClose[i]
            tradeName = "L-MMLoss"
            exitDate =myDate[i]
            numShares = curShares
            exitQuant.append(numShares)
            profit,trades,curShares = exitPos(price,myDate[i],tradeName,numShares)
            if curShares == 0 : mp = marketPosition[i] = 0
            totProfit += profit
            todaysCTE = profit
            listOfTrades.append(trades)
            maxPositionL = maxPositionL - 1
#Long Exit - Profit
        if mp >= 1 and myHigh[i] > entryPrice[-1] + profAmt and barsSinceEntry > 1:
            price = max(myOpen[i],entryPrice[-1] + profAmt)
            tradeName = "L-Prof"
            exitDate =myDate[i]
            numShares = curShares
            exitQuant.append(numShares)
            profit,trades,curShares = exitPos(price,myDate[i],tradeName,numShares)
            if curShares == 0 : mp = marketPosition[i] = 0
            totProfit += profit
            todaysCTE = profit
            listOfTrades.append(trades)
            maxPositionL = maxPositionL - 1
 
# Short Logic
        if (mp !=-1)  and avg1 < avg2 and prevAvg1 > prevAvg2:
            profit = 0
            price = myClose[i]
            if mp >= 1:
                profit,trades,curShares = exitPos(price,myDate[i],"RevLongLiq",curShares)
                todaysCTE = profit
                listOfTrades.append(trades)
                mp = 0
            mp -= 1
            tradeName = "DMA Short"
            marketPosition[i] = mp
            entryPrice.append(price)
            numShares = 1
            entryQuant.append(numShares)
            curShares = curShares + numShares
            trades = tradeInfo('sell',myDate[i],tradeName,entryPrice[-1],numShares,1)
            barsSinceEntry = 1
            totProfit += profit
            listOfTrades.append(trades)
# Short Exit Loss
        if mp <= -1 and myClose[i] >= entryPrice[-1] + stopAmt and barsSinceEntry > 1:
            price = myClose[i]
            tradeName = "S-MMLoss"
            exitDate = myDate[i]
            numShares = curShares
            exitQuant.append(numShares)
            profit,trades,curShares = exitPos(price,myDate[i],tradeName,numShares)
            if curShares == 0 : mp = marketPosition[i] = 0
            totProfit += profit
            todaysCTE = profit
            listOfTrades.append(trades)
            maxPositionS = maxPositionS -1


 ###########  DO NOT CHANGE BELOW ################################################################
        if mp == 0 :
            todaysOTE = 0
            curShares = 0
            entryPrice[:] = []
            maxPositionL = 0
            maxPositionS = 0
        if mp != 0 :
            barsSinceEntry = barsSinceEntry + 1
            todaysOTE = calcTodaysOTE(mp,myClose[i],entryPrice,entryQuant,myBPV)
        todaysEquity = todaysOTE + totProfit
        equity.setEquityInfo(myDate[i],equItm,todaysCTE,todaysOTE)
    if mp >= 1:
        price = myClose[i]
        tradeName = "L-EOD"
        exitDate =myDate[i]
        numShares = curShares
        exitQuant.append(numShares)
        profit,trades,curShares = exitPos(price,myDate[i],tradeName,numShares)
        listOfTrades.append(trades)
    if mp <= -1:
        price = myClose[i]
        tradeName = "S-EOD"
        exitDate =myDate[i]
        numShares = curShares
        exitQuant.append(numShares)
        profit,trades,curShares = exitPos(price,myDate[i],tradeName,numShares)
        listOfTrades.append(trades)
    systemMarket.setSysMarkInfo(sysName,myComName,listOfTrades,equity)
    systemMarketList.append(systemMarket)
    numRuns = numRuns + 1

if numMarkets > 0:
    portfolio.setPortfolioInfo("PortfolioTest",systemMarketList)
    calcSystemResults(systemMarketList)
if numMarkets == 0: print("No markets selected : terminating!")






