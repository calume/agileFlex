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

start = timeit.default_timer()

dirs='condensed/network_5/'
dss.Basic.ClearAll()
dss.Basic.Start(0)
#### Import the Lines ###

Lines = pd.read_csv(dirs+"Lines.txt",delimiter=' ', names=['New','Line','Bus1','Bus2','phases','Linecode','Length','Units'] )
Lines = Lines[Lines['Line'].map(len) > 5]

Lines.reset_index(drop=True, inplace=True)

LoadsIn = pd.read_csv(dirs+"Loads.txt",delimiter=' ', names=['New','Load','Phases','Bus1','kV','kW','PF','Daily'] )

####### Compile the OpenDSS file using the Master.txt directory#########

run_command('Redirect ./'+dirs+'Master.dss')
#
### Set up DSS Commands ####

DSSCircuit = dss.Circuit
DSSLoads= dss.Loads;
DSSBus = dss.Bus
DSSLines = dss.Lines

################### Calculating Load for each Demand ############################
iLoad = DSSLoads.First()
while iLoad>0:
    DSSLoads.kW(2)
    DSSLoads.Vmaxpu(50)
    DSSLoads.Vminpu(0.02) 
    iLoad = DSSLoads.Next()
    
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

Currents = pd.DataFrame(index=range(1,len(Lines)+1),columns=['Name','IA(Amps)','IB(Amps)','IC(Amps)','Rating(Amps)'])
Powers = pd.DataFrame(index=range(1,len(Lines)+1),columns=['Name','PT(kW)','QT(kVAr)','PA(kW)','QA(kVAr)','PB(kW)','QB(kVAr)','PC(kW)','QC(kVAr)'])

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
Loads['Bus']=LoadsIn['Bus1'].str[5:]

while i_Load>0:
   Loads['kW'][i_Load]= DSSLoads.kW()
   Loads['kVAr'][i_Load]= DSSLoads.kvar()
   Loads['PF'][i_Load]= DSSLoads.PF()
   i_Load = DSSLoads.Next()
   
stop = timeit.default_timer()

print('Time: ', stop - start)

##### Set Up NetworkX Graph from coordinates and network outputs ####

G = nx.Graph()

Coords = pd.read_csv(dirs+"XY_Position.csv")
Coords['load']=0

Edge={}

for index, value in Lines['Bus1'].items():
    Edge[index] = int(Lines['Bus1'][index][5:]),int(Lines['Bus2'][index][5:])

pos={}
for index, value in Coords['Node'].items():
    pos[index] = float(Coords['X'][index]),int(Coords['Y'][index])

pos = dict((Coords['Node'][key], value) for (key, value) in pos.items())

G.add_nodes_from(Coords['Node'])
G.add_edges_from(Edge.values())

cmap = plt.cm.YlOrRd
edge_cmap = plt.cm.cool
currentsA = Currents['IA(Amps)'].tolist()
currentsB = Currents['IB(Amps)'].tolist()
currentsC = Currents['IC(Amps)'].tolist()

VoltsA = Voltages['VA'].tolist()
VoltsB = Voltages['VB'].tolist()
VoltsC = Voltages['VC'].tolist()

##### Plot Currents for each Phase ####

plt.figure(1)
plt.subplot(311)
plt.title('Current - Phase A (A)')
nx.draw(G, pos, edge_color=currentsA,with_labels=False, width=2, node_size=7, font_weight='bold', edge_cmap=edge_cmap)
sm = plt.cm.ScalarMappable(cmap=edge_cmap, norm=plt.Normalize(vmin=min(currentsA),vmax=max(currentsA)))
sm._A = []
plt.colorbar(sm,ticks=[min(currentsA),(max(currentsA)+min(currentsA))/2, max(currentsA)])
plt.show()

plt.subplot(312)
plt.title('Current - Phase B (A)')
nx.draw(G, pos, edge_color=currentsB,with_labels=False, width=2, node_size=7, font_weight='bold', edge_cmap=edge_cmap)
sm = plt.cm.ScalarMappable(cmap=edge_cmap, norm=plt.Normalize(vmin=min(currentsB),vmax=max(currentsB)))
sm._A = []
plt.colorbar(sm,ticks=[min(currentsB),(max(currentsB)+min(currentsB))/2, max(currentsB)])
plt.show()

plt.subplot(313)
plt.title('Current - Phase C (A)')
nx.draw(G, pos, edge_color=currentsC,with_labels=False, width=2, node_size=7, font_weight='bold', edge_cmap=edge_cmap)
sm = plt.cm.ScalarMappable(cmap=edge_cmap, norm=plt.Normalize(vmin=min(currentsC),vmax=max(currentsC)))
sm._A = []
plt.colorbar(sm,ticks=[min(currentsC),(max(currentsC)+min(currentsC))/2, max(currentsC)])
plt.show()

############ Plot Voltages for each Phase ############
plt.figure(2)
plt.subplot(311)
plt.title('Voltages - Phase A (A)')
nx.draw(G, pos, node_color=VoltsA,with_labels=False, width=1, node_size=7, font_weight='bold', cmap=cmap)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=min(VoltsA),vmax=max(VoltsA)))
sm._A = []
plt.colorbar(sm,ticks=[min(VoltsA),(max(VoltsA)+min(VoltsA))/2, max(VoltsA)])
plt.show()

plt.subplot(312)
plt.title('Voltages - Phase B (A)')
nx.draw(G, pos, node_color=VoltsB,with_labels=False, width=1, node_size=7, font_weight='bold', cmap=cmap)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=min(VoltsB),vmax=max(VoltsB)))
sm._A = []
plt.colorbar(sm,ticks=[min(VoltsB),(max(VoltsB)+min(VoltsB))/2, max(VoltsB)])
plt.show()

plt.subplot(313)
plt.title('Voltages - Phase C (A)')
ab= nx.draw(G, pos, node_color=VoltsC,with_labels=False, width=1, node_size=7, font_weight='bold', cmap=cmap)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=min(VoltsC),vmax=max(VoltsC)))
sm._A = []
plt.colorbar(sm,ticks=[min(VoltsC),(max(VoltsC)+min(VoltsC))/2, max(VoltsC)])
plt.show()