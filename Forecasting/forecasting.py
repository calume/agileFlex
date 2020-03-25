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
pd.options.mode.chained_assignment = None 
import timeit
from matplotlib import pyplot as plt
from datetime import datetime, timedelta, date, time
import datetime
import os
import random
import csv
import pickle
from sklearn.metrics import mean_absolute_error

###----------------------- Load in Test data Set -------------##########
pick_in = open("../../Data/SM_DataFrame_byAcorn_NH.pickle", "rb")
SM_DataFrame = pickle.load(pick_in)

pick_in = open("../../Data/HP_DataFrame.pickle", "rb")
HP_DataFrame = pickle.load(pick_in)

pick_in = open("../../Data/PV_BySiteName.pickle", "rb")
PV_DataFrame = pickle.load(pick_in)

pick_in = open("../../Data/PV_DistsGMMChosen.pickle", "rb")
PV_DistsGMMChosen = pickle.load(pick_in)

pick_in = open("../../Data/PV_DistsGMMWeights.pickle", "rb")
PV_DistsGMMWeights = pickle.load(pick_in)


## Look at one Day - PV
#pred is the previous days data using persistence forecasting
#true is the actual output for the day in question.


def forecasts(pred,true,Forecast_Type):
    if Forecast_Type=='Day Ahead':   
        mae=mean_absolute_error(true, pred)
        #print('Persistence Day Ahead Weighted NMAE: ',round(mae,3))
    else:
        mae=0
    if (true.index[0].month==12) | (true.index[0].month<=2):      #Dec-Feb
        Season='WintDists'
    if (true.index[0].month>=3) & (true.index[0].month <=5):    #Mar-May
        Season='SpringDists'
    if (true.index[0].month>=6) & (true.index[0].month <=8):    #Jun-Aug
        Season='SummerDists'
    if (true.index[0].month>=9) & (true.index[0].month <=11):   #Sept-Nov
        Season='AutumnDists'
    
    ### fit the gaussian mixtures to the persistence forecast depending on season
    gmmMAE_Pred=pd.Series(index=range(0,len(PV_DistsGMMChosen[Season])))
    for i in gmmMAE_Pred.index:
        gmmMAE_Pred[i]=mean_absolute_error(pred.values, PV_DistsGMMChosen[Season][i][0:len(pred)])
    
    gmmMAE_Pred=gmmMAE_Pred.sort_values()
    
    #    bestFits=gmmMAE_Pred[gmmMAE_Pred<(gmmMAE_Pred.iloc[0]*1.15)]
    WeightedNMAE=pd.Series(index=range(2,10))
    for x in range(2,10):
        GMMBestFit= PV_DistsGMMChosen[Season][gmmMAE_Pred.index[0:x]]
        gmmMAE_True=pd.Series(index=range(0,len(GMMBestFit)))
        
        #Determine optimal number of fits to minimise the Weighter NMAE
        for i in range(0,len(GMMBestFit)):
            gmmMAE_True[i]=mean_absolute_error(true, GMMBestFit[i])
    
        weights_bestFits=PV_DistsGMMWeights[Season][gmmMAE_Pred.index[0:x]]
        weights_bestFits=weights_bestFits/weights_bestFits.sum()
        WeightedNMAE[x]=sum(gmmMAE_True*weights_bestFits)
    
    Fits_Nmin=WeightedNMAE.idxmin()
    GMMBestFit= PV_DistsGMMChosen[Season][gmmMAE_Pred.index[0:Fits_Nmin]]
    weights_bestFits=PV_DistsGMMWeights[Season][gmmMAE_Pred.index[0:Fits_Nmin]]
    weights_bestFits=weights_bestFits/weights_bestFits.sum()
    #print('GMM ' +str(Forecast_Type)+ ' Weighted NMAE with '+str(Fits_Nmin)+' Fits: ',round(WeightedNMAE[Fits_Nmin],3))

    return GMMBestFit, gmmMAE_True, weights_bestFits, WeightedNMAE[Fits_Nmin],mae

#--------------------Visualise Forecast--------------------------#

    #Find best BMM fit
def visualise_forecast(GMMBestFit,Forecast_Type,weights_bestFits,Site,NMAE):
    plt.title(Site+', Error - '+str(round(NMAE,3)),fontsize=9)
    if Forecast_Type=='Day Ahead':   
        plt.plot(pred.values, label='Persistence Forecast',linestyle='--')
    for i in range(0,len(GMMBestFit)):
        plt.plot(GMMBestFit[i], linewidth=weights_bestFits[i]*2)
    plt.plot(true.values, label='Actual', color='black', linestyle=':', linewidth=2)
    times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    #plt.ylabel('PV output normalised',fontsize=8)
    plt.xticks(range(0, 47, 8), times,fontsize=8)
    plt.ylim(0,1)
    plt.yticks(fontsize=8)
    

#-------------------Do multiple Runs---------------------------#

### Date stuff ###

startdate =  date(2014,7,1)
enddate   =  date(2014,7,3)
delta = datetime.timedelta(hours=0.5)

dt = pd.date_range(startdate, enddate, freq=delta) #datetime steps    
dt[0:47]
n=1
DA_WeightedNMAE=pd.Series(index=PV_DataFrame.keys())
ID_WeightedNMAE=pd.Series(index=PV_DataFrame.keys())
DA_PersistanceNMAE=pd.Series(index=PV_DataFrame.keys())
DA_weights_bestFits={}
ID_weights_bestFits={}
DA_GMMBestFit={}
ID_GMMBestFit={}
l=0
for i in PV_DataFrame.keys():
    pred=PV_DataFrame[i]['P_Norm'][dt[0:48]]
    true=PV_DataFrame[i]['P_Norm'][dt[48:96]]
    Forecast_Type='Day Ahead'
    DA_GMMBestFit[i], gmmMAE_True, DA_weights_bestFits[i], DA_WeightedNMAE[i],DA_PersistanceNMAE[i]=forecasts(pred,true,Forecast_Type)
    plt.figure(Forecast_Type)
    plt.subplot(320+n)
    visualise_forecast(DA_GMMBestFit[i],'Day Ahead',DA_weights_bestFits[i],i,DA_WeightedNMAE[i])
    if n==1:
        plt.legend(fontsize=8)
    Forecast_Type='Intraday'
    plt.figure(Forecast_Type)
    plt.subplot(320+n)
    Intraday_True=true[0:20]
    ID_GMMBestFit[i], gmmMAE_True, ID_weights_bestFits[i], ID_WeightedNMAE[i],blank=forecasts(Intraday_True,true,'Intraday')
    visualise_forecast(ID_GMMBestFit[i],'Intraday',ID_weights_bestFits[i],i,ID_WeightedNMAE[i])
    if n==1:
        plt.legend(fontsize=8)
    n=n+1
    l=l+1
    
print('Average NMAE. Day ahead Persistence: ',round(DA_PersistanceNMAE.mean(),3),'Day Ahead GMM: ',round(DA_WeightedNMAE.mean(),3),'Intraday GMM: ',round(ID_WeightedNMAE.mean(),3))

plt.tight_layout()

