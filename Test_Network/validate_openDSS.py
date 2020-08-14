# -*- coding: utf-8 -*-
"""
Created on Thu Aug  1 10:16:26 2019

@author: CalumEdmunds
"""


path = "C:\\Users\\CalumEdmunds\Desktop\\agileFlex\\Test_Network\\network_5"
##path= "C:\\Users\\qsb15202\\Desktop\\AGILE\\fully_observable_lv_feeder"
#
#
######## Importing the OpenDSS Engine  #########
import win32com.client
import scipy.io
import numpy as np
import pandas as pd
from random import uniform
from random import seed
import os
cwd = os.getcwd()
#path=cwd

pd.options.mode.chained_assignment = None 

dirs="network_5/"
  
dssObj = win32com.client.Dispatch("OpenDSSEngine.DSS")
dssText = dssObj.Text

LoadsIn = pd.read_csv(dirs+"Loads.txt",delimiter=' ', names=['New','Load','Phases','Bus1','kV','kW','PF','Daily'] )

Lines = pd.read_csv(dirs+'Lines.txt',delimiter=' ', names=['New','Line','Bus1','Bus2','phases','Linecode','Length','Units'] )

####### Compile the OpenDSS file using the Master.txt directory#########
#dssObj.ClearAll
dssText.Command="ClearAll"
dssText.Command="Compile "+str(path)+"\\Master.dss"

########## Set DSS Commands ############

DSSCircuit = dssObj.ActiveCircuit
DSSLoads=DSSCircuit.Loads
DSSLines = DSSCircuit.Lines
DSSGens=DSSCircuit.Generators


################## Calculating Load for each Demand ############################
iLoad = DSSLoads.First
i=0
while iLoad>0:
    DSSLoads.kW = 2
    #DSSLoads.kvar = 5
    iLoad = DSSLoads.Next
    i = i+1
    
iGen = DSSGens.First
while iGen > 0:
    DSSGens.kV = 0.23
    DSSGens.kW = 1
    DSSGens.PF=1
    DSSGens.Vmaxpu=50
    DSSGens.Vminpu=0.02
    DSSGens.Phases=1
    DSSGens.Model=3
    iGen = DSSGens.Next

#DSSCtrlQueue=DSSCircuit.CtrlQueue
dssObj.Start(0)
dssText.Command="solve mode=snapshot"
DSSCircuit.Solution.Solve

Currents = pd.DataFrame(index=range(0,len(Lines)),columns=['Name','IA(Amps)','IB(Amps)','IC(Amps)','Rating(Amps)'])
Powers = pd.DataFrame(index=range(0,len(Lines)),columns=['Name','PT(kW)','QT(kVAr)','PA(kW)','QA(kVAr)','PB(kW)','QB(kVAr)','PC(kW)','QC(kVAr)'])

########## Export Voltages ###########
bnames = list(DSSCircuit.AllBusNames)
bvs = list(DSSCircuit.AllBusVmagPu)

Voltages = pd.DataFrame(index=range(0,len(bnames)),columns=['Name','VA','VB','VC'])
Voltages['Name']=bnames

Voltages['VA'] = bvs[0::3]
Voltages['VB'] = bvs[1::3]
Voltages['VC'] = bvs[2::3]

i_Line = DSSLines.First
while i_Line > 0:
#while i < len(Lines['Line']):    
    #DSSCircuit.SetActiveElement(Lines['Line'][i])
    curs = list(DSSCircuit.ActiveCktElement.CurrentsMagAng)
    pows = list(DSSCircuit.ActiveCktElement.Powers)
    Currents['Name'][i_Line] = DSSCircuit.ActiveCktElement.Name
    Currents['Rating(Amps)'][i_Line] = DSSCircuit.ActiveCktElement.NormalAmps
    Currents['IA(Amps)'][i_Line]=curs[0]
    Currents['IB(Amps)'][i_Line]=curs[2]
    Currents['IC(Amps)'][i_Line]=curs[4]
    Powers['Name'][i_Line]=DSSCircuit.ActiveCktElement.Name
    Powers['PA(kW)'][i_Line]=round(pows[0],3)
    Powers['QA(kVAr)'][i_Line]=round(pows[1],3)
    Powers['PB(kW)'][i_Line]=round(pows[2],3)
    Powers['QB(kVAr)'][i_Line]=round(pows[3],3)
    Powers['PC(kW)'][i_Line]=round(pows[4],3)
    Powers['QC(kVAr)'][i_Line]=round(pows[5],3)
    Powers['PT(kW)'][i_Line]=round((pows[0]+pows[2]+pows[4]),3)
    Powers['QT(kVAr)'][i_Line]=round((pows[1]+pows[3]+pows[5]),3)
    i_Line = DSSLines.Next
    
lnames = list(DSSLoads.AllNames)
Loads= pd.DataFrame(index=range(0,len(lnames)), columns=['Name','Bus','kW','kVAr','PF'])
i_Load = DSSLoads.First
Loads['Name']=lnames
Loads['Bus']=LoadsIn['Bus1'].str[5:]
i=0
while i_Load>0:
    Loads['kW'][i]= DSSLoads.kW
    Loads['kVAr'][i]= DSSLoads.kvar
    Loads['PF'][i]= DSSLoads.PF
    i_Load = DSSLoads.Next 
    i = i+1

Currents.to_csv('OpenDSS_Currents.csv')
Voltages.to_csv('OpenDSS_Voltages.csv')