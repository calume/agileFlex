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
radiation=pd.read_csv('../../Data/NASA_POWER_AllSkyInsolation_01032014_13092014.csv', skiprows=10)
temp=temp[30:120]
radiation=radiation[92:-31]
#temp=temp[395:483]
tempind=[]
radind=[]
for i in temp.index:    
    tempind.append(datetime.datetime(int(temp['YEAR'][i]),int(temp['MO'][i]),int(temp['DY'][i]),0))

for i in radiation.index:    
    radind.append(datetime.datetime(int(radiation['YEAR'][i]),int(radiation['MO'][i]),int(radiation['DY'][i]),0))

all_temp=temp['T2M']
all_temp.index=tempind

all_rad=radiation['ALLSKY_SFC_SW_DWN']
all_rad.index=radind

plt.figure()
plt.hist(all_temp, bins=4)
plt.xlabel('Temperature (degC)')
plt.ylabel('Frequency')

plt.figure()
plt.hist(all_rad, bins=4)
plt.xlabel('kW-hr/m^2/day')
plt.ylabel('Frequency')

###----------Winter Data------------------#####
pick_in = open("../../Data/Winter14HdRm.pickle", "rb")
Winter_HdRm = pickle.load(pick_in)

pick_in = open("../../Data/Winter14Inputs.pickle", "rb")
WinterInputs = pickle.load(pick_in)

###----------Summer Data------------------#####

pick_in = open("../../Data/Summer14Inputs.pickle", "rb")
SummerInputs = pickle.load(pick_in)

pick_in = open("../../Data/Summer14FtRm.pickle", "rb")
Summer_FtRm = pickle.load(pick_in)

########---------Convert Headroom to feeder+phase column dataframe
Headrm_DF=pd.DataFrame(index=Winter_HdRm[1].index,
        columns=[
            "11",
            "12",
            "13",
            "14",
            "21",
            "22",
            "23",
            "24",
            "31",
            "32",
            "33",
            "34",
        ] )
    
for p in range(1, 4):
    for f in range(1, 5):
        Headrm_DF[str(p) + str(f)] = Winter_HdRm[f][p]

Footrm_DF=pd.DataFrame(index=Summer_FtRm[1].index,
        columns=[
            "11",
            "12",
            "13",
            "14",
            "21",
            "22",
            "23",
            "24",
            "31",
            "32",
            "33",
            "34",
        ] )
    
for p in range(1, 4):
    for f in range(1, 5):
        Headrm_DF[str(p) + str(f)] = Winter_HdRm[f][p]
        Footrm_DF[str(p) + str(f)] = Summer_FtRm[f][p]





#########---------Convert to daily timeseries--------

summer_dates=SummerInputs['pv_delta'].index[:-1]
winter_dates=WinterInputs['demand_delta'].index[:-1]
wkd_dates= (winter_dates.weekday >= 0) & (winter_dates.weekday <= 4)
wknd_dates= (winter_dates.weekday >= 5) & (winter_dates.weekday <= 6)
wkd_dates=winter_dates[wkd_dates]
wknd_dates=winter_dates[wknd_dates]

wkd_temps = all_temp[wkd_dates[range(0, len(wkd_dates), 48)]]
wknd_temps = all_temp[wknd_dates[range(0, len(wknd_dates), 48)]]

Settings={}
Settings['summer Ftrm']={'min': -25, 'max':75, 'Q': 'Q1-','Title': ' Summer Footroom ', 'units':' kW-hr/m^2/day ','min/max':'min'}
Settings['summer pv']={'min': -25, 'max':0, 'Q': 'Q1-','Title': ' Summer PV Adjust ', 'units':' kW-hr/m^2/day ','min/max':'min'}
Settings['winter Hdrm']={'min': -20, 'max':40, 'Q': 'Q1-','Title': ' Winter Headroom ', 'units':' degC ','min/max':'min'}
Settings['winter demand']={'min': -20, 'max':40, 'Q': 'Q99-','Title': ' Winter demand turn-down ', 'units':' degC ','min/max':'min'}

