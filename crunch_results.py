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

def counts(network_summary):
    Chigh_allPeriods={}
    Chigh_count={}
    
    Vhigh_allPeriods={}
    Vhigh_count={}
    
    Vlow_allPeriods={}
    Vlow_count={}
    for p in range(0,3):
        Chigh_allPeriods[p]=[]
        Vhigh_allPeriods[p]=[]
        Vlow_allPeriods[p]=[]
        for i in network_summary:
            if len(network_summary[i][p]['Chigh_lines']) >0:
                for item in network_summary[i][p]['Chigh_lines']:
                    Chigh_allPeriods[p].append(item)
                Chigh_count[p]=collections.Counter(Chigh_allPeriods[p])
                
            if len(network_summary[i][p]['Vhigh_nodes']) >0:
                for item in network_summary[i][p]['Vhigh_nodes']:
                    Vhigh_allPeriods[p].append(item)
                Vhigh_count[p]=collections.Counter(Vhigh_allPeriods[p])
                
            if len(network_summary[i][p]['Vlow_nodes']) >0:
                for item in network_summary[i][p]['Vlow_nodes']:
                    Vlow_allPeriods[p].append(item)
                Vlow_count[p]=collections.Counter(Vlow_allPeriods[p])
    
    return Chigh_count, Vhigh_count, Vlow_count
    
def plots(Network_Path,Chigh_count):
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
    for p in range(0,3):
       #-------- Add colors to lines
       if p in list(Chigh_count.keys()):
           Chigh_count[p].keys()
           newcount = [x+1 for x in list(Chigh_count[p].keys())]
           Lines['Color'].iloc[newcount]='blue'
           Lines['width'].iloc[newcount]= list(Chigh_count[p].values())
           ##### Plot Currents for each Phase ####
           plt.figure(n)
           #plt.figure(311+p)
           plt.title('Current (A) - Phase ' +str(p+1))
           nx.draw(G, pos, with_labels=False, width=Lines['width']/max(Lines['width']), node_size=0.2, node_color=Coords['Color'], edge_color=Lines['Color'], font_weight='bold')
           plt.show()
           plt.tight_layout()
           n=n+1
    return Coords,Lines


def Headroom_calc(network_summary, Customer_Summary, smartmeter, heatpump, pv):
    Headrm={}
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
        
    for i in network_summary:
        Headrm[0][i]=network_summary[i]['Trans_kVA_Headroom']      
        for p in range(1,4):
            for f in range(1,5):
                InputsbyFP['SM'][str(p)+str(f)][i] = np.nan_to_num(smartmeter[i])[custph[p][f].index].sum()
                InputsbyFP['HP'][str(p)+str(f)][i] = np.nan_to_num(heatpump[i])[custph[p][f].index].sum()
                InputsbyFP['PV'][str(p)+str(f)][i] = np.nan_to_num(pv[i])[custph[p][f].index].sum()
    for z in range(1,5):
        Headrm[z]=pd.DataFrame(index=network_summary.keys(), columns=[0,1,2])
        for p in range(0,3):
            for i in network_summary:
                Headrm[z][p][i]=network_summary[i][p]['Chdrm'][z]

    
    return Headrm, Customer_Summary, custph, InputsbyFP

def plot_headroom(Headrm,InputsbyFP):
    times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    plt.figure(0)
    plt.plot(
        Headrm[0].values,
        color="blue",
        linewidth=1,
        linestyle="--",
        label="Secondary Substation Headroom",
    )
    plt.ylabel('Headroom (kVA)')
    plt.title("Network 1 - Secondary Substation Headroom")
    
    plt.xlim([0, 47])
    #plt.ylim([0, 5])
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.xticks(range(0, 47, 8), times)
    
    plt.figure(1)
    plt.title('Headroom (at head supply branch) per phase and feeder')
    
    for p in range(0,3):
        plt.subplot(310+p+1)
        for f in range(1,5):
            plt.plot(
                Headrm[f][p].values,
                linewidth=1,
                #linestyle="--",
                label="Feeder "+str(f),
            )
            plt.plot(np.zeros(48),color='black', linestyle="--",)
        plt.title('Phase '+str(p+1))
        plt.ylabel('Headroom (kW)')
        
        plt.xlim([0, 47])
        #plt.ylim([0, 5])
        
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(range(0, 47, 8), times)  
    plt.legend()
    plt.tight_layout()

    #------- PLot of demand and generation per feeder and phase
    for i in ['SM','HP','PV']:
        times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
        plt.figure()
        for p in range(1,4):
            plt.subplot(310+p)
            for f in range(1,5):
                plt.plot(
                    InputsbyFP[i][str(p)+str(f)].values,
                    linewidth=1,
                    #linestyle="--",
                    label="Feeder "+str(f),
                )
                
            plt.title('Phase '+str(p)+' '+str(i))
            plt.ylabel('Demand/output (kW)')
            
            plt.xlim([0, 47])
            #plt.ylim([0, 5])
            
            plt.xticks(fontsize=8)
            plt.yticks(fontsize=8)
            plt.xticks(range(0, 47, 8), times)  
        plt.legend()
        plt.tight_layout()

