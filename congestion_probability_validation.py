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
# from multiprocessing import Pool
import multiprocessing
from joblib import Parallel, delayed
from tqdm import tqdm
#from Forecasting.Headroom_forecasting import return_temp
from zonal_summary import daily_EVSchedule
from itertools import cycle, islice
from crunch_results_batch import (
    counts,
    plots,
    Headroom_calc,
    plot_headroom,
    plot_flex,
    calc_current_voltage,
)
####----------Set Test Network ------------
start=datetime.now()

pick_in = open("../Data/All_VC_Limits.pickle", "rb")
All_VC = pickle.load(pick_in)

pick_in = open("../Data/SM_byAcorn_NH.pickle", "rb")
SM_DataFrame = pickle.load(pick_in)

pick_in = open("../Data/HP_DataFrame_hh_mean.pickle", "rb")
HP_DataFrame = pickle.load(pick_in)

pick_in = open("../Data/PV_BySiteName.pickle", "rb")
PV_DataFrame = pickle.load(pick_in)

pick_in = open("../Data/Assign_Final.pickle", "rb")
assign = pickle.load(pick_in)

num_cores = multiprocessing.cpu_count()

networks=['network_17/']#,'network_5/','network_10/','network_17/','network_18/']
# inputs = tqdm(networks)
EVCapacitySummary={}
AllEVs={}

#def spool(Network):
for Network in networks:
    print(Network)    
    ########### Create Forecast File if not already Done ##########
    
    #wkd_temps,wknd_temps=hdrm_forecast(Network,Case)
    
    Network_Path = "Test_Network/condensed/"+str(Network)
    ##create_gens(Network_Path)
    
    #### Load in Test data Set ##########
    
    ####  Note: These Data Files can be found in the AGILE dropbox folder:
    ###-- 'AGILE Project Documents\Data\Network_Inputs_SM_PV_HP'
     
    #########----- Plus 1 year to SM timestamps to line up with PV and HP
    # for i in SM_DataFrame.keys():
    #   SM_DataFrame[i].index = SM_DataFrame[i].index + timedelta(days=364)
    
    
    ########--------- Code to load dates with highest HP demand for testing-------------##########
    days=[]
    for w in assign[Network].index:
        if assign[Network][w] != '00PV00HP':
            pick_in = open("../Data/"+str(Network+assign[Network][w])+"_WinterHdRm_Raw.pickle", "rb")
            HdRm = pickle.load(pick_in)
        if assign[Network][w] == '00PV00HP':
            pick_in = open("../Data/"+str(Network+'00PV25HP')+"_WinterHdRm_Raw.pickle", "rb")
            HdRm = pickle.load(pick_in)          
        HdRm=HdRm[w]
        days.append(HdRm.sum(axis=1).idxmin().date())
    days=pd.Series(days).unique()
    ######--------- Run power flow Timeseries--------------------------#
    Voltage_data={}
    daycount=0
    for d in days[:2]:
        print(d)
        pick_in = open('../Data/'+Network+'EV_Dispatch_OneDay.pickle', "rb")
        EV_DataFrame = pickle.load(pick_in)

        #EVCapacitySummary, EV_DataFrame = daily_EVSchedule(Network)
        
        Y=14
        start_date = d#date(2013, 12, 2)
        end_date = d+timedelta(days=2)#date(2013, 12, 4)
        sims_halfhours = pd.date_range(start_date, end_date, freq=timedelta(hours=0.5))
        sims_tenminutes = pd.date_range(start_date, end_date, freq=timedelta(minutes=10))[72:216]
        
        sims=sims_tenminutes
        pick_in = open("../Data/HP_DataFrame_10mins.pickle", "rb")
        HP_DataFrame = pickle.load(pick_in)
        HP_DataFrame = HP_DataFrame.loc[sims]
        
        #all_temps,dummy = return_temp('../')
        
        # if (sims.weekday[0] >= 0) & (sims.weekday[0] <= 4):
        #     daytype='wkd'
        
        # if (sims.weekday[0] >= 5) & (sims.weekday[0] <= 6):
        #     daytype='wknd'
        
        # temp=all_temps[sims[0]-timedelta(hours=12)]
        
        for i in EV_DataFrame.keys():
            EV_DataFrame[i]=EV_DataFrame[i].resample('10T').sum()
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
        
        Customer_Summary, Coords, Lines, Loads = customer_summary(Network_Path, '00PV25HP')
        
        ######------ For when the customer summary table is fixed we laod it in from the pickle file
        pickin = open("../Data/"+str(Network)+"Customer_Summary_Final.pickle", "rb")
        Customer_Summary = pickle.load(pickin)
        Customer_Summary=Customer_Summary['Final']
        for u in EV_DataFrame.keys():
            sub=Customer_Summary[Customer_Summary['zone']==u]
            if len(sub)>0:
                sub=sub.index[0:len(EV_DataFrame[u].columns)]
                Customer_Summary['EV_ID'].loc[sub]=EV_DataFrame[u].columns.values
        
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
            
        pinchClist=list(Lines[Lines['Bus1']=='Bus1=11'].index)
        if Network=='network_10/':
            pinchClist.remove(34)
        
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
                Network,CurArray[i], RateArray, VoltArray[i], PowArray[i], Trans_kVA[i], TransRatekVA, pinchClist,All_VC
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
        Headrm, Footrm, Flow, Rate, Customer_Summary, custph = Headroom_calc(
            network_summary,
            Customer_Summary,
            smartmeter,
            heatpump,
            pv,
            demand,
            demand_delta,
            pv_delta,
            pinchClist
        )
        
        Chigh_count, Vhigh_count, Vlow_count, VHpinch =counts(network_summary,Coords,pinchClist)
        #Coords = plots(Network_Path,Chigh_count, Vhigh_count,Vlow_count,pinchClist,colors)
        Vmax,Vmin,Cmax=calc_current_voltage(CurArray,VoltArray,Coords,Lines,Flow,RateArray, pinchClist,colors)
        #plot_current_voltage(Vmax, Vmin, Cmax, RateArray, pinchClist,colors,Network,'FirstPass')
        #plot_flex(InputsbyFP,pinchClist,colors)
        labels = {"col": "red", "style": "--", "label": "Initial", "TranskVA": TransRatekVA}
        #plot_headroom(Headrm, Footrm, Flow, Rate, labels,pinchClist,InputsbyFP,genres,colors)
        
        if daycount==0:
            Voltage_data['Vmin']=Vmin
            Voltage_data['Flow']=Flow
        else:    
            Voltage_data['Vmin']=Voltage_data['Vmin'].append(Vmin)
            for f in Flow:
                Voltage_data['Flow'][f]=Voltage_data['Flow'][f].append(Flow[f])
        
        daycount=daycount+1
    
    pickle_out = open("../Data/"+Network+"validation/Winter"+str(Y)+"_V_Data.pickle", "wb")
    pickle.dump(Voltage_data, pickle_out)
    pickle_out.close() 
    end=datetime.now()
    #print('Tomorrow is a '+str(daytype)+ ' with forecast temperature '+str(temp)+'deg C')
    time=end-start
    print(str(len(days))+' Days Validation took '+str(time))

inputs = tqdm(networks)

# if __name__ == "__main__":
#     processed_list = Parallel(n_jobs=num_cores)(delayed(spool)(i) for i in inputs)