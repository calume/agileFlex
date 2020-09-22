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
    
    #    plt.figure()
    #    plt.hist(all_temp, bins=4)
    #    plt.xlabel("Temperature (degC)")
    #    plt.ylabel("Frequency")
    #    
    #    plt.figure()
    #    plt.hist(all_rad, bins=4)
    #    plt.xlabel(" Summer All Sky Insolation (kW-hr/m^2/day)") # All Sky Insolation Incident on a Horizontal surface
    #    plt.ylabel("Frequency")
    #    
    #    plt.figure()
    #    plt.hist(all_rad_W, bins=4)
    #    plt.xlabel(" Winter All Sky Insolation (kW-hr/m^2/day)") # All Sky Insolation Incident on a Horizontal surface
    #    plt.ylabel("Frequency")
    return all_temp, all_rad



def prep_inputs(Case,Network,VlimCase):  
    all_temp, all_rad = return_temp('../../')
    ###----------Winter Data------------------#####

    pick_in = open("../../Data/"+VlimCase+"Winter14_10mins_HdRm.pickle", "rb")
    Winter_HdRm = pickle.load(pick_in)


    pick_in = open("../../Data/"+VlimCase+"Winter14_10mins_Ftrm.pickle", "rb")
    Winter_FtRm = pickle.load(pick_in)
    
    # pick_in = open("../../Data/"+VlimCase+"Winter14_10mins_HdRm.pickle", "rb")
    # Winter14_HdRm = pickle.load(pick_in)
    
    # for i in Winter_HdRm.keys():
    #     Winter_HdRm[i]=Winter14_HdRm[i][:-1].append(Winter_HdRm[i][:-1])
    
    cs=[]
    n_zones=len(Winter_HdRm)-2
    for p in range(1, 4):
        for f in range(1, n_zones+1):
            cs.append(str(p)+str(f))
    
    ########---------Convert Headroom to feeder+phase column dataframe
    Headrm_DF = pd.DataFrame(
        index=Winter_HdRm[1].index,
        columns=cs
    )
    
    Footrm_DF = pd.DataFrame(
        index=Winter_FtRm[1].index,
        columns=cs
    )
    
    for p in range(1, 4):
        for f in range(1, n_zones+1):
            Headrm_DF[str(p) + str(f)] = Winter_HdRm[f][p]
            Footrm_DF[str(p) + str(f)] = Winter_FtRm[f][p]
    
    #########---------Convert to daily timeseries--------
    
    #summer_dates = SummerInputs.index[:-1]
    winter_dates = Headrm_DF.index[:-1]
    wkd_dates = (winter_dates.weekday >= 0) & (winter_dates.weekday <= 4)
    wknd_dates = (winter_dates.weekday >= 5) & (winter_dates.weekday <= 6)
    wkd_dates = winter_dates[wkd_dates]
    wknd_dates = winter_dates[wknd_dates]
    
    wkd_temps = all_temp[wkd_dates[range(0, len(wkd_dates), 144)]]
    wknd_temps = all_temp[wknd_dates[range(0, len(wknd_dates), 144)]]
    
    
    dates=[wkd_dates,wknd_dates]
    temps=[wkd_temps,wknd_temps]
    names=['wkd','wknd']
    
    return dates, temps, names, Headrm_DF,Footrm_DF, winter_dates, all_temp


