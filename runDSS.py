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

#demand=[1.936    , 4.292    , 4.684    , 4.556    , 2.052    , 2.962    ,
#       2.234    , 4.38     , 4.342    , 2.246    , 1.822    , 3.51     ,
#       3.83     , 2.176    , 1.758    , 2.974    , 2.424    , 2.212    ,
#       2.966    , 3.192    , 4.514    , 2.802    , 3.506    , 0.384    ,
#       3.03     , 2.464    , 0.       , 6.8980002, 1.486    , 0.       ,
#       4.448    , 2.086    , 3.06     , 2.74     , 3.086    , 2.134    ,
#       0.512    , 4.66     , 1.964    , 2.044    , 1.258    , 3.314    ,
#       0.918    , 3.266    , 2.744    , 1.116    , 3.63     , 2.772    ,
#       3.172    , 3.814    , 2.046    , 4.788    , 0.168    , 4.424    ,
#       2.074    , 1.492    , 1.462    , 0.       , 2.212    , 3.12     ,
#       2.744    , 0.164    , 0.706    , 2.336    , 0.938    , 1.646    ,
#       2.032    , 1.396    , 2.86     , 3.212    , 2.148    , 1.286    ,
#       1.61     , 3.614    , 0.       , 3.752    , 2.86     , 2.174    ,
#       2.436    , 0.492    , 3.654    , 2.362    , 3.484    , 1.896    ,
#       0.826    , 3.616    , 2.518    , 2.14     , 2.786    , 0.362    ,
#       1.75     , 2.91     , 0.       , 2.306    , 3.1      , 0.15     ,
#       1.08     , 2.362    , 1.186    , 3.128    , 3.618    , 0.056    ,
#       1.944    , 3.768    , 3.546    , 2.49     , 2.45     , 2.328    ,
#       5.068    , 2.638    , 2.604    , 2.566    , 1.65     , 1.674    ,
#       2.322    , 1.39     , 1.552    , 0.214    , 0.768    , 0.85     ,
#       5.5780002, 3.264    , 3.27     , 1.744    , 1.294    , 5.558    ,
#       1.824    , 0.746    , 1.956    , 2.214    , 0.958    , 1.62     ,
#       0.038    , 0.152    , 0.774    , 0.568    , 0.6      , 0.554    ,
#       0.244    , 0.228    , 0.364    , 1.88     , 0.774    , 0.204    ,
#       0.4      , 0.228    , 1.698    , 0.13     , 0.774    , 0.27     ,
#       0.334    , 0.532    , 0.994    , 0.346    , 0.6      , 0.502    ,
#       0.152    , 0.49     , 0.19     , 1.88     , 0.228    , 0.438    ,
#       0.082    , 0.446    , 0.376    , 0.568    , 0.152    , 0.32     ,
#       0.346    , 1.494    , 0.45     , 0.236    , 0.376    , 0.228    ,
#       0.446    , 0.446    , 0.346    , 0.19     , 0.27     , 0.436    ,
#       1.698    , 1.698    , 0.45     , 0.898    , 0.6      , 0.618    ,
#       0.57     , 0.57     , 1.03     , 0.774    , 0.502    , 0.32     ,
#       1.698    , 1.88     , 0.27     , 0.376    , 0.36     , 0.346    ,
#       0.994    , 0.13     ]


