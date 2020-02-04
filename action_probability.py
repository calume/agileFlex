# -*- coding: utf-8 -*-
"""
Created on Thu May 02 13:48:06 2019

@author: Calum Edmunds

Scripts to calculate probability of flexibility providers or 'agents' being called 

"""


######## Importing the OpenDSS Engine and other packages #########
import opendssdirect as dss
import pandas as pd
from opendssdirect.utils import run_command
pd.options.mode.chained_assignment = None 
import timeit
import pickle
from matplotlib import pyplot as plt
from datetime import datetime, timedelta, date, time
import datetime
import os
import random
import csv
import numpy as np
from numpy.random import choice
from sensitivity import sensitivity
from runDSS import runDSS
from summary import summary
from actions import actions
from actions_opt import actions_opt
#from actions_opt import SortedF
import cloudpickle
import copy
### Date stuff ###

startdate =  date(2013,8,22)
enddate   =  date(2014,11,17)
delta = datetime.timedelta(hours=0.5)
deltaHalf = datetime.timedelta(hours=0.5)

dt = pd.date_range(startdate, enddate, freq=delta) #datetime steps
dtPVreset = pd.date_range(date(2012,10,1), date(2013,11,17), freq=deltaHalf) #datetime steps

LoadsIn = pd.read_csv("Loads.txt",delimiter=' ', names=['New','Load','Phase','Bus1','kV','kW','PF','Daily'] )
LoadsIn['Phase']=LoadsIn['Bus1'].str[-1:]

########### EV IN ##############
with open('JDEV_kde.cp.pkl', 'rb') as f:
    EV_kde = cloudpickle.load(f)

###########  Smartmeter Data  ###############
with open('SM_kde.cp.pkl', 'rb') as f:
    SM_kde = cloudpickle.load(f)
########### PV IN ##############

with open('PV_kde.cp.pkl', 'rb') as f:
    PV_kde = cloudpickle.load(f)
    
########### HP IN ##############

with open('HP_kde.cp.pkl', 'rb') as f:
    HP_kde = cloudpickle.load(f)

pickle_in = open("SMDistsGMMChosen.pickle","rb")
SM_GM = pickle.load(pickle_in)

pickle_in = open("SMDistsGMMWeights.pickle","rb")
SM_GMW = pickle.load(pickle_in)


######## Assign PV, Agent, EV Tags and Zone per Load Node ############

Flags=pd.DataFrame(0, index=(range(0,len(LoadsIn))), columns=['PV','Agent','EV','SM','HP','Zone'])

Flags['EV'][::1]= 1  # Every house has EV
Flags['PV'][::1]= 6   # Every house has PV 4.5kW  
Flags['Agent'][::1]=1  # Every house is an agent

###### Randomly assing Smart Meters ########
K=list(SM_kde['WintWkndDists'].keys())
for i in Flags.index.tolist():
   Flags['SM'][i]=random.choice(K) 

K=list(HP_kde['WintWkndDists'].keys())
for i in Flags.index.tolist():
   Flags['HP'][i]=random.choice(K) 

#Flags['HP'][::2]=0  # Every 2nd house has a HP

################### Calculating Load for each Demand ############################

#sims = pd.date_range(date(2013,1,10), date(2013,1,20), freq=deltaHalf)
d1=date(2013,6,1)
d2=date(2013,7,1)
sims = pd.date_range(d1, d2, freq=delta)
zind = pd.Series(0,index=sims)

P={}
Gen={}
P_Opt={}
perc=0.2
n=0
PO={}
GenO={}
aa={}
SMd={}
SMC={}
EVd={}
PVd={}
HPd={}
UB={}
LB={}
CongSummary={}
AgentSummary={}
LoadBusByPhase={}


