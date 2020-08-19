##==================================================================
######## Create EV Charging profiles ##############
##==================================================================

import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import pickle

#def create_quants():
EVs=pd.read_csv('testcases/timeseries/Routine_10000EV.csv')

EVTDs=pd.read_csv('testcases/timeseries/RoutineChargeEvents_weeklong_RAW_10000cars.csv')
EVTDs=EVTDs[EVTDs.columns[1:]]

NumberofEVs=1500
EVSample=EVs.sample(n=NumberofEVs)

n=0
NewEVTDs={}
for z in EVSample['name']:
    EVTD_subset=EVTDs[EVTDs['VehicleID']==z]
    EVTD_subset=EVTD_subset[EVTD_subset['ChargeType']=='home']
    
    EVTD_OneDay=pd.DataFrame()
    
    ############Just do Weekdays
    EVTD_subset=EVTD_subset[(EVTD_subset['t0']-720)>=0]
    
    EVTD_OneDay['t_in']=(EVTD_subset['t0']-720)%1440
    EVTD_OneDay['t_out']=(EVTD_subset['t2']-720)%1440
    d=1
    c=0
    EVTD_OneDay['Day']=d
    for i in EVTD_OneDay.index:
        if EVTD_OneDay['t_out'][i]<EVTD_OneDay['t_in'][i]:
            EVTD_OneDay['t_in'][i]=EVTD_OneDay['t_in'][i]-1440
        if c>0 and EVTD_OneDay['t_in'][i] < EVTD_OneDay['t_out'][i-1]:
            d=d+1
        EVTD_OneDay['Day'][i]=d
        c=c+1

    EVTD_OneDay['t_in'],  EVTD_OneDay['t_out'] = EVTD_OneDay['t_in']/10,  EVTD_OneDay['t_out']/10
    
    EVTD_OneDay['EStart']=EVTD_subset['SoCStart']*EVSample['battery(kWh)'].iloc[n]
    EVTD_OneDay['EEnd']=EVTD_subset['SoCEnd']*EVSample['battery(kWh)'].iloc[n]
    
    if n<20:
        plt.figure(z)
        for i in EVTD_OneDay.index:    
            plt.plot([EVTD_OneDay['t_in'][i],EVTD_OneDay['t_out'][i]],[EVTD_OneDay['EStart'][i],EVTD_OneDay['EEnd'][i]],marker='o', ms=2,linestyle='--',linewidth=0.2 )
    NewEVTDs[z]=EVTD_OneDay
    n=n+1

pickle_out = open("../Data/EVTDs_1500EVs_wkd.pickle", "wb")
pickle.dump(NewEVTDs, pickle_out)
pickle_out.close()

pickle_out = open("../Data/EVs_1500EVs_wkd.pickle", "wb")
pickle.dump(EVSample, pickle_out)
pickle_out.close()
