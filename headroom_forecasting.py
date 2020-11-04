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

def percentiles(Case,Network,paths):    
    tsamp=144
    
    pick_in = open(paths+Network+Case+"_HdRm.pickle", "rb")
    Headrm_DF = pickle.load(pick_in)

    pick_in = open(paths+Network+Case+"_Ftrm.pickle", "rb")
    Footrm_DF = pickle.load(pick_in)
    
    winter_dates = Headrm_DF.index[:-1]

    DailyDelta={}
    
    ########-------------- Daily Headroom irrespective of weekday/weekend -------###############
    for c in Headrm_DF.columns:
        print(c)
        dailyrange = range(0, len(winter_dates), tsamp)
        DailyDelta[c] = pd.DataFrame(index=winter_dates[dailyrange], columns=range(0, tsamp),dtype=float)
        for d in DailyDelta[c].index:
            mask = (Headrm_DF[c].index >= d) & (Headrm_DF[c].index < (d + timedelta(days=1)))
            DailyDelta[c].loc[d] = Headrm_DF[c].loc[mask].values
  
    pickle_out = open(paths+Network+Case+"_WinterHdrm_All.pickle", "wb")
    pickle.dump(DailyDelta, pickle_out)
    pickle_out.close()
    
    for c in Footrm_DF.columns:
        print(c)
        dailyrange = range(0, len(winter_dates), tsamp)
        DailyDelta[c] = pd.DataFrame(index=winter_dates[dailyrange], columns=range(0, tsamp),dtype=float)
        for d in DailyDelta[c].index:
            mask = (Footrm_DF[c].index >= d) & (Footrm_DF[c].index < (d + timedelta(days=1)))
            DailyDelta[c].loc[d] = Footrm_DF[c].loc[mask].values

    pickle_out = open(paths+Network+Case+"_WinterFtrm_All.pickle", "wb")
    pickle.dump(DailyDelta, pickle_out)
    pickle_out.close()  
        
    return DailyDelta


def headroom_plots(Network,Case,n,lbls,kva,paths,quant,factor):
    
    pick_in = open(paths+Network+Case+"_WinterHdrm_All.pickle", "rb")
    DailyDelta= pickle.load(pick_in)
    n_zones=len(DailyDelta)
    tsamp=144
    times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    cols = ["grey","#9467bd", "#bcbd22","#ff7f0e","#d62728"]    
    pick_in = open("../Data/"+Network+"Customer_Summary00PV00HP14.pickle", "rb")
    Customer_Summary= pickle.load(pick_in)    
          
    ########## Plot P-5 For all Cases On one Graph ###############
    r = 0
    plt.figure(Network+'Winter headroom, All Cases')           
    for c in DailyDelta.keys():
        dds=DailyDelta[c].quantile(quant)
        dds[dds<0]=dds[dds<0]/0.98
        dds[dds>0]=dds[dds>0]*0.98
        ncs=len(Customer_Summary[Customer_Summary['zone']==c])
        r = r + 1
        ax=plt.subplot(3, int(n_zones/3), r)
        plt.title('Zone '+str(c)+', Customers - '+str(ncs)+'\n kVA/HPs = '+str(kva[Network]['00PV25HP'][c]))
        if r <= int(n_zones)/3:
            plt.title("Feeder " + str(r)+'\n Zone '+str(c)+' Customers - '+str(ncs)+'\n kVA/HPs = '+str(kva[Network]['00PV25HP'][c]))
        if (r-1) % (int(n_zones)/3) == 0:
            plt.ylabel("Phase " + str(c[0]))
        ax.plot(np.full(tsamp, 0), color="red", linestyle="--", linewidth=0.5)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(range(0,tsamp+24,int(tsamp/6)),times)
        plt.plot(dds.values, linewidth=1, color=cols[n], label=lbls[n])
        #plt.plot(DailyDeltaPercentiles['Median'].values, linestyle="--", linewidth=1, color=cols[g], label='Median - '+str(names[g]))
        #plt.ylim(-40, 40)
        plt.ylim(-40, 50)
        plt.xlim(0, tsamp)
        
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    plt.tight_layout()
    plt.legend()



