# -*- coding: utf-8 -*-
"""
Created on Thu May 02 13:48:06 2019

@author: Calum Edmunds
"""


######## Importing the OpenDSS Engine  #########
import opendssdirect as dss
import scipy.io
import numpy as np
import pandas as pd
from random import uniform
from random import seed
from opendssdirect.utils import run_command
pd.options.mode.chained_assignment = None 
import timeit
from matplotlib import pyplot as plt
from datetime import datetime, timedelta, date, time
import datetime
import os
import random
import csv
import pickle
from Test_Network.network_plot import customer_summary
from sklearn.metrics import mean_absolute_error
from runDSS import runDSS, network_visualise
from crunch_results import counts, plots, Headroom_calc, plot_headroom, plot_flex

####----------Set Test Network ------------

Network_Path='Test_Network/Network1/'

####--------- Create Customer Summary ----------

Customer_Summary,Coords,Lines,Loads = customer_summary(Network_Path)
Customer_Summary = Customer_Summary.drop(columns="Color")

#### Load in Test data Set ##########
pick_in = open("../Data/SM_DataFrame_byAcorn_NH.pickle", "rb")
SM_DataFrame = pickle.load(pick_in)

pick_in = open("../Data/HP_DataFrame.pickle", "rb")
HP_DataFrame = pickle.load(pick_in)

pick_in = open("../Data/PV_BySiteName.pickle", "rb")
PV_DataFrame = pickle.load(pick_in)

#---------- Assign Smart Meter and Heat Pump IDs--------------#
#### Smart Meter
#--- only include SMs with data for day 2013-11-15
Customer_Summary['smartmeter_ID']=0
for i in SM_DataFrame.keys():
    acorn_index = Customer_Summary['Acorn_Group'][Customer_Summary['Acorn_Group']==i].index
    SM_reduced=SM_DataFrame[i]['AutumnWkd'].iloc[5712:5760].sum()>0
    SM_reduced=SM_reduced[SM_reduced]
    for z in acorn_index:    
        Customer_Summary['smartmeter_ID'][z] = random.choice(SM_reduced.index)

### Heat Pump
Customer_Summary['heatpump_ID']=0
#--- only include HPs with data for day 2013-11-15
HP_reduced=HP_DataFrame.iloc[31344:31392].sum()>0
HP_reduced=HP_reduced[HP_reduced]
heatpump_index = Customer_Summary['Heat_Pump_Flag'][ Customer_Summary['Heat_Pump_Flag']>0].index
for z in heatpump_index:    
    Customer_Summary['heatpump_ID'][z] = random.choice(HP_reduced.index)

### PV
Customer_Summary['pv_ID']=0
pv_index = Customer_Summary['PV_kW'][Customer_Summary['PV_kW']>0].index
pv_sites=list(PV_DataFrame.keys())
for z in pv_index:    
    Customer_Summary['pv_ID'][z] = random.choice(pv_sites)

##- Minus 1 year from PV timestamps to line up with SM and HP
#for k in pv_sites:
#        PV_DataFrame[k].index=PV_DataFrame[k].index-datetime.timedelta(days=365)

#--------- Run power flow Timeseries--------------------------#
######## test dates: 2013-12-5 to 2014-02-15, mostly full data sets
######## test dates: 2013-8-1 to 2013-9-1, full when PV dates are changed by minus 1 year
start_date = datetime.date(2013, 12, 5)
end_date = datetime.date(2014, 12, 15)

delta_halfhours = datetime.timedelta(hours=0.5)
delta_days = datetime.timedelta(days=1)

sims_halfhours = pd.date_range(start_date, end_date, freq=delta_halfhours)
sims_days = pd.date_range(start_date, end_date, freq=delta_days)

#####------------ Initialise Input--------------------
smartmeter={}
heatpump={}
pv={}
demand={} #Sum of smartmeter, heatpump and EV
demand_delta={} #adjustment for sensitivity, set to 0 when no sensitivity
pv_delta={} #adjustment for sensitivity, set to 0 when no sensitivity

