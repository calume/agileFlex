# -*- coding: utf-8 -*-
"""
Created on Thu May 02 13:48:06 2019
Date ranges
Smart Meter Data: 1/6/2012 - 28/2/2014
Heat Pump Data: 1/12/2013 - 1/3/2015

Full overlap 1/12/2013 to 28/2/2014

@author: Calum Edmunds
"""


######## Importing the OpenDSS Engine  #########
import numpy as np
import pandas as pd

pd.options.mode.chained_assignment = None
from datetime import timedelta, date, datetime
import random
import pickle
from Test_Network.network_plot import customer_summary
from runDSS import runDSS, network_outputs, create_gens
import matplotlib.pyplot as plt
from Forecasting.Headroom_forecasting import return_temp
from zonal_summary import daily_EVSchedule,plotDay
from itertools import cycle, islice
from crunch_results import (
    counts,
    plots,
    Headroom_calc,
    plot_headroom,
    plot_flex,
    plot_current_voltage,
    
    
)


####----------Set Test Network ------------
start=datetime.now()

Case='25PV50HP'
Network='network_1/'

########### Create Forecast File if not already Done ##########

#wkd_temps,wknd_temps=hdrm_forecast(Network,Case)

Network_Path = "Test_Network/"+str(Network)
##create_gens(Network_Path)

#### Load in Test data Set ##########

####  Note: These Data Files can be found in the AGILE dropbox folder:
###-- 'AGILE Project Documents\Data\Network_Inputs_SM_PV_HP'

pick_in = open("../Data/SM_byAcorn_NH.pickle", "rb")
SM_DataFrame = pickle.load(pick_in)

pick_in = open("../Data/HP_DataFrame_hh_mean.pickle", "rb")
HP_DataFrame = pickle.load(pick_in)


pick_in = open("../Data/PV_BySiteName.pickle", "rb")
PV_DataFrame = pickle.load(pick_in)

       
#########----- Plus 1 year to SM timestamps to line up with PV and HP
#for i in SM_DataFrame.keys():
#   SM_DataFrame[i].index = SM_DataFrame[i].index + timedelta(days=364)

def Create_Customer_Summary(sims):
    ####--------- Create Customer Summary ----------
    
    Customer_Summary, Coords, Lines, Loads = customer_summary(Network_Path)
    Customer_Summary = Customer_Summary.drop(columns="Color")
    
    # ---------- Assign Smart Meter and Heat Pump IDs--------------#
    #### Smart Meter
    # --- only include SMs with data
    Customer_Summary["smartmeter_ID"] = 0
    SMlist={}
    for i in SM_DataFrame.keys():
        acorn_index = Customer_Summary["Acorn_Group"][
            Customer_Summary["Acorn_Group"] == i
        ].index
    
        datacount = SM_DataFrame[i].reindex(sims)
        SM_reduced = datacount.count() > (len(datacount) * 0.95)
        print("SMs left " + str(i) + str(sum(SM_reduced)))
        SM_reduced = SM_reduced[SM_reduced]
        SMlist[i]=list(islice(cycle(SM_reduced.index),len(acorn_index)))
        for z in range(0,len(acorn_index)):
            Customer_Summary["smartmeter_ID"].loc[acorn_index[z]] = SMlist[i][z]
    
    ### Heat Pump
    Customer_Summary["heatpump_ID"] = 0
    # --- only include HPs with data for the timesteps modelled
    HP_reduced = HP_DataFrame.reindex(sims.tolist()).count()> (0.9*len(sims))
    
    HP_reduced = HP_reduced[HP_reduced]
    print("HPs left " + str(len(HP_reduced)))
    heatpump_index = Customer_Summary["Heat_Pump_Flag"][
        Customer_Summary["Heat_Pump_Flag"] > 0
    ].index
    HPlist=list(islice(cycle(HP_reduced.index),len(heatpump_index)))
    for z in range(0,len(heatpump_index)):
        Customer_Summary["heatpump_ID"][heatpump_index[z]] = HPlist[z]
    
    Customer_Summary['zone']=0
    for i in Customer_Summary.index:
        Customer_Summary['zone'].loc[i]=str(Customer_Summary['Phase'][i])+str(Customer_Summary['Feeder'][i])
    
    ### PV are assigned randomly
    Customer_Summary["pv_ID"] = 0
    pv_index = Customer_Summary["PV_kW"][Customer_Summary["PV_kW"] > 0].index
    pv_sites = list(islice(cycle(PV_DataFrame.keys()),len(Customer_Summary["pv_ID"])))
    for z in pv_index:
        Customer_Summary["pv_ID"][z] = pv_sites[z]
    
    ## Also remove data <0.005  (overnight)
    for i in pv_sites:
        PV_DataFrame[i][PV_DataFrame[i]["P_kW"] < 0.005] = 0
        ## Assign EVs ######
    
    ######------ For when the customer summary table is fixed we laod it in from the pickle file
    pickin = open("../Data/"+str(Network)+"Customer_Summary"+str(Case)+".pickle", "rb")
    Customer_Summary = pickle.load(pickin)
    for u in EV_DataFrame.keys():
        sub=Customer_Summary[Customer_Summary['Phase']==u[0]]
        sub=sub[sub['Feeder']==u[1]].index[0:len(EV_DataFrame[u].columns)]
        Customer_Summary['EV_ID'].loc[sub]=EV_DataFrame[u].columns.values
    ###----- Here we save the Customer Summary to Fix it so the smartmeter, HP, SM IDs are no longer
    ###------randomly assigned each run. We then load from the pickle file rather than generating it
    
    #    #pickle_out = open("../Data/Customer_Summary15.pickle", "wb")
    #    #pickle.dump(Customer_Summary, pickle_out)
    #    #pickle_out.close()
    return Coords, Lines, Customer_Summary,HP_reduced,HPlist, SMlist


