# -*- coding: utf-8 -*-
"""
Created on Thu May 02 13:48:06 2019

This python script produces forecasts of output from PV, Smart Meter and 
Heat pump. 

The function 'Forecast' uses persistence forecast using a previous days data
then fits gaussian mixtures to produce a range of probable Day Ahead forecasts that 
can be benchmarked against the persistence forecast.

This can also be done Intraday using the first 10 hours of actual data (i.e. at 10am)
to produce an intraday forecast

@author: Calum Edmunds
"""


######## Importing the OpenDSS Engine  #########
import opendssdirect as dss
import scipy.io
import numpy as np
import pandas as pd
from random import uniform
from random import seed
from opendssdirect.utils import run_command
import os,sys,inspect
pd.options.mode.chained_assignment = None
import timeit
from matplotlib import pyplot as plt
from datetime import datetime, timedelta, date, time
import datetime
import random
import csv
import pickle
from sklearn.metrics import mean_absolute_error

pick_in = open("../../Data/Customer_Summary.pickle", "rb")
SM_DataFrame = pickle.load(pick_in)


###----------------------- Load in Test data Set -------------##########
pick_in = open("../../Data/SM_DataFrame_byAcorn_NH.pickle", "rb")
SM_DataFrame = pickle.load(pick_in)

pick_in = open("../../Data/HP_DataFrame.pickle", "rb")
HP_DataFrame = pickle.load(pick_in)

pick_in = open("../../Data/PV_BySiteName.pickle", "rb")
PV_DataFrame = pickle.load(pick_in)

pick_in = open("../../Data/PV_DistsgmmChosen.pickle", "rb")
PV_DistsgmmChosen = pickle.load(pick_in)

pick_in = open("../../Data/PV_DistsgmmWeights.pickle", "rb")
PV_DistsgmmWeights = pickle.load(pick_in)


## PV Forecasting
# pred is the previous days data using persistence forecasting
# true is the actual output for the day in question.

start_date = date(2014, 7, 3)
end_date = date(2014, 7, 5)

delta_halfhours = timedelta(hours=0.5)
sims_halfhours = pd.date_range(start_date, end_date, freq=delta_halfhours)

def forecasts(pred, true, Forecast_Type):
    if Forecast_Type == "Day Ahead":
        DA_Persistence_NMAE = mean_absolute_error(true, pred)
        # print('Persistence Day Ahead Weighted NMAE: ',round(mae,3))
    else:
        DA_Persistence_NMAE = 0
    if (true.index[0].month == 12) | (true.index[0].month <= 2):  # Dec-Feb
        Season = "WintDists"
    if (true.index[0].month >= 3) & (true.index[0].month <= 5):  # Mar-May
        Season = "SpringDists"
    if (true.index[0].month >= 6) & (true.index[0].month <= 8):  # Jun-Aug
        Season = "SummerDists"
    if (true.index[0].month >= 9) & (true.index[0].month <= 11):  # Sept-Nov
        Season = "AutumnDists"

    ### fit the gaussian mixtures to the persistence forecast depending on season
    gmmMAE_Pred = pd.Series(index=range(0, len(PV_DistsgmmChosen[Season])))

    for i in gmmMAE_Pred.index:
        gmmMAE_Pred[i] = mean_absolute_error(
            pred.values, PV_DistsgmmChosen[Season][i][0 : len(pred)]
        )

    gmmMAE_Pred = gmmMAE_Pred.sort_values()
    ###### Choose Best Fit ##########
    gmmBestFit = PV_DistsgmmChosen[Season][gmmMAE_Pred.index[0]]  # [0:Fits_Nmin]]
    ### NMAE for best fit ###########
    DA_gmm_nmae = mean_absolute_error(true.values, gmmBestFit)

    return gmmBestFit, DA_gmm_nmae, DA_Persistence_NMAE, Season


# --------------------Visualise Forecast--------------------------#