#####-------------Initialise Output --------------
#####-- These are produced by the OpenDSS Load Flow
CurArray={}
VoltArray={}
TransArray={}
LoadArray={}
Losses={}
TranskVA_sum={}
network_summary={}
network_summary_new={}
for i in sims_halfhours.tolist():
    print(i)
    #-------------- Sample for each day weekday/weekend and season -----------#
    if (i.weekday()>=5) & (i.weekday() <=6): ###Weekend######
        day='Wknd'
    if (i.weekday()>=0) & (i.weekday() <=4):
        day='Wkd'
    if (i.month==12) | (i.month<=2):      #Dec-Feb
        season='Winter'
    if (i.month>=3) & (i.month <=5):    #Mar-May
        season='Spring'
    if (i.month>=6) & (i.month <=8):    #Jun-Aug
        season='Summer'
    if (i.month>=9) & (i.month <=11):   #Sept-Nov
        season='Autumn'
    
    smartmeter[i] = np.zeros(len(Customer_Summary))
    heatpump[i] = np.zeros(len(Customer_Summary))
    pv[i] = np.zeros(len(Customer_Summary))
    demand[i] = np.zeros(len(Customer_Summary))      
    demand_delta[i] = np.zeros(len(Customer_Summary)) 
    pv_delta[i] = np.zeros(len(Customer_Summary)) 
    
    #-----for each customer set timestep demand and PV output----#
    for z in range(0, len(Customer_Summary)):
        smartmeter[i][z] = SM_DataFrame[Customer_Summary['Acorn_Group'][z]][season+day][Customer_Summary['smartmeter_ID'][z]][i]
        if Customer_Summary['heatpump_ID'][z] != 0:
            heatpump[i][z] = HP_DataFrame[str(Customer_Summary['heatpump_ID'][z])][i]
        if Customer_Summary['PV_kW'][z] != 0:
            pv[i][z] = Customer_Summary['PV_kW'][z]*PV_DataFrame[Customer_Summary['pv_ID'][z]]['P_Norm'][i]
        demand[i][z] = smartmeter[i][z] + heatpump[i][z]
    
    demand[i]=np.nan_to_num(demand[i])
    pv[i]=np.nan_to_num(pv[i])
    
    CurArray[i], VoltArray[i], Losses[i], TranskVA_sum[i], RateArray, TransRatekVA= runDSS(Network_Path,demand[i],pv[i],demand_delta[i],pv_delta[i])
    
    network_summary[i]= network_visualise(CurArray[i], RateArray, VoltArray[i],TranskVA_sum[i],TransRatekVA)
    
    network_summary_new[i] = network_summary[i]

Headrm, Footrm, Flow, Rate, Customer_Summary, custph, InputsbyFP = Headroom_calc(network_summary, Customer_Summary, smartmeter, heatpump, pv,demand,demand_delta,pv_delta)   
Chigh_count, Vhigh_count, Vlow_count=counts(network_summary)
#Coords,Lines = plots(Network_Path,Chigh_count, Vhigh_count,Vlow_count)

labels={'col':'red','style':'--','label': 'Initial'}
plot_headroom(Headrm, Footrm, Flow, Rate, labels)

##----------- Validation of adjusted demand ------------------#
for i in network_summary:
    for p in range(1,4):
        for f in range(1,5):
            if Headrm[f][p][i] <0 and (demand[i][custph[p][f].index].sum() >= pv[i][custph[p][f].index].sum()):
                demand_delta[i][custph[p][f].index] = Headrm[f][p][i] / len(custph[p][f])
            
            if Footrm[f][p][i] <0 and (demand[i][custph[p][f].index].sum() < pv[i][custph[p][f].index].sum()):
                pv_delta[i][custph[p][f][custph[p][f]['PV_kW']>0].index] = (Footrm[f][p][i] / len(custph[p][f][custph[p][f]['PV_kW']>0].index))
    
    if (demand_delta[i].sum() + pv_delta[i].sum()) != 0:
        CurArray[i], VoltArray[i], Losses[i], TranskVA_sum[i], RateArray, TransRatekVA= runDSS(Network_Path,demand[i],pv[i],demand_delta[i],pv_delta[i])
        
        network_summary_new[i]= network_visualise(CurArray[i], RateArray, VoltArray[i],TranskVA_sum[i],TransRatekVA)

Headrm_new, Footrm_new, Flow_new, Rate, Customer_Summary, custph, InputsbyFP_new = Headroom_calc(network_summary_new, Customer_Summary, smartmeter, heatpump, pv,demand,demand_delta,pv_delta)    
Chigh_count_new, Vhigh_count_new, Vlow_count_new=counts(network_summary_new)

labels={'col':'blue','style':'-','label': 'With Adjustments'}
plot_headroom(Headrm_new, Footrm_new, Flow_new,Rate,labels)
plot_flex(InputsbyFP_new)  