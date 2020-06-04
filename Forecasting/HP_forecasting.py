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

###----------------------- Load in Test data Set -------------##########


temp=pd.read_csv('../../Data/heatpump/Grantham_Temp_Daily_20140101_20150101.csv', skiprows=16)
tempind=[]
for i in temp.index:    
    tempind.append(datetime.datetime(int(temp['YEAR'][i]),int(temp['MO'][i]),int(temp['DY'][i]),12))

temp=temp['T2M']
temp.index=tempind
temp=temp[:-1]
tempind=tempind[:-1]
## HP Forecasting
# pred is the previous days data using persistence forecasting
# true is the actual output for the day in question.

start_date = date(2013, 11, 1)
end_date = date(2014, 3, 1)
delta_halfhours = timedelta(hours=0.5)
sims_halfhours = pd.date_range(start_date, end_date, freq=delta_halfhours)

def create_hp_df(sims_halfhours):
    pick_in = open("../../Data/Customer_Summary.pickle", "rb")
    Customer_Summary = pickle.load(pick_in)
    
    pick_in = open("../../Data/HP_DataFrame.pickle", "rb")
    HP_DataFrame = pickle.load(pick_in)
    HP_DataFrame.columns=HP_DataFrame.columns.astype(int)
    hps=list(Customer_Summary['heatpump_ID'][Customer_Summary['heatpump_ID'] != 0])
    
    heatpump=pd.DataFrame(index=sims_halfhours, columns=hps)
    for i in sims_halfhours.tolist():
        heatpump.loc[i]=HP_DataFrame[hps].loc[i]
        
    pickle_out = open("../../Data/heatpump.pickle", "wb")
    pickle.dump(heatpump, pickle_out)
    pickle_out.close()

###create_hp_df(sims_halfhours)

pick_in = open("../../Data/heatpump.pickle", "rb")
heatpump = pickle.load(pick_in)
heatpump=heatpump.loc[:,~heatpump.columns.duplicated()]
heatpump=heatpump.drop(columns=heatpump.columns[heatpump.sum()<1000])
dailymean=[]
for d in range(0,int(len(sims_halfhours[:-1])/48)):
    dailymean.append(heatpump.iloc[d*48:(d+1)*48].sum(axis=1).mean())

dailymeanSeries=pd.Series(dailymean)
dailymeanSeries.index=tempind

def plot(pred,true):
    plt.figure()
    plt.scatter(temp.values,dailymeanSeries.values, color='green', s=1)
    plt.xlabel('Mean Daily Temp (degC)')
    plt.ylabel('Mean Daily Heat Pump Demand (kW)')

    plt.figure()
    
    plt.plot(pred, label='Presistence Forecast')
    plt.plot(true, linestyle='--', label='Actual')
    plt.ylabel('Total Heat Pump Demand (kW)')
    plt.xlabel('Settlement Period')
    plt.legend()

##########Bin dates by temp

TempBins=pd.cut(temp,bins=10, labels=range(1,11), retbins=True)
d=1
###### dailycheck
day=temp.index[d]
pred=heatpump[d*48:(d+1)*48].sum(axis=1)
true=heatpump[(d+1)*48:(d+2)*48].sum(axis=1)

BaseNMAE = mean_absolute_error(true.values,pred.values)

todayBin=TempBins[0][day]
tomorrowBin = TempBins[0][day+timedelta(days=1)]

days=pd.Series(range(0,len(tempind)),index=tempind)

MatchDays=pd.DataFrame(columns=['Day','MAE'])
if todayBin != tomorrowBin:
    MatchDays['Day']=days[TempBins[0]==tomorrowBin][1:]
    #MatchDays=TempBins[0].iloc[MatchDays[1:]]

for i in MatchDays['Day'].index:
    pred_n=heatpump[MatchDays['Day'][i]*48:(MatchDays['Day'][i]+1)*48].sum(axis=1)
    MatchDays['MAE'][i]=float(mean_absolute_error(pred_n.values, pred.values))

plot(pred.values,true.values)

bestday=MatchDays['Day'][MatchDays['MAE'].astype(float).idxmin()]

best_pred=heatpump[bestday*48:(bestday+1)*48].sum(axis=1)

plot(best_pred.values,true.values)
BestNMAE = mean_absolute_error(true.values,best_pred.values)

#Temp = temp.iloc[day+1]
#a = next(i for i in range(11) if Temp > TempBins[1][i] and Temp < TempBins[1][i+1])+1

