# -*- coding: utf-8 -*-
"""
Created on Thu Sep 24 14:16:25 2020

@author: CalumEdmunds
"""

from congestion_probability_batch import runbatch
from voltage_headroom import voltage_limits
from headroom_forecasting import headroom_percentiles
from zonal_summary import EVRealiser
import pickle
from congestion_probability_validation import runvalid

networks=['network_1/','network_5/','network_10/','network_17/','network_18/']
#networks=['network_17/','network_18/']
Cases=['00PV00HP','00PV25HP','25PV50HP','25PV75HP','50PV100HP']
paths="../Data/Lower/factor0.6/"
desc=['225 V limit (Conservative)','216 V Limit (Lower Less conservative)','']
#runbatch(networks,Cases,'Pre')
#voltage_limits(networks,Cases,paths)
#runbatch(networks,Cases,'Post',paths)

quant=0
factor=0.6
nHPs_Final=headroom_percentiles(networks,Cases,paths,quant,factor)
EVRealiser(networks, paths,quant,factor)
runvalid(networks, paths,quant,factor)


###MEGA SUMMARY OF HPs and EVS ############


print(paths,desc[1])
pick_in = open(paths+"nHPs_final.pickle", "rb")
nHPs_Final= pickle.load(pick_in)

for N in networks:
    pick_in = open("../Data/"+N+"Customer_Summary00PV25HP14.pickle", "rb")
    Customer_Summary= pickle.load(pick_in)
    
    pick_in = open(paths+N+"validation/Winter14_V_Data.pickle", "rb")
    SumData= pickle.load(pick_in)
    print('---------------',N,len(Customer_Summary),'Customers',len(SumData['Vmin']),'Timesteps ---------------')
    print('HPs', nHPs_Final[N].sum())
    print('EVs', SumData['EV_summary'].sum().min())
    print('C Violations', (SumData['C_Violations'].sum(axis=1)>0).sum())
    print('V Violations', int(((SumData['Vmin']<0.9).sum(axis=1)>0).sum()))
    
    
    
    