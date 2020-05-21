# -*- coding: utf-8 -*-
"""
Created on Fri Aug  2 11:54:13 2019

@author: qsb15202
"""
######## Importing the OpenDSS Engine  #########
import opendssdirect as dss
import numpy as np
import pandas as pd
import pickle
from opendssdirect.utils import run_command
pd.options.mode.chained_assignment = None

### Set up DSS Commands ####

DSSCircuit = dss.Circuit
DSSLoads= dss.Loads;
DSSBus = dss.Bus
DSSLines = dss.Lines
DSSGens= dss.Generators
DSSTransformers= dss.Transformers

dss.Basic.ClearAll()
dss.Basic.Start(0)
Network_Path='Test_Network/Network1/'

####----- For each Load a generator is created to allow PV to be added
def create_gens(Network_Path):
    LoadsIn = pd.read_csv(str(Network_Path)+"Loads.txt",delimiter=' ', names=['New','Load','Phases','Bus1','kV','kW','PF','Daily'] )
    GensIn = pd.read_csv(str(Network_Path)+"Generators.txt",delimiter=' ',index_col=False,names=['New','Generator','Bus1','kV','kW','PF'])
    
    GensIn['Generator'][0]='Generator.GEN'+str(LoadsIn['Load'][0][9:])
    GensIn['Bus1'][0]=LoadsIn['Bus1'][0]
    for i in LoadsIn.index[1:]:
        print(i)
        GensIn = GensIn.append(GensIn.iloc[i-1],ignore_index=True)
        GensIn['Generator'][i]='Generator.GEN'+str(LoadsIn['Load'][i][9:])
        GensIn['Bus1'][i]=LoadsIn['Bus1'][i]

    GensIn.to_csv(str(Network_Path)+"Generators.txt", sep=" ", index=False, header=False) 


####### Compile the OpenDSS file using the Master.txt directory#########
def runDSS(Network_Path,demand,pv,demand_delta,pv_delta,PFControl):
    Voltages={}
    Currents={}
    Powers={}
    Rates={}
    
    run_command('Redirect ./'+str(Network_Path)+'Master.dss')
       ################### Calculating Load for each Demand ############################
    iLoad = DSSLoads.First()
    while iLoad>0:
        DSSLoads.kW(demand[iLoad-1]+demand_delta[iLoad-1])
        iLoad = DSSLoads.Next()
    
    ################### Calculating Gen for each Demand ############################
    iGen = DSSGens.First()
    while iGen>0:
        DSSGens.kW(pv[iGen-1]+pv_delta[iGen-1])
        if PFControl==1:
            DSSGens.kW((pv[iGen-1]+pv_delta[iGen-1])*0.95)
            DSSGens.PF(-0.95)
        DSSGens.Vmaxpu(1.2)
        DSSGens.Vminpu(0.8)
        DSSGens.Phases(1)
        iGen = DSSGens.Next()
    
    ######### Solve the Circuit ############
    dss.Solution.SolveSnap()
    dss.Monitors.SampleAll()
    
    ############-----Export Results-------------------------#################
    
    ########## Export Voltages ###########
    bvs = list(DSSCircuit.AllBusMagPu())
    Voltages=bvs[0::3],bvs[1::3],bvs[2::3]  
    VoltArray=np.zeros((len(Voltages[0]),3))
    for i in range(0,3):
        VoltArray[:,i]=np.array(Voltages[i], dtype=float)
        
    ########## Export Current and Power ###########
    i_Line = DSSLines.First()
    while i_Line > 0:
        curs =list(dss.CktElement.CurrentsMagAng())
        Currents[i_Line] = curs[0], curs[2], curs[4]
        
        ### Powers() is a complex power, we store the KVAr Apparent Power
        pows =list(dss.CktElement.Powers()) 
        Powers[i_Line] = np.sign(pows[0])*(pows[0]**2+pows[1]**2)**0.5, np.sign(pows[2])*(pows[2]**2+pows[3]**2)**0.5, np.sign(pows[4])*(pows[4]**2+pows[5]**2)**0.5
        
        Rates[i_Line] = dss.CktElement.NormalAmps()
        i_Line = DSSLines.Next()
    
    ########## Store as Arrays ############
    CurArray=np.array(list(Currents.values()), dtype=float)
    PowArray=np.array(list(Powers.values()), dtype=float)
    Losses=dss.Circuit.Losses()[0]/1000
    RateArray=np.array(list(Rates.values()), dtype=float)
    TranskVA=np.sign(dss.Circuit.TotalPower()[0])*(dss.Circuit.TotalPower()[0]**2+dss.Circuit.TotalPower()[1]**2)**0.5
    TransRatekVA=DSSTransformers.kVA()
    return CurArray, VoltArray, PowArray, Losses, TranskVA, RateArray, TransRatekVA

###------- Using the network outputs (voltage and current) from Opendss
###------- network summary is generated including overvoltage and current locations

def network_outputs(CurArray, RateArray, VoltArray, PowArray, TransKVA ,TransRatekVA):

    network_summary={}
    
    for i in range(1,4):
        network_summary[i]={}
        Cseries=pd.Series(CurArray[:,i-1])
        Vseries=pd.Series(VoltArray[:,i-1])
        Pseries=pd.Series(PowArray[:,i-1])
    
        Chigh_lines=list(Cseries[Cseries>RateArray].index)
        Vhigh_nodes=list(Vseries[Vseries>1.1].index)
        Vlow_nodes=list(Vseries[Vseries<0.94].index)
        
        network_summary[i]['Chigh_lines']=Chigh_lines
        network_summary[i]['C_Flow']={}
        network_summary[i]['C_Rate']={}
        
        ##-These Pinch points are network specific but can be calculated using a script
        pinchClist=[0,906,1410,1913]
        ##------- To indicate direction of power flow. When Importing supply voltage will be higher
        #---------Negative power flow represents export. 
        
        for n in range(1,5):
            network_summary[i]['C_Rate'][n]=RateArray[pinchClist[n-1]]*Vseries[1]*.426/(3**0.5)
            network_summary[i]['C_Flow'][n]=Pseries[pinchClist[n-1]]

                
        network_summary[i]['Vhigh_nodes']=Vhigh_nodes
        network_summary[i]['Vlow_nodes']=Vlow_nodes

        network_summary[i]['Chigh_vals']=list(Cseries[Cseries>RateArray])
        network_summary[i]['Vhigh_vals']=list(Vseries[Vseries>1.1])
        network_summary[i]['Vlow_vals']=list(Vseries[Vseries<0.94])
        
    network_summary['Trans_kVA']=-TransKVA
    return network_summary

#from feedbackplot import plots
#plots(Network_Path,VoltArray,CurArray,RateArray)