####### Compile the OpenDSS file using the Master.txt directory#########
def runDSS(Network_Path,demand,pv,demand_delta,pv_delta):
    Voltages={}
    Currents={}
    Rates={}
    
    run_command('Redirect ./'+str(Network_Path)+'Master.dss')
       ################### Calculating Load for each Demand ############################
    iLoad = DSSLoads.First()
    while iLoad>0:
        DSSLoads.kW(demand[iLoad-1]-demand_delta[iLoad-1])
        iLoad = DSSLoads.Next()
    
    ################### Calculating Gen for each Demand ############################
    iGen = DSSGens.First()
    while iGen>0:
        DSSGens.kW(pv[iGen-1]-pv_delta[iGen-1])
        DSSGens.Vmaxpu(1.2)
        DSSGens.Vminpu(0.8)
        DSSGens.Phases(1)
        iGen = DSSGens.Next()
    
    ######### Solve the Circuit ############
    dss.Solution.SolveSnap()
    dss.Monitors.SampleAll()
    
    ############-----Export Results-------------------------#################
    
    ####### Export Transformer kVA #########
    dss.Text.Command("export mon TransPQ")
    Trans_kVA=pd.read_csv('LVTest_Mon_transpq.csv',usecols=[2,3,4])
    Trans_kVA.columns=['S1','S2','S3']
    
    ########## Export Voltages ###########
    bvs = list(DSSCircuit.AllBusMagPu())
    Voltages=bvs[0::3],bvs[1::3],bvs[2::3]  
    VoltArray=np.zeros((len(Voltages[0]),3))
    for i in range(0,3):
        VoltArray[:,i]=np.array(Voltages[i], dtype=float)
        
    ########## Export Current ###########
    i_Line = DSSLines.First()
    while i_Line > 0:
        curs =list(dss.CktElement.CurrentsMagAng())
        Currents[i_Line] = curs[0], curs[2], curs[4]
        Rates[i_Line] = dss.CktElement.NormalAmps()
        i_Line = DSSLines.Next()
    
    ########## Store as Arrays ############
    CurArray=np.array(list(Currents.values()), dtype=float)
    Losses=dss.Circuit.Losses()[0]/1000
    RateArray=np.array(list(Rates.values()), dtype=float)
    TransKVA_sum=sum(Trans_kVA.values[0])
    TransRatekVA=DSSTransformers.kVA()
    return CurArray, VoltArray, Losses, TransKVA_sum, RateArray, TransRatekVA

###------- Using the network outputs (voltage and current) from Opendss
###------- network summary is generated including overvoltage and current locations

def network_visualise(CurArray, RateArray, VoltArray,TransKVA_sum ,TransRatekVA):

    network_summary={}
    
    for i in range(1,4):
        network_summary[i]={}
        Cseries=pd.Series(CurArray[:,i-1]-RateArray)
        Vseries=pd.Series(VoltArray[:,i-1])
    
        Chigh_lines=list(Cseries[Cseries>0].index)
        Vhigh_nodes=list(Vseries[Vseries>1.1].index)
        Vlow_nodes=list(Vseries[Vseries<0.94].index)
        
        network_summary[i]['Chigh_lines']=Chigh_lines
        network_summary[i]['Chdrm']={}
        network_summary[i]['Chdrm'][1]=-Cseries[0]*Vseries[1]*.426/(3**0.5)
        network_summary[i]['Chdrm'][2]=-Cseries[906]*Vseries[1]*.426/(3**0.5)
        network_summary[i]['Chdrm'][3]=-Cseries[1410]*Vseries[1]*.426/(3**0.5)
        network_summary[i]['Chdrm'][4]=-Cseries[1913]*Vseries[1]*.426/(3**0.5)
        
        network_summary[i]['Vhigh_nodes']=Vhigh_nodes
        network_summary[i]['Vlow_nodes']=Vlow_nodes

#        network_summary[i]['Vhdrm']={}
#        
#        network_summary[i]['Vhdrm'][1]=(Vseries[1]-0.94)*.426/(3**0.5)*CurArray[0,i]
#        network_summary[i]['Vhdrm'][2]=(Vseries[907]-0.94)*.426/(3**0.5)*CurArray[906,i]
#        network_summary[i]['Vhdrm'][3]=(Vseries[1411]-0.94)*.426/(3**0.5)*CurArray[1410,i]
#        network_summary[i]['Vhdrm'][4]=(Vseries[1914]-0.94)*.426/(3**0.5)*CurArray[1913,i]

        network_summary[i]['Chigh_vals']=list(Cseries[Cseries>0])
        network_summary[i]['Vhigh_vals']=list(Vseries[Vseries>1.1])
        network_summary[i]['Vlow_vals']=list(Vseries[Vseries<0.94])

    network_summary['Trans_kVA_Headroom']=TransRatekVA-TransKVA_sum
    return network_summary

#from feedbackplot import plots
#plots(Network_Path,VoltArray,CurArray,RateArray)