def percentiles(Case,Network,VlimCase):    
    tsamp=144
    dates, temps, names, Headrm_DF,Footrm_DF, winter_dates,all_temp = prep_inputs(Case,Network,VlimCase)
    tempLabels = range(1, 5)
    TempBins = pd.cut(all_temp, bins=4, labels=tempLabels, retbins=True)
    DailyDelta={}
    DailyDeltaPercentiles = {}
    DailyByBin = {}
    
    ########-------------- Daily Headroom irrespective of weekday/weekend -------###############
    for c in Headrm_DF.columns:
        print(c)
        DailyDeltaPercentiles[c]={}
        dailyrange = range(0, len(winter_dates), tsamp)
        DailyDelta[c] = pd.DataFrame(index=winter_dates[dailyrange], columns=range(0, tsamp),dtype=float)
        for d in DailyDelta[c].index:
            mask = (Headrm_DF[c].index >= d) & (Headrm_DF[c].index < (d + timedelta(days=1)))
            DailyDelta[c].loc[d] = Headrm_DF[c].loc[mask].values
        
        DailyDeltaPercentiles[c]["P1"] = pd.Series(index=range(0, tsamp), dtype=float)
        DailyDeltaPercentiles[c]["P5"] = pd.Series(index=range(0, tsamp), dtype=float)
        DailyDeltaPercentiles[c]["Median"] = pd.Series(index=range(0, tsamp), dtype=float)
        for p in range(0, tsamp):
            DailyDeltaPercentiles[c]["P1"][p] = DailyDelta[c][p].quantile(0.01)
            DailyDeltaPercentiles[c]["P5"][p] = DailyDelta[c][p].quantile(0.05)
            DailyDeltaPercentiles[c]["Median"][p] = DailyDelta[c][p].quantile(0.5)  
    
            # datesBinned = {}
            # DailyByBin[c] = {}
            
    #     for z in tempLabels:
    #         datesBinned[z] = TempBins[0][TempBins[0] == z].index
    #         DailyByBin[c][z] = pd.DataFrame(index=datesBinned[z], columns=range(0, tsamp), dtype=float)
    #         DailyByBin[c]["P1-" + str(z)] = pd.Series(index=range(0, tsamp), dtype=float)
    #         DailyByBin[c]["P5-" + str(z)] = pd.Series(index=range(0, tsamp), dtype=float)
    #         DailyByBin[c]["Median-" + str(z)] = pd.Series(index=range(0, tsamp), dtype=float)
    #         for i in datesBinned[z]:
    #             DailyByBin[c][z].loc[i] = DailyDelta[c].loc[i].values
    #         for p in range(0, tsamp):
    #             DailyByBin[c]["P1-" + str(z)][p] = DailyByBin[c][z][p].quantile(0.01)
    #             DailyByBin[c]["P5-" + str(z)][p] = DailyByBin[c][z][p].quantile(0.05)
    #             DailyByBin[c]["Median-" + str(z)][p] = DailyByBin[c][z][p].quantile(0.5)
    
    pickle_out = open("../../Data/"+VlimCase+"_WinterHdrm_All.pickle", "wb")
    pickle.dump(DailyDeltaPercentiles, pickle_out)
    pickle_out.close()
    
    pickle_out = open("../../Data/"+VlimCase+"_WinterHdrm_Raw.pickle", "wb")
    pickle.dump(DailyDelta, pickle_out)
    pickle_out.close()
    for c in Footrm_DF.columns:
        print(c)
        DailyDeltaPercentiles[c]={}
        dailyrange = range(0, len(winter_dates), tsamp)
        DailyDelta[c] = pd.DataFrame(index=winter_dates[dailyrange], columns=range(0, tsamp),dtype=float)
        for d in DailyDelta[c].index:
            mask = (Footrm_DF[c].index >= d) & (Footrm_DF[c].index < (d + timedelta(days=1)))
            DailyDelta[c].loc[d] = Footrm_DF[c].loc[mask].values
        
        DailyDeltaPercentiles[c]["P1"] = pd.Series(index=range(0, tsamp), dtype=float)
        DailyDeltaPercentiles[c]["P5"] = pd.Series(index=range(0, tsamp), dtype=float)
        DailyDeltaPercentiles[c]["Median"] = pd.Series(index=range(0, tsamp), dtype=float)
        for p in range(0, tsamp):
            DailyDeltaPercentiles[c]["P1"][p] = DailyDelta[c][p].quantile(0.01)
            DailyDeltaPercentiles[c]["P5"][p] = DailyDelta[c][p].quantile(0.05)
            DailyDeltaPercentiles[c]["Median"][p] = DailyDelta[c][p].quantile(0.5)  
    
            datesBinned = {}
            DailyByBin[c] = {}
    pickle_out = open("../../Data/"+VlimCase+"_WinterFtrm_All.pickle", "wb")
    pickle.dump(DailyDeltaPercentiles, pickle_out)
    pickle_out.close()  


            
        # for z in tempLabels:
        #     datesBinned[z] = TempBins[0][TempBins[0] == z].index
        #     DailyByBin[c][z] = pd.DataFrame(index=datesBinned[z], columns=range(0, tsamp), dtype=float)
        #     DailyByBin[c]["P1-" + str(z)] = pd.Series(index=range(0, tsamp), dtype=float)
        #     DailyByBin[c]["P5-" + str(z)] = pd.Series(index=range(0, tsamp), dtype=float)
        #     DailyByBin[c]["Median-" + str(z)] = pd.Series(index=range(0, tsamp), dtype=float)
        #     for i in datesBinned[z]:
        #         DailyByBin[c][z].loc[i] = DailyDelta[c].loc[i].values
        #     for p in range(0, tsamp):
        #         DailyByBin[c]["P1-" + str(z)][p] = DailyByBin[c][z][p].quantile(0.01)
        #         DailyByBin[c]["P5-" + str(z)][p] = DailyByBin[c][z][p].quantile(0.05)
        #         DailyByBin[c]["Median-" + str(z)][p] = DailyByBin[c][z][p].quantile(0.5)
    ###########------------- Calculate Daily Headroom by Weekday/Weekend-------#####
    # for g in range(0,2):

    #     dailyrange = {}
    #     DailyDelta[names[g]] = {}
    #     DailyByBin[names[g]] = {}
    #     DailyDeltaPercentiles[names[g]] = {}
    
    #     tempLabels = range(1, 5)
    #     TempBins = pd.cut(temps[g], bins=4, labels=tempLabels, retbins=True)
        
    #     for c in Headrm_DF.columns:
    #         DailyDeltaPercentiles[names[g]][c]={}
    #         dailyrange = range(0, len(dates[g]), tsamp)
    #         DailyDelta[names[g]][c] = pd.DataFrame(index=dates[g][dailyrange], columns=range(0, tsamp),dtype=float)
    #         for d in DailyDelta[names[g]][c].index:
    #             mask = (Headrm_DF[c].index >= d) & (Headrm_DF[c].index < (d + timedelta(days=1)))
    #             DailyDelta[names[g]][c].loc[d] = Headrm_DF[c].loc[mask].values
            
    #         DailyDeltaPercentiles[names[g]][c]["P1"] = pd.Series(index=range(0, tsamp), dtype=float)
    #         DailyDeltaPercentiles[names[g]][c]["P5"] = pd.Series(index=range(0, tsamp), dtype=float)
    #         DailyDeltaPercentiles[names[g]][c]["Median"] = pd.Series(index=range(0, tsamp), dtype=float)
    #         for p in range(0, tsamp):
    #             DailyDeltaPercentiles[names[g]][c]["P1"][p] = DailyDelta[names[g]][c][p].quantile(0.01)
    #             DailyDeltaPercentiles[names[g]][c]["P5"][p] = DailyDelta[names[g]][c][p].quantile(0.05)
    #             DailyDeltaPercentiles[names[g]][c]["Median"][p] = DailyDelta[names[g]][c][p].quantile(0.5)       
            
    #         datesBinned = {}
    #         DailyByBin[names[g]][c] = {}
            
    #         for z in tempLabels:
    #             datesBinned[z] = TempBins[0][TempBins[0] == z].index
    #             DailyByBin[names[g]][c][z] = pd.DataFrame(index=datesBinned[z], columns=range(0, tsamp), dtype=float)
    #             DailyByBin[names[g]][c]["P1-" + str(z)] = pd.Series(index=range(0, tsamp), dtype=float)
    #             DailyByBin[names[g]][c]["P5-" + str(z)] = pd.Series(index=range(0, tsamp), dtype=float)
    #             DailyByBin[names[g]][c]["Median-" + str(z)] = pd.Series(index=range(0, tsamp), dtype=float)
    #             for i in datesBinned[z]:
    #                 DailyByBin[names[g]][c][z].loc[i] = DailyDelta[names[g]][c].loc[i].values
    #             for p in range(0, tsamp):
    #                 DailyByBin[names[g]][c]["P1-" + str(z)][p] = DailyByBin[names[g]][c][z][p].quantile(0.01)
    #                 DailyByBin[names[g]][c]["P5-" + str(z)][p] = DailyByBin[names[g]][c][z][p].quantile(0.05)
    #                 DailyByBin[names[g]][c]["Median-" + str(z)][p] = DailyByBin[names[g]][c][z][p].quantile(0.5)
    
    # pickle_out = open("../../Data/"+VlimCase+"_WinterHdrm_ByTemp.pickle", "wb")
    # pickle.dump(DailyByBin, pickle_out)
    # pickle_out.close()
    
    # pickle_out = open("../../Data/"+VlimCase+"_WinterHdrm_Raw.pickle", "wb")
    # pickle.dump(DailyDelta, pickle_out)
    # pickle_out.close()
    
        
    return DailyDelta


