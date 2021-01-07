
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
from runDSS import runDSS, create_gens
import matplotlib.pyplot as plt
from crunch_results_batch import (
    counts,
    plots,
    Headroom_calc,
    plot_headroom,
    plot_flex,
    calc_current_voltage,
    plot_current_voltage,
    
)
from itertools import cycle, islice
from openpyxl import load_workbook
#from voltage_headroom import voltage_headroom

networks=['network_10/']#,'network_5/','network_10/','network_18/']#,'network_18/']
Cases=['25PV75HP','50PV100HP']
EVPens=[80,100]
paths="../Data/Dumb/"


def runbatch(networks,Cases,PrePost,paths,EVPens):
    ### --- All VC Limits is Current limits set by Low Voltage
    
       
    ####----------Set Test Network ------------

    start_date = date(2013, 12, 1)
    end_date = date(2013, 12, 31)
    sims_halfhours = pd.date_range(start_date, end_date, freq=timedelta(hours=0.5))
    
    sims = pd.date_range(start_date, end_date, freq=timedelta(minutes=10))
    
    for N in networks:
        for C in Cases:
            for E in EVPens:
                #### Load in Test data Set ##########
    
                pick_in = open("../Data/SM_byAcorn_NH.pickle", "rb")
                SM_DataFrame = pickle.load(pick_in)
                
                pick_in = open("../Data/JDEVResampled.pickle", "rb")
                EV_DataFrame = pickle.load(pick_in)
                EV_DataFrame=EV_DataFrame.fillna(0)
                EV_DataFrame.index=EV_DataFrame.index.time
                pick_in = open("../Data/HP_DataFrame_10mins_pad.pickle", "rb")
                HP_DataFrame = pickle.load(pick_in)
    
                pick_in = open("../Data/PV_BySiteName.pickle", "rb")
                PV_DataFrame = pickle.load(pick_in)
                print(N,C,E)
                Network_Path = "Test_Network/condensed/"+N
                #################create_gens(Network_Path)  ###--- Creates generators in OpenDSS
                       
                
                def Create_Customer_Summary(sims):
                    ####--------- Create Customer Summary ----------
                    
                    Customer_Summary, Coords, Lines, Loads = customer_summary(Network_Path, C)
                    Customer_Summary = Customer_Summary.drop(columns="Color")
                    
                    # ---------- Assign Smart Meter and Heat Pump IDs--------------#
                    #### Smart Meter
                    # --- only include SMs with data for day 2014-3-1
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
                    
                    ### PV are assigned randomly
                    Customer_Summary["pv_ID"] = 0
                    pv_index = Customer_Summary["PV_kW"][Customer_Summary["PV_kW"] > 0].index
                    pv_sites = list(islice(cycle(PV_DataFrame.keys()),len(Customer_Summary["pv_ID"])))
                    for z in pv_index:
                        Customer_Summary["pv_ID"][z] = pv_sites[z]
                    
                    ## Also remove data <0.005  (overnight)
                    for i in pv_sites:
                        PV_DataFrame[i][PV_DataFrame[i]["P_kW"] < 0.005] = 0
                    
                    ###----- Here we save the Customer Summary to Fix it so the smartmeter, HP, SM IDs are no longer
                    ###------randomly assigned each run. We then load from the pickle file rather than generating it
                    
                    pickle_out = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_Customer_Summary.pickle", "wb")
                    pickle.dump(Customer_Summary, pickle_out)
                    pickle_out.close()
                    return Coords, Lines, Customer_Summary,HP_reduced,HPlist, SMlist
                
                #def save_inputs(smartmeter,demand,heatpump,pv,ev,N,C,E):  
                def save_inputs(heatpump,N,C,E):       
#                    pickle_out = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_smartmeter.pickle", "wb")
#                    pickle.dump(smartmeter, pickle_out)
#                    pickle_out.close()
#                    pickle_out = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_demand.pickle", "wb")
#                    pickle.dump(demand, pickle_out)
#                    pickle_out.close()
                    pickle_out = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_heatpump.pickle", "wb")
                    pickle.dump(heatpump, pickle_out)
                    pickle_out.close()