for i in sims.tolist():
    print(i)
   if (i.weekday()>=5) & (i.weekday() <=6): ###Weekend######
       EV=EV_kde#['WkndDists']
       if (i.month==12) | (i.month<=2):      #Dec-Feb
           SM=SM_GM['WintWkndDists']
           SMW=SM_GMW['WintWkndDists']
           HP=HP_kde['WintWkndDists']
           PV=PV_kde['WintDists']
       if (i.month>=3) & (i.month <=5):    #Mar-May
           SM=SM_GM['SpringWkndDists']
           SMW=SM_GMW['SpringWkndDists']
           HP=HP_kde['SpringWkndDists']
           PV=PV_kde['SpringDists']
       if (i.month>=6) & (i.month <=8):    #Jun-Aug
           SM=SM_GM['SummerWkndDists']
           SMW=SM_GMW['SummerWkndDists']
           HP=HP_kde['SummerWkndDists']
           PV=PV_kde['SummerDists']
       if (i.month>=9) & (i.month <=11):   #Sept-Nov
           SM=SM_GM['AutumnWkndDists']
           SMW=SM_GMW['AutumnWkndDists']
           HP=HP_kde['AutumnWkndDists']
           PV=PV_kde['AutumnDists']
   if (i.weekday()>=0) & (i.weekday() <=4): ##Weekday######
       EV=EV_kde#['WkdDists']
       if (i.month==12) | (i.month<=2):      #Dec-Feb
           SM=SM_GM['WintWkdDists']
           SMW=SM_GMW['WintWkdDists']
           HP=HP_kde['WintWkdDists']
           PV=PV_kde['WintDists']
       if (i.month>=3) & (i.month <=5):    #Mar-May
           SM=SM_GM['SpringWkdDists']
           SMW=SM_GMW['SpringWkdDists']
           HP=HP_kde['SpringWkdDists']
           PV=PV_kde['SpringDists']
       if (i.month>=6) & (i.month <=8):    #Jun-Aug
           SM=SM_GM['SummerWkdDists']
           SMW=SM_GMW['SummerWkdDists']
           HP=HP_kde['SummerWkdDists']
           PV=PV_kde['SummerDists']
       if (i.month>=9) & (i.month <=11):   #Sept-Nov
           SM=SM_GM['AutumnWkdDists']
           SMW=SM_GMW['AutumnWkdDists']
           HP=HP_kde['AutumnWkdDists']
           PV=PV_kde['AutumnDists']    
   for z in range(0,len(Flags)):
       n=choice(range(0,len(SM[Flags['SM'][z]])), 1, p=SMW[Flags['SM'][z]])
       SMC[z]=SM[Flags['SM'][z]][n]
       
   for i in range(0,48):
       print(i)
       P[i]=np.zeros(len(Flags))
       Gen[i]=np.zeros(len(Flags))
       Currents={} 
       Voltages={}
       Loads={}
       Rates={}
       CLmax={}
       SMd[i]=np.zeros(len(Flags))
       EVd[i]=np.zeros(len(Flags))
       PVd[i]=np.zeros(len(Flags))
       HPd[i]=np.zeros(len(Flags))  
       UB[i]=np.zeros(len(Flags))
       LB[i]=np.zeros(len(Flags))
   for z in range(0,len(Flags)):
       SM[i][z]=SMC[z][i]

       EVd[i][z]=Flags['EV'][z]
       HPd[i][z]=Flags['HP'][z]
       PVd[i][z]=Flags['PV'][z]
   
       P[i][z] = SMd[i][z] + EVd[i][z] + HPd[i][z]
       Gen[i][z] = PVd[i][z]
       UB[i][z]=int(not(Flags['Agent'][z]))*Gen[i][z]   # Which equates to SMd[i][z]+HPd[i][z]+EVd[i][z]
       LB[i][z]=P[i][z]+Flags['Agent'][z]*(-EVd[i][z]-HPd[i][z])  # Which equates to  SMd[i][z]-PVd[i][z]

   
   u=0*P[i]

   P[i][np.isnan(P[i])] = 0
   PO[i]=copy.copy(P[i])
   GenO[i]=copy.copy(Gen[i])
   ###### Run DSS for initial network state ###########
   n=1
   Loadarray,  CurArray, VoltArray, RateArray, CurMaxInit, VmaxInit, VminInit, Locationsi = runDSS(P[i],Gen[i],u)
    
   ## Run Sensitivity ###
   
   Violperphase,VmaxFlagInit, VminFlagInit, ThermalFlagInit,n,Locations = sensitivity(LoadsIn,P[i], Gen[i],Loadarray,  CurArray, VoltArray, RateArray, CurMaxInit, VmaxInit, VminInit,n)
    
   ### Generate LoadBus Summary  #######

   LoadBusByPhase[i] = summary(LoadsIn,Violperphase,CurMaxInit, VmaxInit, VminInit,P[i],Gen[i],PO[i],LB[i],UB[i])
   

   P[i], Gen[i], LoadBusByPhase[i]  = actions(P[i],Gen[i],LB[i],UB[i],PVd[i],EVd[i],HPd[i],u,n,LoadBusByPhase[i],CurMaxInit,VmaxInit,VminInit,LoadsIn,PO[i])

   if sum(VminFlagInit+VmaxFlagInit+ThermalFlagInit) >0:
       CongSummary[i]={}
       for p in range(0,2):
           CongSummary[i][p]={}
           if ThermalFlagInit[p] ==True:
               CongSummary[i][p]['Thermal']=Locationsi['Cmax'][p]
           if VmaxFlagInit[p] ==True:
               CongSummary[i][p]['Vhigh']=Locationsi['Vmax'][p]
           if VminFlagInit[p] ==True:
               CongSummary[i][p]['Vlow']=Locationsi['Vmin'][p]
   
    ###### Create summary of agent actions ###########
   AgentSummary[i]=pd.DataFrame(index=range(0,len(LoadsIn)),columns=['Bus','Phase','BaseDemand','EV','PV','HP','LoadSetPoint','DemLB','GenUB','DemAdjust','FinalDem','FinalGen','GenAdjust'])
   AgentSummary[i]['Bus']=LoadsIn['Bus1'].str[5:-2]
   AgentSummary[i]['Phase']=LoadsIn['Phase']
   AgentSummary[i]['BaseDemand']=SMd[i]
   AgentSummary[i]['EV']=EVd[i]
   AgentSummary[i]['PV']=PVd[i]
   AgentSummary[i]['HP']=HPd[i]
   AgentSummary[i]['LoadSetPoint']=PO[i]
   AgentSummary[i]['DemLB']=LB[i]
   AgentSummary[i]['GenLB']=UB[i]
   AgentSummary[i]['DemAdjust']=P[i]-PO[i]
   AgentSummary[i]['FinalDem']=P[i]
   AgentSummary[i]['FinalGen']=Gen[i]
   AgentSummary[i]['GenAdjust']=Gen[i]-GenO[i]

pickle_out = open("AgentSummary.pickle","wb")
pickle.dump(AgentSummary, pickle_out)
pickle_out.close()