def headroom_plots(Network,Case,n,lbls,kva,VlimCase):
    # pick_in = open("../../Data/"+VlimCase+"_WinterHdrm_Raw.pickle", "rb")
    # DailyDelta= pickle.load(pick_in)
   
    # pick_in = open("../../Data/"+VlimCase+"_WinterHdrm_ByTemp.pickle", "rb")
    # DailyByBin= pickle.load(pick_in)
    
    pick_in = open("../../Data/"+VlimCase+"_WinterHdrm_All.pickle", "rb")
    DailyDeltaPercentiles= pickle.load(pick_in)
    n_zones=len(DailyDeltaPercentiles)
    tsamp=144
    Y=14
    times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    cols = ["grey","#9467bd", "#bcbd22","#ff7f0e","#d62728"]    
    pick_in = open("../../Data/"+Network+"Customer_Summary"+Case+str(Y)+".pickle", "rb")
    Customer_Summary= pickle.load(pick_in)    
    # #######------------ Plot By temperature Bins-----------------############

    # tempLabels = range(1, 5)
    # dates, temps, names, Headrm_DF,winter_dates,all_temp = prep_inputs(Case,Network)
    # TempBins = pd.cut(all_temp, bins=4, labels=tempLabels, retbins=True)

    # r = 0             
    # for c in DailyByBin.keys():
    #     plt.figure(N+C+'Winter Headroom P5 (kWs) vs Settlement Period')
    #     n = 0
    #     r = r + 1
    #     plt.subplot(3, int(n_zones/3), r)
    #     if r <= int(n_zones)/3:
    #         plt.title("Feeder - " + str(r))
    #     if (r-1) % (int(n_zones)/3) == 0:
    #         plt.ylabel("Phase " + str(c[0]))
    #     plt.plot(np.full(tsamp, 0), color="red", linestyle="--", linewidth=0.5)
    #     plt.xticks(fontsize=8)
    #     plt.yticks(fontsize=8)
    #     plt.xticks(range(0,tsamp+24,int(tsamp/6)),times)
        
    #     for z in tempLabels:
    #         lbl = (str(round(TempBins[1][z - 1], 1))+" - "+str(round(TempBins[1][z], 1))+"degC")
    #         plt.plot(DailyByBin[c]['P5-' + str(z)].values, linewidth=1, color=cols[n], label=lbl)
    #         #plt.ylim(-20, 40)
    #         plt.xlim(0, tsamp)
    #         n = n + 1
    # figManager = plt.get_current_fig_manager()
    # figManager.window.showMaximized()
    # plt.tight_layout()
    # plt.legend()
    
    # #######------------ Plot Scatter temperature Bins-----------------############ 
    #    
    #     plt.figure(N+C+'Daily deg C vs mean daily Delta')
    #     u = 0
    #     for c in DailyByBin.keys():
    #         print(u)
    #         u = u + 1
    #         plt.subplot(3, int(n_zones/3), u)
    #         if u <= int(n_zones)/3:
    #             plt.title("Feeder - " + str(r))
    #         if (u-1) % (int(n_zones)/3) == 0:
    #             plt.ylabel("Phase " + str(c[0]))
    #         plt.scatter(temps.values, DailyDelta[c].mean(axis=1).values, s=0.8)
    #         plt.xticks(fontsize=8)
    #         plt.yticks(fontsize=8)
    #     figManager = plt.get_current_fig_manager()
    #     figManager.window.showMaximized()
    #     plt.tight_layout()
        
    # ######--------- Plot weekday vs weekend ---------------##############
    #names=['wkd','wknd']
    #for g in range(0,2):
    #     r = 0             
    #     for c in DailyByBin['wkd'].keys():
    #         plt.figure(N+C+'Winter headroom, weekday vs Weekend')
    #         n = 0
    #         r = r + 1
    #         plt.subplot(3, int(n_zones/3), r)
    #         if r <= int(n_zones)/3:
    #             plt.title("Feeder - " + str(r))
    #         if (r-1) % (int(n_zones)/3) == 0:
    #             plt.ylabel("Phase " + str(c[0]))
    #         plt.plot(np.full(tsamp, 0), color="red", linestyle="--", linewidth=0.5)
    #         plt.xticks(fontsize=8)
    #         plt.yticks(fontsize=8)
    #         plt.xticks(range(0,tsamp+24,int(tsamp/6)),times)
    #         plt.plot(DailyDeltaPercentiles[names[g]][c]['P5'].values, linewidth=1, color=cols[g], label='P5 - '+str(names[g]))
    #         plt.plot(DailyDeltaPercentiles[names[g]][c]['Median'].values, linestyle="--", linewidth=1, color=cols[g], label='Median - '+str(names[g]))
    #         plt.ylim(-20, 40)
    #         plt.xlim(0, tsamp)
    #         n = n + 1
        
    #     figManager = plt.get_current_fig_manager()
    #     figManager.window.showMaximized()
    #     plt.tight_layout()
    #     plt.legend()
    
    ########## Plot P-5 For all Cases On one Graph ###############
    r = 0
    plt.figure(N+'Winter headroom, All Cases')           
    for c in DailyDeltaPercentiles.keys():
        ncs=len(Customer_Summary[Customer_Summary['zone']==c])
        r = r + 1
        ax=plt.subplot(3, int(n_zones/3), r)
        plt.title('Zone '+str(c)+', Customers - '+str(ncs)+'\n kVA/HPs = '+str(kva[N]['00PV25HP'][c]))
        if r <= int(n_zones)/3:
            plt.title("Feeder " + str(r)+'\n Zone '+str(c)+' Customers - '+str(ncs)+'\n kVA/HPs = '+str(kva[N]['00PV25HP'][c]))
        if (r-1) % (int(n_zones)/3) == 0:
            plt.ylabel("Phase " + str(c[0]))
        ax.plot(np.full(tsamp, 0), color="red", linestyle="--", linewidth=0.5)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(range(0,tsamp+24,int(tsamp/6)),times)
        plt.plot(DailyDeltaPercentiles[c]['P5'].values, linewidth=1, color=cols[n], label=lbls[n])
        #plt.plot(DailyDeltaPercentiles['Median'].values, linestyle="--", linewidth=1, color=cols[g], label='Median - '+str(names[g]))
        #plt.ylim(-40, 40)
        plt.ylim(-40, 50)
        plt.xlim(0, tsamp)
        
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    plt.tight_layout()
    plt.legend()    
    
    return DailyDeltaPercentiles

