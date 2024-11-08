import csv
import tkinter as tk
import os.path
from marketDataClass import marketDataClass
from dataMasterLists import commName, bigPtVal, minMove
from tkinter.filedialog import askopenfilenames
from equityDataClass import equityClass

dataClassList = list()

fileName = "c:\PythonBackTester\dataMaster.csv"
fileName = "dataMaster.csv"
def parseDate(dateString):
    whereIsAslash = dateString.find('/')
    if whereIsAslash != -1:
        x = dateString[0:whereIsAslash]
        tempStr = dateString[whereIsAslash+1:len(dateString)]
        whereIsAslash = tempStr.find('/')
        y = tempStr[0:whereIsAslash]
        z = tempStr[whereIsAslash+1:len(tempStr)]
        tempDate = int(z)*10000 + int(x)*100 + int(y)
        return(tempDate)
    else:
        return(int(dateString)) 
     
        

def getData():
    tempFileList = list()
    totComms = 0
    with open(fileName) as f:
       f_csv = csv.reader(f)
       for row in f_csv:
          commName.append(row[0])
          bigPtVal.append(float(row[1]))
          minMove.append(float(row[2]))
          totComms = totComms + 1      
    f.close
    root = tk.Tk()
    root.withdraw()
    cnt = 0
    files = askopenfilenames(filetypes=(('CSV files', '*.csv'),
                                       ('TXT files', '*.txt')),
                                       title='Select Markets To Test- CSV format only!')
    fileList = root.tk.splitlist(files)

    fileListLen = len(fileList)
    for marketCnt in range(0,fileListLen):
        head,tail = os.path.split(fileList[marketCnt])
        tempStr = tail[0:2]
        commIndex = 0
        foundInDataMaster = 0
        for i in range(totComms):
            if tempStr == commName[i]:
                commIndex = i
                foundInDataMaster = 1
        newDataClass = marketDataClass()
        if foundInDataMaster != 0:
            newDataClass.setDataAttributes(commName[commIndex],bigPtVal[commIndex],minMove[commIndex])
        else:
            newDataClass.setDataAttributes(tail,100,0.01)            
        with open(fileList[marketCnt]) as f:     
            f_csv = csv.reader(f)
            for row in f_csv:
                numCols = len(row)
                for col in range(0,numCols):
                    row[col] = row[col].replace(' ','')                  
                tempStr = row[0]
                isThereAslash = tempStr.find('/')
                isThereAdash = tempStr.find('-')
                if isThereAslash != -1:
                    row[0] = tempStr.replace('/','')
                if isThereAdash != -1:
                    row[0] = tempStr.replace('-','')    
                isThereAdigit = row[0].isdigit()
                if (isThereAdigit):
                    newDataClass.readData(parseDate(row[0]),float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5]),float(row[6]))                              
                    cnt = cnt + 1
        dataClassList.append(newDataClass)
        f.close
    return(dataClassList)
 
