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
from matplotlib import cm
from matplotlib.colors import Normalize 
from scipy.interpolate import interpn

# ------------ Network Voltage Headroom calculation---------##

#### This script takes network current and voltage data, and plots
#### the relationship between minimum voltage and current at the pinch point

#def voltage_headroom(Pflow,Vmin):

networks=['network_1/']#,'network_5/','network_10/','network_17/','network_18/']
Y=14
Cases=['00PV00HP','00PV25HP','25PV50HP','25PV75HP','50PV100HP']#,'25PV25HP','50PV50HP','75PV75HP','100PV100HP']
All_VC_Limits={}
#for Y in [14,15]:
# pick_in = open("../Data/All_VC_Limits.pickle", "rb")
# All_VC = pickle.load(pick_in)

for N in networks:
    AllVmin=pd.DataFrame()
    AllPflow=pd.DataFrame()
    for C in Cases:
        pick_in = open("../Data/"+N+C+"Winter"+str(Y)+"_V_Data.pickle", "rb")
       # pick_in = open("../Data/"+N+"validation/Winter"+str(Y)+"_V_Data0.94.pickle", "rb")
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
            
        #######only include with Data
        #plt.figure()
    for i in trues:#V_data['Pflow'].columns:
        x=AllPflow[i].astype(float).values
        y=AllVmin[i].astype(float).values
        data , x_e, y_e = np.histogram2d( x, y, bins = 30, density = True )
        z = interpn( ( 0.5*(x_e[1:] + x_e[:-1]) , 0.5*(y_e[1:]+y_e[:-1]) ) , data , np.vstack([x,y]).T , method = "splinef2d", bounds_error = False)
        z[np.where(np.isnan(z))] = 0.0
        plt.figure(i)
        idx = z.argsort()
        x, y, z = x[idx], y[idx], z[idx]
        plt.scatter( x, y, c=z,s=1)
    
        norm = Normalize(vmin = np.min(z), vmax = np.max(z))
        cbar = plt.colorbar(cm.ScalarMappable(norm = norm))
        cbar.ax.set_ylabel('Density')

        VC_Fits.loc[i]['m'],VC_Fits.loc[i]['c']=np.polyfit(x,y,1)
        plt.plot(C,C*VC_Fits.loc[i]['m']+VC_Fits.loc[i]['c'], linewidth=0.5)
        V_lim=0.94
        V_lim_u=0.94
        VC_Limit[i]=(V_lim_u-VC_Fits.loc[i]['c'])/VC_Fits.loc[i]['m']
        if y.min() >0.94:
            VC_Limit[i]=max(VC_Limit[i]*0.6,x.max())
        unders=y[x<VC_Limit[i]]
        if sum(unders[unders<V_lim_u])>0:
            VC_Limit[i]=x[y<=V_lim_u].min()
        #VC_Limit[i]=All_VC[N][i]
        # if (len(y[y<V_lim_u])/len(y)*100) <5:
        #     VC_Limit[i]=(V_lim_u-VC_Fits.loc[i]['c'])/VC_Fits.loc[i]['m']
        unders_n=y[x<VC_Limit[i]]
        prob=len(unders_n[unders_n<V_lim_u])/len(unders_n)*100
        print(str(i)+', % Probability of <0.94 p.u at Flow<VCmin '+str(prob))
        # q=0.35
        # prob_lim=0.5
        # if N=='network_17/' and i=='27':
        #     prob_lim=1
        # while prob>prob_lim:
        #     VC_Limit[i]=np.quantile(x[(y<=V_lim_u)&(y>=V_lim)],q)
        #     unders_n=y[x<VC_Limit[i]]
        #     prob=len(unders_n[unders_n<0.94])/len(unders_n)*100
        #     q=q-0.001
        plt.plot([0,VC_Limit[i]*2],[V_lim,V_lim], linewidth=0.5)
        plt.plot([0,VC_Limit[i]*2],[0.9,0.9], linewidth=0.5, linestyle=':', color='black')
        plt.plot([VC_Limit[i],VC_Limit[i]],[0.88,1], linewidth=0.7)
        #plt.title('Network/Zone '+N+i)
        plt.xlabel('Supply cable power flow (kVA)',fontsize=11)
        plt.ylabel('Min Voltage (Amps)',fontsize=11)
        plt.ylim(0.88,1)
        print(str(i)+', % Probability of <0.9 p.u at Flow<VCmin '+str(prob))
    All_VC_Limits[N]=VC_Limit

""" Note on Vlimits"""
""" Say 2% drop acceptable, that is 383.2V which is 0.921 p.u."""
""" Minimum for UK appliances is 216.2 V P-N, which is 374.47 V P-P and 0.9 p.u (for 416 V base)"""

pickle_out = open("../Data/All_VC_Limits.pickle", "wb")
pickle.dump(All_VC_Limits, pickle_out)
pickle_out.close()   