###################------------ plot HPs vs Headroom ----------###############
def HP_vs_Headroom(networks, Cases):
    Customer_Summary={}
    DailyPercentiles={}
    Y=14
    HdrmSum={}
    HPSum={}  
    HdrmAnyBelow={}   
    for N in networks:
        
        Customer_Summary[N]={}
        DailyPercentiles[N]={}
        pick_in = open("../../Data/"+str(N+Cases[0])+"_WinterHdrm_All.pickle", "rb")
        DailyDelta= pickle.load(pick_in)
        HdrmSum[N]=pd.DataFrame(index=list(DailyDelta.keys()), columns=Cases)
        HPSum[N]=pd.DataFrame(index=list(DailyDelta.keys()), columns=Cases)
        HdrmAnyBelow[N]=pd.DataFrame(index=list(DailyDelta.keys()), columns=Cases)
        for C in Cases:        
            VlimCase=N+"upperVlimit/"+C 
            pick_in = open("../../Data/"+N+"Customer_Summary"+C+str(Y)+".pickle", "rb")
            Customer_Summary[N][C]= pickle.load(pick_in)
            
            pick_in = open("../../Data/"+VlimCase+"_WinterHdrm_All.pickle", "rb")
            DailyPercentiles[N][C]= pickle.load(pick_in)
            
            
            for i in DailyPercentiles[N][C].keys():
                #HdrmSum[N][C][i]=(DailyPercentiles[N][C][i]['P5'][:60].sum()+DailyPercentiles[N][C][i]['P5'][96:].sum())/6  ##-- Day PV effect removed
                HdrmSum[N][C][i]=DailyPercentiles[N][C][i]['P5'].sum()/6
                HdrmAnyBelow[N][C][i]=DailyPercentiles[N][C][i]['P5'][DailyPercentiles[N][C][i]['P5']<0].sum()/6
                HPSum[N][C][i]=Customer_Summary[N][C][Customer_Summary[N][C]['zone']==i]['Heat_Pump_Flag'].sum()
        r = 0    
        
        #plt.figure('Number and % of Penetration heatpumps with Total Daily P5 Headroom')
        
        # for i in HPSum[N].index:  
        #     r = r + 1
        #     ax1=plt.subplot(3, int(len(DailyPercentiles[N][C].keys())/3),r)
        #     ax1.plot(HPSum[N].loc[i],HdrmSum[N].loc[i])
        #     ax1.set_xlim(HPSum[N].loc[i].min(),HPSum[N].loc[i].max())
        #     ax2=ax1.twiny()
        #     if len(Customer_Summary[N][C][Customer_Summary[N][C]['zone']==i]) >0:
        #         ax2.plot(HPSum[N].loc[i]/HPSum[N].loc[i].max()*100,np.zeros(len(HPSum[N].loc[i])), color="red", linestyle="--", linewidth=1)
        #         ax2.set_xlim(HPSum[N].loc[i].min()/HPSum[N].loc[i].max()*100,100)
        #     ax1.set_xlabel('# of heatpumps')
        #     ax2.set_xlabel('% of customers')
        #     if r <= int(HPSum[N].index.str[1].max()):
        #         plt.title("Feeder - " + str(r))
        #     if (r-1) % int(HPSum[N].index.str[1].max()) == 0:
        #         ax1.set_ylabel("Phase " + str(i[0]))
        # plt.title('Number and % of Penetration heatpumps with Total Daily P5 Headroom')
    return HPSum, HdrmSum,HdrmAnyBelow, DailyPercentiles, Customer_Summary

