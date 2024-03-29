# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 11:21:14 2019

Script to process PV data for the AGILE Model
The London DataStore PV data is used from: https://data.london.gov.uk/dataset/photovoltaic--pv--solar-panel-energy-generation-data
Hourly Data is used and interpolated to half hourly. (Only 4 months of data was available for 10-minutely and 1-minutely)
Data is available for the Following sites and Data ranges:
Site               Apparent capacity (kW)   Date Range
---------------------------------------------------------
Forest Road	       3.00                     2013-10-01 to 2014-10-03 (366 Days)                  
Suffolk Road	   0.50                     2013-08-28 to 2014-11-09 (448 Days)
Bancroft Close	   3.50                     2013-10-04 to 2014-11-17 (408 Days)
Alverston Close	   3.00                     2013-11-06 to 2014-11-14 (372 Days)
Maple Drive East   4.00                     2013-08-21 to 2014-11-13 (448 Days)
YMCA	           0.45                     2013-09-25 to 2014-11-19 (420 Days)

The script creates 2 pickle files with the data processed:
    
'PV_BySiteName.pickle' - Which contains output (kW and Normalised by capacity) datestamped with a dataframe for each site
'PV_Normalised.pickle' - Which has normalised output by season in 48h rows combined for all sites with timestamps removed.