settings=Settings['summer Ftrm']
dates=summer_dates
data=Footrm_DF[:-1]#SummerInputs['pv_delta']
temps=all_rad

#def advance_forecast(dates,data,temps,settings):
dailyrange={}
DailyDelta={}
DailyByBin={}
cols=['b','c','g','r']
r=0
tempLabels=range(1,5)
#TempBins=pd.cut(temps,bins=[2.06254,3.935,5.8,7.665,9.53], labels=tempLabels, retbins=True)
TempBins=pd.cut(temps,bins=4, labels=tempLabels, retbins=True)
plt.figure(str(settings['Title'])+str(settings['Q'][:-1])+' requirement (kWs) vs Settlement Period')

for c in data.columns:
    dailyrange=range(0, len(dates), 48)

    DailyDelta[c]=pd.DataFrame(index=dates[dailyrange], columns=range(0,48))
    
    for d in DailyDelta[c].index:
        mask=(data[c].index>=d) & (data[c].index<(d+timedelta(days=1)))
        DailyDelta[c].loc[d]=data[c].loc[mask].values
    
    
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
        DailyByBin[c]['Q99-'+str(z)]=pd.Series(index=range(0,48))
        DailyByBin[c]['Q1-'+str(z)]=pd.Series(index=range(0,48))
        DailyByBin[c]['Median-'+str(z)]=pd.Series(index=range(0,48))
        for i in datesBinned[z]:
            DailyByBin[c][z].loc[i]=DailyDelta[c].loc[i].values
        for p in range(0,48):
            DailyByBin[c]['Q99-'+str(z)][p]=DailyByBin[c][z][p].quantile(0.99)
            DailyByBin[c]['Q1-'+str(z)][p]=DailyByBin[c][z][p].quantile(0.01)
            DailyByBin[c]['Median-'+str(z)][p]=DailyByBin[c][z][p].quantile(0.5)
        lbl=str(round(TempBins[1][z-1],1))+' - '+str(round(TempBins[1][z],1))+str(settings['units'])
        y=DailyByBin[c][str(settings['Q'])+str(z)].values
        plt.plot(y, linewidth=1.5, color=cols[n], label=lbl)
        #plt.fill_between(range(0,48),0,y, facecolor=cols[n])
        #plt.plot(DailyByBin[c]['Q95'+str(z)].values, linewidth=0.5, label=lbl, linestyle='--') 
        #plt.plot(DailyByBin[c]['Median'+str(z)].values, linewidth=1, linestyle='--') 
        plt.ylim(settings['min'],settings['max'])
        plt.xlim(0,47)
        n=n+1
plt.tight_layout()
plt.legend()
plt.figure(str(settings['units'])+' vs' +str(settings['Title']))   
u=0
for c in data.columns:
    print(u)
    u=u+1
    plt.subplot(3,4,u)
    if u <5:
        plt.title('Feeder - '+str(u))
    if u==1 or u==5 or u==9:
        plt.ylabel('Phase '+str(c[0]))
        if settings['min/max']=='min':
            vals=DailyDelta[c].min(axis=1).values
        if settings['min/max']=='max':
            vals=DailyDelta[c].max(axis=1).values
    plt.scatter(temps.values,vals,s=0.8)
    #plt.tight_layout()

figManager = plt.get_current_fig_manager()
figManager.window.showMaximized()
   
#return DailyByBin, DailyDelta

#DailyByBin_Wkd=advance_forecast(wkd_dates, wkd_temps,'Week Days')
#DailyByBin_Wknd=advance_forecast(wknd_dates, wknd_temps,'Weekend')

#DailyByBin_All,DailyDelta_All=advance_forecast(winter_dates,WinterInputs['demand_delta'][:-1]*-1, all_temp,' Winter Power Injection: ',' degC','Q99')
    
#DailyByBin_All=advance_forecast(summer_dates, SummerInputs['demand_delta'], all_rad,' Summer Demand Turn-up: ',' kW-hr/m^2/day','Q99')

#DailyByBin_All,DailyDelta_All=advance_forecast(winter_dates,WinterInputs['demand_delta'], all_temp,' Winter Power Injection: ',' degC')