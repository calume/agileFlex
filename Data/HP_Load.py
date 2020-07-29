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

HP_Summary = pd.read_excel("../../Data/RHPP-Beis-Summary.xlsx", sheet_name=0)
HP_Summary_ASHP = HP_Summary[HP_Summary["Heat pump Type"] == "ASHP"]
HP_Summary_ASHP_Domestic = HP_Summary_ASHP["RHPP Name"]#[
#    HP_Summary_ASHP["Site Type"] == "Domestic"
#]

smkeys = [
    "WinterWknd",
    "WinterWkd",
    "SpringWknd",
    "SpringWkd",
    "SummerWknd",
    "SummerWkd",
    "AutumnWknd",
    "AutumnWkd",
]
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

path = "../../Data/heatpump/HP"
IDs = []
for f in os.listdir(path):
    IDs.append(f[-8:-4])
    print(f)

startdate = date(2013, 12, 1)
enddate = date(2015, 3, 1)
delta = timedelta(hours=0.5)
dt = pd.date_range(startdate, enddate, freq=delta)


# This function creates a DataFrame with all Domestic ASHP
#def createDataFrame(IDs):
hist30 = []
path = "../../Data/heatpump/HP/processed_rhpp"
HP_DataFrame = pd.DataFrame(index=dt)
for f in IDs:
    print(f, end=": ")
    HP_RawFile = pd.read_csv(
    path + f + ".csv",
    index_col=["Matlab_time"],
    usecols=["Matlab_time", "Year", "Month", "Ehp", "Edhw"])

        
    # hist2.append(round(((HP_RawFile['Ehp']+HP_RawFile['Edhw'])/1000*30).max(),1))
    # hist30.append(round(HP_DataFrame[f].max()))
    out_datetime = pd.Series(index=range(0, len(HP_RawFile.index)))
    for i in range(0, len(HP_RawFile.index)):
        days = HP_RawFile.index.values[i] % 1
        hours = days % 1 * 24
        minutes = hours % 1 * 60

        out_date = (
            date.fromordinal(int(HP_RawFile.index.values[i]))
            + timedelta(days=days)
            - timedelta(days=366)
        )

        out_datetime[i] = (
            datetime.fromisoformat(str(out_date))
            + timedelta(hours=int(hours))
            + timedelta(minutes=int(minutes))
        )

    HP_RawFile.index = out_datetime
    HP_RawFile["HPTotDem"] = HP_RawFile["Ehp"] + HP_RawFile["Edhw"]

    HP_Out = HP_RawFile["HPTotDem"].resample("2T").sum() / 1000 / 0.5
    HP_DataFrame = pd.concat(
        [HP_DataFrame, HP_Out], axis=1, join="outer", sort=False
    )
    
HP_DataFrame.columns = IDs
HP_reduced = HP_DataFrame.count()>(len(dt)*0.7)
HP_reduced = HP_reduced[HP_reduced]
HP_DataFrame=HP_DataFrame[HP_reduced.index]
    
pickle_out = open("../../Data/HP_DataFrame_2mins.pickle", "wb")
pickle.dump(HP_DataFrame, pickle_out)
pickle_out.close()

#createDataFrame(IDs)

#pick_in = open("../../Data/HP_DataFrame.pickle", "rb")
#HP_DataFrame = pickle.load(pick_in)

# This function plots a histogram of heat pump maximum output
def HPhisto():
    histo30, binz30 = np.histogram(hist30, bins=range(0, int(max(hist30)), 1))
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(binz30[:-1], histo30, width=1, align="edge")
    ax.set_xlim(left=0)  # ,right=5000)
    ax.set_ylabel("Number of households", fontsize=9)
    ax.set_xlabel("Peak Heat Pump Demand / Capacity (kW)", fontsize=9)
    for t in ax.xaxis.get_majorticklabels():
        t.set_fontsize(9)
    for t in ax.yaxis.get_majorticklabels():
        t.set_fontsize(9)
    plt.tight_layout()


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


#HP_BySeason = DataFramebySeason(HP_DataFrame, smkeys)
#pickle_out = open("../../Data/HP_DataFrameBySeason.pickle", "wb")
#pickle.dump(HP_BySeason, pickle_out)
#pickle_out.close()

