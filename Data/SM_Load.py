# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 11:21:14 2019

Script to process Smart Meter (SM) data for the AGILE Model
The London DataStore (or Low Carbon London (LCL) Smart Meter data is used from: https://data.london.gov.uk/dataset/smartmeter-energy-use-data-in-london-households
There is a data for 5,500 customers, A random 187 customers are chosen for sampling to keep data manageable size.
From Files:
-'Power-Networks-LCL-June2015(withAcornGps)v2_1.csv'
-'Power-Networks-LCL-June2015(withAcornGps)v2_2.csv'
-'Power-Networks-LCL-June2015(withAcornGps)v2_10.csv'
-'Power-Networks-LCL-June2015(withAcornGps)v2_11.csv'
-'Power-Networks-LCL-June2015(withAcornGps)v2_100.csv'
-'Power-Networks-LCL-June2015(withAcornGps)v2_101.csv'

Some example analysis of the data is found https://data.london.gov.uk/blog/electricity-consumption-in-a-sample-of-london-households/
Data is available for the Following 187 Households, by Acorn Group:

Acorn Group|Number of customers| Avg Days of Data (per customer)| Peak Demand (kW) | Average Daily Demand (kWh/day) | Average demand (kW)
----------------------------------
Adversity | 55 | 662 | 7.75 |   15.99 | 0.33
Comfortable | 46 | 655 | 9.24 |   19.24 | 0.40
Affluent | 86 | 676 | 11.17 |   25.59 | 0.53

The script creates 3 pickle files with the data processed:
    
- "SM_DataFrame.pickle" - Smart meter raw data for 187 Smart meters (subset of the 5,500 LCL customers).Timestamped

- "SM_Summary.pickle" - Summary of Acorn Group, Date Ranges and Means/Peaks for each household

- "SM_Normalised.pickle" - Customers are combined into Seasonal (and weekday/weekend) daily profiles by ACorn Group

@author: Calum Edmunds
"""

import pandas as pd
import pickle
import numpy as np
import matplotlib.pyplot as plt
import datetime
import os

# --------------------------- Create SM Data Pickle -------------------


startdate =  datetime.date(2011,12,6)
enddate   =  datetime.date(2014,3,1)
delta = datetime.timedelta(hours=0.5)

dt = pd.date_range(startdate, enddate, freq=delta)

#Get list of Smart Meter IDs that are to be stored
def SmartIDs():
    path="Profiles/SM"
    IDs=[]
    for f in os.listdir(path):
        SM_RawFile = pd.read_csv(path+"/"+f,
                        names=["ID", "Tar", "Date", "kWh", "A", "Group"],
                        skiprows=1,
            )
    
        print(f)
        for i in SM_RawFile["ID"].unique():
            IDs.append(i[-4:])
    return IDs

#This function takes in the raw smart meter data and dumps in a pickle file
#Condenses all timeseries into single dataframe

def SMCondensed():
    IDs=SmartIDs()
    SM_Summary = pd.DataFrame(
        index=IDs,
        columns=[
            "AcornGroup",
            "MinDate",
            "MaxDate",
            "Days",
            "Tariff",
            "PeakDemandkW",
            "DemandkWh/Day",
            "AvDemandkW",
        ])
    
    SM_DataFrame=pd.DataFrame(index=dt)
    path="Profiles/SM"
    
    for f in os.listdir(path):
        SM_RawFile = pd.read_csv(path+"/"+f,
                        names=["ID", "Tar", "Date", "kWh", "A", "Group"],
                        skiprows=1,
            )
    
        print(f)
        for i in SM_RawFile["ID"].unique():
            SM_Individual = SM_RawFile[SM_RawFile["ID"] == i]
            SM_Individual['Date'] = pd.to_datetime(SM_Individual["Date"], format="%Y/%m/%d %H:%M:%S")
            z=i[-4:]
            print(i)
            SM_Summary["AcornGroup"][z] = SM_Individual["Group"].iloc[0]
            SM_Summary["MinDate"][z] = SM_Individual['Date'].min()
            SM_Summary["MaxDate"][z] = SM_Individual['Date'].max()
            SM_Summary["Days"][z] = (SM_Individual['Date'].max() - SM_Individual['Date'].min()).days
            SM_Summary["Tariff"][z] = SM_Individual["Tar"].unique()
            SM_Individual['kWh']=SM_Individual['kWh'].replace("Null", 0).astype(float) * 2
            SM_Summary["PeakDemandkW"][z] = SM_Individual["kWh"].max()*2
            SM_Summary["DemandkWh/Day"][z] = SM_Individual["kWh"].sum() / SM_Summary["Days"][z]
            SM_Summary["AvDemandkW"][z] = SM_Individual["kWh"].mean()
            if len(SM_Individual) > 0:
                SM_Stripped=SM_Individual['kWh'].replace("Null", 0).astype(float) * 2
                SM_Stripped.index=pd.to_datetime(SM_Individual["Date"], format="%Y/%m/%d %H:%M:%S")
                SM_Stripped.name=i[-4:]
                SM_Stripped=SM_Stripped[~SM_Stripped.index.duplicated()]
                SM_DataFrame=pd.concat([SM_DataFrame, SM_Stripped],axis=1,join='outer',sort=False)
    SM_Summary[['PeakDemandkW','DemandkWh/Day','Days','AvDemandkW']]=SM_Summary[['PeakDemandkW','DemandkWh/Day','Days','AvDemandkW']].astype(float)
    
    SM_DataFrame.columns=SM_DataFrame.columns.astype(int)
    SM_DataFrame=SM_DataFrame.sort_index(axis=1)
    SM_DataFrame=SM_DataFrame.loc[:,~SM_DataFrame.columns.duplicated()]
    
    pickle_out = open("Pickle/SM_DataFrame.pickle", "wb")
    pickle.dump(SM_DataFrame, pickle_out)
    pickle_out.close()
    
    pickle_out = open("Pickle/SM_Summary.pickle", "wb")
    pickle.dump(SM_Summary, pickle_out)
    pickle_out.close()
    
    
###SMCondensed()

def generate_summaryData():
    pickle_in = open("Pickle/SM_Summary.pickle", "rb")
    SM_Summary = pickle.load(pickle_in)
    
    print(round(SM_Summary.groupby(['AcornGroup']).mean(),2))
    for i in SM_Summary['AcornGroup'].unique():
        print(i)
        print(sum(SM_Summary['AcornGroup']==i))

###----------------------------- Converting to Daily Profiles ------------------------
#
smkeys=['WinterWknd', 'WinterWkd','SpringWknd','SpringWkd','SummerWknd','SummerWkd','AutumnWknd','AutumnWkd']
def Consolidate(smkeys):
    pick_in = open("Pickle/SM_DataFrame.pickle", "rb")
    SM_DataFrame = pickle.load(pick_in)
    
    pick_in = open("Pickle/SM_Summary.pickle", "rb")
    SM_Summary = pickle.load(pick_in)
    
    SM_ByAcorn={}
    AcornGroup=['Adversity','Comfortable','Affluent']
    NewDists = {}
    
    for i in AcornGroup:
        SM_ByAcorn[i]={}
        Acorn_Cols=list(SM_Summary['AcornGroup'][SM_Summary['AcornGroup']==i].index)
        Acorn_Cols=sorted(list(map(int,Acorn_Cols)))
        Locs=[]
        for z in Acorn_Cols:
            Locs.append(SM_DataFrame.columns.get_loc(z))
        print(len(Acorn_Cols))
        Winter=SM_DataFrame.iloc[:,Locs][(SM_DataFrame.index.month==12) | (SM_DataFrame.index.month<=2)]    #Dec-Feb
        Spring=SM_DataFrame.iloc[:,Locs][(SM_DataFrame.index.month>=3) & (SM_DataFrame.index.month<=5)]    #Mar-May
        Summer=SM_DataFrame.iloc[:,Locs][(SM_DataFrame.index.month>=6) & (SM_DataFrame.index.month<=8)]    #Jun-Aug
        Autumn=SM_DataFrame.iloc[:,Locs][(SM_DataFrame.index.month>=9) & (SM_DataFrame.index.month<=11)]    #Sept-Nov
        print(len(Winter.columns))
        ### Wkday/Wkend########
        
        SM_ByAcorn[i]['WinterWknd']=Winter[(Winter.index.weekday>=5) & (Winter.index.weekday<=6)]
        SM_ByAcorn[i]['WinterWkd']=Winter[(Winter.index.weekday>=0) & (Winter.index.weekday<=4)]
        SM_ByAcorn[i]['SpringWknd']=Spring[(Spring.index.weekday>=5) & (Spring.index.weekday<=6)]
        SM_ByAcorn[i]['SpringWkd']=Spring[(Spring.index.weekday>=0) & (Spring.index.weekday<=4)]
        
        SM_ByAcorn[i]['SummerWknd']=Summer[(Summer.index.weekday>=5) & (Summer.index.weekday<=6)]
        SM_ByAcorn[i]['SummerWkd']=Summer[(Summer.index.weekday>=0) & (Summer.index.weekday<=4)]
        
        SM_ByAcorn[i]['AutumnWknd']=Autumn[(Autumn.index.weekday>=5) & (Autumn.index.weekday<=6)]
        SM_ByAcorn[i]['AutumnWkd']=Autumn[(Autumn.index.weekday>=0) & (Autumn.index.weekday<=4)]
    
#    #-------- Converting the data from a single column to rows of 48 hours of Data
#    #'Newdists' contains seasonal normalised output for all sites combined
#        NewDists[i]={}
#        for z in range(0, len(smkeys)):
#            SM_ByAcorn[i][smkeys[z]]=SM_ByAcorn[i][smkeys[z]].loc[:,~SM_ByAcorn[i][smkeys[z]].columns.duplicated()]
#            SM_DataFrame=SM_DataFrame.loc[:,~SM_DataFrame.columns.duplicated()]
#            n=0
#            print(z)
#            NewDists[i][smkeys[z]]=pd.DataFrame(index=range(0,20000),columns=range(0,48))
#            for c in SM_ByAcorn[i][smkeys[z]]:
#                print(c)
#                for d in range(0, int(len(SM_ByAcorn[i][smkeys[z]])/48)):
#                    NewDists[i][smkeys[z]].iloc[n] = SM_ByAcorn[i][smkeys[z]][c].iloc[48*d:48*d+48].values.astype(float)
#                    n=n+1
#            NewDists[i][smkeys[z]] = NewDists[i][smkeys[z]][NewDists[i][smkeys[z]].sum(axis=1) > 0]
#            NewDists[i][smkeys[z]].reset_index(drop=True, inplace=True)
#    
#        pickle_out = open("Pickle/SM_Normalised.pickle", "wb")
#        pickle.dump(NewDists, pickle_out)
#        pickle_out.close()
        return SM_ByAcorn

#Do profiles by Smartmeter by Acorn and Season
AcornGroup=['Adversity','Comfortable','Affluent']
SMDistsByAcorn= {}
for i in AcornGroup:
    SMDistsByAcorn[i]= {}
    for z in smkeys:
        SM_Acorn[i][z]=SM_Acorn[i][z].loc[:,~SM_Acorn[i][z].columns.duplicated()]
        print(z)
        SMDistsByAcorn[i][z]={}
        for c in SM_Acorn[i][z]:
            n=0
            print(c)
            SMDistsByAcorn[i][z][c]=pd.DataFrame(index=range(0,20000),columns=range(0,48))
            for d in range(0, int(len(SM_Acorn[i][z][c])/48)):
                SMDistsByAcorn[i][z][c].iloc[n] = SM_Acorn[i][z][c].iloc[48*d:48*d+48].values.astype(float)
                n=n+1
            SMDistsByAcorn[i][z][c] = SMDistsByAcorn[i][z][c][SMDistsByAcorn[i][z][c].sum(axis=1) > 0]
            SMDistsByAcorn[i][z][c].reset_index(drop=True, inplace=True)
pickle_out = open("Pickle/SM_DailyByAcorn.pickle", "wb")
pickle.dump(SMDistsByAcorn, pickle_out)
pickle_out.close()

#------------------- Data Visualisation -----------------------------#
def SM_Visualise(smkeys):
    pick_in = open("Pickle/SM_Normalised.pickle", "rb")
    SM_Normalised = pickle.load(pick_in)
    plt.figure(1)
    times = ['00:00','04:00','08:00','12:00','16:00','20:00','24:00']
    Seasons = ["Winter", "Spring", "Summer", "Autumn"]
    n=1
    r=0
    for item in smkeys:
        plt.subplot(420 + n)
        
        plt.plot(SM_Normalised['Affluent'][item].mean(),color='#33FF92', label="Affluent")
        plt.plot(SM_Normalised['Comfortable'][item].mean(),color='#17becf', label="Comfortable")
        plt.plot(SM_Normalised['Adversity'][item].mean(),color='#FA8072', label="Adversity")
        plt.xlabel("Settlement Period (half hourly)", fontsize=8)
        #plt.ylabel("Demand (kW)", fontsize=8)
        plt.xlim([0,47])
        plt.ylim([0,2])
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        if n==1:
            plt.legend(fontsize=8)
            plt.title('Weekend (Sat-Sun)', fontsize=9, fontweight="bold")
        if n==2:
            plt.title('Week Day (Mon-Fri)', fontsize=9, fontweight="bold")
        if n%2==1:
            plt.ylabel(Seasons[r], rotation=15, fontsize=9, fontweight="bold")
            r=r+1
        n = n + 1
        plt.xticks(range(0,47,8),times)
#SM_Visualise(smkeys)

#SM_Acorn=Consolidate(smkeys)

#---------- Removing heating loads
#pick_in = open("Pickle/SM_DataFrame.pickle", "rb")
#SM_DataFrame = pickle.load(pick_in)
#Heaters=(SM_DataFrame[SM_DataFrame.index.hour==0]>4).sum()>1
#Heaters=Heaters[Heaters]
        
#for i in SMDistsByAcorn['Affluent']['WinterWkd'][358].index:
#   plt.plot(SMDistsByAcorn['Affluent']['WinterWkd'][358].loc[i], linewidth=0.1)
    