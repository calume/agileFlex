# -*- coding: utf-8 -*-
"""
Created on Wed March 18 13:49:06 2020

This script produces a plot of the test feeder (Feeder1 from LVNS)

From:  https://www.enwl.co.uk/zero-carbon/innovation/smaller-projects/low-carbon-networks-fund/low-voltage-network-solutions/

The feeder has 55 customers spread across the 3 phases. Flexibility is assigned as per Acorn Group.

- Affluent: are assumed to be full adopters of Low carbon technologies, all have Heat Pumps, Electric Vehicles, PV and Home Batteries.
- Comfortable: half of these are assumed to have PV and all are assumed to have solar.
- Adversity: are assumed to not have any low carbon technologies (LCTs) due high capital costs required.

@author: qsb15202
"""



import pandas as pd
import networkx as nx
from matplotlib import pyplot as plt
import pickle
import matplotlib.image as mpimg
from matplotlib.offsetbox import (TextArea, DrawingArea, OffsetImage,
                                  AnnotationBbox)
pd.options.mode.chained_assignment = None 
from tabulate import tabulate
from numpy.random import choice

Feeder='Feed1'
Coords = pd.read_csv(str(Feeder)+"/XY_Position.csv")
Lines = pd.read_csv(str(Feeder)+"/Lines.txt",delimiter=' ', names=['New','Line','Bus1','Bus2','phases','Linecode','Length','Units'] )
Lines = Lines[Lines['Line'].map(len) > 5]
Lines.reset_index(drop=True, inplace=True)
Loads = pd.read_csv(str(Feeder)+"/Loads.txt",delimiter=' ', names=['New','Load','Phases','Bus1','kV','kW','PF','Daily'] )

# The PV distribution of PV capacities has been calculated from the distribution of installed PV capacities with Feed in tariffs.

pvcaplist=[1,1.5,2,2.5,3,3.5,4]
weights=[.01,.08,.13,.15,.14,.12,.37]

LoadsByAcorn={}
LoadsByAcorn['Affluent']=list(range(1,18))
LoadsByAcorn['Comfortable']=list(range(1,18))
LoadsByAcorn['Adversity']=list(range(1,18))

for i in LoadsByAcorn['Affluent']:    
    PVcap=choice(pvcaplist, int(len(LoadsByAcorn['Affluent'])), weights)

#------------------------Define Network Agents----------------------------

Customer_Summary=pd.DataFrame(0, index=(range(0,len(Loads))), columns=['ID','Node','Agent','Acorn_Group','X','Y','Phase','Home_Battery_kW','Home_Battery_kWh','EV_Charger_Size_kW','EV_Battery_Size_kWh','PV_kW','Heat_Pump_kW','Color'])
Customer_Summary['ID']=Loads.index+1
Customer_Summary['Node']=Loads['Bus1'].str[5:-2].astype(int)
Customer_Summary['Acorn_Group'][0:18]='Adversity'
Customer_Summary['Acorn_Group'][18:30]='Comfortable'
Customer_Summary['Acorn_Group'][30:]='Affluent'
Customer_Summary['Phase']=Loads['Bus1'].str[-1]
Customer_Summary['Agent'][Customer_Summary['Acorn_Group']=='Affluent']=1
Customer_Summary['Home_Battery_kW'][Customer_Summary['Acorn_Group']=='Affluent']= 5
Customer_Summary['Home_Battery_kWh'][Customer_Summary['Acorn_Group']=='Affluent']= 13.5
Customer_Summary['EV_Charger_Size_kW'][Customer_Summary['Acorn_Group']=='Affluent']= 7.4
Customer_Summary['EV_Battery_Size_kWh'][Customer_Summary['Acorn_Group']=='Affluent']= 40
MoreComfortable=Customer_Summary['PV_kW'][Customer_Summary['Acorn_Group']=='Comfortable'].index[:int(sum(Customer_Summary['Acorn_Group']=='Comfortable')/2)]
Customer_Summary['PV_kW'][Customer_Summary['Acorn_Group']=='Affluent']= choice(pvcaplist, int(sum(Customer_Summary['Acorn_Group']=='Affluent')), weights)   # Every house has PV
Customer_Summary['PV_kW'][MoreComfortable]= choice(pvcaplist, int(sum(Customer_Summary['Acorn_Group']=='Comfortable')/2), weights)  
Customer_Summary['Heat_Pump_kW'][Customer_Summary['Acorn_Group']=='Affluent']=5
Customer_Summary['Heat_Pump_kW'][Customer_Summary['Acorn_Group']=='Comfortable']=4
     
acorns=['Affluent','Comfortable','Adversity']
colors=['green','#17becf','#FA8072']
        
for i in range(0,3):
    Customer_Summary['Color'][Customer_Summary['Acorn_Group']==acorns[i]]=colors[i]