pick_in = open("../../Data/All_VC_Limits0.94.pickle", "rb")
All_VC = pickle.load(pick_in)

pick_in = open("../../Data/All_C_Limits0.94.pickle", "rb")
All_C = pickle.load(pick_in)

networks=['network_1/','network_5/','network_10/','network_18/','network_17/']
#Cases=['00PV25HP','25PV50HP','25PV75HP','50PV100HP','25PV25HP','50PV50HP','75PV75HP','100PV100HP']
Cases=['00PV00HP','00PV25HP','25PV50HP','25PV75HP','50PV100HP'] ###Cases=['25PV25HP','50PV50HP','75PV75HP','100PV100HP']
lbls=['0% HP, 0% PV','25% HP, 0% PV', '50% HP, 25% PV', '75% HP, 25% PV', '100% HP, 50% PV']  



for N in networks:

    for i in All_VC[N].index:
        All_VC[N].loc[i]=min(All_VC[N].loc[i],All_C[N].loc[i])
    
    q=0
    for C in Cases:
        print(N, C)
        #VlimCase=Network+Case
        VlimCase=N+"upperVlimit/"+C        
        
        ##DailyDelta=percentiles(C,N,VlimCase)
        ##DailyDeltaPercentiles=headroom_plots(N,C,q,lbls,KVA_HP,VlimCase)
        q=q+1