#####- Generate Daily HP demand profiles by season, timestamp removed
def profilesBySM(HP_BySeason):
    HP_DistsBySeason = {}
    for z in smkeys:
        HP_BySeason[z] = HP_BySeason[z].loc[:, ~HP_BySeason[z].columns.duplicated()]
        print(z)
        HP_DistsBySeason[z] = {}
        for c in HP_BySeason[z]:
            n = 0
            print(c)
            HP_DistsBySeason[z][c] = pd.DataFrame(
                index=range(0, 20000), columns=range(0, 48)
            )
            for d in range(0, int(len(HP_BySeason[z][c]) / 48)):
                HP_DistsBySeason[z][c].iloc[n] = (
                    HP_BySeason[z][c].iloc[48 * d : 48 * d + 48].values.astype(float)
                )
                print(HP_BySeason[z][c].iloc[48 * d : 48 * d + 48].index.min())
                print(HP_BySeason[z][c].iloc[48 * d : 48 * d + 48].index.max())
                n = n + 1
            HP_DistsBySeason[z][c] = HP_DistsBySeason[z][c][
                HP_DistsBySeason[z][c].sum(axis=1) > 0
            ]
            HP_DistsBySeason[z][c].reset_index(drop=True, inplace=True)
    return HP_DistsBySeason


# pick_in = open("../../Data/HP_DistsBySeason.pickle", "rb")
# HP_DistsBySeason = pickle.load(pick_in)


def HeatVisuals(times, HP_DistsBySeason):
    n = 1
    HPKeys = list(HP_DistsBySeason["WinterWkd"].keys())
    for z in HPKeys[-4:]:
        plt.subplot(420 + n)
        plt.xlim([0, 47])
        plt.ylim([0, 12])
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(range(0, 47, 8), times)
        if n == 1:
            plt.title("Weekend (Sat-Sun)", fontsize=9, fontweight="bold")
        for i in HP_DistsBySeason["WinterWknd"][z].index:
            plt.plot(HP_DistsBySeason["WinterWknd"][z].loc[i], linewidth=0.5)
        plt.plot(
            HP_DistsBySeason["WinterWknd"][z].mean(), linestyle="--", color="black"
        )
        n = n + 1
        if n % 2 == 0:
            plt.ylabel(z, rotation=25, fontsize=9, fontweight="bold")
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


# HeatVisuals(times,HP_DistsBySeason)


def ConsolidatefromAcornSMs(HP_DistsBySeason):
    HP_DistsConsolidated = {}
    for z in smkeys:
        DFkeys = list(HP_DistsBySeason[z].keys())
        HP_DistsConsolidated[z] = HP_DistsBySeason[z][DFkeys[0]].astype(float)
        for k in DFkeys[1:]:
            HP_DistsConsolidated[z] = HP_DistsConsolidated[z].append(
                HP_DistsBySeason[z][k].astype(float), ignore_index=True
            )
    return HP_DistsConsolidated


# HP_DistsConsolidated = ConsolidatefromAcornSMs(HP_DistsBySeason)
#
# pickle_out = open("../../Data/HP_DistsConsolidated.pickle", "wb")
# pickle.dump(HP_DistsConsolidated, pickle_out)
# pickle_out.close()

# ------------------- Data Visualisation -----------------------------#
def SM_Visualise(HP_DistsConsolidated, smkeys, times):

    plt.figure(1)

    Seasons = ["Winter", "Spring", "Summer", "Autumn"]
    n = 1
    r = 0
    for item in smkeys:
        plt.subplot(420 + n)
        for z in HP_DistsConsolidated[item].index[1:500]:
            plt.plot(HP_DistsConsolidated[item].iloc[z], linewidth=0.3)
        plt.plot(
            HP_DistsConsolidated[item].mean(),
            color="black",
            label="Mean",
            linestyle="--",
        )
        plt.plot(
            HP_DistsConsolidated[item].quantile(0.50),
            color="blue",
            label="Q50",
            linestyle="--",
        )
        plt.plot(
            HP_DistsConsolidated[item].quantile(0.95),
            color="yellow",
            label="Q95",
            linestyle="--",
        )
        # plt.ylabel("Demand (kW)", fontsize=8)
        plt.xlim([0, 47])
        plt.ylim([0, 5])
        # plt.yticks([0,0.5,1,1.5])
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        if n == 1:
            plt.legend(fontsize=8)
            plt.title("Weekend (Sat-Sun)", fontsize=9, fontweight="bold")
        if n == 2:
            plt.title("Week Day (Mon-Fri)", fontsize=9, fontweight="bold")
        if n % 2 == 1:
            plt.ylabel(Seasons[r], rotation=15, fontsize=9, fontweight="bold")
            r = r + 1
        n = n + 1
        plt.xticks(range(0, 47, 8), times)
        plt.tight_layout()


# SM_Visualise(HP_DistsConsolidated, smkeys, times)
