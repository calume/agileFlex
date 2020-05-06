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
    for i in network_summary:
        Headrm[0][i]=network_summary[i]['Trans_kVA_Headroom']
    
    for z in range(1,5):
        Headrm[z]=pd.DataFrame(index=network_summary.keys(), columns=[0,1,2])
        for p in range(0,3):
            for i in network_summary:
                Headrm[z][p][i]=network_summary[i][p]['Chdrm'][z]
    
    custs_grouped=pd.DataFrame(index=[1,2,3,4])
#    custs_grouped['phase']=Customer_Summary['Phase']
    Customer_Summary['feeder']=Customer_Summary['Node'].astype(str).str[0]
#    custs_grouped['smartmeter']=smartmeter
#    custs_grouped['pv']=pv
#    custs_grouped['heatpump']=heatpump
    custs_grouped['total_custs']=Customer_Summary.groupby('feeder').count()['ID'].values
    return Headrm, Customer_Summary, custs_grouped

Headrm, custs_grouped, custs_grouped = Headroom_calc(network_summary, Customer_Summary, smartmeter, heatpump, pv)

def plot_headroom(Headrm):
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



#    plt.plot(PVtot.index,-PVtot, label="PV")
#    plt.plot(EVtot.index,EVtot, label="EV")
#    plt.plot(HPtot.index,HPtot, label="HP")
#    plt.plot(SMtot.index,SMtot, label="SM")
#    plt.plot(Loadsum.index,Loadsum, label="Net Demand")
#    plt.legend()
#    
#    plt.figure(2)
#    plt.subplot(211)
#    plt.plot(Vmax.index,Vmax, label="Vmax")
#    plt.plot(Vmin.index,Vmin, label="Vmin")
#    plt.legend()
#    plt.subplot(212)
#    plt.plot(Cmax.index,Cmax, label="C / Crated Max")
#    plt.legend()
    
#    pickle_in = open("Outputs/ResultsEVHP.pickle","rb")
#    SM = pickle.load(pickle_in)
#    ParamKeys=['Vmax','Vmin','Cmax','Loadsum']
#    CongKeys=['VUC','VLC','CMC']
#    Seasons=['Winter','Spring','Summer','Autumn']
#    Params={'Winter':{},'Spring':{},'Summer':{},'Autumn':{}}
#    #Cong={}
#    ######## By season #######
#    for n in ParamKeys:
#        Params['Winter'][n]=SM[n][(SM[n].index.month==12) | (SM[n].index.month<=2)]    #Dec-Feb
#        Params['Spring'][n]=SM[n][(SM[n].index.month>=3) & (SM[n].index.month<=5)]    #Mar-May
#        Params['Summer'][n]=SM[n][(SM[n].index.month>=6) & (SM[n].index.month<=8)]    #Jun-Aug
#        Params['Autumn'][n]=SM[n][(SM[n].index.month>=9) & (SM[n].index.month<=11)]    #Sept-Nov
#    
#    for p in Seasons:
#        Params[p]['Wkd']={}
#        Params[p]['Wknd']={}
#        for n in ParamKeys:
#            Params[p]['Wkd'][n] = Params[p][n][(Params[p][n].index.weekday>=0) & (Params[p][n].index.weekday<=4)]
#            Params[p]['Wknd'][n] = Params[p][n][(Params[p][n].index.weekday>=5) & (Params[p][n].index.weekday<=6)]
#    
#    for i in Params:
#        Params[i]['VUC']=Params[i]['Vmax'][Params[i]['Vmax']>1.1]
#        Params[i]['VLC']=Params[i]['Vmin'][Params[i]['Vmin']<0.94]
#        Params[i]['CUC']=Params[i]['Cmax'][Params[i]['Cmax']>1]
#        for j in ['Wkd','Wknd']:
#            Params[i][j]['VUC']=Params[i][j]['Vmax'][Params[i][j]['Vmax']>1.1]
#            Params[i][j]['VLC']=Params[i][j]['Vmin'][Params[i][j]['Vmin']<0.94]
#            Params[i][j]['CUC']=Params[i][j]['Cmax'][Params[i][j]['Cmax']>1]
#            histvu,bins = np.histogram(Params[i][j]['VUC'].index.hour,bins=range(0,24))
#            histvl,bins = np.histogram(Params[i][j]['VLC'].index.hour,bins=range(0,24))
#            histcu,bins = np.histogram(Params[i][j]['CUC'].index.hour,bins=range(0,24))
#            fig, ax1 = plt.subplots()
#            ax1.bar(bins[1:],histvl/len(Params[i][j]['Vmin'])*100, label="Low Voltage: < 0.94 p.u." )
#            ax1.bar(bins[1:],histvu/len(Params[i][j]['Vmax'])*100, label="High Voltage: > 1.1 p.u.")
#            ax1.bar(bins[1:],histcu/len(Params[i][j]['Cmax'])*100, color="red", label="Thermal: > Rated A")
#            plt.xlabel('Hour')
#            plt.ylabel('Congestion Probability (%)')
#            plt.title('4 Feeder Network: Congestion probability '+str(i)+' '+str(j))
#            plt.legend()
#            ax2 = ax1.twinx() 
#            ax2.plot(Params[i][j]['Loadsum'].groupby(Params[i][j]['Loadsum'].index.hour).mean(),color = 'black', label='Average net load')
#            ax2.set_ylabel('Average net demand (kW)',color ='black')
#            ax2.legend(loc=3)
#            plt.show()