######--------- Run power flow Timeseries--------------------------#
####### test dates: 2013-6-1 to 2014-6-1, full when SM dates are changed by plus 1 year

#start_date = date(2014, 6, 1)
#end_date = date(2014, 9, 3)
start_date = date(2013, 12, 1)
end_date = date(2013, 12, 3)
sims_halfhours = pd.date_range(start_date, end_date, freq=timedelta(hours=0.5))
sims_tenminutes = pd.date_range(start_date, end_date, freq=timedelta(minutes=10))[72:216]

sims=sims_tenminutes
pick_in = open("../Data/HP_DataFrame_10mins_week.pickle", "rb")
HP_DataFrame = pickle.load(pick_in)
HP_DataFrame = HP_DataFrame.loc[sims]

all_temps,dummy = return_temp('../')

if (sims.weekday[0] >= 0) & (sims.weekday[0] <= 4):
    daytype='wkd'

if (sims.weekday[0] >= 5) & (sims.weekday[0] <= 6):
    daytype='wknd'

temp=all_temps[sims[0]-timedelta(hours=12)]

EVCapacitySummary, EV_DataFrame = daily_EVSchedule(Network,Case, 1, daytype, temp)

for i in EV_DataFrame.keys():
    EV_DataFrame[i].index=(sims_tenminutes.tolist())
for i in SM_DataFrame.keys():
    SM_DataFrame[i]=SM_DataFrame[i].reindex(sims_halfhours.tolist())
    SM_DataFrame[i]=SM_DataFrame[i].resample('10T').mean()
    for k in SM_DataFrame[i].columns:
       SM_DataFrame[i][k]=SM_DataFrame[i][k].interpolate(method='pad')

for i in PV_DataFrame.keys():
    PV_DataFrame[i]=PV_DataFrame[i].reindex(sims_halfhours.tolist())
    PV_DataFrame[i]=PV_DataFrame[i].resample('10T').mean()
    for k in PV_DataFrame[i].columns:
        PV_DataFrame[i][k]=PV_DataFrame[i][k].interpolate(method='pad')

Coords, Lines, Customer_Summary, HP_reduced,HPlist,SMlist = Create_Customer_Summary(sims)  


#####------------ Initialise Input--------------------
smartmeter = {}
heatpump = {}
pv = {}
demand = {}  # Sum of smartmeter, heatpump and EV
demand_delta = {}  # adjustment for sensitivity, set to 0 when no sensitivity
pv_delta = {}  # adjustment for sensitivity, set to 0 when no sensitivity
PFControl = {}  # Reactive power compensation for high voltage control
ev={}
#####-------------Initialise Output --------------
#####-- These are produced by the OpenDSS Load Flow
CurArray = {}
VoltArray = {}
TransArray = {}
LoadArray = {}
PowArray = {}
CurArray_new = {}
VoltArray_new = {}
PowArray_new = {}
Trans_kVA_new = {}
Losses = {}
TranskVA_sum = {}
Trans_kVA = {}
network_summary = {}
network_summary_new = {}

genres=pd.Series(index=sims.tolist(), dtype=float)
genresnew=pd.Series(index=sims.tolist(), dtype=float)
colors = ["#9467bd", "#ff7f0e", "#d62728", "#bcbd22", "#1f77b4", "#bcbd22",'#17becf','#8c564b','#17becf']
bad_halfhours=[]
bad_halfhours_n=[]     
pinchClist=[]
for i in Lines['Line'].str[9:10].unique():
    pinchClist.append(Lines[Lines['Line'].str[9:10] == i].index[0])

