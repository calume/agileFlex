# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 11:21:14 2019

Script to process Heat Pump (HP) data for the AGILE Model

@author: Calum Edmunds
"""

import pandas as pd
import pickle
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta, date
import os

# --------------------------- Create SM Data Pickle -------------------

startdate =  date(2013,12,1)
enddate   =  date(2014,12
                  ,1)
delta = timedelta(minutes=2)

dt = pd.date_range(startdate, enddate, freq=delta)


#Get list of Heat Pump IDs that are to be stored from the BEIS summary
#Only Domestic Air Source Heat Pumps are to be considered

HP_Summary=pd.read_excel('../../Data/RHPP-Beis-Summary.xlsx', sheet_name=0)
HP_Summary_ASHP=HP_Summary[HP_Summary['Heat pump Type']=='ASHP']
HP_Summary_ASHP_Domestic=HP_Summary_ASHP['RHPP Name'][HP_Summary_ASHP['Site Type']=='Domestic']

path="../../Data/heatpump/processed_rhpp"

#lst=[]
#for f in range(0,len(HP_Summary_ASHP_Domestic)):
#    try:
#        HP_RawFile = pd.read_csv(path+HP_Summary_ASHP_Domestic.iloc[f][-4:]+".csv", index_col=['Matlab_time'], usecols=['Matlab_time','Ehp','Edhw'])  
#        lst.append(HP_Summary_ASHP_Domestic.iloc[f][-4:])
#        print(f)
#    except:
#        print()

startdate =  date(2012,2,1)
enddate   =  date(2015,4,1)
delta = timedelta(hours=0.5)
dt = pd.date_range(startdate, enddate, freq=delta)
HP_DataFrame=pd.DataFrame(index=dt)

pick_in = open("../../Data/HP_DataFrame.pickle", "rb")
HP_DataFrame = pickle.load(pick_in)
hist2=[]
hist30=[]
for f in HP_DataFrame.columns:
    print(f, end=": ")
    HP_RawFile = pd.read_csv(path+f+".csv", index_col=['Matlab_time'], usecols=['Matlab_time','Year','Month','Ehp','Edhw'])      
    hist2.append(round(((HP_RawFile['Ehp']+HP_RawFile['Edhw'])/1000*30).max(),1))
    hist30.append(round(HP_DataFrame[f].max()))
#    out_datetime=pd.Series(index=range(0,len(HP_RawFile.index)))
#    for i in range(0,len(HP_RawFile.index)):
#        days = HP_RawFile.index.values[i] % 1
#        hours = days % 1 * 24
#        minutes = hours % 1 * 60
#        seconds = minutes % 1 * 60
#        
#        out_date = date.fromordinal(int(HP_RawFile.index.values[i])) \
#               + timedelta(days=days) \
#               - timedelta(days=366)
#        
#        out_datetime[i] = datetime.fromisoformat(str(out_date)) \
#                  +  timedelta(hours=int(hours)) \
#                   + timedelta(minutes=int(minutes)) \
#                   
#                   
#    HP_RawFile.index= out_datetime
#    HP_RawFile['HPTotDem']=HP_RawFile['Ehp']+HP_RawFile['Edhw']
#    
#    HP_Out=HP_RawFile['HPTotDem'].resample('30T').sum()/1000/0.5
#    
#    HP_DataFrame=pd.concat([HP_DataFrame, HP_Out],axis=1,join='outer',sort=False)
#HP_DataFrame.columns=lst
    
#pickle_out = open("../../Data/HP_DataFrame.pickle", "wb")
#pickle.dump(HP_DataFrame, pickle_out)
#pickle_out.close()

#pick_in = open("../../Data/HP_DataFrame.pickle", "rb")
#HP_DataFrame = pickle.load(pick_in)
    
#------------- Visualise 
histo2,binz2 = np.histogram(hist2,bins=range(0,int(max(hist2)),1))

fig,ax = plt.subplots(figsize=(5,4))
ax.bar(binz2[:-1],histo2,width=1,align='edge')
ax.set_xlim(left=0)#,right=5000)
ax.set_ylabel('Number of households',fontsize=9)
ax.set_xlabel('Peak Heat Pump Demand / Capacity (kW)',fontsize=9)
for t in ax.xaxis.get_majorticklabels(): t.set_fontsize(9)
for t in ax.yaxis.get_majorticklabels(): t.set_fontsize(9)
plt.tight_layout()

histo30,binz30 = np.histogram(hist30,bins=range(0,int(max(hist30)),1))

fig,ax = plt.subplots(figsize=(5,4))
ax.bar(binz30[:-1],histo30,width=1,align='edge')
ax.set_xlim(left=0)#,right=5000)
ax.set_ylabel('Number of households',fontsize=9)
ax.set_xlabel('Peak Heat Pump Demand / Capacity (kW)',fontsize=9)
for t in ax.xaxis.get_majorticklabels(): t.set_fontsize(9)
for t in ax.yaxis.get_majorticklabels(): t.set_fontsize(9)
plt.tight_layout()