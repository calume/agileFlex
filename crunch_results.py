# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 16:39:22 2019

@author: qsb15202
"""
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
import seaborn as sns
import collections
import networkx as nx

#------------ Network Pinch Point Summary Analysis and Visualisation---------##

#### This script takes network current and voltage data, and presents
#### which lines are overloaded for what percentage of the time by half hour

def counts(network_summary,Coords):
    Chigh_allPeriods,  Vhigh_allPeriods, Vlow_allPeriods={}, {}, {}
    Chigh_count, Vhigh_count, Vlow_count = {},{},{}
    VHpinch={}
    for p in range(1,4):
        VHpinch[p]={}
        Chigh_count[p], Vhigh_count[p], Vlow_count[p] = [],[],[]
        Chigh_allPeriods[p], Vhigh_allPeriods[p],  Vlow_allPeriods[p]= [],[],[]
        for i in network_summary:
            VHpinch[p][i]={}
            if len(network_summary[i][p]['Chigh_lines']) >0:
                for item in network_summary[i][p]['Chigh_lines']:
                    Chigh_allPeriods[p].append(item)
                Chigh_count[p]=collections.Counter(Chigh_allPeriods[p])
                
            if len(network_summary[i][p]['Vhigh_nodes']) >0:
                for item in network_summary[i][p]['Vhigh_nodes']:
                    Vhigh_allPeriods[p].append(item)
                Vhigh_count[p]=collections.Counter(Vhigh_allPeriods[p])

                for f in range(1,5):
                    AllCounts=pd.DataFrame()
                    AllCounts['node']=Coords['Node'][network_summary[i][p]['Vhigh_nodes']]
                    AllCounts['voltage']=network_summary[i][p]['Vhigh_vals']
                    AllCounts=AllCounts[AllCounts['node'].astype(str).str[0]==str(f)]
                    if len(AllCounts) >0:
                        VHpinch[p][i][f]=AllCounts['node'][AllCounts['node']==AllCounts['node'].max()].index[0]
                    
            if len(network_summary[i][p]['Vlow_nodes']) >0:
                for item in network_summary[i][p]['Vlow_nodes']:
                    Vlow_allPeriods[p].append(item)
                Vlow_count[p]=collections.Counter(Vlow_allPeriods[p])

    return Chigh_count, Vhigh_count, Vlow_count, VHpinch
    
def plots(Network_Path,Chigh_count, Vhigh_count, Vlow_count):
    Coords = pd.read_csv(str(Network_Path)+'/XY_Position.csv')
    Lines = pd.read_csv(str(Network_Path)+'/Lines.txt',delimiter=' ', names=['New','Line','Bus1','Bus2','phases','Linecode','Length','Units'] )
    Lines.loc[-1]=['New','Trans','Bus1=1','Bus2=11','1','-','-','-']
    Lines.index = Lines.index + 1  # shifting index
    Lines.sort_index(inplace=True) 
    #Lines = Lines[Lines['Line'].map(len) > 5]
    #Lines.reset_index(drop=True, inplace=True)
    ##### Set Up NetworkX Graph from coordinates and network outputs ####
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
    n=1

    #--------- Add colors to nodes
    Coords['Color']='red'
    Coords['Color'][Coords['Node'].astype(str).str[0]=='2']='yellow'
    Coords['Color'][Coords['Node'].astype(str).str[0]=='3']='green'
    Coords['Color'][Coords['Node'].astype(str).str[0]=='4']='orange'
    Coords['Color'].iloc[0]='blue'
    Lines['Color']='white'   
    Lines['width']=1
    Coords['size']=1
    for p in range(1,4):
        #-------- Add colors to Current congested lines
        if len(Chigh_count[p]) >0:
            Chigh_keys = [x+1 for x in list(Chigh_count[p].keys())]
            Lines['Color'].iloc[Chigh_keys]='blue'
            Lines['width'].iloc[Chigh_keys]= list(Chigh_count[p].values())
       
        #-------- Add colors to Voltage congested lines  
        if len(Vhigh_count[p]) >0:
            Vhigh_keys = [x+1 for x in list(Vhigh_count[p].keys())]
            Coords['Color'].iloc[Vhigh_keys]='black'
            Coords['size'].iloc[Vhigh_keys]= list(Vhigh_count[p].values())
            ##### Plot Currents for each Phase ####
        plt.figure()
        #plt.figure(311+p)
        plt.title('Current + High Voltage, Phase  '+str(p))
        nx.draw(G, pos, with_labels=False, width=Lines['width']/max(Lines['width']), node_size=Coords['size']/max(Coords['size']), node_color=Coords['Color'], edge_color=Lines['Color'], font_weight='bold')
        plt.show()
        plt.tight_layout()
    n=n+1

    return Coords


def Headroom_calc(network_summary, Customer_Summary, smartmeter, heatpump, pv,demand,demand_delta,pv_delta):
    Headrm={}
    Footrm={}
    Flow={}
    Rate={}
    Headrm[0]=pd.Series(index=network_summary.keys())
    custph={}
    Customer_Summary['feeder']=Customer_Summary['Node'].astype(str).str[0]
    for p in range(1,4):
        custs=Customer_Summary[Customer_Summary['Phase'].astype(int)==(p)]
        custph[p]={}
        for f in range(1,5):
            custph[p][f]=custs[custs['feeder'].astype(int)==f]
            
    InputsbyFP={}        
    InputsbyFP['SM'] = pd.DataFrame(index=network_summary.keys(),columns=['11','12','13','14','21','22','23','24','31','32','33','34'])
    InputsbyFP['HP'] = pd.DataFrame(index=network_summary.keys(),columns=['11','12','13','14','21','22','23','24','31','32','33','34'])
    InputsbyFP['PV'] = pd.DataFrame(index=network_summary.keys(),columns=['11','12','13','14','21','22','23','24','31','32','33','34'])
    InputsbyFP['demand'] = pd.DataFrame(index=network_summary.keys(),columns=['11','12','13','14','21','22','23','24','31','32','33','34'])   
    InputsbyFP['demand_delta'] = pd.DataFrame(index=network_summary.keys(),columns=['11','12','13','14','21','22','23','24','31','32','33','34'])
    InputsbyFP['pv_delta'] = pd.DataFrame(index=network_summary.keys(),columns=['11','12','13','14','21','22','23','24','31','32','33','34'])
    
    for i in network_summary:
        Headrm[0][i]=network_summary[i]['Trans_kVA']      
        for p in range(1,4):
            for f in range(1,5):
                InputsbyFP['SM'][str(p)+str(f)][i] = np.nan_to_num(smartmeter[i])[custph[p][f].index].sum()
                InputsbyFP['HP'][str(p)+str(f)][i] = np.nan_to_num(heatpump[i])[custph[p][f].index].sum()
                InputsbyFP['PV'][str(p)+str(f)][i] = np.nan_to_num(pv[i])[custph[p][f].index].sum()
                InputsbyFP['demand'][str(p)+str(f)][i] = np.nan_to_num(demand[i])[custph[p][f].index].sum()
                InputsbyFP['demand_delta'][str(p)+str(f)][i] = np.nan_to_num(demand_delta[i])[custph[p][f].index].sum()
                InputsbyFP['pv_delta'][str(p)+str(f)][i] = np.nan_to_num(pv_delta[i])[custph[p][f].index].sum()

    for z in range(1,5):
        Headrm[z]=pd.DataFrame(index=network_summary.keys(), columns=[1,2,3])
        Footrm[z]=pd.DataFrame(index=network_summary.keys(), columns=[1,2,3])
        Flow[z]=pd.DataFrame(index=network_summary.keys(), columns=[1,2,3])
        Rate[z]=pd.DataFrame(index=network_summary.keys(), columns=[1,2,3])
        for p in range(1,4):
            for i in network_summary:
                Flow[z][p][i]=network_summary[i][p]['C_Flow'][z]
                Headrm[z][p][i]=network_summary[i][p]['C_Rate'][z]-network_summary[i][p]['C_Flow'][z]
                Footrm[z][p][i]=network_summary[i][p]['C_Rate'][z]+network_summary[i][p]['C_Flow'][z]
                Rate[z][p][i]=network_summary[i][p]['C_Rate'][z]
                if (-Rate[z][p][i]-3) <= Flow[z][p][i] <= (-Rate[z][p][i]+3) :
                    Footrm[z][p][i]=Rate[z][p][i]+Flow[z][p][i]-1.5
                if Flow[z][p][i] < (-Rate[z][p][i]-3):
                    Footrm[z][p][i]=abs(Rate[z][p][i]+Flow[z][p][i])**0.73*np.sign(Flow[z][p][i])

    return Headrm, Footrm, Flow, Rate, Customer_Summary, custph, InputsbyFP

def plot_headroom(Headrm, Footrm, Flow, Rate, labels):
    times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    plt.figure(0)
    plt.plot(
        Headrm[0].values,
        color=labels['col'],
        linewidth=1,
        linestyle=labels['style'],
        label=labels['label'],
    )
    plt.plot(np.full(48,labels['TranskVA']),color='red', linestyle="--",linewidth=0.5)
    plt.plot(np.full(48,-labels['TranskVA']),color='red', linestyle="--",linewidth=0.5)
    plt.ylabel('Headroom (kVA)')
    plt.title("Network 1 - Secondary Substation Headroom")
    plt.legend()
    plt.xlim([0, 47])
    
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.xticks(range(0, 47, 8), times)
    
    plt.figure()
    plt.title('Headroom (at head supply branch) per phase and feeder')
    
    for p in range(1,4):
        plt.subplot(310+p)
        for f in range(1,5):
            plt.plot(
                Flow[f][p].values,
                linewidth=1,
                #linestyle="--",
                label="Feeder "+str(f),
            )
            plt.plot(Rate[f][p].values,color='red', linestyle="--",linewidth=0.5)
            plt.plot(np.zeros(48),color='blue', linestyle="--",linewidth=0.5)
            plt.plot(-Rate[f][p].values,color='red', linestyle="--",linewidth=0.5)
        plt.title('Phase '+str(p))
        plt.ylabel('Headroom (kW)')
        
        plt.xlim([0, 47])
        plt.ylim([-75, 75])
        
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(range(0, 47, 8), times)  
    
    axes = plt.gca()
    arrow_properties1 = dict(
        facecolor=sns.xkcd_rgb["pale red"], width=4,
        headwidth=8
    )
    arrow_properties2 = dict(
        facecolor=sns.xkcd_rgb["denim blue"], width=4,
        headwidth=8
    )
    
    plt.annotate(
        "", xy=(1, 75),
        xytext=(1, 0),
        arrowprops=arrow_properties1,
        fontsize=10)
    
    plt.annotate(
        "", xy=(1, -75),
        xytext=(1, 0),
        arrowprops=arrow_properties2,
        fontsize=10)
    
    style1 = dict(size=8, color=sns.xkcd_rgb["pale red"], weight='bold')
    style2 = dict(size=8, color=sns.xkcd_rgb["denim blue"], weight='bold')
    
    axes.text(1.5, 60, "Import Headroom", **style1)
    axes.text(1.5, -60, "Export Footroom", **style2)
    plt.legend()
    plt.tight_layout()

def plot_flex(InputsbyFP):
    
    #------- PLot of demand and generation per feeder and phase
    times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    plt.figure()
    for p in range(1,4):
        plt.subplot(310+p)
        for f in range(1,5):
            plt.plot(
                InputsbyFP['demand_delta'][str(p)+str(f)].values+InputsbyFP['pv_delta'][str(p)+str(f)].values,
                linewidth=1,
                linestyle="--",
                label="Feeder "+str(f),
            )
            
        plt.title('Phase '+str(p))
        plt.ylabel('Delta (kW)')
        
        plt.xlim([0, 47])
        #plt.ylim([0, 5])
        
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(range(0, 47, 8), times)  
    plt.legend()
    plt.tight_layout()

def plot_current_voltage(CurArray,VoltArray,Coords,Lines,Flow,RateArray):
    pinchClist=[0,906,1410,1913]
    pinchVlist=[0,906,1410,1913,3142]
    Vmax=pd.DataFrame(index=CurArray.keys(),columns=['11','12','13','14','21','22','23','24','31','32','33','34'])
    Vpinch=pd.DataFrame(index=CurArray.keys(),columns=['11','12','13','14','21','22','23','24','31','32','33','34'])
    Vmin=pd.DataFrame(index=CurArray.keys(),columns=['11','12','13','14','21','22','23','24','31','32','33','34'])
    Cmax=pd.DataFrame(index=CurArray.keys(),columns=['11','12','13','14','21','22','23','24','31','32','33','34'])
    for i in CurArray.keys():
        for p in range(1,4):
            for f in range(1,5):
                Vmax[str(p)+str(f)][i] = VoltArray[i][Coords.index[Coords['Node'].astype(str).str[0]==str(f)].values,p-1].max()
                Vmin[str(p)+str(f)][i] = VoltArray[i][Coords.index[Coords['Node'].astype(str).str[0]==str(f)].values,p-1].min()
                Vpinch[str(p)+str(f)][i] = VoltArray[i][pinchVlist[f]][p-1]
                #Cmax[str(p)+str(f)][i] = (RateArray[Lines.index[Lines['Line'].astype(str).str[9]==str(f)].values]-CurArray[i][Lines.index[Lines['Line'].astype(str).str[9]==str(f)].values,p-1]).max()
                Cmax[str(p)+str(f)][i] = np.sign(Flow[f][p][i])*CurArray[i][pinchClist[f-1],p-1]

    #------- PLot of maximum voltages per phase and feeder
    times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    colors=['#9467bd','#ff7f0e','#d62728','#bcbd22']
    plt.figure()
    for p in range(1,4):
        plt.subplot(310+p)
        for f in range(1,5):
            plt.plot(
                Vmax[str(p)+str(f)].values,
                linewidth=1,
                linestyle="-",
                color=colors[f-1],
                label="Feeder "+str(f),
            )
            plt.plot(
                Vpinch[str(p)+str(f)].values,
                linewidth=1,
                linestyle="--",
                color=colors[f-1],
                #label="Feeder "+str(f),
            )
        plt.plot(np.full(48,1.1),color='red', linestyle="--",linewidth=0.5)
        plt.title('Phase '+str(p))
        plt.ylabel('Max Voltage (p.u.)')
        
        plt.xlim([0, 47])
        plt.ylim([1, 1.15])
        
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(range(0, 47, 8), times)  
    plt.legend()
    plt.tight_layout()

    #------- PLot of Current in supply branch per phase and feeder
    times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    plt.figure()
    for p in range(1,4):
        plt.subplot(310+p)
        for f in range(1,5):
            plt.plot(
                Cmax[str(p)+str(f)].values,
                linewidth=1,
                linestyle="-",
                label="Feeder "+str(f),
            )
        plt.plot(np.full(48,RateArray[pinchClist[f-1]]),color='red', linestyle="--",linewidth=0.5)
        plt.plot(np.full(48,-RateArray[pinchClist[f-1]]),color='red', linestyle="--",linewidth=0.5)
        plt.title('Phase '+str(p))
        plt.ylabel('Current (Amps)')
        
        plt.xlim([0, 47])
        plt.ylim([-200, 200])
        
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(range(0, 47, 8), times)  
    plt.legend()
    plt.tight_layout()

    return Vmax,Vmin,Cmax