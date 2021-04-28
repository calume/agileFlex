# -*- coding: utf-8 -*-
"""
Created on Thu May 02 13:48:06 2019
This python script produces forecasts of headroom calculated using OpenDSS. 
@author: Calum Edmunds
"""


######## Import packages
import scipy.io
import numpy as np
import pandas as pd

pd.options.mode.chained_assignment = None
from matplotlib import pyplot as plt
from datetime import datetime, timedelta, date, time
import datetime
import pickle
from sklearn.metrics import mean_absolute_error
from scipy.optimize import curve_fit

def return_temp(path):
       ###----------------------- Load in Test data Set -------------##########
    
    ########- temperature data from https://power.larc.nasa.gov/data-access-viewer/
    temp = pd.read_csv(
        path+"Data/heatpump/Grantham_Temp_Daily_20131101_20150301.csv", skiprows=16
    )
    radiation = pd.read_csv(
        path+"Data/NASA_POWER_AllSkyInsolation_01032014_13092014.csv", skiprows=10
    )
    
    radiation_W = pd.read_csv(
        path+"Data/NASA_POWER_AllSkyInsolation_01122013_01032014.csv", skiprows=10
    )
    
    temp = temp[30:118]#.append(temp[395:483])
    radiation = radiation[40:-31]
    radiation_W=radiation_W[:-1]
    #temp=temp[395:483]
    tempind = []
    radind = []
    radind_W=[]
    for i in temp.index:
        tempind.append(
            datetime.datetime(
                int(temp["YEAR"][i]), int(temp["MO"][i]), int(temp["DY"][i]), 0
            )
        )
    
    for i in radiation.index:
        radind.append(
            datetime.datetime(
                int(radiation["YEAR"][i]),
                int(radiation["MO"][i]),
                int(radiation["DY"][i]),
                0,
            )
        )
    
    for i in radiation_W.index:
        radind_W.append(
            datetime.datetime(
                int(radiation_W["YEAR"][i]),
                int(radiation_W["MO"][i]),
                int(radiation_W["DY"][i]),
                0,
            )
        )
    
    all_temp = temp["T2M"]
    all_temp.index = tempind
    
    all_rad = radiation["ALLSKY_SFC_SW_DWN"]
    all_rad.index = radind
    
    all_rad_W = radiation_W["ALLSKY_SFC_SW_DWN"]
    all_rad_W.index = radind_W  
    
    # plt.figure()
    # plt.hist(all_temp, bins=4)
    # plt.xlabel("Temperature (degC)")
    # plt.ylabel("Frequency")
    
    # plt.figure()
    # plt.hist(all_rad, bins=4)
    # plt.xlabel(" Summer All Sky Insolation (kW-hr/m^2/day)") # All Sky Insolation Incident on a Horizontal surface
    # plt.ylabel("Frequency")
    
    # plt.figure()
    # plt.hist(all_rad_W, bins=4)
    # plt.xlabel(" Winter All Sky Insolation (kW-hr/m^2/day)") # All Sky Insolation Incident on a Horizontal surface
    # plt.ylabel("Frequency")
    return all_temp, all_rad


Network='network_18/'
Case='00PV00HP'#,'00PV25HP','25PV50HP','25PV75HP','50PV100HP']

def percentiles(Case,Network):    
    all_temp, all_rad = return_temp('../')
    ###----------Winter Data------------------#####
    
    pick_in = open("../Data/Upper/"+Network+Case+"_WinterHdrm_All.pickle", "rb")
    DailyDelta = pickle.load(pick_in)
    
    
    tsamp=144
    tempLabels = range(1, 5)
    TempBins = pd.cut(all_temp, bins=4, labels=tempLabels, retbins=True)
    DailyDeltaPercentiles = {}
    DailyByBin = {}
    
    ########-------------- Daily Headroom irrespective of weekday/weekend -------###############
    for c in DailyDelta.keys():
       
        datesBinned = {}
        DailyByBin[c] = {}
            
        for z in tempLabels:
            datesBinned[z] = TempBins[0][TempBins[0] == z].index
            DailyByBin[c][z] = pd.DataFrame(index=datesBinned[z], columns=range(0, tsamp), dtype=float)
            for i in datesBinned[z]:
                DailyByBin[c][z].loc[i] = DailyDelta[c].loc[i].values
    
    
    pickle_out = open("../Data/Upper/"+Network+Case+"_WinterHdrm_ByTemp.pickle", "wb")
    pickle.dump(DailyByBin, pickle_out)
    pickle_out.close()
    
        
    return DailyDelta, DailyByBin


