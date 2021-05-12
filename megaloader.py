# -*- coding: utf-8 -*-
"""
Created on Thu Sep 24 14:16:25 2020

Megaloader is the top level script loading in functions from other scripts. The overall running order is as follows:
    
1. Create customer data (based on Cases) for all Networks 
---- raw_input_data() function within congestion_probability_batch.py
    
2. Power flow then is run using PV, Smartmeter (SM) and heat pump (HP) data for all cases 
---- do_loadflows(sims) function within congestion_probability_batch.py

3. The zonal minimum voltage and zonal supply cable power flow is determined 
---- calc_current_voltage function (in crunch_results_batch.py) within congestion_probability_batch.py
    
4. Using the resulting zonal power flows and minimum voltages, Power flow limits are estimated per zone
---- voltage_limits(networks,Cases,paths) function

5. Headroom and footroom are calculated for each timestep
----  Headroom_calc function (in crunch_results_batch.py) called from post_process() within congestion_probability_batch.py

6. Daily profiles of headroom and footroom are calculated, number of EVs and HPs are also calculated and saved in pickle files
---- headroom_percentiles function within headroom_forecasting.py runs
    ---- percentiles() creates daily profiles
    ---- HP_vs_Headroom() calculates headroom
    ---- EV numbers are estimated per zone based on daily headroom
    ---- HP cases are assigned (based on headroom) and new customer summaries created
    
7. Calculate number of optimised EVs (10 successful attempts).
---- EVRealiser function within zonal_summary.py

8. Do EV optimisation for successful EV number. Then validate using congestion_probability_validation.py
--Load flow is run and headroom is re-calculated for comparison
----- EVRealiser function within zonal_summary.py (with flag to say its not 10 attempts, but 2 instead)
----- runvalid within congestion_probability_validation.py 
-----------runvalid calls save_outputs, post_process from congestion_probability_batch.py


============== Required Data Folder Structure ==================

Data/network_X/       ------------ Stores calculated Zonal Vmin, Pflow and C Violations
Data/Raw              -------------Stores the raw data (input dataframes of demand and output results of current, Voltage Arrays)
Data/Upper/           -------------Stores the calculated nEVs and HPs (assigned cases)
-----Upper/network_X/ -------------Stores calculated headrooms, both as timeseries and daily profiles. Also stores All_VC_limits.pickle which is the Power flow limit for minimum voltage
Data/Validation       -------------Stores validation results arrays
Data/Validation/network_X/ --------Stores new headrooms for validation results 

@author: Calum Edmunds
"""

from congestion_probability_batch import runbatch
from voltage_headroom import voltage_limits
from headroom_forecasting import headroom_percentiles
from zonal_summary import EVRealiser
import pickle
from congestion_probability_validation import runvalid
import pandas as pd
from datetime import timedelta, date, datetime

networks=['network_18/']#,'network_5/','network_10/','network_17/','network_18/']

Cases=['25PV50HP']#,'00PV25HP','25PV50HP','25PV75HP','50PV100HP']
#Txs=pd.Series([750,500,1000,1000,750],index=networks)  ###---- These are the Tx ratings, not needed as they are stored in the OpenDSS files but there for reference
desc=['225 V limit (Upper Conservative)','216 V Limit (Lower Less conservative)','']   ####---- 225 V corresponds to 0.94 p.u in voltage_headroom.py, 216 V corresponds to 0.9 p.u.

###--- Within function runbatch(data_path,networks,Cases,PrePost,paths,VC)
###--- 'data_path' is the path where Load flow outputs are stored
###--- 'paths' sets the path for output headroom data that is specific to the Upper Minimum Voltage Power flow limit
upath="../Data/Upper/"
""" Steps 1 and 2 - Customer Data and Load Flow"""
###---runbatch function with ‘Pre’ generates the data from the OpenDSS loadflow 
###---(including dataframes of SM,HP,PV data assigned 10minutely per customer) 

# runbatch('../Data/Raw/',networks,Cases,'Pre',paths='',VC=False)

# """Step 3 - Zonal Minimum voltage"""
# ###---runbatch function with ‘Post’ with VC==True. This outputs the Vmin_DF, 
# ###---and PFlow_DF per zone. (Minimum voltage and supply cable power flow)

# runbatch('../Data/Raw/',networks,Cases,'Post','../Data/',VC=True)

# """Step 4 - Zonal power flow Limit"""
# ###--- Power flow limits for minimum voltage are estimated per zone.

# voltage_limits(networks,Cases,upath)

# """Step 5 - Headroom and Footroom"""
# ###--- Using the power flow limits the headroom and footroom are calculated

# runbatch('../Data/',networks,Cases,'Post',upath, VC=False)

# """Step 6 - Headroom/Footroom Daily, and Number of EVs and HPs"""
quant=0.02
factor=1
# headroom_percentiles(networks,Cases,upath,quant,factor)

# """Step 7 - Optimise EVs: 10 Successfull attempts """

#EVRealiser(networks, upath,quant,factor,Valid=False)

"""Step 8 - Optimise EVs: Validate on Network with maximum HPs """

####--- Function runvalid(data_path,networks,paths,quant,factor)
start = date(2014, 1, 22)
end = date(2014, 1, 24)
        
evtype_O='OptEV'
C_Viol_O, V_Viol_O, T_Viol_O=runvalid('../Data/Validation/',networks, upath,quant,factor,evtype_O,start,end)

###--- For Dumb EV Validation
evtype='Dumb'
C_Viol, V_Viol, T_Viol=runvalid('../Data/Validation/',networks, upath,quant,factor,evtype,start,end)

