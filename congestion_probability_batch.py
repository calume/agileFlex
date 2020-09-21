
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


### --- All VC Limits is Current limits set by Low Voltage

pick_in = open("../Data/All_VC_Limits0.94.pickle", "rb")
All_VC = pickle.load(pick_in)

####----------Set Test Network ------------
start=datetime.now()

networks=['network_1/','network_5/','network_10/','network_18/','network_17/',]
All_C_Limits={}
Cases=['00PV00HP']#,'00PV25HP','25PV50HP','25PV75HP','50PV100HP']#,'25PV25HP','50PV50HP','75PV75HP','100PV100HP']
FullSummmary={}
for N in networks:
    FullSummmary[N]={}
    for C in Cases:
        FullSummmary[N][C]={}
        for Y in [14]:#,15]:
            #### Load in Test data Set ##########

            pick_in = open("../Data/SM_byAcorn_NH.pickle", "rb")
            SM_DataFrame = pickle.load(pick_in)
            
            pick_in = open("../Data/HP_DataFrame_hh_mean.pickle", "rb")
            HP_DataFrame = pickle.load(pick_in)
#            pick_in = open("../Data/JDEVResampled.pickle", "rb")
#            EV_DataFrame = pickle.load(pick_in)
#            
            pick_in = open("../Data/PV_BySiteName.pickle", "rb")
            PV_DataFrame = pickle.load(pick_in)
            print(N,C,Y)
            FullSummmary[N][C][Y]={}
            Network_Path = "Test_Network/condensed/"+N
            #################create_gens(Network_Path)  ###--- Creates generators in OpenDSS
                   
            #########----- Plus 1 year to SM timestamps to line up with PV and HP
            if Y ==15:
                for i in SM_DataFrame.keys():
                   SM_DataFrame[i].index = SM_DataFrame[i].index + timedelta(days=364)
            
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
                
#                pickle_out = open("../Data/"+N+"upperVlimit/Customer_Summary"+C+str(Y)+".pickle", "wb")
#                pickle.dump(Customer_Summary, pickle_out)
#                pickle_out.close()
                return Coords, Lines, Customer_Summary,HP_reduced,HPlist, SMlist
            
            
            ######--------- Run power flow Timeseries--------------------------#
            ####### test dates: 2013-6-1 to 2014-6-1, full when SM dates are changed by plus 1 year
            ########--------- Code to load dates with highest HP demand for testing-------------##########

            # HP_DataFrame.columns=HP_DataFrame.columns.astype(int)
            # zone=Customer_Summary[Customer_Summary['zone']=='24']
            #HPs=Customer_Summary['heatpump_ID'][Customer_Summary['heatpump_ID']>0]
            #HPs=zone['heatpump_ID'][zone['heatpump_ID']>0]
            # HP_DataFrame[HPs].sum(axis=1).resample('1D').sum().idxmax()
            # HP_DataFrame[HPs].sum(axis=1).resample('1D').max().idxmax()
            # Highest total HP demand - 2014-01-12 
            # Highest peak HP demand - 2014-03-24
            
            #start_date = date(2014, 6, 1)
            #end_date = date(2014, 9, 3)
            start_date = date(2000+Y-1, 12, 1)
            end_date = date(2000+Y, 2, 27)
            sims_halfhours = pd.date_range(start_date, end_date, freq=timedelta(hours=0.5))
            sims_tenminutes = pd.date_range(start_date, end_date, freq=timedelta(minutes=10))
            
            sims=sims_tenminutes[:1]
        
            pick_in = open("../Data/HP_DataFrame_10mins_pad.pickle", "rb")
            HP_DataFrame = pickle.load(pick_in)
            HP_DataFrame = HP_DataFrame.loc[sims]
            
            for i in SM_DataFrame.keys():
                SM_DataFrame[i]=SM_DataFrame[i].reindex(sims_halfhours.tolist())
                SM_DataFrame[i]=SM_DataFrame[i].resample('10T').mean()
                for k in SM_DataFrame[i].columns:
                   SM_DataFrame[i][k]=SM_DataFrame[i][k].interpolate(method='pad')
            #EV_DataFrame=EV_DataFrame.append(EV_DataFrame.iloc[-1:])
            #EV_DataFrame.index=sims_tenminutes

            #for k in EV_DataFrame.columns:
            #   EV_DataFrame[k]=EV_DataFrame[k].interpolate(method='pad')            
            
            for i in PV_DataFrame.keys():
                if Y==14:
                    PV_DataFrame[i]=PV_DataFrame[i].reindex(sims_halfhours.tolist())
                if Y==15:
                    PV_DataFrame[i]=PV_DataFrame[i].reindex((sims_halfhours-timedelta(days=365)).tolist())
                PV_DataFrame[i]=PV_DataFrame[i].resample('10T').mean()
                for k in PV_DataFrame[i].columns:
                    PV_DataFrame[i][k]=PV_DataFrame[i][k].interpolate(method='pad')
                
            Coords, Lines, Customer_Summary, HP_reduced,HPlist,SMlist = Create_Customer_Summary(sims)  
            ##Customer_Summary, Coords, Lines, Loads = customer_summary(Network_Path, C)
            ####------ For when the customer summary table is fixed we laod it in from the pickle file