HPSum, HdrmSum,HdrmAnyBelow, DailyPercentiles, Customer_Summary=HP_vs_Headroom(networks, Cases)


EVAvg=14.2 #kWh charge / day
Thresh=150

nEVs={}
#nEVs_shift={}
EVs={}
KVA_HP={}
KVA_LIM=pd.Series(index=networks,dtype=float)
Allsums=pd.DataFrame(index=Cases+['Total Customers'],dtype=int)
cols = ["grey","#9467bd", "#bcbd22","#ff7f0e","#d62728"] 
mk=['o','^','*','P']
count=1
for N in networks:
    plt.figure(N)
    nEVs[N]=(HdrmSum[N]/EVAvg).astype(int)
    nEVs[N]=nEVs[N][nEVs[N]>0].fillna(0).astype(float)
    for c in nEVs[N].columns:
        for j in nEVs[N][c].index:
            nEVs[N][c].loc[j]=min(nEVs[N][c].loc[j],HPSum[N]['50PV100HP'].loc[j])
    EVs[N]=nEVs[N].copy()
    KVA_HP[N]=nEVs[N].copy()
    for i in nEVs[N].columns:
        EVs[N][i]=EVs[N][i]/HPSum[N]['50PV100HP']
        EVs[N][i]=EVs[N][i].astype(float).round(decimals=2)
    EVs[N][EVs[N]>1]=1
    
    #nEVs[N]['00PV00HP']=0
    o=0
    for i in nEVs[N].columns[1:]:
        KVA_HP[N][i]=round((All_VC[N]/HPSum[N][i]).astype(float),2)
        #nEVs[N][i]=HdrmSum[N][i][HdrmSum[N][i]>0].fillna(0).astype(float)/EVAvg
        if count==len(networks):
            plt.scatter(All_VC[N]/HPSum[N][i],HdrmSum[N][i], marker=mk[o], edgecolors=cols[o], facecolors='none',label=i)
        else:
            plt.scatter(All_VC[N]/HPSum[N][i],HdrmSum[N][i], marker=mk[o], edgecolors=cols[o], facecolors='none')
        o=o+1
    C=np.arange(0.3,10,step=0.1)
    x=np.nan_to_num(KVA_HP[N].astype(float).values.flatten())
    y=np.nan_to_num(HdrmSum[N].astype(float).values.flatten())    
    def func (x,a,b,c):
        return a *np.log(b*x)+c
    try:
        kva_lim=x[y<5].max()
        kva_plim=np.quantile(x[y<5],0.95)
        KVA_LIM[N]=kva_lim
        m1,m,c=np.polyfit(x,y,2)
        #popt, pcov = curve_fit(func, x, y)
        #plt.plot(C, func(C, *popt))
        plt.plot(C,(m1*C**2+m*C+c), linewidth=0.5)
        plt.plot(np.zeros(16),linestyle=':', linewidth='0.5')
        plt.plot([kva_lim,kva_lim],[y.min(),y.max()],linestyle='--', linewidth='0.5')
        #plt.plot([kva_plim,kva_plim],[y.min(),y.max()],linestyle=':', linewidth='1.5') 
    except:
        print('Cant Fit')

    plt.xlabel('Minimum kVA Limit per Heatpump')
    plt.ylabel('Total Daily Headroom (kVAh)')
    ab=nEVs[N].sum().astype(int)
    ab.name=N
    Allsums=Allsums.join(ab.astype(int))
    Allsums[N]['Total Customers']=HPSum[N]['50PV100HP'].sum()
    count=count+1
