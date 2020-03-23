# -*- coding: utf-8 -*-
"""
Created on Thu May 02 13:48:06 2019

@author: Calum Edmunds
"""


######## Importing the OpenDSS Engine  #########
import opendssdirect as dss
import scipy.io
import numpy as np
import pandas as pd
from random import uniform
from random import seed
from opendssdirect.utils import run_command
pd.options.mode.chained_assignment = None 
import timeit
from matplotlib import pyplot as plt
from datetime import datetime, timedelta, date, time
import datetime
import os
import random
import csv
import pickle
import cloudpickle

### Date stuff ###

startdate =  date(2013,10,1)
enddate   =  date(2014,11,17)
delta = datetime.timedelta(hours=1)
deltaHalf = datetime.timedelta(hours=0.5)

dt = pd.date_range(startdate, enddate, freq=delta) #datetime steps
dtPVreset = pd.date_range(date(2012,10,1), date(2013,11,17), freq=deltaHalf) #datetime steps

##### Start Timer ####

start = timeit.default_timer()

####### Compile the OpenDSS file using the Master.txt directory#########

run_command('Redirect ./ENW_MED/Master.dss')

LoadsIn = pd.read_csv("ENW_MED/Loads.txt",delimiter=' ', names=['New','Load','Phase','Bus1','kV','kW','PF','Daily'] )
LoadsIn['Phase']=LoadsIn['Bus1'].str[-1:]

#
### Set up DSS Commands ####

DSSCircuit = dss.Circuit
DSSLoads= dss.Loads;
DSSBus = dss.Bus
DSSLines = dss.Lines

#dss.Basic.ClearAll()
#dss.Basic.Start(0)

###########  Smartmeter Data  ###############
########### EV IN ##############
with open('EV_kde.cp.pkl', 'rb') as f:
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
    
######## Assign PV, Agent, EV Tags and Zone per Load Node ############

Flags=pd.DataFrame(0, index=(range(0,len(LoadsIn))), columns=['PV','Agent','EV','SM','HP','Zone'])

Flags['EV'][::1]= 1  # Every 2nd house has EV
Flags['PV'][::4]= 5

   # Every house has PV 4kW  
Flags['Agent'][::4]=1  # Every 2nd house is an agent

###### Randomly assing Smart Meters ########
K=list(SM_kde['WintWkndDists'].keys())
for i in Flags.index.tolist():
   Flags['SM'][i]=random.choice(K) 

K=list(HP_kde['WintWkndDists'].keys())
for i in Flags.index.tolist():
   Flags['HP'][i]=random.choice(K) 

#Flags['HP'][::1]=0  # Every 2nd house has a HP

################### Calculating Load for each Demand ############################

#sims = pd.date_range(date(2013,1,10), date(2013,1,20), freq=deltaHalf)
sims = pd.date_range(date(2012,1,1), date(2014,1,1), freq=delta)

