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

    GMMBestFit= PV_DistsGMMChosen[Season][gmmMAE_Pred.index[0]]#[0:Fits_Nmin]]
    weights_bestFits=PV_DistsGMMWeights[Season][gmmMAE_Pred.index[0]]#:Fits_Nmin]]
    weights_bestFits=weights_bestFits/weights_bestFits.sum()
    #print('GMM ' +str(Forecast_Type)+ ' Weighted NMAE with '+str(Fits_Nmin)+' Fits: ',round(WeightedNMAE[Fits_Nmin],3))

    return GMMBestFit, gmmMAE_Pred[0],mae,Season

#--------------------Visualise Forecast--------------------------#

    #Find best BMM fit
def visualise_forecast(GMMBestFit,Forecast_Type,Day,GMM_NMAE,Persistence_NMAE):
    plt.title('Day '+str(Day+1)+', MAE (Error): GMM-'+str(round(GMM_NMAE,3)),fontsize=9)
    if Forecast_Type=='Day Ahead':   
        plt.title('Day '+str(Day+1)+', MAE (Error): GMM-'+str(round(GMM_NMAE,3))+' Persistence:'+str(round(Persistence_NMAE,3)),fontsize=9)
        plt.plot(pred.values, label='Persistence Forecast',linestyle='--')
    plt.plot(GMMBestFit, label='GMM Best Fit')
    plt.plot(true.values, label='Actual', color='black', linestyle=':', linewidth=2)
    times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    plt.xticks(range(0, 47, 8), times,fontsize=8)
    plt.ylim(0,1)
    plt.yticks(fontsize=8)
    

#-------------------Do multiple Runs---------------------------#

### Date stuff ###

#### Year #####
startdate =  date(2013,11,7)
enddate   =  date(2014,11,13)
days=range(0,365)

### Week ###
#startdate =  date(2014,7,1)
#enddate   =  date(2014,7,10)
#days=range(0,8)

delta = datetime.timedelta(hours=0.5)
dt = pd.date_range(startdate, enddate, freq=delta) #datetime steps    
n=1
DA_WeightedNMAE=pd.Series(index=days)
ID_WeightedNMAE=pd.Series(index=days)
DA_PersistanceNMAE=pd.Series(index=days)
DA_GMMBestFit={}
ID_GMMBestFit={}


Seasons=pd.Series(index=days)
for i in days:
    print(i)
    pred=PV_DataFrame['Alverston Close']['P_Norm'][dt[i*48:(i+1)*48]]
    true=PV_DataFrame['Alverston Close']['P_Norm'][dt[(i+1)*48:(i+2)*48]]
    Forecast_Type='Day Ahead'
    DA_GMMBestFit[i], DA_WeightedNMAE[i],DA_PersistanceNMAE[i],Season=forecasts(pred,true,Forecast_Type)
#    plt.figure(Forecast_Type)
#    plt.subplot(420+n)
#    visualise_forecast(DA_GMMBestFit[i],'Day Ahead',i,DA_WeightedNMAE[i],DA_PersistanceNMAE[i])
#    if n==1:
#        plt.legend(fontsize=8)
    Forecast_Type='Intraday'
#    plt.figure(Forecast_Type)
#    plt.subplot(420+n)
    Intraday_True=true[0:20]
    ID_GMMBestFit[i], ID_WeightedNMAE[i],blank,Season=forecasts(Intraday_True,true,'Intraday')
#    visualise_forecast(ID_GMMBestFit[i],'Intraday',i,ID_WeightedNMAE[i],0)
#    if n==1:
#        plt.legend(fontsize=8)
#    n=n+1
    Seasons[i]=Season
print('Average NMAE. Day ahead Persistence: ',round(DA_PersistanceNMAE.mean(),3),'Day Ahead GMM: ',round(DA_WeightedNMAE.mean(),3),'Intraday GMM: ',round(ID_WeightedNMAE.mean(),3))

#plt.tight_layout()

#Summary=pd.DataFrame(index=days, columns=['DA GMM','Persistence','ID GMM','Season'])
#Summary['DA GMM']=DA_WeightedNMAE
#Summary['Persistence']=DA_PersistanceNMAE
#Summary['ID GMM']=ID_WeightedNMAE
#Summary['Season']=Seasons
#Summary['Season']=Summary['Season'].str[:-5]
#Summary['Season'][Summary['Season']=='Wint']='Winter'
#Summary.boxplot(by='Season')