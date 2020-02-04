# -*- coding: utf-8 -*-
"""
Created on Fri Aug  2 11:54:13 2019

@author: qsb15202
"""
######## Importing the OpenDSS Engine  #########
import opendssdirect as dss
import numpy as np
import pandas as pd
from opendssdirect.utils import run_command
pd.options.mode.chained_assignment = None

### Set up DSS Commands ####

DSSCircuit = dss.Circuit
DSSLoads= dss.Loads;
DSSBus = dss.Bus
DSSLines = dss.Lines
DSSGens= dss.Generators

####### Create a generator for each load #########

LoadsIn = pd.read_csv("Loads.txt",delimiter=' ', names=['New','Load','Phases','Bus1','kV','kW','PF','Daily'] )
GensIn = pd.read_csv("Generators.txt",delimiter=' ', names=['New','Generator','Bus1','kV','kW','PF'])

#GensIn['Generator'][0]='Generator.GEN'+str(LoadsIn['Load'][0][9:])
#GensIn['Bus1'][0]=LoadsIn['Bus1'][0]
#for i in LoadsIn.index[1:]:
#    print(i)
#    GensIn = GensIn.append(GensIn.iloc[i-1],ignore_index=True)
#    GensIn['Generator'][i]='Generator.GEN'+str(LoadsIn['Load'][i][9:])
#    GensIn['Bus1'][i]=LoadsIn['Bus1'][i]
#
#GensIn.to_csv("Generators.txt", sep=" ", index=False, header=False) 

#dss.Basic.ClearAll()
#dss.Basic.Start(0)
#P= np.array([11.50034239,  2.47454889,  0.61089075,  4.40891062,  9.42233832,
#        4.36033616,  1.25117596,  1.66008232,  1.86465633,  2.69840792,
#        0.86844222,  4.56870632, 12.15824116,  4.91312382,  6.61092013,
#        1.73990761,  2.61695063,  2.04417424,  0.75918933,  2.69252254,
#        2.03992466,  1.66443946,  6.6702814 ,  0.7590303 , 10.23056161,
#        4.02688667,  5.66458177,  4.80274726,  0.46542819,  8.86541455,
#        0.35190725])
#u=0*P
#P=P*0+5
#
#Gen=P
#Gen=Gen*0+10
####### Compile the OpenDSS file using the Master.txt directory#########
def runDSS(P,Gen,u):
    Voltages={}
    Currents={}
    Rates={}
    Locations={}
    #index=('Cmax','Vmax','Vmin'))
    run_command('Redirect ./Master.dss')
       ################### Calculating Load for each Demand ############################
    iLoad = DSSLoads.First()
    while iLoad>0:
        DSSLoads.kW(P[iLoad-1]-u[iLoad-1])
        iLoad = DSSLoads.Next()
    
    ################### Calculating Gen for each Demand ############################
    iGen = DSSGens.First()
    while iGen>0:
        DSSGens.kW(Gen[iGen-1])
        iGen = DSSGens.Next()
    
    ######### Solve the Circuit ############
    run_command('Solve')
      
    ########## Export Voltages ###########
    bvs = list(DSSCircuit.AllBusMagPu())
    Voltages=bvs[0::3],bvs[1::3],bvs[2::3]  
    VoltArray=np.zeros((len(Voltages[0]),3))
    for i in range(0,3):
        VoltArray[:,i]=np.array(Voltages[i], dtype=float)
        
    ########## Export Current ###########
    i_Line = DSSLines.First()
    while i_Line > 0:
        curs = list(dss.CktElement.CurrentsMagAng())
        Currents[i_Line] = curs[0], curs[2], curs[4]
        Rates[i_Line] = dss.CktElement.NormalAmps()
        i_Line = DSSLines.Next()
    #t_Line = DSSTransformers.First
    #dss.CktElement.CurrentsMagAng()
    
    CurArray=np.array(list(Currents.values()), dtype=float)
    RateArray=np.array(list(Rates.values()), dtype=float)
    
    ########## Export Loads ###########
    i_Load = DSSLoads.First()
    Loads = {}
    while i_Load>0:
        Loads[i_Load]=[DSSLoads.kW(),DSSLoads.kvar(),DSSLoads.PF()]
        i_Load = DSSLoads.Next()
    Loadarray=np.array(list(Loads.values()), dtype=float)
    #### Maximum Current ####
    
    CurMax = np.zeros((1,3))
    Locations['Cmax']={}
    for i in range(0,3):
        CurMax[:,i]=(CurArray[:,i]-RateArray).max()
        C=pd.Series(CurArray[:,i]-RateArray)
        C=list(C[C>0.5].index)
        Locations['Cmax'][i]=C
    #### Maximum Voltage ####
    Vmax = np.zeros((1,3))
    Locations['Vmax']={}
    for i in range(0,3):
        Vmax[:,i]=VoltArray[:,i].max()
        Vmx=pd.Series(VoltArray[:,i])
        Vmx=list(Vmx[Vmx>1.1].index)
        Locations['Vmax'][i]=Vmx
    #### Minimum Voltage ####
    Vmin = np.zeros((1,3))
    Locations['Vmin']={}
    for i in range(0,3):
        Vmin[:,i]=VoltArray[:,i].min()
        Vmn=pd.Series(VoltArray[:,i])
        Vmn=list(Vmn[Vmn<0.94].index)
        Locations['Vmin'][i]=Vmn
    ################### Display Gen ############################

    iGen = DSSGens.First()
    while iGen>0:
        iGen = DSSGens.Next()
    return Loadarray, CurArray, VoltArray, RateArray, CurMax, Vmax, Vmin, Locations
    

