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

def plotDay(prices, gen, genmin,v2g,zone,nEVs,nCusts):
    ########-----------Plot Results----------#############
    prices.index=prices['timeperiod']
    prices=prices['cost(pounds/kwh)']
    gen=gen['Grid'].rename('PG_Max')
    genmin=genmin['Grid'].rename('PG_Min')
    results=pd.read_excel('results/results.xlsx', sheet_name='EVs')
    summary=pd.DataFrame(results.groupby(['Time period']).sum()['Charging(kW)'])
    discharge=pd.DataFrame(results.groupby(['Time period']).sum()['Discharging(kW)'])
    summary=summary.join(prices,how='outer')
    summary=summary.join(gen,how='outer')
    summary=summary.join(genmin,how='outer')
    summary=summary.join(v2g,how='outer')
    summary=summary.join(discharge,how='outer')
    
    times = ['12:00','16:00','20:00','24:00','04:00','08:00','12:00']
    fig, ax1 = plt.subplots()
    
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
    ax2.legend(lns, labs, loc=0)
    ax2.set_xlim(0,144)
    plt.xticks(range(0,168,24),times)
    plt.title('Zone- '+str(zone)+'. Max EVs - '+str(nEVs)+' / '+str(nCusts)+' customers')
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()
    
start=datetime.now()
#def daily_EVSchedule(Network,Case, factor):
Network='network_5/'
Case='00PV25HP'
factor=1
daytype='All'#'wkd'
start_date = date(2013, 12, 1)
end_date = date(2013, 12, 3)
delta_tenminutes = timedelta(minutes=10)
dt1 = pd.date_range(start_date, end_date, freq=timedelta(minutes=30))[24:73]
dt2 = pd.date_range(start_date, end_date, freq=delta_tenminutes)[72:216]

#pick_in = open("../Data/Network1SummerHdRm.pickle", "rb")
#SummerHdRm = pickle.load(pick_in)

pick_in = open("../Data/"+str(Network)+"Customer_Summary"+str(Case)+"14.pickle", "rb")
Customer_summary = pickle.load(pick_in)

pick_in = open("../Data/"+str(Network+Case)+"_WinterHdrm_"+str(daytype)+".pickle", "rb")
WinterHdRm = pickle.load(pick_in)

pick_in = open("../Data/"+str(Network+Case)+"_WinterFtrm_"+str(daytype)+".pickle", "rb")
WinterFtRm = pickle.load(pick_in)

pick_in = open("../Data/nEVs_NoShifting.pickle", "rb")
nEVs_All = pickle.load(pick_in)

EVTDs =  pd.read_csv('testcases/timeseries/Routine_10000EVTD.csv')
EVs = pd.read_csv('testcases/timeseries/Routine_10000EV.csv')

########------ Customers by Phase/Feeder ---------###
custsbyzone=[]
for c in list(WinterHdRm.keys()):
    CbyP=Customer_summary[Customer_summary['Phase']==c[0]]
    custsbyzone.append(len(CbyP[CbyP['Feeder']==c[1]]))

priceIn=pd.read_csv('Prices.csv')
priceIn['Total']=priceIn['DUoS']/100+0.032
priceIn=priceIn['Total']
priceIn.index=dt1
priceIn=priceIn.resample('10T').mean()
priceIn=priceIn.interpolate(method='pad')[:-1]

EVCapacitySummary=pd.DataFrame(columns=['Zone','Customers','EV Capacity'], index=range(0,len(WinterHdRm)))
EVCapacitySummary['Zone']=WinterHdRm.keys()
EVCapacitySummary['Customers']=custsbyzone
EVCapacitySummary['EV Capacity Reduced']=0
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