plt.legend()
plt.xlim(0,10)
plt.ylim(-1000,1000)

assign={}
v2gZones={}
AllHdRms=pd.DataFrame(index=Cases+['Total Zones'])
v2gs=pd.DataFrame(index=Cases+['Total Zones'])
for N in networks:
    aa=HdrmAnyBelow[N][HdrmAnyBelow[N]<-2].count()
    aa.name=N
    AllHdRms=AllHdRms.join(aa)    
    AllHdRms[N]['Total Zones']=len(HdrmSum[N]['00PV25HP'])
    
    aa=(HdrmSum[N][HdrmAnyBelow[N]<0]>Thresh).sum()
    aa.name=N
    v2gs=v2gs.join(aa)    
    v2gs[N]['Total Zones']=len(HdrmSum[N]['00PV25HP'])    
    
    for i in All_VC[N].index:
        All_VC[N].loc[i]=min(All_VC[N].loc[i],All_C[N].loc[i])
    
    q=0
    for C in Cases:
        VlimCase=N+"upperVlimit/"+C 
        #print(N, C)
        ##DailyDelta=percentiles(C,N)
        DailyDeltaPercentiles=headroom_plots(N,C,q,lbls,KVA_HP,VlimCase)
        q=q+1

    assign[N]=pd.Series(index=HdrmSum[N].index)
    v2gZones[N]=[]
    for i in HdrmSum[N].index:
        if sum(HdrmAnyBelow[N].loc[i]==0) ==0:
            assign[N][i]='00PV00HP'
        if sum(HdrmAnyBelow[N].loc[i]<0) ==0:
            assign[N][i]='50PV100HP'
        if sum(HdrmAnyBelow[N].loc[i]<0) >0 and sum(HdrmAnyBelow[N].loc[i]==0)>0:
            assign[N][i]=HdrmAnyBelow[N].loc[i][HdrmAnyBelow[N].loc[i]==0].index[-1]
        if sum(HdrmSum[N].loc[i][HdrmAnyBelow[N].loc[i]<-2]>Thresh)>0:
            aa=HdrmSum[N].loc[i][HdrmAnyBelow[N].loc[i]<0]
            assign[N][i]=aa[aa>Thresh].index[-1]
            v2gZones[N].append(i)

