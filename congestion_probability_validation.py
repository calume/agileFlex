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
#from Forecasting.Headroom_forecasting import return_temp
from zonal_summary import EVRealiser
from congestion_probability_batch import save_outputs, post_process

def runvalid(data_path,networks,paths,quant,factor,evtype,start_date,end_date):
    ####----------Set Test Network ------------
    
    EVCapacitySummary={}
    
    for N in networks:
        print(N)    

        
        Network_Path = "Test_Network/condensed/"+str(N)

        ####----- I previously ran this for worst case days. But instead I propose to simply run for a week. Makes processing much easier
        ####----- if the days and timesteps are consecutive. Im sure this could be sorted out
        # ###--- Load dates with highest HP demand for validation
        # days=[]
        # for w in assign[N].index:
        #     pick_in = open(paths+N+assign[N][w]+"_WinterHdRm_All.pickle", "rb")
        #     HdRm = pickle.load(pick_in)      
        #     HdRm=HdRm[w]
        #     days.append(HdRm.sum(axis=1).idxmin().date())
        # days=pd.Series(days).unique()
        # ######--------- Run power flow Timeseries--------------------------#
        # Voltage_data={}
        # daycount=0
        # for d in days:
        #  print(d)
        pick_in = open("../Data/SM_byAcorn_NH.pickle", "rb")
        SM_DataFrame = pickle.load(pick_in)
        
        
        pick_in = open("../Data/PV_BySiteName.pickle", "rb")
        PV_DataFrame = pickle.load(pick_in)
        
        sims_halfhours = pd.date_range(start_date, end_date, freq=timedelta(hours=0.5))
        sims_tenminutes = pd.date_range(start_date, end_date, freq=timedelta(minutes=10))[72:216]
        
        sims=sims_tenminutes
        
        ###--- Load in Dumb and Smart EV profiles and reindex
        pick_in = open("../Data/JDEVResampled.pickle", "rb")
        EV_DataFrame_Dumb = pickle.load(pick_in)
        EV_DataFrame_Dumb=EV_DataFrame_Dumb.fillna(0)
        EV_DataFrame_Dumb.index=sims

        if evtype=='OptEV':
            print('optimised #############')
            EVCapacitySummary, EV_DataFrame, V2G_Perc = EVRealiser(networks, paths,quant,factor,True)
        
        if evtype=='Dumb':
            print('Dumb #############')
            pick_in = open(paths+str(N)+"EV_DataFrame_Smart.pickle", "rb")
            EV_DataFrame = pickle.load(pick_in)
        
        for i in EV_DataFrame:
            EV_DataFrame[i]=EV_DataFrame[i][~EV_DataFrame[i].index.duplicated(keep='first')]
            EV_DataFrame[i].index=sims
        
        pick_in = open("../Data/HP_DataFrame_10mins_pad.pickle", "rb")
        HP_DataFrame = pickle.load(pick_in)
        HP_DataFrame = HP_DataFrame.loc[sims]
        

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
        pickin = open(paths+str(N)+"Customer_Summary_Final.pickle", "rb")
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
        PowArray = {}
        Losses = {}
        Trans_kVA = {}

        
        genres=pd.Series(index=sims.tolist(), dtype=float)
        colors = ["#9467bd", "#ff7f0e", "#d62728", "#bcbd22", "#1f77b4", "#bcbd22",'#17becf','#8c564b','#17becf']

        pinchClist=list(Lines[Lines['Bus1']=='Bus1=11'].index)
        if N=='network_10/':
            pinchClist.remove(34)
        TransAll=pd.Series(index=sims)
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
                    
                    if evtype=='OptEV':
                        ev[i][z] = EV_DataFrame[Customer_Summary["zone"][z]][Customer_Summary["EV_ID"][z]][i]

                    ###--- We have assigned the same EV IDs as for smart charging----##                   
                    if evtype=='Dumb':
                        ev[i][z] = EV_DataFrame_Dumb[Customer_Summary["EV_ID"][z]][i]
        
            ev[i] = np.nan_to_num(ev[i])   
            demand[i] = np.nan_to_num(demand[i])
            pv[i] = np.nan_to_num(pv[i])
            
            demand[i] = smartmeter[i] + heatpump[i] + ev[i]
        
            ###------ Demand includes Smartmeter and heatpump

        
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
                Network_Path, demand[i], pv[i],ev[i]
            )
        
        save_outputs(data_path,CurArray, RateArray, VoltArray, PowArray, Trans_kVA, TransRatekVA,N,evtype)
               
        post_process('../Data/Validation/',data_path,N, evtype, True,sims,Network_Path,'../Data/Validation/')  
        post_process('../Data/Validation/',data_path,N, evtype, False,sims,Network_Path,'../Data/Validation/')         
        
        pick_in = open('../Data/Validation/'+N+evtype+"_C_Violations.pickle", "rb")
        C_violations = pickle.load(pick_in)
        
        pick_in = open('../Data/Validation/'+N+evtype+"_Vmin_DF.pickle", "rb")
        Vmin = pickle.load(pick_in)
        
        pick_in = open('../Data/Validation/'+N+evtype+"_TxHdrm.pickle", "rb")
        Tx = pickle.load(pick_in)
        
        C_Viol=round((C_violations.sum(axis=1)>0).sum()/144*100,1)
        V_Viol=round((((Vmin<0.9).sum(axis=1)>0).sum())/144*100,1)
        T_Viol=round((Tx<0).sum()/144*100,1)
         
        return C_Viol, V_Viol, T_Viol

        
     ####--------------------- Below is the Old Way I stored the Results which links in with the code in Megaloader to summarise Results
     ####----------------------I have left in, this is a duplication of data and i may remove at some point and store one copy of data.
