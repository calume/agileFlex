# -*- coding: utf-8 -*-
"""
Created on Thu May 02 13:48:06 2019

This python script produces forecasts of output from Heat pump Data from RHPPS. 

The function 'Forecast' uses persistence forecast using a previous days data
then fits gaussian mixtures to produce a range of probable Day Ahead forecasts that 
can be benchmarked against the persistence forecast.

This can also be done Intraday using the first 10 hours of actual data (i.e. at 10am)
to produce an intraday forecast

@author: Calum Edmunds
"""


######## Import packages
import scipy.io
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None
from matplotlib import pyplot as plt
from datetime import datetime, timedelta, date, time
import datetime
import pickle
from sklearn.metrics import mean_absolute_error


smkeys = [
    "WinterWknd",
    "WinterWkd",
    "SpringWknd",
    "SpringWkd",
    "SummerWknd",
    "SummerWkd",
    "AutumnWknd",
    "AutumnWkd",
]

###----------------------- Load in Test data Set -------------##########

########- temperature data from https://power.larc.nasa.gov/data-access-viewer/
temp=pd.read_csv('../../Data/heatpump/Grantham_Temp_Daily_20131101_20150301.csv', skiprows=16)
tempind=[]
for i in temp.index:    
    tempind.append(datetime.datetime(int(temp['YEAR'][i]),int(temp['MO'][i]),int(temp['DY'][i]),0))

temp=temp['T2M']
temp.index=tempind
temp=temp[:-1]
tempind=tempind[:-1]
## HP Forecasting
# pred is the previous days data using persistence forecasting
# true is the actual output for the day in question.

start_date = date(2013, 11, 1)
end_date = date(2015, 3, 1)
delta_halfhours = timedelta(hours=0.5)
sims_halfhours = pd.date_range(start_date, end_date, freq=delta_halfhours)

def seasonal():
    pick_in = open("../../Data/HP_DataFrameBySeason.pickle", "rb")
    HP_DataFrame = pickle.load(pick_in)
    for i in smkeys:
        HP_reduced = HP_DataFrame[i].loc[sims_halfhours.tolist()].sum() > 0
        HP_reduced=HP_reduced[HP_reduced]
        HP_DataFrame[i] = HP_DataFrame[i][HP_reduced.index]
    
    keepdays={}
    keep_HP={}
    #Total_HP_DataFrame=pd.DataFrame
    totalHP={}
    for i in smkeys:
        keep_HP[i]=[]
        keepdays[i]=[]
        totalHP[i]={}
        totalHP[i]['HPNorm_kW_hh']=[]
        totalHP[i]['HPNorm_Date']=[]
        for d in range(0,int(len(HP_DataFrame[i])/48)):
            HP_fullday_ID=HP_DataFrame[i].iloc[d*48:(d+1)*48].sum() > 0
            HP_Day_Reduced=HP_fullday_ID[HP_fullday_ID]
            if len(HP_Day_Reduced) > 35:
                keep_HP[i].append(list(HP_Day_Reduced.index))
                keepdays[i].append(d)
                
        for z in range(0,len(keepdays[i])):
            totalHP[i]['HPNorm_kW_hh'].append(HP_DataFrame[i][keep_HP[i][z]].iloc[keepdays[i][z]*48:(keepdays[i][z]+1)*48].sum(axis=1)/len(keep_HP[i][z]))
            totalHP[i]['HPNorm_Date'].append(HP_DataFrame[i].iloc[keepdays[i][z]*48].name)
    return totalHP

def plot_forecast(pred,true,title):
    plt.figure()
    plt.title(title)
    plt.plot(pred, label='Forecast')
    plt.plot(true, linestyle='--', label='Actual')
    plt.ylabel('Total Heat Pump Demand (kW)')
    plt.xlabel('Settlement Period')
    plt.legend()

totalHP=seasonal()

TempBins=pd.cut(temp,bins=20, labels=range(1,21), retbins=True)
days=pd.Series(range(0,len(tempind)),index=tempind)