#                    pickle_out = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_pv.pickle", "wb")
#                    pickle.dump(pv, pickle_out)
#                    pickle_out.close()
#                    pickle_out = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_ev.pickle", "wb")
#                    pickle.dump(ev, pickle_out)
#                    pickle_out.close()
    
                def save_outputs(CurArray, RateArray, VoltArray, PowArray, Trans_kVA, TransRatekVA,N,C,E):
                    pickle_out = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_CurArray.pickle", "wb")
                    pickle.dump(CurArray, pickle_out)
                    pickle_out.close() 
                    pickle_out = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_RateArray.pickle", "wb")
                    pickle.dump(RateArray, pickle_out)
                    pickle_out.close()
                    pickle_out = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_VoltArray.pickle", "wb")
                    pickle.dump(VoltArray, pickle_out)
                    pickle_out.close()   
                    pickle_out = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_PowArray.pickle", "wb")
                    pickle.dump(PowArray, pickle_out)
                    pickle_out.close()
                    pickle_out = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_Trans_kVA.pickle", "wb")
                    pickle.dump(Trans_kVA, pickle_out)
                    pickle_out.close()
                    pickle_out = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_TransRatekVA.pickle", "wb")
                    pickle.dump(TransRatekVA, pickle_out)
                    pickle_out.close()
                    
                def load_inputs(N,C,E):
                    pick_in = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_smartmeter.pickle", "rb")
                    smartmeter = pickle.load(pick_in)
                    pick_in = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_demand.pickle", "rb")
                    demand = pickle.load(pick_in)
                    pick_in = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_heatpump.pickle", "rb")
                    heatpump = pickle.load(pick_in)
                    pick_in = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_pv.pickle", "rb")
                    pv = pickle.load(pick_in)
                    pick_in = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_ev.pickle", "rb")
                    ev = pickle.load(pick_in)   
                    return(smartmeter,demand,heatpump,pv,ev)
                
                def load_outputs(N,C,E):
                    pick_in = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_CurArray.pickle", "rb")
                    CurArray = pickle.load(pick_in)
                    pick_in = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_RateArray.pickle", "rb")
                    RateArray = pickle.load(pick_in)
                    pick_in = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_VoltArray.pickle", "rb")
                    VoltArray = pickle.load(pick_in)
                    pick_in = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_PowArray.pickle", "rb")
                    PowArray = pickle.load(pick_in)    
                    pick_in = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_Trans_kVA.pickle", "rb")
                    Trans_kVA = pickle.load(pick_in) 
                    pick_in = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_TransRatekVA.pickle", "rb")
                    TransRatekVA = pickle.load(pick_in) 
    
                    return(CurArray, RateArray, VoltArray, PowArray, Trans_kVA, TransRatekVA)
            
                
                ######--------- Run power flow Timeseries--------------------------#
                def raw_input_data():
    
                    
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
                    ##Customer_Summary, Coords, Lines, Loads = customer_summary(Network_Path, C)
                    ####------ For when the customer summary table is fixed we laod it in from the pickle file
                    #pickin = open("../Data/"+str(N)+"Customer_Summary"+str(C)+str(Y)+".pickle", "rb")
                    #Customer_Summary = pickle.load(pickin)
                         
                    #####------------ Initialise Input--------------------
                    smartmeter = {}
                    heatpump = {}
                    pv = {}
#                    evdailys=pd.DataFrame(index=np.unique(sims.date), columns=range(0,len(Customer_Summary)))
#                    ev={}
#                    evflags=np.zeros(len(Customer_Summary))
                    demand = {}  # Sum of smartmeter, heatpump and EV
                    #####-------------Initialise Output --------------
                    #####-- These are produced by the OpenDSS Load Flow
                    c=1
#                    for a in evdailys.columns:
#                        evdailys[a]=EV_DataFrame.columns[len(evdailys)*(c-1):len(evdailys)*c]
#                        c=c+1
#                        if len(evdailys)*c > len(EV_DataFrame.columns):
#                            c=1
                    
#                    for u in Customer_Summary['zone'].unique():
#                        idx=Customer_Summary[Customer_Summary['zone']==u].index[::(int(100/E))]
#                        evflags[idx]=1
                    for i in sims.tolist():
                        print(i)
                        # -------------- Sample for each day weekday/weekend and season -----------#
                        ##-- Needed for SM data, and will be used for sampling --#
                        #smartmeter[i] = np.zeros(len(Customer_Summary))
                        #ev[i] = np.zeros(len(Customer_Summary))
                        heatpump[i] = np.zeros(len(Customer_Summary))
                        #pv[i] = np.zeros(len(Customer_Summary))
