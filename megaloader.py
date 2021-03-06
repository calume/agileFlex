# -*- coding: utf-8 -*-
"""
Created on Thu Sep 24 14:16:25 2020

@author: CalumEdmunds
"""

from congestion_probability_batch import runbatch
from voltage_headroom import voltage_limits
from headroom_forecasting import headroom_percentiles
from zonal_summary import EVRealiser
from zonal_summary_valid import daily_EVSchedule
import pickle
from congestion_probability_validation import runvalid
import pandas as pd

networks=['network_1/','network_5/','network_10/','network_17/','network_18/']

Cases=['00PV00HP','00PV25HP','25PV50HP','25PV75HP','50PV100HP']
#Txs=pd.Series([750,500,1000,1000,750],index=networks)
paths="../Data/Upper/"
desc=['225 V limit (Upper Conservative)','216 V Limit (Lower Less conservative)','']
runbatch(networks,Cases,'Pre',paths,VC=False)
#runbatch(networks,Cases,'Post',paths,VC=True)
#voltage_limits(networks,Cases,paths)
#runbatch(networks,Cases,'Post',paths, VC=False)
#
#quant=0
#factor=0.5
#headroom_percentiles(networks,Cases,paths,quant,factor)
#EVRealiser(networks, paths,quant,factor)
####daily_EVSchedule(networks[0], paths,quant,factor)
#timers=runvalid(networks, paths,quant,factor)


###########MEGA SUMMARY OF HPs and EVS ############

print(paths,desc[1])
pick_in = open(paths+"nHPs_final.pickle", "rb")
nHPs_Final= pickle.load(pick_in)

###---- Problem ZOnes----### Results are removed if:  1) issues with 0% HP already and 2) No EVS

pick_in = open("../Data/Problem_Zones.pickle", "rb")   ###--- The Problem Zones File is generated from voltage_headroom_report.py
OPZs= pickle.load(pick_in)  ### Original Problem ZOnes
summary=pd.DataFrame(index=networks,columns=(['Network','HPs','EVs','C Violations (%)','V Violations (%)','T Violations (%)', 'V2G Delivered (%)']))
TransRatekVA=pd.Series(index=networks)
for N in networks:              
        
    pick_in = open("../Data/"+N+"Customer_Summary00PV25HP14.pickle", "rb")
    Customer_Summary= pickle.load(pick_in)
    
    pick_in = open(paths+N+"validation/Winter14_V_Data.pickle", "rb")
    SumData= pickle.load(pick_in)
    pick_in = open("../Data/Raw/"+N[:-1]+"_00PV00HP_TransRatekVA.pickle", "rb")
    TransRatekVA[N]= pickle.load(pick_in)
    
    V_ViolMod=SumData['Vmin']
    C_ViolMod=SumData['C_Violations']
    
    print('---------------',N,len(Customer_Summary),'Customers',len(SumData['Vmin']),'Timesteps ---------------')
    
    if len(OPZs[N]['LV'])>0:
        print('========V Problem Zones===========')
        for m in OPZs[N]['LV'].index.str[1].unique():
            for z in V_ViolMod.columns[V_ViolMod.columns.str[1]==m]:
                print(z, 'nEVs', SumData['EV_summary'].loc[z].min())
                if SumData['EV_summary'].sum(axis=1)[z]==0:
                    print('Zone', z, (V_ViolMod[z]<0.9).sum(), 'Voltage violations Removed (Problem Zone: No EVs, No HPS)')
                    V_ViolMod[z]=0.91
            
    if len(OPZs[N]['HC'])>0:
        print('===========C Problem Zones=======')
        for m in OPZs[N]['HC'].index.str[1].unique():
            for z in C_ViolMod.columns[C_ViolMod.columns.str[1]==m]:
                print(z, 'nEVs', SumData['EV_summary'].loc[z].min())
                if SumData['EV_summary'].sum(axis=1)[z]==0:
                    print('Zone', z, (C_ViolMod[z]>0).sum(), 'Current violations Removed (Problem Zone: No EVs, No HPS)')
                    C_ViolMod[z]=0
    
    print('===========Hosting Capacity And violations=======')
    
    print('HPs', nHPs_Final[N].sum())
    print('EVs', SumData['EV_summary'].sum().min())
    cviols=C_ViolMod.sum(axis=1)
    print('---C Violations:', (cviols>0).sum(),'(',round((cviols>0).sum()/len(cviols)*100,1),'%','of timesteps)')
    print('Problem Zones',C_ViolMod.sum()[C_ViolMod.sum()>0].index.values)
    print('N  Violations',C_ViolMod.sum()[C_ViolMod.sum()>0].values,'\n')
    vviols=(V_ViolMod<0.9).sum(axis=1)
    print('---V Violations:', (vviols>0).sum(),'(',round((vviols>0).sum()/len(vviols)*100,1),'%','of timesteps)' )
    
    print('Problem Zones',(V_ViolMod<0.9).sum()[(V_ViolMod<0.9).sum()>0].index.values)
    print('N  Violations',(V_ViolMod<0.9).sum()[(V_ViolMod<0.9).sum()>0].values,'\n')
    print('v2g Deliveried', SumData['V2gPerc'].mean(),'\n')
    
    print('Transformer Violations',round(sum(-SumData['Trans_kVA']>TransRatekVA[N])/len(SumData['Trans_kVA'])*100,1),'\n')
     
    summary['Network'][N]=N[8:-1]
    summary['HPs'][N]=str(nHPs_Final[N].sum()) +' ('+ str(round(nHPs_Final[N].sum()/len(Customer_Summary)*100,1))+'%)'
    summary['EVs'][N]=str(SumData['EV_summary'].sum().min()) + ' ('+ str(round(SumData['EV_summary'].sum().min()/len(Customer_Summary)*100,1))+'%)'
    summary['C Violations (%)'][N]=round((cviols>0).sum()/len(cviols)*100,1)
    summary['V Violations (%)'][N]=round((vviols>0).sum()/len(vviols)*100,1)
    summary['T Violations (%)'][N]=round(sum(-SumData['Trans_kVA']>TransRatekVA[N])/len(SumData['Trans_kVA'])*100,1)
    summary['V2G Delivered (%)'][N]=round(SumData['V2gPerc'].mean(),1)
    
print(summary)