print('')
print('---------------Number of EVs----------------------')
print(Allsums.astype(int))
print('--------------------------------------------------')
print('')
print('---------------kVA per Heatpump Limit-------------')
print(KVA_LIM)
print('--------------------------------------------------')
print('')
print('--------------------Number of Zones Needing Upgrade To meet HP Demand----------------------------')
print(AllHdRms.astype(int))
print('-------------------------------------------------------------------------------------------------')
print('')
print('--------------------Number of Zones with Headroom for V2G to support HPs-------------------------')
print(v2gs.astype(int))
print('-------------------------------------------------------------------------------------------------')        
pickle_out = open("../../Data/nEVs_NoShifting0.94.pickle", "wb")
pickle.dump(nEVs, pickle_out)
pickle_out.close()


# #     ##==============---------- Calculate Max HPs and Max Possible EVs------------================

# EVTDs =  pd.read_csv('../testcases/timeseries/Routine_10000EVTD.csv')
# EVs = pd.read_csv('../testcases/timeseries/Routine_10000EV.csv')
# all_means=[]
# for i in range(0,1000):
#     EVSample=EVs.sample(10)
#     EVTDSample=pd.DataFrame()
#     for s in EVSample['name']:
#         EVTDSample=EVTDSample.append(EVTDs[EVTDs['name']==s]) 
#     Daily=(EVTDSample['EEnd']-EVTDSample['EStart']).sum()/len(EVSample)
#     print(Daily)
#     all_means.append(Daily)
# print('Multi Mean Q95',np.quantile(all_means,0.95))  

# histo, binz = np.histogram(all_means, bins=range(0, int(max(all_means)), 1))
# fig, ax = plt.subplots(figsize=(5, 4))
# ax.bar(binz[:-1], histo, width=1, align="edge")
# ax.set_xlim(left=0,right=25)
# ax.set_ylabel("Frequency", fontsize=11)
# ax.set_xlabel("Mean EV Daily Charge (kWh)", fontsize=11)
# for t in ax.xaxis.get_majorticklabels():
#     t.set_fontsize(11)
# for t in ax.yaxis.get_majorticklabels():
#     t.set_fontsize(11)
# plt.plot([np.mean(all_means),np.mean(all_means)],[0,max(histo)], linewidth=1, color='black', label='Mean')
# plt.plot([np.quantile(all_means,0.75),np.quantile(all_means,0.75)],[0,max(histo)], linewidth=1,linestyle='--', color='orange', label='Q75')
# plt.plot([np.quantile(all_means,0.95),np.quantile(all_means,0.95)],[0,max(histo)], linewidth=1,linestyle=':', color='red', label='Q95')
# plt.grid(linewidth=0.2)
# plt.legend()
# plt.tight_layout()




#########-------------Create Mixed HP Penetration Customer Summaries--------############
for N in networks:
    Customer_Summary[N]['Final']=Customer_Summary[N]['00PV25HP']
    for i in HdrmSum[N].index:
        if assign[N][i] != '00PV00HP':
            ind=Customer_Summary[N]['Final'][Customer_Summary[N]['Final']['zone']==i].index
            Customer_Summary[N]['Final'].loc[ind]=Customer_Summary[N][assign[N][i]].loc[ind]
        else:
            ind=Customer_Summary[N]['Final'][Customer_Summary[N]['Final']['zone']==i].index
            Customer_Summary[N]['Final']['heatpump_ID'].loc[ind]=0
            Customer_Summary[N]['Final']['Heat_Pump_Flag'].loc[ind]=0
            Customer_Summary[N]['Final']['pv_ID'].loc[ind]=0
            Customer_Summary[N]['Final']['PV_kW'].loc[ind]=0
        pickle_out = open("../../Data/"+N+"Customer_Summary_Final0.94.pickle", "wb")
        pickle.dump(Customer_Summary[N], pickle_out)
        pickle_out.close()
pickle_out = open("../../Data/Assign_Final0.94.pickle", "wb")
pickle.dump(assign, pickle_out)
pickle_out.close()