def headroom_plots(Network):
    pick_in = open("../Data/Upper/Assign_Final.pickle", "rb")
    assign = pickle.load(pick_in)
    pick_in = open("../Data/Upper/network_18/00PV00HP_WinterHdrm_ByTemp.pickle", "rb")
    DailyDelta= pickle.load(pick_in)
       
    n_zones=len(DailyDelta)
    tsamp=144
    times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    cols = ["grey","#9467bd", "#bcbd22","#ff7f0e","#d62728"]     
    #######------------ Plot By temperature Bins-----------------############
    
    all_temp, all_rad = return_temp('../')
    tempLabels = range(1, 5)
    TempBins = pd.cut(all_temp, bins=4, labels=tempLabels, retbins=True)
    plt.figure(Network+'Winter Headroom P5 (kWs) vs Settlement Period')
    r = 0
    lns=[':','--','-.','-']             
    for c in DailyDelta.keys():
        
        Case=assign[Network][c]
    
        pick_in = open("../Data/Upper/"+Network+Case+"_WinterHdrm_ByTemp.pickle", "rb")
        DailyByBin= pickle.load(pick_in)
        
        pick_in = open("../Data/Upper/"+Network+Case+"_WinterHdrm_All.pickle", "rb")
        DailyDelta= pickle.load(pick_in)        
        n = 0
        r = r + 1
        plt.subplot(3, int(n_zones/3), r)
        if r <= int(n_zones)/3:
            plt.title("Feeder - " + str(r))
        if (r-1) % (int(n_zones)/3) == 0:
            plt.ylabel("Phase " + str(c[0]))
        plt.plot(np.full(tsamp, 0), color="red", linestyle="--", linewidth=0.5)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(range(0,tsamp+24,int(tsamp/6)),times)
        
        for z in tempLabels:
            lbl = (str(round(TempBins[1][z - 1], 1))+" - "+str(round(TempBins[1][z], 1))+"degC")
            plt.plot(DailyByBin[c][z].quantile(0.02), linewidth=1, color=cols[n], label=lbl,linestyle=lns[n])
            #plt.ylim(-20,
            plt.xlim(0, tsamp)
            n=n+1
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    plt.tight_layout()
    plt.legend()
    
    #######------------ Plot Scatter temperature Bins-----------------############ 
        
    plt.figure(Network+'Daily deg C vs mean daily Delta')
    alldata=pd.DataFrame(index=all_temp.index, columns=DailyDelta.keys())
    for c in DailyDelta.keys():
        Case=assign[Network][c]
        pick_in = open("../Data/Upper/"+Network+Case+"_WinterHdrm_All.pickle", "rb")
        DailyDelta= pickle.load(pick_in)
        for d in all_temp.index:
            alldata[c][d]=DailyDelta[c].quantile(0.1,axis=1)[d]
            
    plt.scatter(all_temp.values, alldata.mean(axis=1).values, s=0.8)
    plt.xlabel=('Temperature')
    plt.ylabel('Mean of 2nd Quantile Daily Headroom')
    plt.xticks(fontsize=8)


def headroom_percentiles(networks,Cases):
    q=0
    for N in networks:
        # for C in Cases:
        #     DailyDelta,DailyByBin=percentiles(C,N)
        #     q=q+1
        n=0
        DailyByBin=headroom_plots(N)

    return DailyByBin

networks=['network_18/']
Cases=['00PV00HP','00PV25HP','25PV50HP','25PV75HP','50PV100HP']
DailyByBin=headroom_percentiles(networks, Cases)
