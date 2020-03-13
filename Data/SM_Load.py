# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 11:21:14 2019

Script to process Smart Meter (SM) data for the AGILE Model
The London DataStore (or Low Carbon London (LCL) Smart Meter data is used from: https://data.london.gov.uk/dataset/smartmeter-energy-use-data-in-london-households
There is a data for 5,500 customers, A random 368 customers are chosen for sampling to keep data manageable size.
Some example analysis of the data is found https://data.london.gov.uk/blog/electricity-consumption-in-a-sample-of-london-households/
Data is available for the Following Households and Data ranges:


The script creates 2 pickle files with the data processed:
    
"SM_RawData.pickle" - Smart meter raw data for 115 Smart meters (subset of the 5,500 LCL customers)

@author: Calum Edmunds
"""

import pandas as pd
import pickle
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
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
            IDs.append(i[-3:])
    return IDs

IDs=SmartIDs()

#This function takes in the raw smart meter data and dumps in a pickle file
#Condenses all timeseries into single dataframe

def SMCondensed():
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
            z=i[-3:]
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
                SM_Stripped.name=i[-3:]
                SM_Stripped=SM_Stripped[~SM_Stripped.index.duplicated()]
                SM_DataFrame=pd.concat([SM_DataFrame, SM_Stripped],axis=1,join='outer',sort=False)

    pickle_out = open("Pickle/SM_DataFrame.pickle", "wb")
    pickle.dump(SM_DataFrame, pickle_out)
    pickle_out.close()
    
    pickle_out = open("Pickle/SM_Summary.pickle", "wb")
    pickle.dump(SM_Summary, pickle_out)
    pickle_out.close()