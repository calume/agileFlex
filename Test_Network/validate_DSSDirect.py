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
import networkx as nx
from matplotlib import pyplot as plt

#def run_pf():
#dirs=["network_1/","network_5/","network_10/","network_17/","network_18"]
dirs=["condensed/network_1/","condensed/network_5/","condensed/network_10/","condensed/network_17/","condensed/network_18/"]

#dirs=["condensed/network_18/"]

for i in dirs:
    print(i)
    start = timeit.default_timer()
    
    dss.Basic.ClearAll()
    dss.Basic.Start(0)
    #### Import the Lines ###
    
    
    
    #
    #Lines = pd.read_csv(dirs+"Lines.txt",delimiter=' ', names=['New','Line','Bus1','Bus2','phases','Linecode','Length','Units'] )
    #LoadsIn = pd.read_csv(dirs+"Loads.txt",delimiter=' ', names=['New','Load','Phases','Bus1','kV','kW','PF','Daily'] )
    
    ####### Compile the OpenDSS file using the Master.txt directory#########
    
    ##run_command('Redirect ./'+i+'masterNetwork'+i[18:-1]+'_pruned.dss')
    run_command('Redirect ./'+i+'Master.dss')
    #
    ### Set up DSS Commands ####
    
    DSSCircuit = dss.Circuit
    DSSLoads= dss.Loads
    DSSBus = dss.Bus
    DSSLines = dss.Lines
    DSSGens = dss.Generators
    
    ################### Calculating Load for each Demand ############################
    iLoad = DSSLoads.First()
    while iLoad>0:
        DSSLoads.kW(2)
        DSSLoads.Vmaxpu(50)
        DSSLoads.Vminpu(0.02)    
        iLoad = DSSLoads.Next()

#    iGen = DSSGens.First()
#    while iGen > 0:
#        DSSGens.kV(0.23)
#        DSSGens.kW(1)
#        DSSGens.PF(1)
#        DSSGens.Vmaxpu(50)
#        DSSGens.Vminpu(0.02)
#        DSSGens.Phases(1)
#        DSSGens.Model(1)
#        iGen = DSSGens.Next()
    
        
    ######### Solve the Circuit ############
    #dss.Solution.SolveSnap()
    run_command('Solve')
    
    ########## Export Voltages ###########
    bnames = list(DSSCircuit.AllBusNames())
    bvs = list(DSSCircuit.AllBusMagPu())
    
    Voltages = pd.DataFrame(index=range(0,len(bnames)),columns=['Name','VA','VB','VC'])
    Voltages['Name']=bnames
    
    Voltages['VA'] = bvs[0::3]
    Voltages['VB'] = bvs[1::3]
    Voltages['VC'] = bvs[2::3]
    
    ########## Export Current and Power ###########
    
    Currents = pd.DataFrame(index=range(1,len(DSSLines.AllNames())+1),columns=['Name','IA(Amps)','IB(Amps)','IC(Amps)','Rating(Amps)'])
    Powers = pd.DataFrame(index=range(1,len(DSSLines.AllNames())+1),columns=['Name','PT(kW)','QT(kVAr)','PA(kW)','QA(kVAr)','PB(kW)','QB(kVAr)','PC(kW)','QC(kVAr)'])
    
    i_Line = DSSLines.First()
    while i_Line > 0:    
        curs = list(dss.CktElement.CurrentsMagAng())
        pows = list(dss.CktElement.Powers())
        Currents['Name'][i_Line] = dss.CktElement.Name()
        Currents['Rating(Amps)'][i_Line] = dss.CktElement.NormalAmps()
        Currents['IA(Amps)'][i_Line]=curs[0]
        Currents['IB(Amps)'][i_Line]=curs[2]
        Currents['IC(Amps)'][i_Line]=curs[4]
        Powers['Name'][i_Line]=dss.CktElement.Name()
        Powers['PA(kW)'][i_Line]=round(pows[0],3)
        Powers['QA(kVAr)'][i_Line]=round(pows[1],3)
        Powers['PB(kW)'][i_Line]=round(pows[2],3)
        Powers['QB(kVAr)'][i_Line]=round(pows[3],3)
        Powers['PC(kW)'][i_Line]=round(pows[4],3)
        Powers['QC(kVAr)'][i_Line]=round(pows[5],3)
        Powers['PT(kW)'][i_Line]=round((pows[0]+pows[2]+pows[4]),3)
        Powers['QT(kVAr)'][i_Line]=round((pows[1]+pows[3]+pows[5]),3)
        i_Line = DSSLines.Next()
        
    lnames = list(DSSLoads.AllNames())
    Loads= pd.DataFrame(index=range(1,len(lnames)+1),columns=['Name','Bus','kW','kVAr','PF'])
    i_Load = DSSLoads.First()
    Loads['Name']=lnames
    
    while i_Load>0:
        Loads['kW'][i_Load]= DSSLoads.kW()
        Loads['kVAr'][i_Load]= DSSLoads.kvar()
        Loads['PF'][i_Load]= DSSLoads.PF()
        i_Load = DSSLoads.Next()
       
    stop = timeit.default_timer()
    
    print('Time: ', stop - start)
    
    
    Currents.to_csv(i+'DSSDirect_Currents_con.csv')
    Voltages.to_csv(i+'DSSDirect_Voltages_con.csv')


# #def error_and_plot():
dirs=["network_1/","network_5/","network_10/","network_17/","network_18/"]
for i in dirs:
    Voltages_con=pd.read_csv('condensed/'+i+'/DSSDirect_Voltages_con.csv')
    Voltages=pd.read_csv(i+'DSSDirect_Voltages.csv')
    Voltages_combined=Voltages_con.merge(Voltages, left_on='Name', right_on='Name')
    
    
    # plt.figure(i)
    # plt.scatter(Voltages_combined['Name'],Voltages_combined['VA_x'], color='orange', s=2, label='Condensed')
    # plt.scatter(Voltages_combined['Name'],Voltages_combined['VA_y'], color='blue', s=0.2, label='Original')
    # ticks=np.arange(0,len(Voltages_combined['Name']),step=100)
    # plt.xticks(ticks,Voltages_combined['Name'][ticks])
    # plt.legend()
    
    ErrorA=((Voltages_combined['VA_x']-Voltages_combined['VA_y'])/Voltages_combined['VA_x']*100).mean()
    ErrorB=((Voltages_combined['VB_x']-Voltages_combined['VB_y'])/Voltages_combined['VB_x']*100).mean()
    ErrorC=((Voltages_combined['VC_x']-Voltages_combined['VC_y'])/Voltages_combined['VC_x']*100).mean()
    
    OverallError=(ErrorA+ErrorB+ErrorC)/3
    print(i,OverallError)