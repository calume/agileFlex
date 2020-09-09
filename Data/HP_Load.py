# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 11:21:14 2019

Script to process Heat Pump (HP) data for the AGILE Model

@author: Calum Edmunds
"""

import pandas as pd
import pickle
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta, date
import os

# Get list of Heat Pump IDs that are to be stored from the BEIS summary
# Only Domestic Air Source Heat Pumps are to be considered

# HP_Summary = pd.read_excel("../../Data/RHPP-Beis-Summary.xlsx", sheet_name=0)
# HP_Summary_ASHP = HP_Summary[HP_Summary["Heat pump Type"] == "ASHP"]
# HP_Summary_ASHP_Domestic = HP_Summary_ASHP["RHPP Name"]#[
# #    HP_Summary_ASHP["Site Type"] == "Domestic"
# #]

# smkeys = [
#     "WinterWknd",
#     "WinterWkd",
#     "SpringWknd",
#     "SpringWkd",
#     "SummerWknd",
#     "SummerWkd",
#     "AutumnWknd",
#     "AutumnWkd",
# ]
times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]


# This function returns a list of Heat Domestic ASHP for collating
#def getlist():
#    lst = []
#    for f in range(0, len(HP_Summary_ASHP_Domestic)):
#        try:
#            lst.append(HP_Summary_ASHP_Domestic.iloc[f][-4:])
#            print(f)
#        except:
#            print()
#    return lst

# path = "../../Data/heatpump/HP"
# IDs = []
# for f in os.listdir(path):
#     IDs.append(f[-8:-4])
#     print(f)

startdate = date(2013, 12, 1)
enddate = date(2014, 2, 27)
delta = timedelta(minutes=10)
dt = pd.date_range(startdate, enddate, freq=delta)


# # This function creates a DataFrame with all Domestic ASHP
# #def createDataFrame(IDs):
# hist30 = []
# path = "../../Data/heatpump/HP/processed_rhpp"
# HP_DataFrame = pd.DataFrame(index=dt)
# for f in IDs:
#     print(f, end=": ")
#     HP_RawFile = pd.read_csv(
#     path + f + ".csv",
#     index_col=["Matlab_time"],
#     usecols=["Matlab_time", "Year", "Month","Day","Hour","Minute", "Ehp", "Edhw"])
#     HP_index=[]
#     for i in range(0, len(HP_RawFile.index)):
#         HP_index.append(datetime(HP_RawFile['Year'].iloc[i],HP_RawFile['Month'].iloc[i],HP_RawFile['Day'].iloc[i],HP_RawFile['Hour'].iloc[i],HP_RawFile['Minute'].iloc[i]))    
#     # hist2.append(round(((HP_RawFile['Ehp']+HP_RawFile['Edhw'])/1000*30).max(),1))
#     # hist30.append(round(HP_DataFrame[f].max()))
    
#     HP_RawFile.index = HP_index
#     HP_RawFile["HPTotDem"] = HP_RawFile["Ehp"] + HP_RawFile["Edhw"]

# #    HP_Out = HP_RawFile["HPTotDem"] / 1000 *30   # Convert Wh/2mins into kW
#     HP_Out = HP_RawFile["HPTotDem"].resample('10T').max() / 1000 *30   # Convert Wh/10mins into kW
#     HP_DataFrame = pd.concat(
#         [HP_DataFrame, HP_Out], axis=1, join="outer", sort=False
#     )

# HP_DataFrame.columns = IDs
# HP_DataFrame=HP_DataFrame.loc[dt]

# HP_reduced = HP_DataFrame.count()>(len(dt)*0.4)
# HP_reduced = HP_reduced[HP_reduced]
# HP_DataFrame=HP_DataFrame[HP_reduced.index]

# pickle_out = open("../../Data/HP_DataFrame_10mins_max.pickle", "wb")
# pickle.dump(HP_DataFrame, pickle_out, protocol=pickle.HIGHEST_PROTOCOL)
# pickle_out.close()


#pickle_out = open("../../Data/HP_DataFrame_2mins.pickle", "wb")
#pickle.dump(HP_DataFrame, pickle_out)
#pickle_out.close()

#HP_DataFrame_hh_max=HP_DataFrame.resample("30T").max()
#
#pickle_out = open("../../Data/HP_DataFrame_hh_max.pickle", "wb")
#pickle.dump(HP_DataFrame_hh_max, pickle_out)
#pickle_out.close()
#
#HP_DataFrame_hh_mean=HP_DataFrame.resample("30T").mean()
#
#pickle_out = open("../../Data/HP_DataFrame_hh_mean.pickle", "wb")
#pickle.dump(HP_DataFrame_hh_mean, pickle_out)
#pickle_out.close()

#createDataFrame(IDs)

pick_in = open("../../Data/HP_DataFrame_10mins_pad.pickle", "rb")
HP_DataFrame = pickle.load(pick_in)

HP_reduced = HP_DataFrame.reindex(dt.tolist()).count()> (0.9*len(dt))

HP_reduced = HP_reduced[HP_reduced]

HP_DataFrame = HP_DataFrame[HP_reduced.index].loc[dt]

HP_reduced = HP_DataFrame.sum()>0
HP_reduced = HP_reduced[HP_reduced]
HP_DataFrame = HP_DataFrame[HP_reduced.index].loc[dt]

pickle_out = open("../../Data/HP_DataFrame_10mins_pad.pickle", "wb")
pickle.dump(HP_DataFrame, pickle_out)
pickle_out.close()

tsamp=144

# This function plots a histogram of heat pump maximum output

#####- Generate Daily HP demand profiles by season, timestamp removed
#def profilesBySM(HP_BySeason):


# HP_DailyDataFrame={}
# for c in HP_DataFrame.columns:
#     n = 0
#     print(c)
#     dailyrange = range(0, len(dt), tsamp)
#     HP_DailyDataFrame[c] = pd.DataFrame(
#         index=dt[dailyrange], columns=range(0, tsamp)
#     )
#     for d in range(0, int(len(HP_DataFrame[c]) / tsamp)):
#         HP_DailyDataFrame[c].iloc[n] = (
#             HP_DataFrame[c].iloc[tsamp * d : tsamp * d + tsamp].values.astype(float)
#         )
#         # print(HP_DataFrame[c].iloc[tsamp * d : tsamp * d + tsamp].index.min())
#         # print(HP_DataFrame[c].iloc[tsamp * d : tsamp * d + tsamp].index.max())
#         n = n + 1
#     HP_DailyDataFrame[c] = HP_DailyDataFrame[c][
#         HP_DailyDataFrame[c].sum(axis=1) > 0
#     ].fillna(0)

# pickle_out = open("../../Data/HP_DailyDataFrame_10min_pad.pickle", "wb")
# pickle.dump(HP_DailyDataFrame, pickle_out)
# pickle_out.close()
#
#pick_in = open("../../Data/HP_DailyDataFrame_10min_pad.pickle", "rb")
#HP_DailyDataFrame = pickle.load(pick_in)
#
#
#HP_DistsConsolidated = {}
#DFkeys = list(HP_DailyDataFrame.keys())
#HP_DistsConsolidated = HP_DailyDataFrame[DFkeys[0]].astype(float)
#for k in DFkeys:
#    HP_DistsConsolidated = HP_DistsConsolidated.append(
#        HP_DailyDataFrame[k].astype(float), ignore_index=True
#    )
#
#pickle_out = open("../../Data/HP_DistsConsolidated_10min_pad.pickle", "wb")
#pickle.dump(HP_DistsConsolidated, pickle_out)
#pickle_out.close()
#
#pick_in = open("../../Data/HP_DistsConsolidated_10min_pad.pickle", "rb")
#HP_DistsConsolidated = pickle.load(pick_in)
#
#
## ------------------- Data Visualisation -----------------------------#
##def SM_Visualise(HP_DistsConsolidated, smkeys, times):
#allmeans=[]
#for z in HP_DailyDataFrame:
#    allmeans.append(HP_DailyDataFrame[z].sum().mean()/6)
#    
## for z in HP_DailyDataFrame:
##     plt.plot(HP_DailyDataFrame[z].mean(), linewidth=0.3)
#    
#plt.plot(
#    HP_DistsConsolidated.mean(),
#    color="black",
#    label="Mean",
#    linestyle="-",
#)
#plt.plot(
#    HP_DistsConsolidated.quantile(0.50),
#    color="blue",
#    label="Q50",
#    linestyle="--",
#)
#plt.plot(
#    HP_DistsConsolidated.quantile(0.95),
#    color="red",
#    label="Q95",
#    linestyle="-.",
#)
#plt.plot(
#    HP_DistsConsolidated.quantile(0.75),
#    color="green",
#    label="Q75",
#    linestyle=":",
#)
#plt.ylabel("10-minutely sampled demand (kW)", fontsize=11)
#plt.xlim([0, tsamp])
#plt.ylim([0, 4])
#plt.grid(linewidth=0.2)
## plt.yticks([0,0.5,1,1.5])
#plt.xticks(fontsize=11)
#plt.yticks(fontsize=11)
#plt.legend(fontsize=11)
#plt.xticks(range(0,tsamp+24,int(tsamp/6)),times)
#plt.tight_layout()
#
#
#histo30, binz30 = np.histogram(allmeans, bins=range(0, int(max(allmeans)), 1))
#fig, ax = plt.subplots(figsize=(5, 4))
#ax.bar(binz30[:-1], histo30, width=1, align="edge")
#ax.set_xlim(left=0,right=50)
#ax.set_ylabel("Number of HPs", fontsize=11)
#ax.set_xlabel("Mean Daily Demand (kWh/day)", fontsize=11)
#for t in ax.xaxis.get_majorticklabels():
#    t.set_fontsize(11)
#for t in ax.yaxis.get_majorticklabels():
#    t.set_fontsize(11)
#plt.tight_layout()

#HP_BySeason = DataFramebySeason(HP_DataFrame, smkeys)
#pickle_out = open("../../Data/HP_DataFrameBySeason.pickle", "wb")
#pickle.dump(HP_BySeason, pickle_out)
#pickle_out.close()


def HeatVisuals(times, HP_DistsBySeason):
    n = 1
    HPKeys = list(HP_DistsBySeason["WinterWkd"].keys())
    for z in HPKeys[-4:]:
        plt.subplot(420 + n)
        plt.xlim([0, 47])
        plt.ylim([0, 12])
        plt.xticks(fontsize=11)
        plt.yticks(fontsize=11)
        plt.xticks(range(0, 47, 8), times)
        if n == 1:
            plt.title("Weekend (Sat-Sun)", fontsize=11, fontweight="bold")
        for i in HP_DistsBySeason["WinterWknd"][z].index:
            plt.plot(HP_DistsBySeason["WinterWknd"][z].loc[i], linewidth=0.5)
        plt.plot(
            HP_DistsBySeason["WinterWknd"][z].mean(), linestyle="--", color="black"
        )
        n = n + 1
        if n % 2 == 0:
            plt.ylabel(z, rotation=25, fontsize=11, fontweight="bold")
        plt.subplot(420 + n)
        plt.xlim([0, 47])
        plt.ylim([0, 12])
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(range(0, 47, 8), times)
        for i in HP_DistsBySeason["WinterWkd"][z].index:
            plt.plot(HP_DistsBySeason["WinterWkd"][z].loc[i], linewidth=0.5)
        plt.plot(HP_DistsBySeason["WinterWkd"][z].mean(), linestyle="--", color="black")
        if n == 2:
            plt.title("Week Day (Mon-Fri)", fontsize=9, fontweight="bold")
        n = n + 1

def DataFramebySeason(HP_DataFrame, smkeys):
    HP_DataFrame = HP_DataFrame.loc[sims_halfhours]
    HP_BySeason = {}
    Winter = HP_DataFrame[
        (HP_DataFrame.index.month == 12) | (HP_DataFrame.index.month <= 2)
    ]  # Dec-Feb
    Spring = HP_DataFrame[
        (HP_DataFrame.index.month >= 3) & (HP_DataFrame.index.month <= 5)
    ]  # Mar-May
    Summer = HP_DataFrame[
        (HP_DataFrame.index.month >= 6) & (HP_DataFrame.index.month <= 8)
    ]  # Jun-Aug
    Autumn = HP_DataFrame[
        (HP_DataFrame.index.month >= 9) & (HP_DataFrame.index.month <= 11)
    ]  # Sept-Nov
    print(len(Winter.columns))
    ### Wkday/Wkend########

    HP_BySeason["WinterWknd"] = Winter[
        (Winter.index.weekday >= 5) & (Winter.index.weekday <= 6)
    ]
    HP_BySeason["WinterWkd"] = Winter[
        (Winter.index.weekday >= 0) & (Winter.index.weekday <= 4)
    ]
    HP_BySeason["SpringWknd"] = Spring[
        (Spring.index.weekday >= 5) & (Spring.index.weekday <= 6)
    ]
    HP_BySeason["SpringWkd"] = Spring[
        (Spring.index.weekday >= 0) & (Spring.index.weekday <= 4)
    ]
    HP_BySeason["SummerWknd"] = Summer[
        (Summer.index.weekday >= 5) & (Summer.index.weekday <= 6)
    ]
    HP_BySeason["SummerWkd"] = Summer[
        (Summer.index.weekday >= 0) & (Summer.index.weekday <= 4)
    ]
    HP_BySeason["AutumnWknd"] = Autumn[
        (Autumn.index.weekday >= 5) & (Autumn.index.weekday <= 6)
    ]
    HP_BySeason["AutumnWkd"] = Autumn[
        (Autumn.index.weekday >= 0) & (Autumn.index.weekday <= 4)
    ]

    return HP_BySeason

# SM_Visualise(HP_DistsConsolidated, smkeys, times)