#            pickin = open("../Data/"+str(N)+"Customer_Summary"+str(C)+str(Y)+".pickle", "rb")
#            Customer_Summary = pickle.load(pickin)
            
            
            #####------------ Initialise Input--------------------
            smartmeter = {}
            heatpump = {}
            pv = {}
            ev={}
            demand = {}  # Sum of smartmeter, heatpump and EV
            demand_delta = {}  # adjustment for sensitivity, set to 0 when no sensitivity
            pv_delta = {}  # adjustment for sensitivity, set to 0 when no sensitivity
            PFControl = {}  # Reactive power compensation for high voltage control
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
            if N=='network_10/':
                pinchClist.remove(34)
            for i in sims.tolist():
                print(N,C,Y, i)
                # -------------- Sample for each day weekday/weekend and season -----------#
                ##-- Needed for SM data, and will be used for sampling --#
                smartmeter[i] = np.zeros(len(Customer_Summary))
                ev[i] = np.zeros(len(Customer_Summary))
                heatpump[i] = np.zeros(len(Customer_Summary))
                pv[i] = np.zeros(len(Customer_Summary))
                demand[i] = np.zeros(len(Customer_Summary))
                demand_delta[i] = np.zeros(len(Customer_Summary))
                pv_delta[i] = np.zeros(len(Customer_Summary))
                ##--- By Defailt Power Factor control is off, only when thermal overloads
                ##-- are PFControl turned on
                PFControl[i] = 0
                # -----for each customer set timestep demand and PV output----#
                
                for z in range(0, len(Customer_Summary)):
                    #ev[i][z]=EV_DataFrame.loc[i][EV_DataFrame.columns[z]]
                    smartmeter[i][z] = SM_DataFrame[Customer_Summary["Acorn_Group"][z]][Customer_Summary["smartmeter_ID"][z]][i]
                    if Customer_Summary["heatpump_ID"][z] != 0:
                        heatpump[i][z] = HP_DataFrame[str(Customer_Summary["heatpump_ID"][z])][i]
                    if Customer_Summary["PV_kW"][z] != 0:
                        ipv=i
                        if Y==15:
                            ipv=i-timedelta(days=365)
                        pv[i][z] = (Customer_Summary["PV_kW"][z] * PV_DataFrame[Customer_Summary["pv_ID"][z]]["P_Norm"][ipv]) 
                    demand[i][z] = smartmeter[i][z] + heatpump[i][z] #+ev[i][z]
            
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
                    N,CurArray[i], RateArray, VoltArray[i], PowArray[i], Trans_kVA[i], TransRatekVA, pinchClist, All_VC
                )
                
                if converged==False:
                    j=i-timedelta(hours=0.5)
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
            #Chigh_count, Vhigh_count, Vlow_count, VHpinch =counts(network_summary,Coords,pinchClist)
            #Coords = plots(Network_Path,Chigh_count, Vhigh_count,Vlow_count,pinchClist,colors,'FirstPass')
            #Vmax,Vmin,Cmax=calc_current_voltage(CurArray,VoltArray,Coords,Lines,Flow,RateArray, pinchClist,colors)
            #plot_current_voltage(Vmax, Vmin, Cmax, RateArray, pinchClist,colors,N,'FirstPass')
            #plot_headroom(Headrm, Footrm, Flow, Rate, labels,pinchClist,InputsbyFP,genres,colors,'FirstPass')
            labels = {"col": "red", "style": "--", "label": "Initial", "TranskVA": TransRatekVA}
            
            #=============== This below code is for creating Current Limits for Voltage======##########
