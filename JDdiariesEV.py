# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 16:05:12 2019

@author: qsb15202
"""

import pandas as pd
from datetime import datetime, timedelta, date, time
import pickle
from matplotlib import pyplot as plt
start=datetime(2011, 1, 1)
end=datetime(2011, 1, 2)
datelist = pd.date_range(start,end, freq='10T').tolist()
#date=datetime(1/1/2010,2/1/2010)
#
#EVTDs =  pd.read_csv('testcases/timeseries/Routine_10000EVTD.csv')
#EVs = pd.read_csv('testcases/timeseries/Routine_10000EV.csv')
#
#Summary=pd.DataFrame(index=range(0,144),columns=EVs['name'])
#Summary.columns=EVs['name']
#
#Pdc={}
#E={}
#Ptrace={}
#
#for i in EVTDs.index:
#     timerange=range(EVTDs['t_in'][i],EVTDs['t_out'][i])
#     EStart = EVTDs['EStart'][i]
#     EEnd = EVTDs['EEnd'][i]
#     bsize=EVs['battery(kWh)'][EVs['name']==EVTDs['name'][i]].values
#     Pmax=EVs['capacity(kW)'][EVs['name']==EVTDs['name'][i]].values
#     dt=1/6
#     gamma=0.8
#    
#     E[i] = EStart
#     Ptrace[i]=[]
#    
#     for t in timerange:
#        
#         S = E[i]/bsize
#        
#         if S < gamma:
#            
#             Pdc[i] = Pmax
#            
#         else:
#            
#             Pdc[i] = Pmax*(1/(1-gamma))*(1-S)
#            
#         dE = Pdc[i]*dt
#        
#         E[i]+=dE
#        
#         Ptrace[i].append(Pdc[i][0])
#        
#         if E[i] > bsize:
#            
#             E[i]=bsize
#            
#             break
#    
#     Summary[EVTDs['name'][i]][EVTDs['t_in'][i]:EVTDs['t_out'][i]]=Ptrace[i]
#
#Summary = Summary.loc[:, Summary.columns[(Summary.sum() > 50)]]
#Summary.fillna(0)
#SumN=Summary.iloc[72:144,:]
#SumN=SumN.append(Summary.iloc[0:72,:])
#SumN.index=datelist[0:144]
#SumN=SumN.asfreq('10T')
##SumN=SumN.resample('60T').sum()/6
#
#pickle_out = open("../Data/JDEVResampled.pickle", "wb")
#pickle.dump(SumN, pickle_out)
#pickle_out.close()

pick_in = open("../Data/JDEVResampled.pickle", "rb")
SumN = pickle.load(pick_in)

times = ['00:00','04:00','08:00','12:00','16:00','20:00','00:00']
SumN=SumN.fillna(0)
plt.plot(SumN.quantile(q=0.5,axis=1).values,linestyle="--",label='Median')
plt.plot(SumN.mean(axis=1).values,label='Mean')
plt.ylabel('EV Charge Demand (kW)',fontsize=11)
plt.legend()
plt.xlim(0,144)
plt.xticks(range(0,168,24),times)
plt.grid(linewidth=0.2)