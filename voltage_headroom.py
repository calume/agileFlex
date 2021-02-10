# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 16:39:22 2019

Script purpose: Zonal Minimum Voltage Power Flow limit 

The voltage_limits function takes network power flow and minimum voltage data, and plots
the relationship between minimum voltage and supply cable power flow

voltage_limits estimates the a power flow limit for each zone based on keeping the minimum voltage above a defined limit (0.94 p.u.) 

@author: Calum Edmunds
"""
import scipy.io
import numpy as np
import pandas as pd
import pickle
from matplotlib import pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize 
from scipy.interpolate import interpn


####--- The Vheaders function is for working out the supply cable voltage, not used except in reporting----##
def Vheaders():
    for N in networks:
        for C in Cases:
            print(N,C)
            pick_in = open("../Data/Raw/"+N[:-1]+'_'+C+"_VoltArray.pickle", "rb")
            V_raw = pickle.load(pick_in)
            All_header_V=pd.DataFrame(index=V_raw.keys(),columns=range(1,4))
            for i in V_raw.keys():
                #print(i)
                for p in range(1,4):
                    All_header_V.loc[i][p]=V_raw[i][1][p-1]
    
            pickle_out = open("../Data/Raw/"+N[:-1]+'_'+C+"_headerV_DF.pickle", "wb")
            pickle.dump(All_header_V, pickle_out)
            pickle_out.close()   

    VsMins=pd.DataFrame(index=Cases,columns=range(1,4))
    VsMax=pd.DataFrame(index=Cases,columns=range(1,4))
    for N in networks:
        for C in Cases:
            pick_in = open("../Data/Raw/"+N[:-1]+'_'+C+"_headerV_DF.pickle", "rb")
            V_raws = pickle.load(pick_in)
            VsMins.loc[C]=V_raws.min()
            VsMax.loc[C]=V_raws.max()

####--- voltage_limits estimates a power flow limit based on minimum voltage and power flow data---####
####--- Data is considered for all cases in the absense of EV
####--- The lowest acceptable limit is V_lim_u which is set at 0.94

def voltage_limits(networks,Cases,paths):

    All_VC_Limits={}
    
    for N in networks:
        print(N)
        AllVmin=pd.DataFrame()
        AllPflow=pd.DataFrame()
    
        for C in Cases:
            pick_in = open("../Data/"+N+C+"_Vmin_DF.pickle", "rb")
            V_min = pickle.load(pick_in)

            pick_in = open("../Data/"+N+C+"_PFlow_DF.pickle", "rb")
            Pflow = pickle.load(pick_in)   
                    
            AllVmin=AllVmin.append(V_min)
            AllPflow=AllPflow.append(Pflow)
            
            ###--- trues is a list of zones with power flow (removing zones with no customers)
            trues=round(AllPflow.sum(),3)>0
            trues=trues[trues].index
            
            ###--- VC_Fits stores the linear interpolation of the V_min vs Pflow, y = mx + c
            VC_Fits=pd.DataFrame(columns=['m','c'], index=trues)
            VC_Limit=pd.Series(index=trues, dtype=float)
            
            C=np.arange(0,100,step=10)
            
            ###--- Plotting code has been commented out.
            #plt.figure()
        for i in trues:
            x=AllPflow[i].astype(float).values
            y=AllVmin[i].astype(float).values
            # data , x_e, y_e = np.histogram2d( x, y, bins = 30, density = True )
            # z = interpn( ( 0.5*(x_e[1:] + x_e[:-1]) , 0.5*(y_e[1:]+y_e[:-1]) ) , data , np.vstack([x,y]).T , method = "splinef2d", bounds_error = False)
            # z[np.where(np.isnan(z))] = 0.0
            # plt.figure(i)
            # idx = z.argsort()
            # x, y, z = x[idx], y[idx], z[idx]
            # plt.scatter( x, y, c=z,s=1)
        
            # norm = Normalize(vmin = np.min(z), vmax = np.max(z))
            # cbar = plt.colorbar(cm.ScalarMappable(norm = norm))
            # cbar.ax.set_ylabel('Density')
#    
            VC_Fits.loc[i]['m'],VC_Fits.loc[i]['c']=np.polyfit(x,y,1)
#            plt.plot(C,C*VC_Fits.loc[i]['m']+VC_Fits.loc[i]['c'], linewidth=0.5)

            ###--- The lowest acceptable limit is V_lim_u which is set at 0.94
            V_lim_u=0.94
            ###- interpolate the Pflow limit based on when best fit line hits the V_lim_u.
            VC_Limit[i]=(V_lim_u-VC_Fits.loc[i]['c'])/VC_Fits.loc[i]['m']
            ###--- if there are no Vmins below V_lim_u, then the Pflow limit is set to the larger of the maximum Pflow recorded 
            ###--- or 60% of the interpolated Pflow limit
            if y.min() >V_lim_u:
                VC_Limit[i]=max(VC_Limit[i]*0.6,x.max())
            unders=y[x<VC_Limit[i]]
            
            ###--- if there are cases where the voltage is below V_lim_u then we set the Pflow limit as 
            ###--- the Pflow corresponding to the minimum PF where Vmin<V_lim_u was observed.
            if sum(unders[unders<V_lim_u])>0:
                VC_Limit[i]=x[y<=V_lim_u].min()
    
            unders_n=y[x<VC_Limit[i]]
            prob=len(unders_n[unders_n<V_lim_u])/len(unders_n)*100
            print(str(i)+', % Probability of <0.94 p.u at Flow<VCmin '+str(prob))
            ###--- Plotting code has been commented out.
            # plt.plot([0,VC_Limit[i]*2],[V_lim_u,V_lim_u], linewidth=0.5)
            # plt.plot([0,VC_Limit[i]*2],[0.9,0.9], linewidth=0.5, linestyle=':', color='black')
            # plt.plot([VC_Limit[i],VC_Limit[i]],[0.88,1], linewidth=0.7)
            # plt.xlabel('Supply cable power flow (kVA)',fontsize=11)
            # plt.ylabel('Min Voltage (Amps)',fontsize=11)
            # plt.ylim(0.88,1)
            # plt.xlim(0,120)
        All_VC_Limits[N]=VC_Limit
        
        """ Note on Vlimits"""
        """ Say 2% drop acceptable, that is 383.2V which is 0.921 p.u."""
        """ Minimum for UK appliances is 216.2 V P-N, which is 374.47 V P-P and 0.9 p.u (for 416 V base)"""
        
        pickle_out = open(paths+N+"All_VC_Limits.pickle", "wb")
        pickle.dump(All_VC_Limits, pickle_out)
        pickle_out.close()   
        
