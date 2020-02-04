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

#P= np.array([11.50034239,  2.47454889,  0.61089075,  4.40891062,  9.42233832,
#        4.36033616,  1.25117596,  1.66008232,  1.86465633,  2.69840792,
#        0.86844222,  4.56870632, 12.15824116,  4.91312382,  6.61092013,
#        1.73990761,  2.61695063,  2.04417424,  0.75918933,  2.69252254,
#        2.03992466,  1.66443946,  6.6702814 ,  0.7590303 , 10.23056161,
#        4.02688667,  5.66458177,  4.80274726,  0.46542819,  8.86541455,
#        0.35190725])
###
#LB = [0.3236565 , 0.49340403, 0.61089075, 0.2689442 , 0.43846933,
#       0.2804749 , 0.82462984, 1.66008232, 0.16869679, 2.69840792,
#       0.86844222, 0.47940806, 0.42811769, 4.91312382, 0.85294843,
#       0.33321091, 0.40231143, 0.4445636 , 0.75918933, 0.85867965,
#       2.03992466, 0.14023854, 0.2072955 , 0.7386037 , 0.29484422,
#       0.76649432, 0.43227695, 3.56414363, 0.46542819, 0.67357485,
#       0.35190725]
###
#UB = [15.11958717,  5.86970013,  0.61089075,  7.81649618,  9.42233832,
#        4.36033616,  1.25117596,  1.66008232,  1.86465633,  5.45278591,
#        0.86844222,  7.88778071, 12.15824116,  4.91312382,  9.90486571,
#        1.73990761,  2.61695063,  2.04417424,  0.75918933,  2.69252254,
#        2.58965467,  1.66443946,  6.6702814 ,  0.7590303 , 10.23056161,
#        4.02688667,  5.66458177,  4.80274726,  1.35899827,  8.86541455,
#        0.35190725]
#
#PVd= [0, 0        , 0, 0        , 0,
#       0        , 0, 0        , 0, 0        ,
#       0, 0        , 0, 0        , 0,
#       0        , 0, 0        , 0, 0        ,
#       0, 0        , 0, 0       , 0,
#       0        , 0, 0        , 0, 0        ,
#       0]
#
#EVd= [14.79593067,  0        ,  0        ,  0        ,  8.98386899,
#        0        ,  0.42654611,  0        ,  1.69595954,  0        ,
#        0        ,  0        , 11.73012346,  0        ,  9.05191729,
#        0        ,  2.21463921,  0        ,  0        ,  0        ,
#        0.54973   ,  0        ,  6.46298591,  0        ,  9.93571739,
#        0        ,  5.23230482,  0        ,  0.89357009,  0        ,
#        0        ]
#
#HPd= [0        , 5.37629611, 0        , 7.54755198, 0        ,
#       4.07986126, 0        , 0        , 0        , 2.754378  ,
#       0        , 7.40837265, 0        , 0        , 0        ,
#       1.40669669, 0        , 1.59961065, 0        , 1.83384288,
#       0        , 1.52420092, 0        , 0.0204266 , 0        ,
#       3.26039235, 0        , 1.23860363, 0        , 8.1918397 ,
#       0        ]
#
#
#u=0*P
#PO=copy.copy(P)
#n=0
#Loadarray,  CurArray, VoltArray, RateArray, CurMaxInit, VmaxInit, VminInit, Locationsi = runDSS(P,u)
#
#   ## Run Sensitivity ###
#   
#Violperphase,VmaxFlagInit, VminFlagInit, ThermalFlagInit,n,Locations = sensitivity(LoadsIn,P,Loadarray, CurArray, VoltArray, RateArray, CurMaxInit, VmaxInit, VminInit,n)
#
#   ### Generate Summary (LoadBus) #######
#
#LoadBusByPhase = summary(LoadsIn,Violperphase,CurMaxInit, VmaxInit, VminInit,P,PO,LB,UB)