print(evtype_O,'C Violations', C_Viol_O, '% of timesteps')
print(evtype_O,'Low Voltage Violations', V_Viol_O, '% of timesteps')
print(evtype_O,'Tx Violations', T_Viol_O, '% of timesteps')

print(evtype,'C Violations', C_Viol, '% of timesteps')
print(evtype,'Low Voltage Violations', V_Viol, '% of timesteps')
print(evtype,'Tx Violations', T_Viol, '% of timesteps')

'''Below is the summary of validated results, this wont work any more, at least not the summary of violations for validation'''
# ###########MEGA SUMMARY OF HPs and EVS ############

# print(paths,desc[1])
# pick_in = open(paths+"nHPs_final.pickle", "rb")
# nHPs_Final= pickle.load(pick_in)

# ###---- Problem ZOnes----### Results are removed if:  1) issues with 0% HP already and 2) No EVS

# pick_in = open("../Data/Problem_Zones.pickle", "rb")   ###--- The Problem Zones File is generated from voltage_headroom_report.py
# OPZs= pickle.load(pick_in)  ### Original Problem ZOnes
# summary=pd.DataFrame(index=networks,columns=(['Network','HPs','EVs','C Violations (%)','V Violations (%)','T Violations (%)', 'V2G Delivered (%)']))
# TransRatekVA=pd.Series(index=networks)
# for N in networks:              
        
#     pick_in = open("../Data/"+N+"Customer_Summary00PV25HP14.pickle", "rb")
#     Customer_Summary= pickle.load(pick_in)
    
#     pick_in = open(paths+N+"validation/Winter14_V_Data.pickle", "rb")
#     SumData= pickle.load(pick_in)
#     pick_in = open("../Data/Raw/"+N[:-1]+"_00PV00HP_TransRatekVA.pickle", "rb")
#     TransRatekVA[N]= pickle.load(pick_in)
    
#     V_ViolMod=SumData['Vmin']
#     C_ViolMod=SumData['C_Violations']
    
#     print('---------------',N,len(Customer_Summary),'Customers',len(SumData['Vmin']),'Timesteps ---------------')
    
#     if len(OPZs[N]['LV'])>0:
#         print('========V Problem Zones===========')
#         for m in OPZs[N]['LV'].index.str[1].unique():
#             for z in V_ViolMod.columns[V_ViolMod.columns.str[1]==m]:
#                 print(z, 'nEVs', SumData['EV_summary'].loc[z].min())
#                 if SumData['EV_summary'].sum(axis=1)[z]==0:
#                     print('Zone', z, (V_ViolMod[z]<0.9).sum(), 'Voltage violations Removed (Problem Zone: No EVs, No HPS)')
#                     V_ViolMod[z]=0.91
            
#     if len(OPZs[N]['HC'])>0:
#         print('===========C Problem Zones=======')
#         for m in OPZs[N]['HC'].index.str[1].unique():
#             for z in C_ViolMod.columns[C_ViolMod.columns.str[1]==m]:
#                 print(z, 'nEVs', SumData['EV_summary'].loc[z].min())
#                 if SumData['EV_summary'].sum(axis=1)[z]==0:
#                     print('Zone', z, (C_ViolMod[z]>0).sum(), 'Current violations Removed (Problem Zone: No EVs, No HPS)')
#                     C_ViolMod[z]=0
    
#     print('===========Hosting Capacity And violations=======')
    
#     print('HPs', nHPs_Final[N].sum())
#     print('EVs', SumData['EV_summary'].sum().min())
#     cviols=C_ViolMod.sum(axis=1)
#     print('---C Violations:', (cviols>0).sum(),'(',round((cviols>0).sum()/len(cviols)*100,1),'%','of timesteps)')
#     print('Problem Zones',C_ViolMod.sum()[C_ViolMod.sum()>0].index.values)
#     print('N  Violations',C_ViolMod.sum()[C_ViolMod.sum()>0].values,'\n')
#     vviols=(V_ViolMod<0.9).sum(axis=1)
#     print('---V Violations:', (vviols>0).sum(),'(',round((vviols>0).sum()/len(vviols)*100,1),'%','of timesteps)' )
    
#     print('Problem Zones',(V_ViolMod<0.9).sum()[(V_ViolMod<0.9).sum()>0].index.values)
#     print('N  Violations',(V_ViolMod<0.9).sum()[(V_ViolMod<0.9).sum()>0].values,'\n')
#     print('v2g Deliveried', SumData['V2gPerc'].mean(),'\n')
    
#     print('Transformer Violations',round(sum(-SumData['Trans_kVA']>TransRatekVA[N])/len(SumData['Trans_kVA'])*100,1),'\n')
     
#     summary['Network'][N]=N[8:-1]
#     summary['HPs'][N]=str(nHPs_Final[N].sum()) +' ('+ str(round(nHPs_Final[N].sum()/len(Customer_Summary)*100,1))+'%)'
#     summary['EVs'][N]=str(SumData['EV_summary'].sum().min()) + ' ('+ str(round(SumData['EV_summary'].sum().min()/len(Customer_Summary)*100,1))+'%)'
#     summary['C Violations (%)'][N]=round((cviols>0).sum()/len(cviols)*100,1)
#     summary['V Violations (%)'][N]=round((vviols>0).sum()/len(vviols)*100,1)
#     summary['T Violations (%)'][N]=round(sum(-SumData['Trans_kVA']>TransRatekVA[N])/len(SumData['Trans_kVA'])*100,1)
#     summary['V2G Delivered (%)'][N]=round(SumData['V2gPerc'].mean(),1)
    
# print(summary)