#                        demand[i] = np.zeros(len(Customer_Summary))
                        # -----for each customer set timestep demand and PV output----#
#                        EVRel=EV_DataFrame.loc[i.time()]
#                        dailysrel=evdailys.loc[i.date()]
                        
                        for z in range(0, len(Customer_Summary)):
                            #ev[i][z]=EVRel[dailysrel].iloc[z]*evflags[z]
                            #smartmeter[i][z] = SM_DataFrame[Customer_Summary["Acorn_Group"][z]][Customer_Summary["smartmeter_ID"][z]][i]
                            if Customer_Summary["heatpump_ID"][z] != 0:
                                heatpump[i][z] = HP_DataFrame[str(Customer_Summary["heatpump_ID"][z])][i]
#                            if Customer_Summary["PV_kW"][z] != 0:
#                                pv[i][z] = (Customer_Summary["PV_kW"][z] * PV_DataFrame[Customer_Summary["pv_ID"][z]]["P_Norm"][i]) 
                            #demand[i][z] = smartmeter[i][z] + heatpump[i][z] +ev[i][z]
                    
                        ###------ Demand includes Smartmeter and heatpump
                        #demand[i] = np.nan_to_num(demand[i])
                        #pv[i] = np.nan_to_num(pv[i])
                    
#                    save_inputs(smartmeter,demand,heatpump,pv,ev, N,C, E)
                    save_inputs(heatpump,N,C, E)
#                    return evdailys,ev,evflags,Customer_Summary
                    return Customer_Summary
                            
                def do_loadflows(sims,Customer_Summary):
                    smartmeter,demand,heatpump,pv,ev=load_inputs(N, C,E)
                    demand={}
                    CurArray = {}
                    VoltArray = {}
                    PowArray = {}
                    Losses = {}
                    Trans_kVA = {}
                    genres=pd.Series(index=sims.tolist(), dtype=float)
                    for i in sims.tolist():
                        demand[i] = smartmeter[i] + heatpump[i] +ev[i]
                        demand[i] = np.nan_to_num(demand[i])
                        print(i)
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
                        ) = runDSS(Network_Path, demand[i], pv[i],ev[i])
                                
                    save_outputs(CurArray, RateArray, VoltArray, PowArray, Trans_kVA, TransRatekVA,N,C, E)
                    
                def post_process(N,C,E):
                    #smartmeter,demand,heatpump,pv=load_inputs(N, C, E)
                    Customer_Summary, Coords, Lines, Loads = customer_summary(Network_Path, C)
                    pinchClist=list(Lines[Lines['Bus1']=='Bus1=11'].index)
                    
                    if N=='network_10/':
                        pinchClist.remove(28)
                    
                    CurArray, RateArray, VoltArray, PowArray, Trans_kVA, TransRatekVA = load_outputs(N, C,E)

                    colors = ["#9467bd", "#ff7f0e", "#d62728", "#bcbd22", "#1f77b4", "#bcbd22",'#17becf','#8c564b','#17becf']
                    #####----- Data is converted to DataFrames (Slow process could be removed to speed things up)
                    ####=========== Create List of Zones (feeders and phases) for Flow DataFrame Columns
                   
                    Vmin,C_Violations=calc_current_voltage(CurArray,VoltArray,Coords,Lines, RateArray, pinchClist,colors,sims)
                    
                    
                    pickle_out = open("../Data/Dumb/"+N+C+'EV'+str(E)+"_C_Violations.pickle", "wb")
                    pickle.dump(C_Violations, pickle_out)
                    pickle_out.close()            
                    
                    pickle_out = open("../Data/Dumb/"+N+C+'EV'+str(E)+"_Vmin_DF.pickle", "wb")
                    pickle.dump(Vmin, pickle_out)
                    pickle_out.close()     

                if PrePost=='Pre':
                    raw_input_data()
                    Customer_Summary=raw_input_data()
                    do_loadflows(sims,Customer_Summary)
                if PrePost=='Post':
                    post_process(N, C, E)

runbatch(networks,Cases,'Pre',paths,EVPens)
runbatch(networks,Cases,'Post',paths,EVPens)