#             Vmin,C_Violations=calc_current_voltage(CurArray,VoltArray,Coords,Lines, RateArray, pinchClist,colors,sims)      
#             TransAll[i]=Trans_kVA[i]
#             #Vmax,Vmin, C_Violations=calc_current_voltage(CurArray,VoltArray,Coords,Lines,RateArray, pinchClist,colors)
#             #plot_flex(InputsbyFP,pinchClist,colors)
#             labels = {"col": "red", "style": "--", "label": "Initial", "TranskVA": TransRatekVA}
#             #plot_headroom(Headrm, Footrm, Flow, Rate, labels,pinchClist,InputsbyFP,genres,colors)
#             if daycount==0:
#                 Voltage_data['EV_summary']=pd.DataFrame(columns=days)
#                 Voltage_data['EV_summary'][d]=EVCapacitySummary['EV Capacity New']
#                 Voltage_data['Vmin']=Vmin
#                 Voltage_data['C_Violations']=C_Violations
#                 Voltage_data['Trans_kVA']=TransAll
#                 Voltage_data['V2gPerc']=pd.Series(index=days,dtype=float)
#                 Voltage_data['V2gPerc'][d]=np.mean(V2G_Perc)
#             else:
#                 Voltage_data['EV_summary'][d]=EVCapacitySummary['EV Capacity New']
#                 Voltage_data['Vmin']=Voltage_data['Vmin'].append(Vmin)
#                 Voltage_data['C_Violations']=Voltage_data['C_Violations'].append(C_Violations)
#                 Voltage_data['Trans_kVA']=Voltage_data['Trans_kVA'].append(TransAll)
#                 Voltage_data['V2gPerc'][d]=np.mean(V2G_Perc)
# #                for f in Flow:
# #                    Voltage_data['Flow'][f]=Voltage_data['Flow'][f].append(Flow[f])
            
#             daycount=daycount+1
        
#         pickle_out = open(paths+N+"validation/Winter"+str(Y)+"_V_Data.pickle", "wb")
#         pickle.dump(Voltage_data, pickle_out)
#         pickle_out.close() 
#         end=datetime.now()
#         #print('Tomorrow is a '+str(daytype)+ ' with forecast temperature '+str(temp)+'deg C')
#         time=end-start
#         print(str(len(days))+' Days Validation took '+str(time))
#         print('Total Current Violations', Voltage_data['C_Violations'].sum())
#         print('Total Low Voltages', (Voltage_data['Vmin']<0.9).sum())