# -*- coding: utf-8 -*-
"""
Created on Fri Aug  2 11:54:13 2019

@author: qsb15202
"""
######## Importing the OpenDSS Engine  #########

import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None
from runDSS import runDSS
import opendssdirect as dss
DSSCircuit = dss.Circuit
DSSLoads= dss.Loads;
DSSBus = dss.Bus
DSSLines = dss.Lines


def sensitivity(LoadsIn,P,Gen,Loadarray,  CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin,n):
   perc = 0.5   # The percentage change for sensitivities
   #### initialise ###
   ThermalFlag=[False,False,False]
   VminFlag=[False,False,False]
   VmaxFlag=[False,False,False]
    
   Violperphase={}
    
   ############## Thermal Sensitivity, also covers low voltage #############
   ####### First check Downward Demand, for Import constraint ###########
   ###### Per Phase Sensitivity ######
   for p in range(0,3):
       phaseInd = LoadsIn[LoadsIn['Phase'].astype(int)==(p+1)].index
       Violations=pd.DataFrame(index=phaseInd)
       Locations=0
       if CurMax[:,p] > 0:
          ThermalFlag[p]=True
          CurMaxSensDown=np.zeros((len(phaseInd),3))
          CurPercPercDown=np.zeros((len(phaseInd)))
          CurMaxSensUp=np.zeros((len(phaseInd),3))
          CurPercPercUp=np.zeros((len(phaseInd)))  
          for i in range(0,len(phaseInd)):
              u=0*P
              u[phaseInd[i]] = abs(perc*P[phaseInd[i]])
              n=n+1
              LS, CS, VS, RS, CurMaxSensDown[i], Vmaxi, Vmini, Locations = runDSS(P,Gen,u)
              CurPercPercDown[i] = (CurMaxSensDown[i,p]-CurMax[:,p]) / abs(u[phaseInd[i]])#abs(u[phaseInd[i]])   #If better this is Negative Number
     
      ###### If downward demand didnt help, run upward demand for export constraint ########
              if CurMaxSensDown[i,p] > CurMax[:,p]:  #If CurPercPercDown[i] is positive then max has increased, made worse
                  u=0*P
                  u[phaseInd[i]] = -abs(perc*P[phaseInd[i]])  #Load is added, P -- u = P + u
                  n=n+1
                  LS, CS, VS, RS, CurMaxSensUp[i], Vmaxi, Vmini, Locations = runDSS(P,Gen,u)
                  CurPercPercUp[i] = (CurMaxSensUp[i,p]-CurMax[:,p]) / abs(u[phaseInd[i]])
          Violations['CurPercPercUp']=CurPercPercUp
          Violations['CurPercPercDown']=CurPercPercDown
       ######### Min Voltage sensitivity, downward demand. Will aready be covered if Thermal problem ###########
       if Vmin[:,p] < 0.94:
          VminFlag[p]=True
          VminSensDown=np.zeros((len(phaseInd),3))
          VminPercPercDown=np.zeros((len(phaseInd)))
          VminSensUp=np.zeros((len(phaseInd),3))
          VminPercPercUp=np.zeros((len(phaseInd)))
          for i in range(0,len(phaseInd)):
              u=0*P
              u[phaseInd[i]] = abs(perc*P[phaseInd[i]])
              n=n+1
              LS, CS, VS, RS, CurMaxi, Vmaxi, VminSensDown[i], Locations = runDSS(P,Gen,u)
              VminPercPercDown[i] = (VminSensDown[i,p]-Vmin[:,p]) / abs(u[phaseInd[i]]) 
            
            ###### If downward demand didnt help, run upward demand just incase ########
              if VminSensDown[i,p] < Vmin[:,p]:
                  u=0*P
                  u[phaseInd[i]] = -abs(perc*P[phaseInd[i]])
                  n=n+1
                  LS, CS, VS, RS, CurMaxi, Vmaxi, VminSensUp[i], Locations = runDSS(P,Gen,u)
                  VminPercPercUp[i] = (VminSensUp[i,p]-Vmin[:,p]) / abs(u[phaseInd[i]])    
          Violations['VminPercPercUp']=VminPercPercUp
          Violations['VminPercPercDown']=VminPercPercDown          
          ######### Max Voltage sensitivity, with upward demand/downward generation ###########
       if Vmax[:,p] > 1.1:
             VmaxFlag[p]=True
             VmaxSensUp=np.zeros((len(phaseInd),3))
             VmaxPercPercUp=np.zeros((len(phaseInd)))
             VmaxSensDown=np.zeros((len(phaseInd),3))
             VmaxPercPercDown=np.zeros((len(phaseInd)))
             for i in range(0,len(phaseInd)):
                 u=0*P
                 u[phaseInd[i]] = -abs(perc*P[phaseInd[i]])
                 n=n+1
                 LS, CS, VS, RS, CurMaxi, VmaxSensUp[i], Vmini, Locations = runDSS(P,Gen,u)
                 VmaxPercPercUp[i] = (VmaxSensUp[i,p]-Vmax[:,p]) / abs(u[phaseInd[i]])
                 ###### If upward demand didnt help, run downward demand just incase ########
                 if VmaxSensUp[i].max() > Vmax.max():
                     u=0*P
                     u[phaseInd[i]] = abs(perc*P[phaseInd[i]])
                     n=n+1
                     LS, CS, VS, RS, CurMaxi, VmaxSensDown[i], Vmini, Locations = runDSS(P,Gen,u)
                     VmaxPercPercDown[i] = (VmaxSensDown[i,p]-Vmax[:,p]) / abs(u[phaseInd[i]])
             Violations['VmaxPercPercDown']=VmaxPercPercDown         
             Violations['VmaxPercPercUp']=VmaxPercPercUp
       Violperphase[p]=Violations
   return Violperphase,VmaxFlag, VminFlag, ThermalFlag, n, Locations

