# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 16:39:22 2019

@author: qsb15202
"""
import scipy.io
import numpy as np
import pandas as pd
import pickle
from matplotlib import pyplot as plt

# ------------ Network Voltage Headroom calculation---------##

#### This script takes network current and voltage data, and plots
#### the relationship between minimum voltage and current at the pinch point

#def voltage_headroom(Pflow,Vmin):

networks=['network_1/','network_5/','network_10/','network_17/','network_18/']
Y=14
Cases=['25PV50HP','00PV25HP','25PV50HP','25PV75HP','50PV100HP','25PV25HP','50PV50HP','75PV75HP','100PV100HP']
All_VC_Limits={}
for N in networks:
    AllVmin=pd.DataFrame()
    AllPflow=pd.DataFrame()
    for C in Cases:
        pick_in = open("../Data/"+N+C+"Winter"+str(Y)+"_V_Data.pickle", "rb")
        V_data = pickle.load(pick_in)
        cs=[]
        for p in range(1, 4):
            for f in range(1, len(V_data['Flow'].keys())+1):
                cs.append(str(p)+str(f))         
        Pflow = pd.DataFrame(index=V_data['Vmin'].index,columns=cs)  
        for p in range(1,4):
            for f in range(1, len(V_data['Flow'].keys())+1):
                Pflow[str(p)+str(f)]=V_data['Flow'][f][p]

        AllVmin=AllVmin.append(V_data['Vmin'])
        AllPflow=AllPflow.append(Pflow)
        
    trues=round(AllPflow.sum(),3)>0
    trues=trues[trues].index
     
    VC_Fits=pd.DataFrame(columns=['m','c'], index=trues)
    VC_Limit=pd.Series(index=trues, dtype=float)
    
    C=np.arange(0,100,step=10)
        
    #only include with Data
    plt.figure()
    for i in trues:#V_data['Pflow'].columns:
        #plt.figure()
        plt.scatter(AllPflow[i],AllVmin[i],s=0.2)
        VC_Fits.loc[i]['m'],VC_Fits.loc[i]['c']=np.polyfit(AllPflow[i].astype(float).values,AllVmin[i].astype(float).values,1)
        plt.plot(C,C*VC_Fits.loc[i]['m']+VC_Fits.loc[i]['c'], linewidth=0.5)
        VC_Limit[i]=(0.94-VC_Fits.loc[i]['c'])/VC_Fits.loc[i]['m']
        if sum(AllVmin[i].astype(float).values<=0.94)>0:
            VC_Limit[i]=0.85*AllPflow[i].astype(float).values[AllVmin[i].astype(float).values<=0.94].min()
            if i=="17" and N=='network_17/':
                VC_Limit[i]=0.75*AllPflow[i].astype(float).values[AllVmin[i].astype(float).values<=0.94].min()
        plt.plot([0,VC_Limit[i]],[0.94,0.94], linewidth=0.5)
        plt.plot([VC_Limit[i],VC_Limit[i]],[0.9,0.94], linewidth=0.5)
        plt.title('Network/Zone '+N+i)
        plt.xlabel('Supply Power (kVA)')
        plt.ylabel('Min Voltage (Amps)')
        plt.ylim(0.9,1)
    
    All_VC_Limits[N]=VC_Limit

pickle_out = open("../Data/All_VC_Limits.pickle", "wb")
pickle.dump(All_VC_Limits, pickle_out)
pickle_out.close()   