#            Voltage_data={}
#            Voltage_data['Vmin']=Vmin
#            Voltage_data['Flow']=Flow
#            
#            pickle_out = open("../Data/"+N+C+"Winter"+str(Y)+"_V_Data.pickle", "wb")
#            pickle.dump(Voltage_data, pickle_out)
#            pickle_out.close()            

#            pickle_out = open("../Data/"+N+"upperVlimit/"+C+"Winter"+str(Y)+"_10mins_Hdrm.pickle", "wb")
#            pickle.dump(Headrm, pickle_out)
#            pickle_out.close()            
#
#            pickle_out = open("../Data/"+N+"upperVlimit/"+C+"Winter"+str(Y)+"_10mins_Ftrm.pickle", "wb")
#            pickle.dump(Footrm, pickle_out)
#            pickle_out.close()
            
            #----------- Calculation of adjusted demand for Thermal Violations------------------#

        #     for i in network_summary:
        #         print('Adjusts',N,C,Y,i)
        #         for p in range(1, 4):
        #             for f in range(1, len(pinchClist)+1):
        #                 if Headrm[f][p][i] < 0 and Flow[f][p][i] > 0 and len(custph[p][f])>0:
        #                     Dem_ratio= (Flow[f][p][i]+Headrm[f][p][i])/Flow[f][p][i]
        #                     demand_delta[i][custph[p][f].index] = -demand[i][custph[p][f].index]*(1-Dem_ratio)
            
        #                 if Footrm[f][p][i] < 0 and Flow[f][p][i] < 0 and len(custph[p][f])>0:
        #                     demand_delta[i][custph[p][f].index] = Footrm[f][p][i] / len(custph[p][f])
        #                     PFControl[i] = 1
            
        #                 ####----- Check Secondary Substation-------###
                        
        #                 # if Headrm[0][i] > labels["TranskVA"] and len(custph[p][f])>0:
        #                 #     demand_delta[i][custph[p][f].index]=min(demand_delta[i][custph[p][f].index],-(Headrm[0][i]-labels["TranskVA"])/len(demand_delta[i]))
                        
        #                 # if Headrm[0][i] < -labels["TranskVA"] and len(pv_delta[i][custph[p][f][custph[p][f]["PV_kW"] > 0].index])>0:
        #                 #     demand_delta[i][custph[p][f][custph[p][f]["PV_kW"] > 0].index]=min(demand_delta[i][custph[p][f][custph[p][f]["PV_kW"] > 0].index][0],-((-Headrm[0][i]-labels["TranskVA"])/sum((Customer_Summary['PV_kW']>0))))
                            
        #         if (demand_delta[i].sum() + pv_delta[i].sum()) != 0:
        #             (
        #                 CurArray_new[i],
        #                 VoltArray_new[i],
        #                 PowArray_new[i],
        #                 Losses[i],
        #                 Trans_kVA_new[i],
        #                 RateArray,
        #                 TransRatekVA,
        #                 genresnew[i],
        #                 converged,
        #             ) = runDSS(
        #                 Network_Path, demand[i], pv[i], demand_delta[i], pv_delta[i], PFControl[i]
        #             )
            
        #             network_summary_new[i] = network_outputs(
        #                 N,
        #                 CurArray_new[i],
        #                 RateArray,
        #                 VoltArray_new[i],
        #                 PowArray_new[i],
        #                 Trans_kVA_new[i],
        #                 TransRatekVA,
        #                 pinchClist,
        #                 All_VC
        #             )
        #         if converged==False:
        #             j=i-timedelta(hours=0.5)
        #             bad_halfhours_n.append(i)
        #             network_summary_new[i]=network_summary_new[j]
        #             CurArray_new[i],VoltArray_new[i],PowArray_new[i],Trans_kVA_new[i] = CurArray_new[j],VoltArray_new[j],PowArray_new[j],Trans_kVA_new[j]
        #     (
        #         Headrm_new,
        #         Footrm_new,
        #         Flow_new,
        #         Rate,
        #         Customer_Summary,
        #         custph
        #     ) = Headroom_calc(
        #         network_summary_new,
        #         Customer_Summary,
        #         smartmeter,
        #         heatpump,
        #         pv,
        #         demand,
        #         demand_delta,
        #         pv_delta,
        #         pinchClist
        #     )
                
        #     labels = {
        #         "col": "blue",
        #         "style": "-",
        #         "label": "With Adjustments",
        #         "TranskVA": TransRatekVA,
        #     }
        #     #plot_headroom(Headrm_new, Footrm_new, Flow_new, Rate, labels,pinchClist,InputsbyFP_new,genresnew,colors,'Adjusts')
        #     #plot_flex(InputsbyFP_new,pinchClist,colors,'Adjusts')
        #     Chigh_count_new, Vhigh_count_new, Vlow_count_new, VHpinch_new = counts(network_summary_new, Coords,pinchClist)
        #     #Coords = plots(Network_Path, Chigh_count_new, Vhigh_count_new, Vlow_count_new,pinchClist,colors,'Adjusts')
        #     Vmax_new, Vmin_new, Cmax_new = calc_current_voltage(
        #         CurArray_new, VoltArray_new, Coords, Lines, Flow_new, RateArray, pinchClist, colors
        #     )
        #     #plot_current_voltage(Vmax_new, Vmin_new, Cmax_new, RateArray, pinchClist,colors,N,'Adjusts')
            
        #     ## - residual demand - plt.plot(InputsbyFP_new['demand']+InputsbyFP_new['demand_delta'])
            
        # FullSummmary[N][C][Y]['Customer Summary']=Customer_Summary
        # FullSummmary[N][C][Y]['Chigh_count_new']=Chigh_count_new
        # FullSummmary[N][C][Y]['Vhigh_count_new']=Vhigh_count_new
        # FullSummmary[N][C][Y]['Vlow_count_new']=Vlow_count_new
        # FullSummmary[N][C][Y]['Bad_Timesteps']=bad_halfhours_n
        
        # end=datetime.now()
        # time=end-start
        aa=list(Customer_Summary['zone'].unique())
        aa.sort()
        All_C_Limits[N]=pd.Series(index=aa)
        for k in range(1,4): 
            for l in network_summary[i][k]['C_Rate'].keys():
                All_C_Limits[N][str(k)+str(l)]=network_summary[i][k]['C_Rate'][l]

pickle_out = open("../Data/All_C_Limits0.94.pickle", "wb")
pickle.dump(All_C_Limits, pickle_out)
pickle_out.close()

# pickle_out = open("../Data/Full_Batch_Summary.pickle", "wb")
# pickle.dump(FullSummmary, pickle_out)
# pickle_out.close()

# demseries=pd.DataFrame(index=demand.keys(),columns=(range(0,75)))
# for i in demand.keys():
#     demseries.loc[i]=demand[i][125:]
# file='Network1_Feeder4_Demand_1Day_10Minutely_100HPs_withEVs.xlsx'
# demseries.to_excel(file, sheet_name="Demand")

# book = load_workbook(file)
# writer = pd.ExcelWriter(file, engine='openpyxl')
# writer.book = book
# writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
# VminDF=pd.DataFrame()
# VminDF['Phase1']=Vmin['14']
# VminDF['Phase2']=Vmin['24']
# VminDF['Phase3']=Vmin['34']
# VminDF.to_excel(writer, "Vmin", columns=None, header=True, index=True, startrow=0)
# writer.save()
    