###################------------ plot HPs vs Headroom ----------###############
def HP_vs_Headroom(networks, Cases,paths,quant,factor):
    Customer_Summary={}
    DailyDelta={}
    HdrmSum={}
    HPSum={}  
    HdrmAnyBelow={}   
    for N in networks:
        
        Customer_Summary[N]={}
        DailyDelta[N]={}
        pick_in = open(paths+N+'00PV00HP'+"_WinterHdrm_All.pickle", "rb")
        DailyDeltaKeys= pickle.load(pick_in)
        HdrmSum[N]=pd.DataFrame(index=list(DailyDeltaKeys.keys()), columns=Cases)
        HPSum[N]=pd.DataFrame(index=list(DailyDeltaKeys.keys()), columns=Cases)
        HdrmAnyBelow[N]=pd.DataFrame(index=list(DailyDeltaKeys.keys()), columns=Cases)
        for C in Cases:        
            pick_in = open("../Data/"+N+"Customer_Summary"+C+"14.pickle", "rb")
            Customer_Summary[N][C]= pickle.load(pick_in)
            
            pick_in = open(paths+N+C+"_WinterHdrm_All.pickle", "rb")
            DailyDelta[N][C]= pickle.load(pick_in)
            
            
            for i in DailyDelta[N][C].keys():
                aboves = (DailyDelta[N][C][i].quantile(quant))[DailyDelta[N][C][i].quantile(quant)>=0].sum()
                belows = (DailyDelta[N][C][i].quantile(quant))[DailyDelta[N][C][i].quantile(quant)<0].sum()
                #HdrmSum[N][C][i]=(DailyPercentiles[N][C][i]['P5'][:60].sum()+DailyPercentiles[N][C][i]['P5'][96:].sum())/6  ##-- Day PV effect removed
                HdrmSum[N][C][i]=((aboves*0.98)+(belows/0.98) *factor)/6
                HdrmAnyBelow[N][C][i]=factor*(belows/0.98)/6
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
    return HPSum, HdrmSum,HdrmAnyBelow, DailyDelta, Customer_Summary


lbls=['0% HP, 0% PV','25% HP, 0% PV', '50% HP, 25% PV', '75% HP, 25% PV', '100% HP, 50% PV']  

# ########================ PLOT Single ZONE for report===================
# times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
# cols = ["grey","#9467bd", "#bcbd22","#ff7f0e","#d62728"]    
# style = ["--", ":", "-.", "--","-"]
# c=0
# tsamp=144
# Network='network_1/'
# for Case in Cases:
#     pick_in = open("../Data/"+Network+Case+"_WinterHdrm_All.pickle", "rb")
#     DailyDelta= pickle.load(pick_in)
#     # for i in DailyDelta['14'].index:
#     #     plt.plot(DailyDelta['14'].loc[i].values,linewidth=0.05)
#     plt.plot(DailyDelta['11'].quantile(0.05), label=lbls[c], linestyle=style[c],linewidth=2)
#     c=c+1
# #plt.title('Network 1 - Zone 14 Headroom')
# plt.ylabel('Headroom (kVA)',fontsize=11)
# plt.xticks(range(0,tsamp+24,int(tsamp/6)),times,fontsize=11)
# plt.plot(np.full(tsamp, 0), color="black", linestyle="--", linewidth=0.5)
# plt.legend(fontsize=11)
# plt.xlim(0, tsamp)
# plt.ylim(-25, 60)

#######------------- Create Table of Limits --------#############
def limit_table(paths,networks):  
    pick_in = open("../Data/All_C_Limits.pickle", "rb")
    All_C = pickle.load(pick_in)
    All_VCs={}
    All_Cs={}
    for N in networks:
        pick_in = open(paths+N+"All_VC_Limits.pickle", "rb")
        All_VC = pickle.load(pick_in)
        print(N)
        All_VCs[N]=pd.DataFrame(dtype=float)
        All_Cs[N]=pd.DataFrame(dtype=float)
        for p in range(1,4):
            pp=All_VC[N][All_VC[N].index.str[0]==str(p)]
            pp.index=pp.index.str[1].values
            pc=All_C[N][All_C[N].index.str[0]==str(p)]
            pc.index=pc.index.str[1].values
            All_VCs[N][p]=pp.round(1)
            All_Cs[N][p]=pc.round(1)
            
            for i in All_VCs[N][p].index:
                All_VCs[N][p][i]=min(All_VCs[N][p].loc[i],All_Cs[N][p].loc[i])
                
                All_VCs[N][p][i]=str(All_VCs[N][p][i])+' ('+str(str(All_Cs[N][p][i]))+')'
            
        All_VCs[N]=All_VCs[N].fillna('N/A')   
        print(All_VCs[N].to_latex())
        