#------------------- Plot the network with icons for each LCT type
    
def Network_plot(Coords,Lines,Loads):
    ##### Set Up NetworkX Graph from coordinates and network outputs ####
    EV_Icon = mpimg.imread('Feed1/EVIcon2.png')
    EVbox = OffsetImage(EV_Icon, zoom=0.3)
    
    HP_Icon = mpimg.imread('Feed1/HeatPump.png')
    HPbox = OffsetImage(HP_Icon, zoom=0.3)
    
    powerwall_Icon = mpimg.imread('Feed1/powerwall.png')
    powerwallbox = OffsetImage(powerwall_Icon, zoom=0.3)  
    
    PV_Icon = mpimg.imread('Feed1/PV_Icon.png')
    PVbox = OffsetImage(PV_Icon, zoom=0.3)
    
    House = mpimg.imread('Feed1/house.png')
    Housebox = OffsetImage(House, zoom=0.15)
    
    G = nx.Graph()
   
    Edge={}
    
    for index, value in Lines['Bus1'].items():
       Edge[index] = int(Lines['Bus1'][index][5:]),int(Lines['Bus2'][index][5:])
   
    pos={}
    for index, value in Coords['Node'].items():
       pos[index] = float(Coords['X'][index]),int(Coords['Y'][index])
   
    pos = dict((Coords['Node'][key], value) for (key, value) in pos.items())
   
    G.add_nodes_from(Coords['Node'])
    G.add_edges_from(Edge.values())
   
    ##### Plot Currents for each Phase ####
    fig, ax = plt.subplots()
    nx.draw(G, pos, with_labels=False, width=1, node_size=2)
    for i in Loads.index:
        Customer_Summary['X'][i]=Coords['X'][Coords['Node']==int(Loads['Bus1'][i][5:-2])].astype(float)
        Customer_Summary['Y'][i]=Coords['Y'][Coords['Node']==int(Loads['Bus1'][i][5:-2])].astype(float)
        plt.annotate(i+1, (Customer_Summary['X'][i]-1, Customer_Summary['Y'][i]+3),fontsize=12,color=Customer_Summary['Color'][i],weight="bold")
        if Customer_Summary['PV_kW'][i]>0:
            ab = AnnotationBbox(PVbox, [Customer_Summary['X'][i], Customer_Summary['Y'][i]],frameon=False, pad=0)
            ax.add_artist(ab)
        if Customer_Summary['EV_Charger_Size_kW'][i]>0:
            ab = AnnotationBbox(EVbox, [Customer_Summary['X'][i], Customer_Summary['Y'][i]-3],frameon=False, pad=0)
            ax.add_artist(ab)
        if Customer_Summary['Acorn_Group'][i]=='Adversity':
            ab = AnnotationBbox(Housebox, [Customer_Summary['X'][i], Customer_Summary['Y'][i]],frameon=False, pad=0)
            ax.add_artist(ab)
        if Customer_Summary['Acorn_Group'][i]=='Comfortable' and Customer_Summary['PV_kW'][i]==0:
            ab = AnnotationBbox(Housebox, [Customer_Summary['X'][i], Customer_Summary['Y'][i]],frameon=False, pad=0)
            ax.add_artist(ab)
        if Customer_Summary['Home_Battery_kW'][i]>0:
            ab = AnnotationBbox(powerwallbox, [Customer_Summary['X'][i]+2, Customer_Summary['Y'][i]],frameon=False, pad=0)
            ax.add_artist(ab)
        if Customer_Summary['Heat_Pump_kW'][i]>0:
            ab = AnnotationBbox(HPbox, [Customer_Summary['X'][i]-3, Customer_Summary['Y'][i]-1],frameon=False, pad=0)
            ax.add_artist(ab)
        offset=[0,6,12,18,24]
    plt.annotate('Acorn Group', (480,40),fontsize=10,color="black",weight="bold")
    for i in range(0,3):
        plt.annotate(acorns[i], (480,35-offset[i]),fontsize=9,color=colors[i],weight="bold")
        
    boxes=[PVbox,EVbox,powerwallbox,HPbox,Housebox]
    intros=['PV Owner','EV Owner','Home Battery Owner','Heat Pump Owner','Non-Agent']
    plt.annotate('Legend', (449,160),fontsize=10,color="black",weight="bold")
    for i in range(0,5):
        plt.annotate(intros[i], (454, 154-offset[i]),fontsize=9,color='black')
        ab = AnnotationBbox(boxes[i], [450, (155-offset[i])],frameon=False, pad=0)
        ax.add_artist(ab)
    plt.show()
    plt.tight_layout()

Network_plot(Coords,Lines,Loads)
Customer_Summary.style.hide_index()
print(tabulate(Customer_Summary.drop(columns='Color'), tablefmt="pipe", headers="keys", showindex=False))