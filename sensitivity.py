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
      if CurMax[:,p] > 0.5 or Vmin[:,p] < 0.94 or Vmax[:,p] > 1.1:
          if CurMax[:,p] > 0.5:
              ThermalFlag[p]=True
          if Vmin[:,p] < 0.94:
              VminFlag[p]=True
          if Vmax[:,p] > 1.1:
              VmaxFlag[p]=True          
          CurMaxSensDown=np.zeros((len(phaseInd),3))
          CurPercPercDown=np.zeros((len(phaseInd)))
          CurMaxSensUp=np.zeros((len(phaseInd),3))
          CurPercPercUp=np.zeros((len(phaseInd)))
          VminSensDown=np.zeros((len(phaseInd),3))
          VminPercPercDown=np.zeros((len(phaseInd)))
          VminSensUp=np.zeros((len(phaseInd),3))
          VminPercPercUp=np.zeros((len(phaseInd)))
          VmaxSensUp=np.zeros((len(phaseInd),3))
          VmaxPercPercUp=np.zeros((len(phaseInd)))
          VmaxSensDown=np.zeros((len(phaseInd),3))
          VmaxPercPercDown=np.zeros((len(phaseInd)))      
          ###### Downward demand. In case of import constraint ############
          for i in range(0,len(phaseInd)):
              u=0*P
              ug=0*Gen
              u[phaseInd[i]] = abs(perc*P[phaseInd[i]])
              n=n+1
              LS, CS, VS, RS, CurMaxSensDown[i], VmaxSensDown[i], VminSensDown[i], Locations = runDSS(P,Gen,u,ug)
              CurPercPercDown[i] = (CurMaxSensDown[i,p]-CurMax[:,p]) / abs(u[phaseInd[i]])#abs(u[phaseInd[i]])   #If better this is Negative Number
              VminPercPercDown[i] = (VminSensDown[i,p]-Vmin[:,p]) / abs(u[phaseInd[i]]) 
              VmaxPercPercDown[i] = (VmaxSensDown[i,p]-Vmax[:,p]) / abs(u[phaseInd[i]])
              
              ###### If downward demand didnt help, run downward generation for export constraint ########
              if CurMaxSensDown[i,p] > CurMax[:,p]:  #If CurPercPercDown[i] is positive then max has increased, made worse
                  u=0*P
                  ug=0*Gen
                  #u[phaseInd[i]] = -abs(perc*P[phaseInd[i]])  #Load is added, P -- u = P + u
                  ug[phaseInd[i]] = abs(perc*Gen[phaseInd[i]])  #Generation turned down Gen-ug
                  n=n+1
                  LS, CS, VS, RS, CurMaxSensUp[i], VmaxSensUp[i], VminSensUp[i], Locations = runDSS(P,Gen,u,ug)
                  CurPercPercUp[i] = (CurMaxSensUp[i,p]-CurMax[:,p]) / abs(ug[phaseInd[i]])
                  VminPercPercUp[i] = (VminSensUp[i,p]-Vmin[:,p]) / abs(ug[phaseInd[i]])  
                  VmaxPercPercUp[i] = (VmaxSensUp[i,p]-Vmax[:,p]) / abs(ug[phaseInd[i]])
                  
          Violations['CurPercPercUp']=CurPercPercUp
          Violations['CurPercPercDown']=CurPercPercDown
          Violations['VminPercPercUp']=VminPercPercUp
          Violations['VminPercPercDown']=VminPercPercDown 
          Violations['VmaxPercPercDown']=VmaxPercPercDown         
          Violations['VmaxPercPercUp']=VmaxPercPercUp          
          Violperphase[p]=Violations
   return Violperphase,VmaxFlag, VminFlag, ThermalFlag, n, Locations