def headroom_percentiles(networks,Cases,paths,quant,factor):
    q=5
    for N in networks:
    ###### ------------------ Create Daily Headroom Profiles -------------
        for C in Cases:
            print(N, C)
            DailyDelta=percentiles(C,N,paths)
            q=q+1
    
    
    HPSum, HdrmSum,HdrmAnyBelow, DailyDelta, Customer_Summary=HP_vs_Headroom(networks, Cases,paths,quant,factor)
    
    
    EVAvg=14.2 #kWh charge / day
    Thresh=120
    
    ########================ CALCULATE number of EVs ==============#######
    
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
        #plt.figure(N)
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
    
    ab=nEVs[N].sum().astype(int)
    ab.name=N
    Allsums=Allsums.join(ab.astype(int))
    Allsums[N]['Total Customers']=HPSum[N]['50PV100HP'].sum()
    count=count+1
    
    
    #######================= Calculate  Number of Heatpumps and V2G ZOnes =##################
    
    assign={}
    v2gZones={}
    AllHdRms=pd.DataFrame(index=Cases+['Total Zones'])
    v2gs=pd.DataFrame(index=Cases+['Total Zones'])
    for N in networks:
        aa=HdrmAnyBelow[N][HdrmAnyBelow[N]<0].count()
        aa.name=N
        AllHdRms=AllHdRms.join(aa)    
        AllHdRms[N]['Total Zones']=len(HdrmSum[N]['00PV25HP'])
        
        aa=(HdrmSum[N][HdrmAnyBelow[N]<0]>Thresh).sum()
        aa.name=N
        v2gs=v2gs.join(aa)    
        v2gs[N]['Total Zones']=len(HdrmSum[N]['00PV25HP'])    
        
        # for i in All_VC[N].index:
        #     All_VC[N].loc[i]=min(All_VC[N].loc[i],All_C[N].loc[i])
        
        q=0
        for C in Cases:
            ##headroom_plots(N,C,q,lbls,KVA_HP,paths,quant,factor)
            q=q+1
    
        assign[N]=pd.Series(index=HdrmSum[N].index,dtype=object)
        v2gZones[N]=[]
        for i in HdrmSum[N].index:
            if sum(HdrmAnyBelow[N].loc[i]==0) ==0:
                assign[N][i]='00PV00HP'
            if sum(HdrmAnyBelow[N].loc[i]<0) ==0:
                assign[N][i]='50PV100HP'
            if sum(HdrmAnyBelow[N].loc[i]<0) >0 and sum(HdrmAnyBelow[N].loc[i]==0)>0:
                assign[N][i]=HdrmAnyBelow[N].loc[i][HdrmAnyBelow[N].loc[i]==0].index[-1]
            if sum(HdrmSum[N].loc[i][HdrmAnyBelow[N].loc[i]<0]>Thresh)>0:
                aa=HdrmSum[N].loc[i][HdrmAnyBelow[N].loc[i]<0]
                assign[N][i]=aa[aa>Thresh].index[-1]
                v2gZones[N].append(i)
    
    
    nEVs_Final={}
    nHPs_Final={}
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
            pickle_out = open(paths+N+"Customer_Summary_Final.pickle", "wb")
            pickle.dump(Customer_Summary[N], pickle_out)
            pickle_out.close()
        nEVs_Final[N]=pd.Series(index=nEVs[N].index,dtype=int)
        nHPs_Final[N]=pd.Series(index=nEVs[N].index,dtype=int)
        for k in nEVs[N].index:
            Case=assign[N][k]
            nEVs_Final[N][k]=nEVs[N][Case][k]
            nHPs_Final[N][k]=HPSum[N][Case][k]
    nEVs_Final['network_17/']['27']=0
    nEVs_Final['network_5/']['13']=0
    pickle_out = open(paths+"nEVs_NoShifting.pickle", "wb")
    pickle.dump(nEVs_Final, pickle_out)
    pickle_out.close()
    
    pickle_out = open(paths+"nHPs_final.pickle", "wb")
    pickle.dump(nHPs_Final, pickle_out)
    pickle_out.close()
        
    pickle_out = open(paths+"Assign_Final.pickle", "wb")
    pickle.dump(assign, pickle_out)
    pickle_out.close()
#    
    
    print('---------------Number of EVs----------------------')
    for N in networks:
        print(N,'\n',nEVs_Final[N],'\n Total', sum(nEVs_Final[N]))
    print('')
    
    print('---------------Number of Heat Pumps-----------------------')
    for N in networks:
        Customer_Summary[N]['Final']['heatpump_ID']
        print(N,'\n',nHPs_Final[N],'\n Total', sum(nHPs_Final[N]))
    
    print('-----------------Assignation---------------------------------')
    print(assign)
    
    print('--------------------V2G Zones with Headroom for V2G to support HPs-------------------------')
    print(v2gZones)
    print('-------------------------------------------------------------------------------------------------')        
    

####==============---------- Calculate Max HPs and Max Possible EVs------------================

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

#######----- Histogram of EV daily charge---------------=================

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




