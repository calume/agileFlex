# -*- coding: utf-8 -*-
"""
Created on Fri Oct 25 13:01:37 2019

@author: qsb15202
"""

import opendssdirect as dss
import numpy as np
import pandas as pd
from opendssdirect.utils import run_command
pd.options.mode.chained_assignment = None
import networkx as nx
from matplotlib import pyplot as plt
from datetime import datetime
from sensitivity import sensitivity
from runDSS import runDSS
from summary import summary
import copy
start = datetime.now()

LoadsIn = pd.read_csv("Loads.txt",delimiter=' ', names=['New','Load','Phase','Bus1','kV','kW','PF','Daily'] )
LoadsIn['Phase']=LoadsIn['Bus1'].str[-1:]

def actions(P,Gen,LB,UB,PVd,EVd,HPd,u,ug,n,LoadBusByPhase,CurMaxInit,VmaxInit,VminInit,LoadsIn,PO):
    ########### Take Actions ############
    grad=1
    Cgrad=1
    CurMax=CurMaxInit
    Vmax=VmaxInit
    Vmin=VminInit
    for p in range(0,3):
        #print('Phase '+str(p+1))
        while Vmax[:,p] > 1.1 or Vmin[:,p] < 0.94 or CurMax[:,p] > 0.5:
          ###########  Make adjustments to relieve Vmin ###########
          while Vmin[:,p] < 0.94:
             print('Low Voltage Violation')
             UpInd=LoadBusByPhase[p][LoadBusByPhase[p]['UHDRm']>0].index
             DownInd=LoadBusByPhase[p][LoadBusByPhase[p]['LHDRm']>0].index
             if len(UpInd)==0:
                 #print('Insufficient Upward AGENT Flexibility')
                 UB=0
                 Loadarray,  CurArray, VoltArray, RateArray, CurMaxInit, VmaxInit, VminInit, Locationsi = runDSS(P,Gen,u,ug)
                 Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,P,Gen,Loadarray,CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
                 LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,P,Gen,PO,LB,UB)
             if len(DownInd)==0:
                 #print('Low Voltage: Insufficient Downward AGENT Flexibility. Load shedding Required')
                 LB=PO-EVd-HPd
                 Loadarray,  CurArray, VoltArray, RateArray, CurMaxInit, VmaxInit, VminInit, Locationsi = runDSS(P,Gen,u,ug)
                 Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,P,Gen,Loadarray,CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
                 LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,P,Gen,PO,LB,UB)
    
             ########### Turn down generation ##########
             print('Phase '+str(p+1))
             print('Vmin (p.u)' +str(Vmin[:,p]))
             for z in UpInd:
                 if LoadBusByPhase[p]['VMin-Dem-UP'].loc[z] > 0 and LoadBusByPhase[p]['VMin-Dem-UP'][z] > LoadBusByPhase[p]['VMin-Dem-DOWN'][z]:
                    u[z]= -(0.94 - Vmin[:,p])/LoadBusByPhase[p]['VMin-Dem-UP'][z]/(len(UpInd)*grad)
                    #u[z]= -(0.94 - Vmin[:,p])/LoadBusByPhase[p]['VMin-Dem-UP'][UpInd].mean()/(len(UpInd)*grad)
                    Gen[z]= max((Gen[z]+u[z]),UB[z])
                    
             ########### Turn Down Demand ##########       
             for z in DownInd:
                 if LoadBusByPhase[p]['VMin-Dem-DOWN'][z] > 0 and LoadBusByPhase[p]['VMin-Dem-DOWN'][z] > LoadBusByPhase[p]['VMin-Dem-UP'][z]:
                    u[z]= (0.94 - Vmin[:,p])/LoadBusByPhase[p]['VMin-Dem-DOWN'][z]/(len(DownInd)*grad)
                    #u[z]= (0.94 - Vmin[:,p])/LoadBusByPhase[p]['VMin-Dem-DOWN'][DownInd].mean()/(len(DownInd)*grad)
                    P[z]= max((P[z]-u[z]),LB[z])
             PN=copy.copy(P)       
             print('Adjustments per agent (kW)')
             print(u)
             print('New Agent Set Points (kW)')
             print(P)
             print('New Agent PV Set Points (kW)')
             print(Gen)
             u=P*0
             ug=Gen*0
             Loadarray,  CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,Locations = runDSS(P,Gen,u,ug)
             Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,P,Gen,Loadarray,CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
             LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,PN,Gen,PO,LB,UB)
             print(Vmin[:,p])
             
            ###########  Make adjustments to relieve Vmax ###########
          while Vmax[:,p] > 1.1:
             print('High Voltage Violation')
             UpInd=LoadBusByPhase[p][LoadBusByPhase[p]['UHDRm']>0].index
             DownInd=LoadBusByPhase[p][LoadBusByPhase[p]['LHDRm']>0].index
             if len(UpInd)==0:
                 #print('Insufficient AGENT Upward Flexibility: Non Agent Adjustments required')
                 UB=0
                 Loadarray,  CurArray, VoltArray, RateArray, CurMaxInit, VmaxInit, VminInit, Locationsi = runDSS(P,Gen,u,ug)
                 Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,P,Gen,Loadarray,CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
                 LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,P,Gen,PO,LB,UB)
             if len(DownInd)==0:
                 #print('Insuficcient AGENT Downward Flexibility')
                 LB=PO-EVd-HPd
                 Loadarray,  CurArray, VoltArray, RateArray, CurMaxInit, VmaxInit, VminInit, Locationsi = runDSS(P,Gen,u,ug)
                 Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,P,Gen,Loadarray,CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
                 LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,P,Gen,PO,LB,UB)
    
             print('Phase '+str(p+1))
             print('Vmax (p.u)'+str(Vmax[:,p]))
             for z in UpInd:
                 ########### Turn Down Generation ##########  
                 if LoadBusByPhase[p]['VMax-Dem-UP'][z] < 0 and LoadBusByPhase[p]['VMax-Dem-UP'][z] < LoadBusByPhase[p]['VMax-Dem-DOWN'][z]:
                    u[z]= -(1.1 - Vmax[:,p])/LoadBusByPhase[p]['VMax-Dem-UP'][z]/(len(UpInd)*grad)
                    #u[z]= (1.1 - Vmax[:,p])/LoadBusByPhase[p]['VMax-Dem-UP'][UpInd].mean()/(len(UpInd)*grad)
                    Gen[z]= max((Gen[z]+u[z]),UB[z])
             
             for z in DownInd:
                 ########### Turn Down Demand ##########  
                 if LoadBusByPhase[p]['VMax-Dem-DOWN'][z] < 0 and LoadBusByPhase[p]['VMax-Dem-DOWN'][z] < LoadBusByPhase[p]['VMax-Dem-UP'][z]:
                    u[z]= -(1.1 - Vmax[:,p])/LoadBusByPhase[p]['VMax-Dem-DOWN'][z]/(len(DownInd)*grad)
                    #u[z]= -(1.1 - Vmax[:,p])/LoadBusByPhase[p]['VMax-Dem-DOWN'][DownInd].mean()/(len(DownInd)*grad)
                    P[z]= max((P[z]-u[z]),LB[z])
    
             print('Adjustments per agent (kW)')
             print(u)
             print('New Agent Set Points (kW)')
             print(P)
             print('New Agent PV Set Points (kW)')
             print(Gen)
             PN=copy.copy(P)  
             u=P*0
             ug=Gen*0
             Loadarray,  CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,Locations = runDSS(P,Gen,u,ug)
             Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,P,Gen,Loadarray,CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
             LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,PN,Gen,PO,LB,UB)
             print(Vmax[:,p])
            ###########  Make adjustments to relieve Cmax  ###########         
          while CurMax[:,p] > 0.5:
             print('Thermal Violation')
             UpInd=LoadBusByPhase[p][LoadBusByPhase[p]['UHDRm']>0].index
             DownInd=LoadBusByPhase[p][LoadBusByPhase[p]['LHDRm']>0].index
             if len(UpInd)==0:
                 #print('Insufficient Upward Flexibility: ')
                 UB=0
                 Loadarray,  CurArray, VoltArray, RateArray, CurMaxInit, VmaxInit, VminInit, Locationsi = runDSS(P,Gen,u,ug)
                 Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,P,Gen,Loadarray,  CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
                 LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,P,Gen,PO,LB,UB)
             if len(DownInd)==0:
                 #print('Insuficcient Downward Flexibility')
                 LB=PO-EVd-HPd
                 Loadarray,  CurArray, VoltArray, RateArray, CurMaxInit, VmaxInit, VminInit, Locationsi = runDSS(P,Gen,u,ug)
                 Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,P,Gen,Loadarray,CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
                 LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,P,Gen,PO,LB,UB)
    
            
             print('Phase '+str(p+1))
             print('Max Current Overload (A)'+str(CurMax[:,p]))
             for z in UpInd:
                 ########### Turn Down Generation ##########  
                 if LoadBusByPhase[p]['Cmax-Dem-UP'][z] < 0 and LoadBusByPhase[p]['Cmax-Dem-UP'][z] < LoadBusByPhase[p]['Cmax-Dem-DOWN'][z]:
                    u[z]= CurMax[:,p]/LoadBusByPhase[p]['Cmax-Dem-UP'][z]/(len(UpInd)*grad)
                    #u[z]= CurMax[:,p]/LoadBusByPhase[p]['Cmax-Dem-UP'][UpInd].mean()/(len(UpInd)*Cgrad)
                    Gen[z]= max((Gen[z]+u[z]),UB[z])
                    
             for z in DownInd:
                 ########### Turn Down Demand ##########  
                 if LoadBusByPhase[p]['Cmax-Dem-DOWN'][z] < 0 and LoadBusByPhase[p]['Cmax-Dem-DOWN'][z] < LoadBusByPhase[p]['Cmax-Dem-UP'][z]:
                    u[z]= -CurMax[:,p]/LoadBusByPhase[p]['Cmax-Dem-DOWN'][z]/(len(DownInd)*Cgrad)
                    #u[z]= -CurMax[:,p]/LoadBusByPhase[p]['Cmax-Dem-DOWN'][DownInd].mean()/(len(DownInd)*Cgrad)
                    P[z]= max((P[z]-u[z]),LB[z])
    
             print('Adjustments per agent (kW)')
             print(u)
             print('New Agent Set Points (kW)')
             print(P)
             print('New Agent PV Set Points (kW)')
             print(Gen)
             PN=copy.copy(P)  
             u=P*0
             ug=Gen*0
             Loadarray,  CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,Locations = runDSS(PN,Gen,u,ug)
             Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,PN,Gen,Loadarray,CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
             LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,PN,Gen,PO,LB,UB)
             print(CurMax[:,p])
             
    return P, Gen, LoadBusByPhase

   
   