# Find best GMM fit
def visualise_forecast(gmmBestFit, Forecast_Type, Day, DA_gmm_nmae, Persistence_NMAE):
    plt.title(
        "Day " + str(Day + 1) + ", NMAE (%) - gmm: " + str(round(DA_gmm_nmae * 100, 1)),
        fontsize=9,
    )
    if Forecast_Type == "Day Ahead":
        plt.title(
            "Day "
            + str(Day + 1)
            + ", NMAE (%) - gmm: "
            + str(round(DA_gmm_nmae * 100, 1))
            + " Persistence:"
            + str(round(Persistence_NMAE * 100, 1)),
            fontsize=9,
        )
        plt.plot(pred.values, label="Persistence Forecast", linestyle="--")
    plt.plot(gmmBestFit, label="gmm Best Fit")
    plt.plot(true.values, label="Actual", color="black", linestyle=":", linewidth=2)
    times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    plt.xticks(range(0, 47, 8), times, fontsize=8)
    plt.ylim(0, 1)
    plt.yticks(fontsize=8)


# -------------------Do multiple Runs---------------------------#


def multirun():
    ### Date stuff ###
    ### Year #####
    startdate = date(2013, 11, 7)
    enddate = date(2014, 11, 13)
    days = range(0, 365)

    ### Week ###
    # startdate =  date(2014,7,1)
    # enddate   =  date(2014,7,10)
    # days=range(0,8)
    delta = datetime.timedelta(hours=0.5)
    dt = pd.date_range(startdate, enddate, freq=delta)  # datetime steps
    n = 1
    ID_DA_gmm_nmae = pd.Series(index=days)
    DA_DA_gmm_nmae = pd.Series(index=days)
    DA_PersistanceNMAE = pd.Series(index=days)
    DA_gmmBestFit = {}
    ID_gmmBestFit = {}

    DA_mape = pd.DataFrame(index=days, columns=range(0, 48))
    ID_mape = pd.DataFrame(index=days, columns=range(0, 48))
    True_DF = pd.DataFrame(index=days, columns=range(0, 48))
    Seasons = pd.Series(index=days)
    All_DA_Mapes = pd.DataFrame(index=range(len(days) * 48), columns=["DAgmm", "True"])
    a = 0
    for i in days:
        print(i)
        pred = PV_DataFrame["Alverston Close"]["P_Norm"][dt[i * 48 : (i + 1) * 48]]
        true = PV_DataFrame["Alverston Close"]["P_Norm"][
            dt[(i + 1) * 48 : (i + 2) * 48]
        ]
        Forecast_Type = "Day Ahead"
        DA_gmmBestFit[i], DA_DA_gmm_nmae[i], DA_PersistanceNMAE[i], Season = forecasts(
            pred, true, Forecast_Type
        )

        #    plt.figure(Forecast_Type)
        #    plt.subplot(420+n)
        #    visualise_forecast(DA_gmmBestFit[i],'Day Ahead',i,DA_DA_gmm_nmae[i],DA_PersistanceNMAE[i])
        #    if n==1:
        #        plt.legend(fontsize=8)
        #    Forecast_Type='Intraday'
        #    plt.figure(Forecast_Type)
        #    plt.subplot(420+n)
        Intraday_True = true[0:20]
        ID_gmmBestFit[i], ID_DA_gmm_nmae[i], blank, Season = forecasts(
            Intraday_True, true, "Intraday"
        )
        #    visualise_forecast(ID_gmmBestFit[i],'Intraday',i,ID_DA_gmm_nmae[i],0)
        #    if n==1:
        #        plt.legend(fontsize=8)
        #    n=n+1
        Seasons[i] = Season
        for h in range(0, 48):
            True_DF.iloc[i] = true.values
            DA_mape[h][i] = DA_gmmBestFit[i][h] - true[h]
            ID_mape[h][i] = ID_gmmBestFit[i][h] - true[h]
            All_DA_Mapes["DAgmm"][a] = DA_mape[h][i]
            All_DA_Mapes["True"][a] = true[h]
            a = a + 1
    print(
        "Average NMAE. Day ahead Persistence: ",
        round(DA_PersistanceNMAE.mean() * 100, 2),
        "Day Ahead gmm: ",
        round(DA_DA_gmm_nmae.mean() * 100, 2),
        "Intraday gmm: ",
        round(ID_DA_gmm_nmae.mean() * 100, 2),
    )

    # plt.tight_layout()

    Summary = pd.DataFrame(
        index=days, columns=["DA gmm", "Persistence", "ID gmm", "Season"]
    )
    Summary["DA gmm"] = DA_DA_gmm_nmae
    Summary["Persistence"] = DA_PersistanceNMAE
    Summary["ID gmm"] = ID_DA_gmm_nmae
    Summary["Season"] = Seasons
    Summary["Season"] = Summary["Season"].str[:-5]
    Summary["Season"][Summary["Season"] == "Wint"] = "Winter"
    # Summary.boxplot(by='Season')
    return All_DA_Mapes, DA_mape, ID_mape, Summary


