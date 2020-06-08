# -*- coding: utf-8 -*-
"""
Created on Thu May 02 13:48:06 2019

This python script produces forecasts of headroom calculated using OpenDSS. 

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
temp=temp[30:120]
#temp=temp[395:483]
tempind=[]
for i in temp.index:    
    tempind.append(datetime.datetime(int(temp['YEAR'][i]),int(temp['MO'][i]),int(temp['DY'][i]),0))

pick_in = open("../../Data/WinterHdRm.pickle", "rb")
Winter_HdRm = pickle.load(pick_in)

pick_in = open("../../Data/WinterNetworkSummary.pickle", "rb")
Winter_NetworkSummary = pickle.load(pick_in)

pick_in = open("../../Data/WinterInputs.pickle", "rb")
WinterInputs = pickle.load(pick_in)

#pick_in = open("../../Data/Winter15Inputs.pickle", "rb")
#WinterInputs = pickle.load(pick_in)

all_temp=temp['T2M']
all_temp.index=tempind

## HP Forecasting
# pred is the previous days data using persistence forecasting
# true is the actual output for the day in question.

start_date = date(2014, 12, 1)
end_date = date(2015, 3, 1)
delta_halfhours = timedelta(hours=0.5)
sims_halfhours = pd.date_range(start_date, end_date, freq=delta_halfhours)

#plt.hist(TempBins[0])
#########---------Convert to daily timeseries--------

WinterInputs['demand_delta']=WinterInputs['demand_delta'][:-1]*-1

all_dates=WinterInputs['demand_delta'].index
wkd_dates= (all_dates.weekday >= 0) & (all_dates.weekday <= 4)
wknd_dates= (all_dates.weekday >= 5) & (all_dates.weekday <= 6)
wkd_dates=WinterInputs['demand_delta'].index[wkd_dates]
wknd_dates=WinterInputs['demand_delta'].index[wknd_dates]

wkd_temps = all_temp[wkd_dates[range(0, len(wkd_dates), 48)]]
wknd_temps = all_temp[wknd_dates[range(0, len(wknd_dates), 48)]]

def advance_forecast(dates, temps,plot_title):
    dailyrange={}
    DailyDelta={}
    DailyByBin={}
    cols=['b','c','g','r']
    r=0
    tempLabels=range(1,5)
    TempBins=pd.cut(temps,bins=[2.06254,3.935,5.8,7.665,9.53], labels=tempLabels, retbins=True)
    plt.figure(str(plot_title)+' P99 Power Injection Requirement (kWs) by Temperature Range')
    plt.tight_layout()
    for c in WinterInputs['demand_delta'].columns:
        dailyrange=range(0, len(dates), 48)
    
        DailyDelta[c]=pd.DataFrame(index=dates[dailyrange], columns=range(0,48))
        
        for d in DailyDelta[c].index:
            mask=(WinterInputs['demand_delta'][c].index>=d) & (WinterInputs['demand_delta'][c].index<(d+timedelta(days=1)))
            DailyDelta[c].loc[d]=WinterInputs['demand_delta'][c].loc[mask].values
        
        
        datesBinned={}
        DailyByBin[c]={}
        n=0
        r=r+1
        plt.tight_layout()
        plt.subplot(3,4,r)
        if r <5:
            plt.title('Feeder - '+str(r))
        if r%2!=0:
            plt.ylabel('Phase '+str(c[0]))
        for z in tempLabels:
            datesBinned[z]=TempBins[0][TempBins[0]==z].index
            DailyByBin[c][z]=pd.DataFrame(index=datesBinned[z], columns=range(0,48))
            DailyByBin[c]['Q95'+str(z)]=pd.Series(index=range(0,48))
            DailyByBin[c]['Q99'+str(z)]=pd.Series(index=range(0,48))
            DailyByBin[c]['Median'+str(z)]=pd.Series(index=range(0,48))
            for i in datesBinned[z]:
                DailyByBin[c][z].loc[i]=DailyDelta[c].loc[i].values
            for p in range(0,48):
                DailyByBin[c]['Q99'+str(z)][p]=DailyByBin[c][z][p].quantile(0.99)
                #DailyByBin[c]['Q95'+str(z)][p]=DailyByBin[c][z][p].quantile(0.95)
                DailyByBin[c]['Median'+str(z)][p]=DailyByBin[c][z][p].quantile(0.5)
            lbl=str(round(TempBins[1][z-1],1))+' - '+str(round(TempBins[1][z],1))+' deg C'
            y=DailyByBin[c]['Q99'+str(z)].values
            plt.plot(y, linewidth=1.5, color=cols[n], label=lbl)
            plt.fill_between(range(0,48),0,y, facecolor=cols[n])
            #plt.plot(DailyByBin[c]['Q95'+str(z)].values, linewidth=0.5, label=lbl, linestyle='--') 
            #plt.plot(DailyByBin[c]['Median'+str(z)].values, linewidth=1, linestyle='--') 
            plt.ylim(0,25)
            n=n+1
    plt.legend()
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    plt.tight_layout()
#    plt.figure(c)       
#    plt.scatter(temps.values,DailyDelta[c].max(axis=1).values,s=0.8)
#    plt.xlabel('Temp degC')
#    plt.ylabel('Mean daily adjust (kW)')
    return DailyByBin

#DailyByBin_Wkd=advance_forecast(wkd_dates, wkd_temps,'Week Days')
#DailyByBin_Wknd=advance_forecast(wknd_dates, wknd_temps,'Weekend')

DailyByBin_All=advance_forecast(all_dates, all_temp,'All Days')