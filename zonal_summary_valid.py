# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 11:31:31 2020

@author: CalumEdmunds
"""
import pickle
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None
from matplotlib import pyplot as plt
from datetime import datetime, timedelta, date, time
from runfile import main
from shutil import copyfile
from openpyxl import load_workbook
import random
import multiprocessing
from joblib import Parallel, delayed
from tqdm import tqdm
num_cores = multiprocessing.cpu_count()


def plotDay(prices, gen, genmin,v2g,zone,nEVs,nCusts,results):
    ########-----------Plot Results----------#############
    prices.index=prices['timeperiod']
    prices=prices['cost(pounds/kwh)']
    gen=gen['Grid'].rename('PG_Max')
    genmin=genmin['Grid'].rename('PG_Min')
    summary=pd.DataFrame(results.groupby(['Time period']).sum()['Charging(kW)'])
    discharge=pd.DataFrame(results.groupby(['Time period']).sum()['Discharging(kW)'])
    summary=summary.join(prices,how='outer')
    summary=summary.join(gen,how='outer')
    summary=summary.join(genmin,how='outer')
    summary=summary.join(v2g,how='outer')
    summary=summary.join(discharge,how='outer')
    
    times = ['12:00','16:00','20:00','24:00','04:00','08:00','12:00']
    fig, ax1 = plt.subplots()
    fig.canvas.set_window_title(zone)
    color = 'tab:red'
    ax1.set_xlabel('time')
    ax1.set_ylabel('Headroom / EV Charge/Discharge (kW)', color=color)
    lns1=ax1.plot(summary.index, summary['Charging(kW)']-summary['Discharging(kW)'], color=color, label="Net EV Charge")
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_xlim(0,144)
    
    lns2=ax1.plot(summary.index, summary['PG_Min'], color='red', linestyle="--", label="Footroom")
    lns3=ax1.plot(summary.index, summary['v2g'], color='black', linestyle=":", label="V2G Request")
    lns4=ax1.plot(summary.index, summary['PG_Max'], color='green', linestyle="--", label="Headroom")
    
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    
    color = 'tab:blue'
    ax2.set_ylabel('Price (£/kWh)', color=color)  # we already handled the x-label with ax1
    lns5=ax2.plot(summary.index, summary['cost(pounds/kwh)'], color=color, label="Grid+V2G Price")
    ax2.tick_params(axis='y', labelcolor=color)
    
    lns = lns1+lns2+lns3+lns4+lns5
    labs = [l.get_label() for l in lns]
    ax2.legend(lns, labs,loc='center')
    ax2.set_xlim(0,144)
    plt.xticks(range(0,168,24),times)
    plt.title('Zone- '+str(zone)+'. Max EVs - '+str(nEVs)+' / '+str(nCusts)+' customers')
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()
    
start=datetime.now()
networks=['network_1/','network_5/','network_10/','network_17/','network_18/']

def daily_EVSchedule(Network):

#pick_in = open("../Data/nEVs_NoShifting.pickle", "rb")
#nEVs_All = pickle.load(pick_in)
    
    pick_in = open("../Data/"+str(Network)+"nEVs_Realised0.94.pickle", "rb")
    nEVs_All = pickle.load(pick_in)

#for Network in networks:
    factor=0.95
    daytype='All'#'wkd'
    start_date = date(2013, 12, 1)
    end_date = date(2013, 12, 3)
    delta_tenminutes = timedelta(minutes=10)
    dt1 = pd.date_range(start_date, end_date, freq=timedelta(minutes=30))[24:73]
    dt2 = pd.date_range(start_date, end_date, freq=delta_tenminutes)[72:216]
    
    #pick_in = open("../Data/Network1SummerHdRm.pickle", "rb")
    #SummerHdRm = pickle.load(pick_in)
    
    pick_in = open("../Data/"+str(Network)+"Customer_Summary_Final0.94.pickle", "rb")
    Customer_summary = pickle.load(pick_in)
    
    Customer_summary=Customer_summary['Final']
    
    pick_in = open("../Data/Assign_Final0.94.pickle", "rb")
    assign = pickle.load(pick_in)
    
    EVTDs =  pd.read_csv('testcases/timeseries/Routine_10000EVTD.csv')
    EVs = pd.read_csv('testcases/timeseries/Routine_10000EV.csv')
    
    ########------ Customers by Phase/Feeder ---------###
    custsbyzone=[]
    for c in (nEVs_All.index):
        CbyP=Customer_summary[Customer_summary['Phase']==c[0]]
        custsbyzone.append(len(CbyP[CbyP['Feeder']==c[1]]))
    
    priceIn=pd.read_csv('Prices.csv')
    priceIn['Total']=priceIn['DUoS']/100+0.032
    priceIn=priceIn['Total']
    priceIn.index=dt1
    priceIn=priceIn.resample('10T').mean()
    priceIn=priceIn.interpolate(method='pad')[:-1]
    
    EVCapacitySummary=pd.DataFrame(columns=['Zone','Customers','EV Capacity'], index=nEVs_All.index)
    EVCapacitySummary['Zone']=nEVs_All.index
    EVCapacitySummary['Customers']=custsbyzone
    EVCapacitySummary['EV Capacity']=0
    EVCapacitySummary['EV Capacity New']=0
    status={}
    AllEVs={}
    k=0
    
    # if -1.2 <= temp <= 1.9:
    #     TR=1
    # if 1.9 < temp <= 4.9:
    #     TR=2
    # if 4.9 < temp <= 8:
    #     TR=3
    # if 8 < temp <= 11:
    #     TR=2
    
    ###------------Update Assign Dataframe with 10x solvable nEVs -once only-----------######
    
    #nEVs_All[Network]['Realised']=0
    
    for i in nEVs_All.index:
        Case=assign[Network][i]
        EVCapacitySummary['EV Capacity'].loc[i]=nEVs_All[i]
        nEVs=int(nEVs_All[i])
        #nEVs=int(nEVs_All[Network]['Realised'][i])
        j=1
        #if Case != '00PV00HP':
        pick_in = open("../Data/"+Network+"upperVlimit/"+Case+"_WinterHdrm_"+str(daytype)+".pickle", "rb")
        WinterHdRm = pickle.load(pick_in)
        
        pick_in = open("../Data/"+Network+"upperVlimit/"+Case+"_WinterFtrm_"+str(daytype)+".pickle", "rb")
        WinterFtRm = pickle.load(pick_in)
        
        a=WinterHdRm[i]['P5']*factor
        a.index=dt2
        hdrm=a[74:].append(a[:74])
        
        b=WinterFtRm[i]['P5']*factor
        b.index=dt2
        ftrm=b[74:].append(b[:74])
            
        status[k]={}
        status[k][0]='Fail'
        l=1
        b=0

        while (status[k][l-1]=='Fail' and nEVs>0) or (j<2 and nEVs>0): 
            net=Network[8:-1]
            optfile='testcases/timeseries/EVDay01_mix'+net+'.xlsx'
            copyfile('testcases/timeseries/EVDay01_base.xlsx', optfile)        
            gen=pd.read_excel(optfile, sheet_name='genseries')
            genmin=pd.read_excel(optfile, sheet_name='genmin')
            prices=pd.read_excel(optfile, sheet_name='timeseriesGen')
           
            gen['Grid']=hdrm.values
            v2g=gen['Grid'].rename('v2g')
            v2g[v2g>0]=0
            prices['cost(pounds/kwh)']=priceIn.values
            prices['cost(pounds/kwh)'][gen['Grid']<0]=prices['cost(pounds/kwh)'][gen['Grid']<0]+0.175
            
            gen['Grid'][gen['Grid']<0]=0
            
            genmin['Grid']=-ftrm.values
            #genmin['Grid'][genmin['Grid']>0]=0
            EVSample=EVs.sample(n=nEVs)
            EVTDSample=pd.DataFrame()
            for s in EVSample['name']:
                EVTDSample=EVTDSample.append(EVTDs[EVTDs['name']==s])        
            EV_Avg=(EVTDSample['EEnd']-EVTDSample['EStart']).sum()/len(EVSample)
            book = load_workbook(optfile)
               
            writer = pd.ExcelWriter(optfile, engine='openpyxl')
            writer.book = book
            writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
            
            EVSample.to_excel(writer, "EVs", columns=None, header=True, index=False, startrow=0)
            EVTDSample.to_excel(writer, "EVsTravelDiary", columns=None, header=True, index=False, startrow=0)
            gen.to_excel(writer, "genseries", columns=None, header=True, index=False, startrow=0)
            genmin.to_excel(writer, "genmin", columns=None, header=True, index=False, startrow=0)
            prices.to_excel(writer, "timeseriesGen", columns=None, header=True, index=False, startrow=0)
            
            writer.save()
            try:
                status[k][l]=main(net)
            except:
                status[k][l]='Fail'
                b=b+1
                print(Network, Case,',Zone',i,', nEVs ', nEVs,', run',j,'Avg Charge',round(EV_Avg,1), 'kWh ,Fail')
                j=1
                nEVs=nEVs-1
            
            if status[k][l]=='Success':
                b=0
                j=j+1
                results=pd.read_excel('results/results'+net+'.xlsx', sheet_name='EVs')
            EVCapacitySummary['EV Capacity New'][i]=nEVs
            #nEVs_All['Realised'][i]=nEVs
            
            # netCharge=pd.Series(results.groupby(['Time period']).sum()['Charging(kW)']-results.groupby(['Time period']).sum()['Discharging(kW)'])
            # advancePeriods=genmin['Grid'][genmin['Grid']<0]
            # if (hdrm<0).any()==True and status[k][l]=='Success' and (((advancePeriods-netCharge)[netCharge.index].round(2)<0).any())==True:
            #     nEVs=nEVs-1
            #     EVCapacitySummary['EV Capacity Reduced'][k]=nEVs
            #     status[k][l]='Fail'
            #     b=1
            l=l+1
        k=k+1
        
#        if status[k-1][l-1]=='Success':
#            plotDay(prices, gen, genmin,v2g,i,nEVs,len(Customer_summary[Customer_summary['zone']==i]),results)
#                
            
            #########----------- Write Outputs for Validation --------############
            
        dems={}
        if status[k-1][l-1] =='Success':
            IDs=results['name'].unique()
            
            for z in IDs:
                dems[z]=results['Charging(kW)'][results['name']==z]-results['Discharging(kW)'][results['name']==z]
                dems[z].index=dt2[results['Time period'][results['name']==z]-1] 
                dems[z]=dems[z].rename(z)
            AllEVs[i]=pd.DataFrame(index=dt2,dtype=float)
            
            for z in IDs:
                AllEVs[i]=AllEVs[i].join(dems[z], how='outer')
            print(Network, Case,',Zone',i,', nEVs ', nEVs,', run',j,'Avg Charge',round(EV_Avg,1), 'kWh ,Success')
        else:
            print(Network, Case,',Zone',i,', nEVs ', nEVs,', run',j,'Avg Charge',round(EV_Avg,1), 'kWh , No EVs')   
    pickle_out = open("../Data/"+str(Network)+"EV_Dispatch_OneDay0.94.pickle", "wb")
    pickle.dump(AllEVs, pickle_out)
    pickle_out.close()
    
#    pickle_out = open("../Data/"+str(Network)+"nEVs_Realised.pickle", "wb")
#    pickle.dump(nEVs_All[Network]['Realised'], pickle_out)
#    pickle_out.close()
#    
    end=datetime.now()
    
    t_time=end-start
    print('Days Optimisation took '+str(t_time))


    return EVCapacitySummary, AllEVs

# #networks=['network_1/','network_5/','network_10/','network_17/','network_18/']
# networks=['network_17/','network_18/']
# inputs = tqdm(networks)

# if __name__ == "__main__":
#     processed_list = Parallel(n_jobs=num_cores)(delayed(daily_EVSchedule)(i) for i in inputs)


# EVCapacitySummary={}
# AllEVs={}
# for N in networks:
#     EVCapacitySummary[N]={}
#     AllEVs[N]={}
#     daily_EVSchedule(N)

##########--- Sample Table for report
#EVSS=EVTDSample.copy()
#evsinH=((EVSS['t_in']*10)//60+12).values.astype(str)
#evsinM=((EVSS['t_in']*10)%60).values.astype(str)
#
#evsoutH=(((EVSS['t_out']*10)//60+12)%12).values.astype(str)
#evsoutM=((EVSS['t_out']*10)%60).values.astype(str)
#for i in range(0,len(evsinH)):
#    evsinH[i]=evsinH[i]+evsinM[i]
#
#for i in range(0,len(evsoutH)):
#    evsoutH[i]=evsoutH[i]+evsoutM[i]
#
#EVSS['t_in']=evsinH.astype(int)
#EVSS['t_out']=evsoutH.astype(int)
##EVSS['t_out']=EVSS['t_out']%1440
#
#EVSS['EStart']=EVSS['EStart'].round(1)
#EVSS['EEnd']=EVSS['EEnd'].round(1)
#
#EVSS['name']=EVSS['name'].astype(str).str[6:]


#######---------DUOS Plot -------------##########
times2 = ["12:00", "18:00", "00:00", "06:00"]
priceIn=pd.read_csv('Prices.csv')
plt.bar(priceIn.index,priceIn['DegradationLow (V2GB)'].values, label='Degradation', hatch='X')
plt.bar(priceIn.index,priceIn['DUoS'].values, label='DUoS', color='red',hatch='.',bottom=priceIn['DegradationLow (V2GB)'].values)
plt.bar(priceIn.index,priceIn['V2G'].values, label='V2G', bottom=(priceIn['DUoS'].values+priceIn['DegradationLow (V2GB)'].values), hatch='+')
plt.legend()
plt.grid(linewidth=0.2)
plt.ylabel('Price (p/kWh)')
plt.xlim([0, 47])
plt.xticks(range(0,48,12),times2)