for i in WinterHdRm.keys():
    
    #a=WinterHdRm[i]['P5-'+str(TR)]*factor
    a=WinterHdRm[i]['P5']*0.7
    a.index=dt2
    hdrm=a[74:].append(a[:74])
    
    b=WinterFtRm[i]['P5']*0.8
    b.index=dt2
    ftrm=b[74:].append(b[:74])
        
    status[k]={}
    status[k][0]='Fail'
    l=1

    nEVs=int(nEVs_All[Network][Case][i])
    b=0
    c=0
    while status[k][l-1]=='Fail': 
        copyfile('testcases/timeseries/EVDay01_base.xlsx', 'testcases/timeseries/EVDay01_mix.xlsx')        
     
        gen=pd.read_excel('testcases/timeseries/EVDay01_mix.xlsx', sheet_name='genseries')
        genmin=pd.read_excel('testcases/timeseries/EVDay01_mix.xlsx', sheet_name='genmin')
        prices=pd.read_excel('testcases/timeseries/EVDay01_mix.xlsx', sheet_name='timeseriesGen')
       
        gen['Grid']=hdrm.values
        v2g=gen['Grid'].rename('v2g')
        v2g[v2g>0]=0
        prices['cost(pounds/kwh)']=priceIn.values
        prices['cost(pounds/kwh)'][gen['Grid']<0]=prices['cost(pounds/kwh)'][gen['Grid']<0]+0.125
        
        gen['Grid'][gen['Grid']<0]=0
        
        genmin['Grid']=-ftrm.values
        #genmin['Grid'][genmin['Grid']>0]=0

        EVSample=EVs.sample(n=nEVs)
        EVTDSample=pd.DataFrame()
        for s in EVSample['name']:
            EVTDSample=EVTDSample.append(EVTDs[EVTDs['name']==s])        


        
        
        book = load_workbook('testcases/timeseries/EVDay01_mix.xlsx')
           
        writer = pd.ExcelWriter('testcases/timeseries/EVDay01_mix.xlsx', engine='openpyxl')
        writer.book = book
        writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        
        EVSample.to_excel(writer, "EVs", columns=None, header=True, index=False, startrow=0)
        EVTDSample.to_excel(writer, "EVsTravelDiary", columns=None, header=True, index=False, startrow=0)
        gen.to_excel(writer, "genseries", columns=None, header=True, index=False, startrow=0)
        genmin.to_excel(writer, "genmin", columns=None, header=True, index=False, startrow=0)
        prices.to_excel(writer, "timeseriesGen", columns=None, header=True, index=False, startrow=0)
        
        writer.save()
        try:
            status[k][l]=main()
        except:
            status[k][l]='Fail'
        print('=================Zone '+i+' ======================')
        print('========================= Number of EVs is '+str(nEVs)+'======================')
        if status[k][l]=='Success' and b==0:
            EVCapacitySummary['EV Capacity'][k]=nEVs
        c=c+1
        if c > 3:
            nEVs=nEVs-1
            c=0
        results=pd.read_excel('results/results.xlsx', sheet_name='EVs')
        # netCharge=pd.Series(results.groupby(['Time period']).sum()['Charging(kW)']-results.groupby(['Time period']).sum()['Discharging(kW)'])
        # advancePeriods=genmin['Grid'][genmin['Grid']<0]
        # if (hdrm<0).any()==True and status[k][l]=='Success' and (((advancePeriods-netCharge)[netCharge.index].round(2)<0).any())==True:
        #     nEVs=nEVs-1
        #     EVCapacitySummary['EV Capacity Reduced'][k]=nEVs
        #     status[k][l]='Fail'
        #     b=1
        l=l+1
    k=k+1


    plotDay(prices, gen, genmin,v2g,i,nEVs,len(Customer_summary[Customer_summary['zone']==i]))
        
    
    #########----------- Write Outputs for Validation --------############
    
    dems={}
    IDs=results['name'].unique()
    
    for z in IDs:
        dems[z]=results['Charging(kW)'][results['name']==z]-results['Discharging(kW)'][results['name']==z]
        dems[z].index=dt2[results['Time period'][results['name']==z]-1] 
        dems[z]=dems[z].rename(z)
    AllEVs[i]=pd.DataFrame(index=dt2,dtype=float)
    
    for z in IDs:
        AllEVs[i]=AllEVs[i].join(dems[z], how='outer')
    
pickle_out = open("../Data/"+str(Network)+"EV_Dispatch_OneDay"+str(Case)+".pickle", "wb")
pickle.dump(AllEVs, pickle_out)
pickle_out.close()

end=datetime.now()

t_time=end-start
print('Days Optimisation took '+str(t_time))

#return EVCapacitySummary, AllEVs

# Case='25PV50HP'
# Network='network_1/'
# factor=1
# EVCapacitySummary, AllEVs=daily_EVSchedule(Network,Case, factor)