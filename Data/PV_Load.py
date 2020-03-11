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
import time
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
from datetime import datetime, timedelta, date, time
import datetime
import matplotlib.dates as mdates
from matplotlib.ticker import LinearLocator, FormatStrFormatter
from matplotlib import cm
import scipy as sp
from scipy import optimize
from numpy import exp
from scipy.stats import boxcox
from scipy.stats import gaussian_kde
from statsmodels.nonparametric.kde import KDEUnivariate
import cloudpickle

pd.options.mode.chained_assignment = None
from sklearn import mixture

# -------- Resampling Timestamped HH Data Per site ('PV_BySiteName.pickle')---------#
# PVAll['P_GEN'] is the average kW output from the min and max hourly values
# PVAll['P_GEN_Norm'] to contain P_Gen normalised by capacity

PVAll = pd.read_csv("HourlyPV.csv", index_col="datetime")
PVAll["P_GEN"] = (PVAll["P_GEN_MIN"] + PVAll["P_GEN_MAX"]) / 2
PVAll["P_GEN_Norm"] = PVAll["P_GEN"]
PVAll.index = pd.to_datetime(PVAll.index)

PVOutput_BySiteName = {}  # To contain PV output per site (kW and normalised)
PV = pd.Series()  # to contain the combined normalised output of all sites

Site_Names = list(PVAll["Substation"].unique())

# PV Capacities. Apparent capacities from the London datastore dataset notes (word doc)
PVCapacities = pd.Series([3, 0.5, 3.5, 3, 4, 0.45], index=PVAll["Substation"].unique())

# PV output is normalised resampled to half hourly then stored in a dataframe by site
for item in Site_Names:
    PVOutput_BySiteName[item] = pd.DataFrame()
    PVAll["P_GEN_Norm"][PVAll["Substation"] == item] = (
        PVAll["P_GEN"][PVAll["Substation"] == item] / PVCapacities[item]
    )
    PVOutput_BySiteName[item]["P_kW"] = PVAll["P_GEN"][PVAll["Substation"] == item]
    PVOutput_BySiteName[item]["P_Norm"] = PVAll["P_GEN_Norm"][
        PVAll["Substation"] == item
    ]
    PVOutput_BySiteName[item] = PVOutput_BySiteName[item].resample("30Min")
    PVOutput_BySiteName[item] = PVOutput_BySiteName[item].interpolate(
        method="linear", limit=1
    )
    PVOutput_BySiteName[item][PVOutput_BySiteName[item] < 0.001] = 0
    PVOutput_BySiteName[item] = PVOutput_BySiteName[item].fillna(0)
    PV = PV.append(PVOutput_BySiteName[item]["P_Norm"])

pickle_out = open("Pickle/PV_BySiteName.pickle", "wb")
pickle.dump(PVOutput_BySiteName, pickle_out)

# ------------------------ Normalise PV Data by capacity---------------------#
# To create seasonal distributions, all sites are combined and normalised

PVS = {}
PVS["WintDists"] = PV[(PV.index.month == 12) | (PV.index.month <= 2)]  # Dec-Feb
PVS["SpringDists"] = PV[(PV.index.month >= 3) & (PV.index.month <= 5)]  # Mar-May
PVS["SummerDists"] = PV[(PV.index.month >= 6) & (PV.index.month <= 8)]  # Jun-Aug
PVS["AutumnDists"] = PV[(PV.index.month >= 9) & (PV.index.month <= 11)]  # Sept-Nov

PVS["WintDists"] = PV[(PV.index.month == 12) | (PV.index.month <= 2)]  # Dec-Feb
PVS["SpringDists"] = PV[(PV.index.month >= 3) & (PV.index.month <= 5)]  # Mar-May
PVS["SummerDists"] = PV[(PV.index.month >= 6) & (PV.index.month <= 8)]  # Jun-Aug
PVS["AutumnDists"] = PV[(PV.index.month >= 9) & (PV.index.month <= 11)]

# Converting the data from a single column to rows of 48 hours of Data
#'Newdists' contains seasonal normalised output for all sites combined
Dists = {}
Distkeys = ["WintDists", "SpringDists", "SummerDists", "AutumnDists"]
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


# ------------------ Visualisation of the Data ---------------------------

# By site
n = 0
colors = ["#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
for item in PVOutput_BySiteName:
    plt.figure(item)
    plt.scatter(
        PVOutput_BySiteName[item]["P_kW"].index,
        PVOutput_BySiteName[item]["P_kW"],
        s=0.5,
        c=colors[n],
    )
    plt.ylabel("Output(kW)")
    n = n + 1

# By Season
for item in NewDists:
    plt.figure(item)
    for i in NewDists[item].index:
        plt.plot(NewDists[item].iloc[i], linewidth=0.1)
    plt.ylabel("Output(fraction of capacity)")
    n = n + 1

qrts = {}
for item in NewDists:
    qrts[item] = {}
    qrts[item]["q1"] = np.empty(1)
    qrts[item]["q2"] = np.empty(1)
    qrts[item]["q3"] = np.empty(1)
    qrts[item]["max"] = np.empty(1)
    qrts[item]["mean"] = np.empty(1)
    for i in NewDists[item]:
        qrts[item]["q1"] = np.append(qrts[item]["q1"], NewDists[item][i].quantile(0.25))
        qrts[item]["q2"] = np.append(qrts[item]["q2"], NewDists[item][i].quantile(0.5))
        qrts[item]["q3"] = np.append(qrts[item]["q3"], NewDists[item][i].quantile(0.75))
        #        qrts[item]['max']=np.append(qrts[item]['max'],(NewDists[item][i].quantile(0.75)+((NewDists[item][i].quantile(0.75)-NewDists[item][i].quantile(0.25))*1.5)))
        qrts[item]["max"] = np.append(qrts[item]["max"], NewDists[item][i].max())
        qrts[item]["mean"] = np.append(qrts[item]["mean"], NewDists[item][i].mean())

    qrts[item]["q1"] = np.delete(qrts[item]["q1"], 0)
    qrts[item]["q2"] = np.delete(qrts[item]["q2"], 0)
    qrts[item]["q3"] = np.delete(qrts[item]["q3"], 0)
    qrts[item]["max"] = np.delete(qrts[item]["max"], 0)
    qrts[item]["mean"] = np.delete(qrts[item]["mean"], 0)

style = ["-", "-", "-", "-", "--"]
colors = ["#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
for item in qrts:
    n = 0
    plt.figure(item)
    for z in qrts[item]:
        plt.plot(
            qrts[item][z], color=colors[n], linewidth=1.8, label=z, linestyle=style[n]
        )
        n = n + 1
    plt.legend()