@author: Calum Edmunds
"""
import pandas as pd
import pickle
import numpy as np
import matplotlib.pyplot as plt
import datetime
pd.options.mode.chained_assignment = None


def PVLoad():
    # -------- Resampling Timestamped HH Data Per site ('PV_BySiteName.pickle')---------#
    # PVAll['P_GEN'] is the average kW output from the min and max hourly values
    # PVAll['P_GEN_Norm'] to contain P_Gen normalised by capacity
    
    PVAll = pd.read_csv("../../Data/HourlyPV.csv", index_col="datetime")
    PVAll["P_GEN"] = (PVAll["P_GEN_MIN"] + PVAll["P_GEN_MAX"]) / 2
    PVAll["P_GEN_Norm"] = PVAll["P_GEN"]
    PVAll.index = pd.to_datetime(PVAll.index)
    
    PVOutput_BySiteName = {}  # To contain PV output per site (kW and normalised)
    PV = pd.Series()  # to contain the combined normalised output of all sites
    
    # Site_Names = list(PVAll["Substation"].unique())
    Site_Names = [
        "Alverston Close",
        "Forest Road",
        "Suffolk Road",
        "Bancroft Close",
        "Maple Drive East",
        "YMCA",
    ]
    # PV Capacities. Apparent capacities from the London datastore dataset notes (word doc)
    PVCapacities = pd.Series(
        [3, 0.5, 3.5, 3, 4, 0.45], index=PVAll["Substation"].unique()
    )
    startdate = datetime.date(2013, 12, 1)
    enddate = datetime.date(2014, 2, 27)
    delta = datetime.timedelta(hours=0.5)
    dt = pd.date_range(startdate, enddate, freq=delta)
    # PV output is normalised resampled to half hourly then stored in a dataframe by site
    for item in Site_Names:
        print(item,PVAll["P_GEN"][PVAll["Substation"] == item].max())
        PVOutput_BySiteName[item] = pd.DataFrame()
        PVAll["P_GEN_Norm"][PVAll["Substation"] == item] = (
            PVAll["P_GEN"][PVAll["Substation"] == item]
            / PVAll["P_GEN"][PVAll["Substation"] == item].max()
        )
        PVOutput_BySiteName[item]["P_kW"] = PVAll["P_GEN"][PVAll["Substation"] == item]
        PVOutput_BySiteName[item]["P_Norm"] = PVAll["P_GEN_Norm"][
            PVAll["Substation"] == item
        ]
        PVOutput_BySiteName[item] = PVOutput_BySiteName[item].resample("30Min")
        PVOutput_BySiteName[item] = PVOutput_BySiteName[item].interpolate(
            method="linear", limit=1
        )
        PVOutput_BySiteName[item][PVOutput_BySiteName[item] < 0.003] = 0
        PVOutput_BySiteName[item] = PVOutput_BySiteName[item].fillna(0)
        PV = PV.append(PVOutput_BySiteName[item]["P_Norm"])
        
        #PVOutput_BySiteName[item]=PVOutput_BySiteName[item].reindex(dt)
    pickle_out = open("../../Data/PV_BySiteName_All.pickle", "wb")
    pickle.dump(PVOutput_BySiteName, pickle_out)
    
    # ------------------------ Normalise PV Data by capacity---------------------#
    # To create seasonal distributions, all sites are combined and normalised
    
    PVS = {}
    PVS["Winter"] = PV[(PV.index.month == 12) | (PV.index.month <= 2)]  # Dec-Feb
    PVS["Spring"] = PV[(PV.index.month >= 3) & (PV.index.month <= 5)]  # Mar-May
    PVS["Summer"] = PV[(PV.index.month >= 6) & (PV.index.month <= 8)]  # Jun-Aug
    PVS["Autumn"] = PV[(PV.index.month >= 9) & (PV.index.month <= 11)]  # Sept-Nov
    
    # Converting the data from a single column to rows of 48 hours of Data
    #'Newdists' contains seasonal normalised output for all sites combined
    Dists = {}
    Distkeys = ["Winter", "Spring", "Summer", "Autumn"]
    NewDists = {}
    for z in range(0, len(Distkeys)):
        Dists[Distkeys[z]] = pd.DataFrame(columns=range(0, 48), index=range(0, 809))
        for i in range(0, 1440, 30):
            a = PVS[Distkeys[z]][
                PVS[Distkeys[z]].index.hour * 60 + PVS[Distkeys[z]].index.minute == i
            ].values
            Dists[Distkeys[z]][i / 30][0 : len(a)] = a
        NewDists[Distkeys[z]] = Dists[Distkeys[z]][Dists[Distkeys[z]].sum(axis=1) > 0]
        NewDists[Distkeys[z]].reset_index(drop=True, inplace=True)
    pickle_out = open("../../Data/PV_Normalised.pickle", "wb")
    pickle.dump(NewDists, pickle_out)
    
    distsBySite={}
    sites=list(PVOutput_BySiteName.keys())
    NewdistsBySite={}
    for z in range(0, len(PVOutput_BySiteName)):
        distsBySite[sites[z]] = pd.DataFrame(columns=range(0, 48), index=range(0, 809))
        for i in range(0, 1440, 30):
            a = PVOutput_BySiteName[sites[z]]['P_kW'][
                PVOutput_BySiteName[sites[z]].index.hour * 60 + PVOutput_BySiteName[sites[z]].index.minute == i
            ].values
            distsBySite[sites[z]][i / 30][0 : len(a)] = a
        NewdistsBySite[sites[z]] = distsBySite[sites[z]][distsBySite[sites[z]].sum(axis=1) > 0]
        NewdistsBySite[sites[z]].reset_index(drop=True, inplace=True)
        
    return PVOutput_BySiteName,PVS,NewdistsBySite
 


def PV_Visualisation(NewdistsBySite):
    # ------------------ Visualisation of the Data ---------------------------
    pickin = open("../../Data/PV_Normalised.pickle", "rb")
    NewDists = pickle.load(pickin)
    pickin = open("../../Data/PV_BySiteName.pickle", "rb")
    PVOutput_BySiteName = pickle.load(pickin)
    # By site
    plt.figure(1)
    n = 1
    colors = [
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    ]
    for item in PVOutput_BySiteName:
        plt.subplot(320 + n)
        plt.title(item, fontsize=9)
        plt.scatter(
            PVOutput_BySiteName[item]["P_kW"].index,
            PVOutput_BySiteName[item]["P_kW"],
            s=0.5,
            c=colors[n],
        )
        plt.ylabel("Output(kW)", fontsize=8)
        plt.xticks(fontsize=7)
        plt.yticks(fontsize=8)
        n = n + 1
    plt.tight_layout()

    plt.figure(2)
    # By Season
    n = 1
    Seasons = ["Winter", "Spring", "Summer", "Autumn"]
    times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"]
    for item in Seasons:
        plt.subplot(220 + n)
        plt.title(Seasons[n - 1], fontsize=9)
        for i in NewDists[item].index:
            plt.plot(NewDists[item].iloc[i], linewidth=0.1)
        plt.xlabel("Settlement Period (half hourly)", fontsize=8)
        plt.ylabel("Output(fraction of capacity)", fontsize=8)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        n = n + 1

    qrts = {}  # qrts will contain quartiles (q1,q2,q3,max and mean)
    for item in Seasons:
        qrts[item] = {}
        qrts[item]["q1"] = np.empty(1)
        qrts[item]["q2"] = np.empty(1)
        qrts[item]["q3"] = np.empty(1)
        qrts[item]["max"] = np.empty(1)
        qrts[item]["mean"] = np.empty(1)
        for i in NewDists[item]:
            qrts[item]["q1"] = np.append(
                qrts[item]["q1"], NewDists[item][i].quantile(0.25)
            )
            qrts[item]["q2"] = np.append(
                qrts[item]["q2"], NewDists[item][i].quantile(0.5)
            )
            qrts[item]["q3"] = np.append(
                qrts[item]["q3"], NewDists[item][i].quantile(0.75)
            )
            qrts[item]["max"] = np.append(qrts[item]["max"], NewDists[item][i].max())
            qrts[item]["mean"] = np.append(qrts[item]["mean"], NewDists[item][i].mean())

        qrts[item]["q1"] = np.delete(qrts[item]["q1"], 0)
        qrts[item]["q2"] = np.delete(qrts[item]["q2"], 0)
        qrts[item]["q3"] = np.delete(qrts[item]["q3"], 0)
        qrts[item]["max"] = np.delete(qrts[item]["max"], 0)
        qrts[item]["mean"] = np.delete(qrts[item]["mean"], 0)

    style = ["-", "-", "-", "--", "--"]
    colors = [
        "#d62728",
        "#9467bd",
        "#8c564b",
        "black",
        "white",
        "#bcbd22",
        "#17becf",
    ]

    i = 1
    for item in qrts:
        n = 0
        plt.subplot(220 + i)
        for z in qrts[item]:
            plt.plot(
                qrts[item][z],
                color=colors[n],
                linewidth=1.5,
                label=z,
                linestyle=style[n],
            )
            n = n + 1
        plt.legend(fontsize=8)
        i = i + 1
    plt.tight_layout()
    ###########================ Dists kW by Site =================###
    plt.figure(3)
    # By site
    n = 1
    sites=list(PVOutput_BySiteName.keys())
    for item in sites:
        plt.subplot(220 + n)
        plt.title(sites[n - 1], fontsize=10)
        for i in NewdistsBySite[item].index:
            plt.plot(NewdistsBySite[item].iloc[i], linewidth=0.05)
        #plt.xlabel("Settlement Period (half hourly)", fontsize=9)
        plt.ylabel("Output(kW)", fontsize=9)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        n = n + 1

    qrts = {}  # qrts will contain quartiles (q1,q2,q3,max and mean)
    for item in sites:
        qrts[item] = {}
        qrts[item]["Q50"] = np.empty(1)
        # qrts[item]["Q75"] = np.empty(1)
        # qrts[item]["Max"] = np.empty(1)
        qrts[item]["Mean"] = np.empty(1)
        for i in NewdistsBySite[item]:
            qrts[item]["Q50"] = np.append(
                qrts[item]["Q50"], NewdistsBySite[item][i].quantile(0.5)
            )
            # qrts[item]["Q75"] = np.append(
            #     qrts[item]["Q75"], NewdistsBySite[item][i].quantile(0.75)
            # )
            # qrts[item]["Max"] = np.append(qrts[item]["Max"], NewdistsBySite[item][i].max())
            qrts[item]["Mean"] = np.append(qrts[item]["Mean"], NewdistsBySite[item][i].mean())

        qrts[item]["Q50"] = np.delete(qrts[item]["Q50"], 0)
        # qrts[item]["Q75"] = np.delete(qrts[item]["Q75"], 0)
        # qrts[item]["Max"] = np.delete(qrts[item]["Max"], 0)
        qrts[item]["Mean"] = np.delete(qrts[item]["Mean"], 0)

    style = ["--", ":", "-.", "--"]
    colors =["black", "blue", "#d62728", "#bcbd22", "#1f77b4", "#bcbd22",'#17becf','#8c564b','#17becf']
    i = 1
    times2 = ["00:00", "06:00", "12:00", "18:00"]
    for item in qrts:
        n = 0
        plt.subplot(220 + i)
        for z in qrts[item]:
            plt.plot(
                qrts[item][z],
                color=colors[n],
                linewidth=2,
                label=z,
                linestyle=style[n],
            )
            n = n + 1    
        i = i + 1
        plt.grid(linewidth=0.2)
        plt.xlim([0, 47])
        plt.xticks(range(0,48,12),times2)
        
    plt.tight_layout()
    plt.legend(fontsize=8)
    return qrts, NewDists, PVOutput_BySiteName


## ----------to run the functions--------------
PVOutput_BySiteName,PVS,NewdistsBySite=PVLoad()
#qrts, NewDists, PVOutput_BySiteName=PV_Visualisation(NewdistsBySite)
