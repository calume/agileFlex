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

The script creates 4 pickle files with the data processed:
    
- "SM_DataFrame.pickle" - Smart meter raw data for 187 Smart meters (subset of the 5,500 LCL customers).Timestamped

- "SM_Summary.pickle" - Summary of Acorn Group, Date Ranges and Means/Peaks for each household

- 'SM_DistsByAcorn_NH' Costumers by acorn group with overnight heating demand removed

- "SM_Consolidated_NH.pickle" - Customers are combined into Seasonal (and weekday/weekend) daily profiles by ACorn Group, Heating demand removed

@author: Calum Edmunds
"""

import pandas as pd
import pickle
import numpy as np
import matplotlib.pyplot as plt
import datetime
import os

# --------------------------- Create SM Data Pickle -------------------


startdate = datetime.date(2013, 11, 7)
enddate = datetime.date(2014, 10, 3)
delta = datetime.timedelta(hours=0.5)

dt = pd.date_range(startdate, enddate, freq=delta)

# Get list of Smart Meter IDs that are to be stored
def SmartIDs():
    path = "Profiles/SM"
    IDs = []
    for f in os.listdir(path):
        SM_RawFile = pd.read_csv(
            path + "/" + f,
            names=["ID", "Tar", "Date", "kWh", "A", "Group"],
            skiprows=1,
        )

        print(f)
        for i in SM_RawFile["ID"].unique():
            IDs.append(i[-4:])
    return IDs


# This function takes in the raw smart meter data and dumps in a pickle file
# Condenses all timeseries into single dataframe


def SMCondensed():
    IDs = SmartIDs()
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
        ],
    )

    SM_DataFrame = pd.DataFrame(index=dt)
    path = "Profiles/SM"

    for f in os.listdir(path):
        SM_RawFile = pd.read_csv(
            path + "/" + f,
            names=["ID", "Tar", "Date", "kWh", "A", "Group"],
            skiprows=1,
        )

        print(f)
        for i in SM_RawFile["ID"].unique():
            SM_Individual = SM_RawFile[SM_RawFile["ID"] == i]
            SM_Individual["Date"] = pd.to_datetime(
                SM_Individual["Date"], format="%Y/%m/%d %H:%M:%S"
            )
            z = i[-4:]
            print(i)
            SM_Summary["AcornGroup"][z] = SM_Individual["Group"].iloc[0]
            SM_Summary["MinDate"][z] = SM_Individual["Date"].min()
            SM_Summary["MaxDate"][z] = SM_Individual["Date"].max()
            SM_Summary["Days"][z] = (
                SM_Individual["Date"].max() - SM_Individual["Date"].min()
            ).days
            SM_Summary["Tariff"][z] = SM_Individual["Tar"].unique()
            SM_Summary["PeakDemandkW"][z] = SM_Individual["kWh"].max() * 2
            SM_Summary["DemandkWh/Day"][z] = (
                SM_Individual["kWh"].sum() / SM_Summary["Days"][z]
            )
            SM_Summary["AvDemandkW"][z] = (SM_Individual["kWh"] * 2).mean()
            if len(SM_Individual) > 0:
                SM_Stripped = SM_Individual["kWh"].replace("Null", 0).astype(float) * 2
                SM_Stripped.index = pd.to_datetime(
                    SM_Individual["Date"], format="%Y/%m/%d %H:%M:%S"
                )
                SM_Stripped.name = i[-4:]
                SM_Stripped = SM_Stripped[~SM_Stripped.index.duplicated()]
                SM_DataFrame = pd.concat(
                    [SM_DataFrame, SM_Stripped], axis=1, join="outer", sort=False
                )
    SM_Summary[["PeakDemandkW", "DemandkWh/Day", "Days", "AvDemandkW"]] = SM_Summary[
        ["PeakDemandkW", "DemandkWh/Day", "Days", "AvDemandkW"]
    ].astype(float)
    SM_Summary.index = SM_Summary.index.astype(int)
    SM_Summary = SM_Summary.sort_index(axis=0)
    SM_Summary = SM_Summary[~SM_Summary.index.duplicated()]
    SM_DataFrame.columns = SM_DataFrame.columns.astype(int)
    SM_DataFrame = SM_DataFrame.sort_index(axis=1)
    SM_DataFrame = SM_DataFrame.loc[:, ~SM_DataFrame.columns.duplicated()]
    SM_DataFrame = SM_DataFrame.resample("30T").mean()

    pickle_out = open("../../Data/SM_DataFrame.pickle", "wb")
    pickle.dump(SM_DataFrame, pickle_out)
    pickle_out.close()

    pickle_out = open("../../Data/SM_Summary.pickle", "wb")
    pickle.dump(SM_Summary, pickle_out)
    pickle_out.close()


# This function prints summary data for the customers


def generate_summaryData():
    pickle_in = open("../../Data/SM_Summary.pickle", "rb")
    SM_Summary = pickle.load(pickle_in)

    print(round(SM_Summary.groupby(["AcornGroup"]).mean(), 2))
    for i in SM_Summary["AcornGroup"].unique():
        print(i)
        print(sum(SM_Summary["AcornGroup"] == i))


###----------------------------- Converting to Daily Profiles ------------------------
pick_in = open("../../Data/SM_Summary.pickle", "rb")
SM_Summary = pickle.load(pick_in)
SM_Summary = SM_Summary[~SM_Summary.index.duplicated()]
SM_Summary.index = SM_Summary.index.astype(int)
SM_Summary = SM_Summary.sort_index(axis=0)

pick_in = open("../../Data/SM_DataFrame.pickle", "rb")
SM_DataFrame = pickle.load(pick_in)
SM_DataFrame = SM_DataFrame.resample("30T").mean()
SM_DataFrame = SM_DataFrame.loc[:, ~SM_DataFrame.columns.duplicated()]


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
AcornGroup = ["Adversity", "Comfortable", "Affluent"]
times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
elexon_class1 = pd.read_excel(
    "Profiles/Average_Profiling_data_Elexon.xlsx", sheet_name="class1", index_col=0
)
elexon_class2 = pd.read_excel(
    "Profiles/Average_Profiling_data_Elexon.xlsx", sheet_name="class2", index_col=0
)

# This function categorises the data by Acorn Group and by Season
def DataFramebySeason(SM_DataFrame, SM_Summary, smkeys, AcornGroup):
    SM_ByAcorn = {}

    for i in AcornGroup:
        SM_ByAcorn[i] = {}
        Acorn_Cols = list(SM_Summary["AcornGroup"][SM_Summary["AcornGroup"] == i].index)
        # Acorn_Cols=sorted(list(map(int,Acorn_Cols)))
        Locs = []
        for z in Acorn_Cols:
            Locs.append(SM_DataFrame.columns.get_loc(z))
        print(len(Acorn_Cols))
        Winter = SM_DataFrame.iloc[:, Locs][
            (SM_DataFrame.index.month == 12) | (SM_DataFrame.index.month <= 2)
        ]  # Dec-Feb
        Spring = SM_DataFrame.iloc[:, Locs][
            (SM_DataFrame.index.month >= 3) & (SM_DataFrame.index.month <= 5)
        ]  # Mar-May
        Summer = SM_DataFrame.iloc[:, Locs][
            (SM_DataFrame.index.month >= 6) & (SM_DataFrame.index.month <= 8)
        ]  # Jun-Aug
        Autumn = SM_DataFrame.iloc[:, Locs][
            (SM_DataFrame.index.month >= 9) & (SM_DataFrame.index.month <= 11)
        ]  # Sept-Nov
        print(len(Winter.columns))
        ### Wkday/Wkend########

        SM_ByAcorn[i]["WinterWknd"] = Winter[
            (Winter.index.weekday >= 5) & (Winter.index.weekday <= 6)
        ]
        SM_ByAcorn[i]["WinterWkd"] = Winter[
            (Winter.index.weekday >= 0) & (Winter.index.weekday <= 4)
        ]
        SM_ByAcorn[i]["SpringWknd"] = Spring[
            (Spring.index.weekday >= 5) & (Spring.index.weekday <= 6)
        ]
        SM_ByAcorn[i]["SpringWkd"] = Spring[
            (Spring.index.weekday >= 0) & (Spring.index.weekday <= 4)
        ]

        SM_ByAcorn[i]["SummerWknd"] = Summer[
            (Summer.index.weekday >= 5) & (Summer.index.weekday <= 6)
        ]
        SM_ByAcorn[i]["SummerWkd"] = Summer[
            (Summer.index.weekday >= 0) & (Summer.index.weekday <= 4)
        ]

        SM_ByAcorn[i]["AutumnWknd"] = Autumn[
            (Autumn.index.weekday >= 5) & (Autumn.index.weekday <= 6)
        ]
        SM_ByAcorn[i]["AutumnWkd"] = Autumn[
            (Autumn.index.weekday >= 0) & (Autumn.index.weekday <= 4)
        ]

    return SM_ByAcorn


# DataFramebySeason(SM_DataFrame, SM_Summary, smkeys, AcornGroup)
# pickle_out = open("../../Data/SM_Summary.pickle", "wb")
# pickle.dump(SM_Summary, pickle_out)
# pickle_out.close()


# -------- Converting the data from a single column to rows of 48 hours of Data
# Daily profiles are created by Smartmeter categorised Acorn and Season
def profilesBySM(SM_ByAcorn):
    SM_DistsByAcorn = {}
    for i in AcornGroup:
        SM_DistsByAcorn[i] = {}
        for z in smkeys:
            SM_ByAcorn[i][z] = SM_ByAcorn[i][z].loc[
                :, ~SM_ByAcorn[i][z].columns.duplicated()
            ]
            print(z)
            SM_DistsByAcorn[i][z] = {}
            for c in SM_ByAcorn[i][z]:
                n = 0
                print(c)
                SM_DistsByAcorn[i][z][c] = pd.DataFrame(
                    index=range(0, 20000), columns=range(0, 48)
                )
                for d in range(0, int(len(SM_ByAcorn[i][z][c]) / 48)):
                    SM_DistsByAcorn[i][z][c].iloc[n] = (
                        SM_ByAcorn[i][z][c]
                        .iloc[48 * d : 48 * d + 48]
                        .values.astype(float)
                    )
                    # print(SM_ByAcorn[i][z][c].iloc[48*d:48*d+48].index.min())
                    # print(SM_ByAcorn[i][z][c].iloc[48*d:48*d+48].index.max())
                    n = n + 1
                SM_DistsByAcorn[i][z][c] = SM_DistsByAcorn[i][z][c][
                    SM_DistsByAcorn[i][z][c].sum(axis=1) > 0
                ]
                SM_DistsByAcorn[i][z][c].reset_index(drop=True, inplace=True)
    return SM_DistsByAcorn


# ------------------- Data Visualisation -----------------------------#
def SM_Visualise(SM_DistsConsolidated, smkeys, times):

    plt.figure(1)

    Seasons = ["Winter", "Spring", "Summer", "Autumn"]
    n = 1
    r = 0
    for item in smkeys:
        plt.subplot(420 + n)
        plt.plot(elexon_class1[item].values, linestyle="--", label="Elexon Class 1")
        plt.plot(elexon_class2[item].values, linestyle=":", label="Elexon Class 2")
        plt.plot(
            SM_DistsConsolidated["Affluent"][item].mean(),
            color="#33FF92",
            label="Affluent",
        )
        plt.plot(
            SM_DistsConsolidated["Comfortable"][item].mean(),
            color="#17becf",
            label="Comfortable",
        )
        plt.plot(
            SM_DistsConsolidated["Adversity"][item].mean(),
            color="#FA8072",
            label="Adversity",
        )
        plt.xlabel("Settlement Period (half hourly)", fontsize=8)
        # plt.ylabel("Demand (kW)", fontsize=8)
        plt.xlim([0, 47])
        plt.ylim([0, 1.5])
        # plt.yticks([0,0.5,1,1.5,2])
        plt.yticks([0, 0.5, 1, 1.5])
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


## ---------- Removing heating loads
# pick_in = open("../../Data/SM_DistsByAcorn.pickle", "rb")
# SM_DistsByAcorn = pickle.load(pick_in)


def Heaters(SM_DataFrame):
    Heaters = (SM_DataFrame[SM_DataFrame.index.hour == 0] > 4).sum() > 1
    Heaters = Heaters[Heaters]
    HeatersSort = (
        SM_DataFrame[SM_DataFrame[Heaters.index].index.hour == 0].sum()
        + SM_DataFrame[SM_DataFrame[Heaters.index].index.hour == 1].sum()
    ).sort_values()
    ToRemove = HeatersSort[HeatersSort > 2000].index
    return ToRemove, HeatersSort


# ----------------- Visualise Heat Loads ----------
def HeatVisuals(times, SM_DistsByAcorn, SM_DataFrame, HeatersSort):
    n = 1
    for z in HeatersSort[-4:].index:
        plt.subplot(420 + n)
        plt.xlim([0, 47])
        plt.ylim([0, 12])
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(range(0, 47, 8), times)
        if n == 1:
            plt.title("Weekend (Sat-Sun)", fontsize=9, fontweight="bold")
        for i in SM_DistsByAcorn["Affluent"]["WinterWknd"][z].index:
            plt.plot(SM_DistsByAcorn["Affluent"]["WinterWknd"][z].loc[i], linewidth=0.5)
        plt.plot(
            SM_DistsByAcorn["Affluent"]["WinterWknd"][z].mean(),
            linestyle="--",
            color="black",
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
        for i in SM_DistsByAcorn["Affluent"]["WinterWkd"][z].index:
            plt.plot(SM_DistsByAcorn["Affluent"]["WinterWkd"][z].loc[i], linewidth=0.5)
        plt.plot(
            SM_DistsByAcorn["Affluent"]["WinterWkd"][z].mean(),
            linestyle="--",
            color="black",
        )
        if n == 2:
            plt.title("Week Day (Mon-Fri)", fontsize=9, fontweight="bold")
        n = n + 1


# ------------ Rerun for dropped columns due to Heating
def removeHeating(SM_DataFrame, SM_Summary, ToRemove):
    SM_DataFrame_NH = SM_DataFrame.drop(columns=ToRemove)
    SM_Summary_NH = SM_Summary.drop(index=ToRemove)
    SM_Summary_NH = SM_Summary_NH[~SM_Summary_NH.index.duplicated()]
    SM_ByAcorn_NH = DataFramebySeason(
        SM_DataFrame_NH, SM_Summary_NH, smkeys, AcornGroup
    )

    return SM_Summary_NH, SM_DataFrame_NH, SM_ByAcorn_NH


# Create new DF with heat demand removed
def nowdf(SM_DataFrame):
    ToRemove, HeatersSort = Heaters(SM_DataFrame)
    SM_Summary_NH, SM_DataFrame_NH, SM_ByAcorn_NH = removeHeating(
        SM_DataFrame, SM_Summary, ToRemove
    )
    # ToRemove_NH, HeatersSort_NH = Heaters(SM_DataFrame_NH)
    return SM_Summary_NH, SM_DataFrame_NH, SM_ByAcorn_NH


# Convert from Individual SMs by Acorn to consolidated by ACorn
def ConsolidatefromAcornSMs(SM_DistsByAcorn_NH):
    SM_DistsConsolidated = {}
    for i in AcornGroup:
        SM_DistsConsolidated[i] = {}
        for z in smkeys:
            DFkeys = list(SM_DistsByAcorn_NH[i][z].keys())
            SM_DistsConsolidated[i][z] = SM_DistsByAcorn_NH[i][z][DFkeys[0]].astype(
                float
            )
            for k in DFkeys[1:]:
                SM_DistsConsolidated[i][z] = SM_DistsConsolidated[i][z].append(
                    SM_DistsByAcorn_NH[i][z][k].astype(float), ignore_index=True
                )
    return SM_DistsConsolidated


def createnewDailyByAcorn():
    SM_ByAcorn = DataFramebySeason(SM_DataFrame, SM_Summary, smkeys, AcornGroup)
    SM_DistsByAcorn = profilesBySM(SM_ByAcorn)
    pickle_out = open("../../Data/SM_DistsByAcorn.pickle", "wb")
    pickle.dump(SM_DistsByAcorn, pickle_out)
    pickle_out.close()


##- Plus 1 year to SM timestamps to line up with PV and HP
SM_DataFrame.index = SM_DataFrame.index + datetime.timedelta(days=364)

SM_Summary_NH, SM_DataFrame_NH, SM_ByAcorn_NH = nowdf(SM_DataFrame)

pickle_out = open("../../Data/SM_DataFrame_byAcorn_NH.pickle", "wb")
pickle.dump(SM_ByAcorn_NH, pickle_out)
pickle_out.close()