MAE_Base={}
MAE_Upgrade={}
MAE_Base_Av={}
MAE_Upgrade_Av={}

#smkeys2 = ["WinterWknd"]
for k in smkeys:
    
    MAE_Base[k]=[]
    MAE_Upgrade[k]=[]
    MatchDays={}
    for d in range(1,len(totalHP[k]['HPNorm_kW_hh'][:-1])):
        pred=totalHP[k]['HPNorm_kW_hh'][d].values
        true=totalHP[k]['HPNorm_kW_hh'][d+1].values
        MAE_Base[k].append(mean_absolute_error(true,pred))
        
        day=totalHP[k]['HPNorm_Date'][d]
        #plot_forecast(pred,true,str(day)+'Original')
        todayBin=TempBins[0][day]
        tomorrowBin = TempBins[0][day+timedelta(days=1)]
    
        MatchDays[d]=pd.DataFrame(columns=['Day','Date','MAE'])
        
        if todayBin != tomorrowBin:
            seasonals = TempBins[0][totalHP[k]['HPNorm_Date']]
            if seasonals.index.contains(day+timedelta(days=1)):
                print('sadasda')
                seasonals.drop(day+timedelta(days=1))
                
            MatchDays[d]['Date']=seasonals[seasonals==tomorrowBin].index
        
            for i in range(0,len(MatchDays[d]['Date'])):
                HP_Normdate_Series=pd.Series(totalHP[k]['HPNorm_Date'])
                matchday=HP_Normdate_Series[HP_Normdate_Series==MatchDays[d]['Date'][i]]
                MatchDays[d]['Day'][i]=matchday.index.values[0]
                pred_n=totalHP[k]['HPNorm_kW_hh'][matchday.index.values[0]]
                MatchDays[d]['MAE'][i]=float(mean_absolute_error(pred_n, pred))
        
        if len(MatchDays[d]) > 0:
            bestday=MatchDays[d]['Day'][MatchDays[d]['MAE'].astype(float).idxmin()]
        
            best_pred=totalHP[k]['HPNorm_kW_hh'][bestday].values
        
            #plot_forecast(best_pred,true,str(day)+'Upgrade')
            MAE_Upgrade[k].append(mean_absolute_error(true,best_pred))
        
    MAE_Base_Av[k]=np.array(MAE_Base[k]).mean()
    MAE_Upgrade_Av[k]=np.array(MAE_Upgrade[k]).mean()

##dailymeanSeries=pd.Series(dailymean)
##dailymeanSeries.index=tempind
#
#def plot_temp_mean():
#    plt.figure()
#    plt.scatter(temp.values,dailymeanSeries.values, color='green', s=1)
#    plt.xlabel('Mean Daily Temp (degC)')
#    plt.ylabel('Mean Daily Heat Pump Demand (kW)')
#


#plot_forecast(pred.values,true.values)
#BaseNMAE = mean_absolute_error(true.values,pred.values)
#
##########Bin dates by temp


#days=pd.Series(range(0,len(tempind)),index=tempind)

#MatchDays=pd.DataFrame(columns=['Day','MAE'])
#if todayBin != tomorrowBin:
#    MatchDays['Day']=days[TempBins[0]==tomorrowBin][1:]
#    #MatchDays=TempBins[0].iloc[MatchDays[1:]]
#
#for i in MatchDays['Day'].index:
#    pred_n=heatpump[MatchDays['Day'][i]*48:(MatchDays['Day'][i]+1)*48].sum(axis=1)
#    MatchDays['MAE'][i]=float(mean_absolute_error(pred_n.values, pred.values))
##
#plot(pred.values,true.values)
#
#bestday=MatchDays['Day'][MatchDays['MAE'].astype(float).idxmin()]
#
#best_pred=heatpump[bestday*48:(bestday+1)*48].sum(axis=1)
#
#plot(best_pred.values,true.values)
#BestNMAE = mean_absolute_error(true.values,best_pred.values)
#
##Temp = temp.iloc[day+1]
##a = next(i for i in range(11) if Temp > TempBins[1][i] and Temp < TempBins[1][i+1])+1
#