def actions_opt(P,LB,UB,PVd,EVd,HPd,u,n,LoadBusByPhase,CurMaxInit,VmaxInit,VminInit,LoadsIn,PO):
    ########### Take Actions ############
    grad=1
    Cgrad=1
    CurMax=CurMaxInit
    Vmax=VmaxInit
    Vmin=VminInit
    for p in range(0,3):
        print(p)
        while Vmax[:,p] > 1.1 or Vmin[:,p] < 0.94 or CurMax[:,p] > 0.5:
          ###########  Make adjustments to relieve Vmin Pro-RATA ###########
          while Vmin[:,p] < 0.94:
             UpInd=LoadBusByPhase[p][LoadBusByPhase[p]['UHDRm']>0].index
             DownInd=LoadBusByPhase[p][LoadBusByPhase[p]['LHDRm']>0].index
             if len(UpInd)==0:
                 print('Insufficient Upward AGENT Flexibility')
                 UB=PO+PVd
                 Loadarray,  CurArray, VoltArray, RateArray, CurMaxInit, VmaxInit, VminInit, Locationsi = runDSS(P,u)
                 Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,P,Loadarray,  CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
                 LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,P,PO,LB,UB)
             if len(DownInd)==0:
                 print('Insufficient Downward AGENT Flexibility')
                 LB=PO-EVd-HPd
                 Loadarray,  CurArray, VoltArray, RateArray, CurMaxInit, VmaxInit, VminInit, Locationsi = runDSS(P,u)
                 Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,P,Loadarray,  CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
                 LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,P,PO,LB,UB)
    
    
             print(p)
             print(Vmin[:,p])
             for z in UpInd:
                 if LoadBusByPhase[p]['VMin-Dem-UP'].loc[z] > 0 and LoadBusByPhase[p]['VMin-Dem-UP'][z] > LoadBusByPhase[p]['VMin-Dem-DOWN'][z]:
                    #u[z]= (0.94 - Vmin[:,p])/LoadBusByPhase[p]['VMin-Dem-UP'][UpInd].mean()/(len(UpInd)*grad)
                    u[z]= -(0.94 - Vmin[:,p])/LoadBusByPhase[p]['VMin-Dem-UP'][z]/(len(UpInd)*grad)
                    P[z]= min((P[z]-u[z]),UB[z])
                    
             for z in DownInd:
                 if LoadBusByPhase[p]['VMin-Dem-DOWN'][z] > 0 and LoadBusByPhase[p]['VMin-Dem-DOWN'][z] > LoadBusByPhase[p]['VMin-Dem-UP'][z]:
                    #u[z]= (0.94 - Vmin[:,p])/LoadBusByPhase[p]['VMin-Dem-DOWN'][DownInd].mean()/(len(DownInd)*grad)
                    u[z]= (0.94 - Vmin[:,p])/LoadBusByPhase[p]['VMin-Dem-DOWN'][z]/(len(DownInd)*grad)
                    P[z]= max((P[z]-u[z]),LB[z])
             PN=copy.copy(P)       
    
             print(u)
             print(P)
             u=P*0
             Loadarray,  CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,Locations = runDSS(P,u)
             Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,P,Loadarray,  CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
             LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,PN,PO,LB,UB)
             print(Vmin[:,p])
             
            ###########  Make adjustments to relieve Vmax Pro-RATA ###########
          while Vmax[:,p] > 1.1:
             UpInd=LoadBusByPhase[p][LoadBusByPhase[p]['UHDRm']>0].index
             DownInd=LoadBusByPhase[p][LoadBusByPhase[p]['LHDRm']>0].index
             if len(UpInd)==0:
                 print('Insufficient Upward Flexibility')
                 UB=PO+PVd
                 Loadarray,  CurArray, VoltArray, RateArray, CurMaxInit, VmaxInit, VminInit, Locationsi = runDSS(P,u)
                 Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,P,Loadarray,  CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
                 LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,P,PO,LB,UB)
             if len(DownInd)==0:
                 print('Insuficcient Downward Flexibility')
                 LB=PO-EVd-HPd
                 Loadarray,  CurArray, VoltArray, RateArray, CurMaxInit, VmaxInit, VminInit, Locationsi = runDSS(P,u)
                 Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,P,Loadarray,  CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
                 LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,P,PO,LB,UB)
    
             print(p)
             print(Vmax[:,p])
             for z in UpInd:
                 if LoadBusByPhase[p]['VMax-Dem-UP'][z] < 0 and LoadBusByPhase[p]['VMax-Dem-UP'][z] < LoadBusByPhase[p]['VMax-Dem-DOWN'][z]:
                    #u[z]= -(1.1 - Vmax[:,p])/LoadBusByPhase[p]['VMax-Dem-UP'][UpInd].mean()/(len(UpInd)*grad)
                    u[z]= (1.1 - Vmax[:,p])/LoadBusByPhase[p]['VMax-Dem-UP'][z]/(len(UpInd)*grad)
                    P[z]= min((P[z]-u[z]),UB[z])
             
             for z in DownInd:           
                 if LoadBusByPhase[p]['VMax-Dem-DOWN'][z] < 0 and LoadBusByPhase[p]['VMax-Dem-DOWN'][z] < LoadBusByPhase[p]['VMax-Dem-UP'][z]:
                    #u[z]= -(1.1 - Vmax[:,p])/LoadBusByPhase[p]['VMax-Dem-DOWN'][DownInd].mean()/(len(DownInd)*grad)
                    u[z]= -(1.1 - Vmax[:,p])/LoadBusByPhase[p]['VMax-Dem-DOWN'][z]/(len(DownInd)*grad)
                    P[z]= max((P[z]-u[z]),LB[z])
    
             print(u)
             print(P)
             PN=copy.copy(P)  
             u=P*0
             Loadarray,  CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,Locations = runDSS(P,u)
             Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,P,Loadarray,  CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
             LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,PN,PO,LB,UB)
             print(Vmax[:,p])
            ###########  Make adjustments to relieve Cmax Pro-RATA ###########         
          while CurMax[:,p] > 0.5:
             UpInd=LoadBusByPhase[p][LoadBusByPhase[p]['UHDRm']>0].index
             DownInd=LoadBusByPhase[p][LoadBusByPhase[p]['LHDRm']>0].index
             if len(UpInd)==0:
                 print('Insufficient Upward Flexibility')
                 UB=PO+PVd
                 Loadarray,  CurArray, VoltArray, RateArray, CurMaxInit, VmaxInit, VminInit, Locationsi = runDSS(P,u)
                 Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,P,Loadarray,  CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
                 LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,P,PO,LB,UB)
             if len(DownInd)==0:
                 print('Insuficcient Downward Flexibility')
                 LB=PO-EVd-HPd
                 Loadarray,  CurArray, VoltArray, RateArray, CurMaxInit, VmaxInit, VminInit, Locationsi = runDSS(P,u)
                 Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,P,Loadarray,  CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
                 LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,P,PO,LB,UB)
    
    
             print(p)
             print(CurMax[:,p])
             for z in UpInd:
                 if LoadBusByPhase[p]['Cmax-Dem-UP'][z] < 0 and LoadBusByPhase[p]['Cmax-Dem-UP'][z] < LoadBusByPhase[p]['Cmax-Dem-DOWN'][z]:
                    #u[z]= (CurMax[:,p]/LoadBusByPhase[p]['Cmax-Dem-UP'][UpInd].mean())/(len(UpInd)*Cgrad)
                    u[z]= CurMax[:,p]/LoadBusByPhase[p]['Cmax-Dem-UP'][z]/(len(UpInd)*Cgrad)
                    P[z]= min((P[z]-u[z]),UB[z])
                    
             for z in DownInd:           
                 if LoadBusByPhase[p]['Cmax-Dem-DOWN'][z] < 0 and LoadBusByPhase[p]['Cmax-Dem-DOWN'][z] < LoadBusByPhase[p]['Cmax-Dem-UP'][z]:
                    #u[z]= -(CurMax[:,p]/LoadBusByPhase[p]['Cmax-Dem-DOWN'][DownInd].mean())/(len(DownInd)*Cgrad)
                    u[z]= -CurMax[:,p]/LoadBusByPhase[p]['Cmax-Dem-DOWN'][z]/(len(DownInd)*Cgrad)
                    P[z]= max((P[z]-u[z]),LB[z])
    
             print(u)
             print(P)
             PN=copy.copy(P)  
             u=P*0
             Loadarray,  CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,Locations = runDSS(PN,u)
             Violations,VmaxFlag, VminFlag, ThermalFlag,n,Locations = sensitivity(LoadsIn,PN,Loadarray,  CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n)
             LoadBusByPhase = summary(LoadsIn,Violations,CurMax, Vmax, Vmin,PN,PO,LB,UB)
             print(CurMax[:,p])
             
    return P, LoadBusByPhase

#plots(LoadBusByPhase,VoltArray,CurArray,RateArray)


   
   