def visualise_overall_error():
    All_DA_Mapes, DA_mape, ID_mape, Summary = multirun()
    Overs = pd.DataFrame()
    Overs["True"] = All_DA_Mapes["True"][All_DA_Mapes["DAgmm"] > 0]
    Overs["DAgmm"] = All_DA_Mapes["DAgmm"][All_DA_Mapes["DAgmm"] > 0]
    Unders = pd.DataFrame()
    Unders["True"] = All_DA_Mapes["True"][All_DA_Mapes["DAgmm"] < 0]
    Unders["DAgmm"] = abs(All_DA_Mapes["DAgmm"][All_DA_Mapes["DAgmm"] < 0])

    bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
    Error_quartiles = pd.DataFrame(
        index=bins[1:], columns=["overq95", "overq50", "underq95", "underq50"]
    )

    for z in bins[1:-1]:
        Error_quartiles["overq95"][z] = Overs["DAgmm"][
            Overs["True"].between(z, (z + 0.1))
        ].quantile(0.95)
        Error_quartiles["overq50"][z] = Overs["DAgmm"][
            Overs["True"].between(z, (z + 0.1))
        ].quantile(0.5)
        Error_quartiles["underq95"][z] = -Unders["DAgmm"][
            Unders["True"].between(z, (z + 0.1))
        ].quantile(0.95)
        Error_quartiles["underq50"][z] = -Unders["DAgmm"][
            Unders["True"].between(z, (z + 0.1))
        ].quantile(0.5)

    types = {}
    types["DA_mape"] = DA_mape
    types["ID_mape"] = ID_mape
    for x in types:
        lowers95 = []
        uppers95 = []
        lowers50 = []
        uppers50 = []
        plt.figure(x)
        for i in DA_mape:
            lowers95.append(-abs(types[x][i][types[x][i] < 0] * 100).quantile(0.95))
            uppers95.append(abs(types[x][i][types[x][i] > 0] * 100).quantile(0.95))
            lowers50.append(-abs(types[x][i][types[x][i] < 0] * 100).quantile(0.50))
            uppers50.append(abs(types[x][i][types[x][i] > 0] * 100).quantile(0.50))
        plt.plot(lowers95, color="red", linestyle="--", label="Q95 underestimates")
        plt.plot(uppers95, color="blue", linestyle="--", label="Q95 overestimates")
        plt.plot(lowers50, color="red", linestyle=":", label="Q50 underestimates")
        plt.plot(uppers50, color="blue", linestyle=":", label="Q50 overestimates")
        plt.xlabel("Settlement Period (half hourly)", fontsize=8)
        plt.ylabel("Error (%)", fontsize=8)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.legend()

    plt.figure("By Output")
    plt.plot(
        Error_quartiles["overq95"],
        color="red",
        linestyle="--",
        label="Q95 Overestimates",
    )
    plt.plot(
        Error_quartiles["underq95"],
        color="blue",
        linestyle="--",
        label="Q95 Underestimates",
    )
    plt.plot(
        Error_quartiles["overq50"],
        color="red",
        linestyle=":",
        label="Q50 Overestimates",
    )
    plt.plot(
        Error_quartiles["underq50"],
        color="blue",
        linestyle=":",
        label="Q50 Underestimates",
    )
    plt.xlabel("Output-fraction of capacity", fontsize=8)
    plt.ylabel("Error (%)", fontsize=8)
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.legend()
    
multirun()