for i in sims.tolist():
    print(i)
    # -------------- Sample for each day weekday/weekend and season -----------#
    ##-- Needed for SM data, and will be used for sampling --#
    smartmeter[i] = np.zeros(len(Customer_Summary))
    heatpump[i] = np.zeros(len(Customer_Summary))
    ev[i] = np.zeros(len(Customer_Summary))
    pv[i] = np.zeros(len(Customer_Summary))
    demand[i] = np.zeros(len(Customer_Summary))
    demand_delta[i] = np.zeros(len(Customer_Summary))
    pv_delta[i] = np.zeros(len(Customer_Summary))
    ##--- By Defailt Power Factor control is off, only when thermal overloads
    ##-- are PFControl turned on
    PFControl[i] = 0
    # -----for each customer set timestep demand and PV output----#
    for z in range(0, len(Customer_Summary)):
        smartmeter[i][z] = SM_DataFrame[Customer_Summary["Acorn_Group"][z]][Customer_Summary["smartmeter_ID"][z]][i]
        if Customer_Summary["heatpump_ID"][z] != 0:
            heatpump[i][z] = HP_DataFrame[str(Customer_Summary["heatpump_ID"][z])][i]
        if Customer_Summary["PV_kW"][z] != 0:
            pv[i][z] = (
                Customer_Summary["PV_kW"][z]
                * PV_DataFrame[Customer_Summary["pv_ID"][z]]["P_Norm"][i]#-timedelta(days=364)]
            )
        if Customer_Summary["EV_ID"][z] != 0:
            ev[i][z] = EV_DataFrame[Customer_Summary["zone"][z]][Customer_Summary["EV_ID"][z]][i]
        ev[i] = np.nan_to_num(ev[i])    
        demand[i][z] = smartmeter[i][z] + heatpump[i][z] + ev[i][z]

    ###------ Demand includes Smartmeter and heatpump
    demand[i] = np.nan_to_num(demand[i])
    pv[i] = np.nan_to_num(pv[i])

    ###---- Load Flow is run and currents, voltages etc are rteurned
    (
        CurArray[i],
        VoltArray[i],
        PowArray[i],
        Losses[i],
        Trans_kVA[i],
        RateArray,
        TransRatekVA,
        genres[i],
        converged
    ) = runDSS(
        Network_Path, demand[i], pv[i], demand_delta[i], pv_delta[i], PFControl[i] 
    )
            
    ###--- These are converted into headrooms and summarised in network_summary
    network_summary[i] = network_outputs(
        Network_Path,CurArray[i], RateArray, VoltArray[i], PowArray[i], Trans_kVA[i], TransRatekVA, pinchClist
    )
    
    if converged==False:   
        j=i-timedelta(minutes=10)
        bad_halfhours.append(i)
        network_summary[i]=network_summary[j]
        CurArray[i],VoltArray[i],PowArray[i],Trans_kVA[i] = CurArray[j],VoltArray[j],PowArray[j],Trans_kVA[j]
    ###---- A new network summary is created to store any adjustments
    network_summary_new[i] = network_summary[i]
    genresnew[i]=genres[i]
    CurArray_new[i], VoltArray_new[i], PowArray_new[i], Trans_kVA_new[i] = CurArray[i], VoltArray[i], PowArray[i], Trans_kVA[i]

#####----- Data is converted to DataFrames (Slow process could be removed to speed things up)
Headrm, Footrm, Flow, Rate, Customer_Summary, custph, InputsbyFP = Headroom_calc(
    network_summary,
    Customer_Summary,
    smartmeter,
    heatpump,
    pv,
    ev,
    demand,
    demand_delta,
    pv_delta,
    pinchClist
)
Chigh_count, Vhigh_count, Vlow_count, VHpinch =counts(network_summary,Coords,pinchClist)
Coords = plots(Network_Path,Chigh_count, Vhigh_count,Vlow_count,pinchClist,colors)
Vmax,Vmin,Cmax=plot_current_voltage(CurArray,VoltArray,Coords,Lines,Flow,RateArray, pinchClist,colors)
plot_flex(InputsbyFP,pinchClist,colors)
labels = {"col": "red", "style": "--", "label": "Initial", "TranskVA": TransRatekVA}
plot_headroom(Headrm, Footrm, Flow, Rate, labels,pinchClist,InputsbyFP,genres,colors)

end=datetime.now()
print('=========== RESULTS FOR '+str(Network)+' Case '+str(Case)+'==============')
print('Tomorrow is a '+str(daytype)+ ' with forecast temperature '+str(temp)+'deg C')
time=end-start
print('Days Optimisation took '+str(time))
print('Number of EVs able to charge is '+str(EVCapacitySummary['EV Capacity'].sum())+' out of '+str(EVCapacitySummary['Customers'].sum())+' Customers')

#pickle_out = open("../Data/100HPDec1st2013_2mins_Hdrm.pickle", "wb")
#pickle.dump(Headrm, pickle_out)
#pickle_out.close()