Vmax=pd.Series(index=sims)
Vmin=pd.Series(index=sims)
CLmax={}
Cmax=pd.Series(index=sims)
Loadsum=pd.Series(index=sims)
SMd={}
EVd={}
PVd={}
HPd={}
for i in sims.tolist():
   print(i)
   
   Currents={} 
   Voltages={}
   Loads={}
   Rates={}
   CLmax={}
   EV=0
   PV=0
   SM=0
   HP=0   
   if (i.weekday()>=5) & (i.weekday() <=6): ###Weekend######
       EV=EV_kde['WkndDists']
       if (i.month==12) | (i.month<=2):      #Dec-Feb
           SM=SM_kde['WintWkndDists']
           HP=HP_kde['WintWkndDists']
           PV=PV_kde['WintDists']
       if (i.month>=3) & (i.month <=5):    #Mar-May
           SM=SM_kde['SpringWkndDists']
           HP=HP_kde['SpringWkndDists']
           PV=PV_kde['SpringDists']
       if (i.month>=6) & (i.month <=8):    #Jun-Aug
           SM=SM_kde['SummerWkndDists']
           HP=HP_kde['SummerWkndDists']
           PV=PV_kde['SummerDists']
       if (i.month>=9) & (i.month <=11):   #Sept-Nov
           SM=SM_kde['AutumnWkndDists']
           HP=HP_kde['AutumnWkndDists']
           PV=PV_kde['AutumnDists']
   if (i.weekday()>=0) & (i.weekday() <=4): ##Weekday######
       EV=EV_kde['WkdDists']
       if (i.month==12) | (i.month<=2):      #Dec-Feb
           SM=SM_kde['WintWkdDists']
           HP=HP_kde['WintWkdDists']
           PV=PV_kde['WintDists']
       if (i.month>=3) & (i.month <=5):    #Mar-May
           SM=SM_kde['SpringWkdDists']
           HP=HP_kde['SpringWkdDists']
           PV=PV_kde['SpringDists']
       if (i.month>=6) & (i.month <=8):    #Jun-Aug
           SM=SM_kde['SummerWkdDists']
           HP=HP_kde['SummerWkdDists']
           PV=PV_kde['SummerDists']
       if (i.month>=9) & (i.month <=11):   #Sept-Nov
           SM=SM_kde['AutumnWkdDists']
           HP=HP_kde['AutumnWkdDists']
           PV=PV_kde['AutumnDists']
   iLoad = DSSLoads.First()        
   SMd[i]=np.zeros(len(Flags))
   EVd[i]=np.zeros(len(Flags))
   PVd[i]=np.zeros(len(Flags))
   HPd[i]=np.zeros(len(Flags))
   if PV[i.hour] != 0:
       samp=max(PV[i.hour].resample(1),0)
   while iLoad>0:
      SMd[i][iLoad-1]=max(SM[Flags['SM'][iLoad-1]][i.hour].resample(1),0)
      if Flags['HP'][iLoad-1] ==0:
          HPd[i][iLoad-1]=0
      else:
          HPd[i][iLoad-1]=max(HP[Flags['HP'][iLoad-1]][i.hour].resample(1),0)
      EVd[i][iLoad-1]=max(EV[i.hour].resample(1),0)*Flags['EV'][iLoad-1]
      if PV[i.hour] == 0:
          PVd[i][iLoad-1]=0
      else:
          PVd[i][iLoad-1]=samp*Flags['PV'][iLoad-1]
      DSSLoads.kW(SMd[i][iLoad-1]+HPd[i][iLoad-1]+EVd[i][iLoad-1]-PVd[i][iLoad-1])
      iLoad = DSSLoads.Next()
   #print(SMd[i].sum()-PVd[i].sum()+EVd[i].sum()+HPd[i].sum())
   ######### Solve the Circuit ############
   
   #dss.Solution.SolveSnap()
   run_command('Solve')
     ########## Export Voltages ###########
   bvs = list(DSSCircuit.AllBusMagPu())
   #Voltages[i]=bvs[0::3],bvs[1::3],bvs[2::3]
   Vmax[i]=max(bvs)
   Vmin[i]=min(bvs)
   
   ########## Export Current ###########
   i_Line = DSSLines.First()
   while i_Line > 0:
      curs = list(dss.CktElement.CurrentsMagAng())
      Currents = curs[0], curs[2], curs[4]
      Rates[i_Line] = dss.CktElement.NormalAmps()
      CLmax[i_Line]= max(np.array(Currents)/Rates[i_Line])
      i_Line = DSSLines.Next()

   Cmax[i]=max(CLmax.values())
  
   ########## Export Loads ###########
   i_Load = DSSLoads.First()
   
   while i_Load>0:
      Loads[i_Load]=DSSLoads.kW()#,DSSLoads.kvar(),DSSLoads.PF()]
      i_Load = DSSLoads.Next()
   Loadsum[i] = sum(Loads.values())
   #print(Loadsum[i])
Alls={}

Alls['Vmax']=Vmax
Alls['Vmin']=Vmin
Alls['HPd']=HPd
Alls['PVd']=PVd
Alls['EVd']=EVd
Alls['SMd']=SMd
Alls['Cmax']=Cmax
Alls['Loadsum']=Loadsum

PVtot=pd.Series(index=PVd.keys())
EVtot=pd.Series(index=PVd.keys())
SMtot=pd.Series(index=PVd.keys())
HPtot=pd.Series(index=PVd.keys())
for i in PVd:
    PVtot[i]=PVd[i].sum()
    EVtot[i]=EVd[i].sum()
    HPtot[i]=HPd[i].sum()
    SMtot[i]=SMd[i].sum()
    
Alls['PVtot']=PVtot
Alls['EVtot']=EVtot
Alls['HPtot']=HPtot
Alls['SMtot']=SMtot
   
stop = timeit.default_timer()

print('Time: ', stop - start)

print('Max current '+str(round(Cmax.max(),3))+' A')
print('Max voltage '+str(round(Vmax.max(),3))+' p.u')
print('Min voltage '+str(round(Vmin.max(),3))+' p.u')

pickle_out = open("Outputs/ResultsEVHP.pickle","wb")
pickle.dump(Alls, pickle_out)



plt.plot(PVtot.index,-PVtot, label="PV")
plt.plot(EVtot.index,EVtot, label="EV")
plt.plot(HPtot.index,HPtot, label="HP")
plt.plot(SMtot.index,SMtot, label="SM")
plt.plot(Loadsum.index,Loadsum, label="Net Demand")
plt.legend()

plt.figure(2)
plt.subplot(211)
plt.plot(Vmax.index,Vmax, label="Vmax")
plt.plot(Vmin.index,Vmin, label="Vmin")
plt.legend()
plt.subplot(212)
plt.plot(Cmax.index,Cmax, label="C / Crated Max")
plt.legend()