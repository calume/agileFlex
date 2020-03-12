# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 11:21:14 2019

Script to process Smart Meter (SM) data for the AGILE Model
The London DataStore (or Low Carbon London (LCL) Smart Meter data is used from: https://data.london.gov.uk/dataset/smartmeter-energy-use-data-in-london-households
There is a data for 5,500 customers, The first 100 customers are chosen for sampling to keep data manageable size.
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
import matplotlib.dates as mdates

# --------------------------- Create SM Data Pickle -------------------
# This function takes in the raw smart meter data and dumps in a pickle file
# Each dataframe in the dictionary is a smart meter


def SMData_load():
    H = pd.read_csv(
        "Profiles/Power-Networks-LCL-June2015(withAcornGps)v2_1.csv",
        names=["ID", "Tar", "Date", "kWh", "A", "Group"],
    )
    H2 = pd.read_csv(
        "Profiles/Power-Networks-LCL-June2015(withAcornGps)v2_2.csv",
        names=["ID", "Tar", "Date", "kWh", "A", "Group"],
    )
    H3 = pd.read_csv(
        "Profiles/Power-Networks-LCL-June2015(withAcornGps)v2_10.csv",
        names=["ID", "Tar", "Date", "kWh", "A", "Group"],
    )
    H4 = pd.read_csv(
        "Profiles/Power-Networks-LCL-June2015(withAcornGps)v2_11.csv",
        names=["ID", "Tar", "Date", "kWh", "A", "Group"],
    )
    HS = {}
    for i in range(2, 364):
        if i < 10:
            s = "0" + str(i)
        else:
            s = i
        if i <= 35:
            HS[i] = H[H["ID"] == "MAC0000" + str(s)]
            HS[i].index = pd.to_datetime(HS[i]["Date"], format="%Y/%m/%d %H:%M:%S")
            if len(HS[i]) == 0:
                HS.pop(i)
        if i >= 36 and i <= 69:
            HS[i] = H2[H2["ID"] == "MAC0000" + str(s)]
            HS[i].index = pd.to_datetime(HS[i]["Date"], format="%Y/%m/%d %H:%M:%S")
            if len(HS[i]) == 0:
                HS.pop(i)
        if i >= 295 and i <= 326:
            HS[i] = H3[H3["ID"] == "MAC000" + str(s)]
            HS[i].index = pd.to_datetime(HS[i]["Date"], format="%Y/%m/%d %H:%M:%S")
            if len(HS[i]) == 0:
                HS.pop(i)
        if i >= 326 and i <= 363:
            HS[i] = H4[H4["ID"] == "MAC000" + str(s)]
            HS[i].index = pd.to_datetime(HS[i]["Date"], format="%Y/%m/%d %H:%M:%S")
            if len(HS[i]) == 0:
                HS.pop(i)
    for i in HS.keys():
        HS[i]["kWh"] = HS[i]["kWh"].replace("Null", 0).astype(float)
        HS[i]=HS[i].drop(columns=['Tar','Date','A'])

    pickle_out = open("Pickle/SM_RawData.pickle", "wb")
    pickle.dump(HS, pickle_out)
    pickle_out.close()


SMData_load()
# ------------------------ DO stuff with the data -------------

pickle_in = open("Pickle/SM_RawData.pickle", "rb")
SM_Raw = pickle.load(pickle_in)

i = 2
SM_Summary = pd.DataFrame(
    index=SM_Raw.keys(),
    columns=[
        "AcornGroup",
        "MinDate",
        "MaxDate",
        "Days",
        "PeakDemandkW",
        "SumDemandkWh/Day",
        "AvDemandkW",
    ],
)

for i in SM_Raw.keys():
    SM_Raw[i]["kW"] = (
        SM_Raw[i]["kWh"].replace("Null", 0).astype(float) * 2
    )  # Convert kWh to kW
    SM_Summary["AcornGroup"][i] = SM_Raw[i]["Group"][0]
    SM_Summary["MinDate"][i] = SM_Raw[i].index.min()
    SM_Summary["MaxDate"][i] = SM_Raw[i].index.max()
    SM_Summary["Days"][i] = (SM_Raw[i].index.max() - SM_Raw[i].index.min()).days
    SM_Summary["PeakDemandkW"][i] = SM_Raw[i]["kW"].max()
    SM_Summary["SumDemandkWh/Day"][i] = SM_Raw[i]["kWh"].sum() / SM_Summary["Days"][i]
    SM_Summary["AvDemandkW"][i] = SM_Raw[i]["kWh"].mean()
