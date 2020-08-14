#==================================================================
# runfile.py
# This is a top level script.
# EV charging scheduling problem
# ---Author---
# W. Bukhsh,
# wbukhsh@gmail.com
# OATS
# Copyright (c) 2019 by W. Bukhsh, Glasgow, Scotland
# OATS is distributed under the GNU GENERAL PUBLIC LICENSE v3. (see LICENSE file for details).
#==================================================================

import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import pickle

def create_quants():
    EVs=pd.read_csv('testcases/timeseries/Routine_10000EV.csv')
    
    EVTDs=pd.read_csv('testcases/timeseries/RoutineChargeEvents_weeklong_RAW_10000cars.csv')
    EVTDs=EVTDs[EVTDs.columns[1:]]
    
    EVDist=EVs['battery(kWh)']
    
    NumberofEVs=850
    
    Quants75=pd.DataFrame(index=range(0,NumberofEVs),columns=['t_in','t_out','EStart','EEnd'])
    Quants95=pd.DataFrame(index=range(0,NumberofEVs),columns=['t_in','t_out','EStart','EEnd'])
    n=0
    NewEVs=pd.DataFrame(index=range(0,NumberofEVs),columns=EVs.columns)
    NewEVTDs={}
    for z in Quants75.index:
        EV_subset=EVs.sort_values('battery(kWh)')[z*10:(z+1)*10]
        EV_subset=EV_subset[EV_subset['battery(kWh)']==EV_subset['battery(kWh)'].iloc[0]]
        NewEVs.iloc[z]=EV_subset.iloc[0]
        NewEVs['name'][z]=z+1
        EVTD_subset=EVTDs[EVTDs['VehicleID'].isin(EV_subset['name'])]
        EVTD_subset=EVTD_subset[EVTD_subset['ChargeType']=='home']
        
        EVTD_OneDay=pd.DataFrame()
        
        ############Just do Weekdays
        EVTD_subset=EVTD_subset[EVTD_subset['t0']>7200]
        
        EVTD_OneDay['t_in']=EVTD_subset['t0']%1440
        EVTD_OneDay['t_out']=EVTD_subset['t2']%1440
        
        for i in EVTD_OneDay.index:
            if EVTD_OneDay['t_out'][i]<EVTD_OneDay['t_in'][i]:
                EVTD_OneDay['t_out'][i]=EVTD_OneDay['t_out'][i]+1440
                
        EVTD_OneDay['t_in'],  EVTD_OneDay['t_out'] = EVTD_OneDay['t_in']/10-72,  EVTD_OneDay['t_out']/10-72
        
        EVTD_OneDay['EStart']=EVTD_subset['SoCStart']*EV_subset['battery(kWh)'].iloc[0]
        EVTD_OneDay['EEnd']=EVTD_subset['SoCEnd']*EV_subset['battery(kWh)'].iloc[0]
        
        quan=0.75
        Quants75['t_in'][z], Quants75['t_out'][z] = EVTD_OneDay['t_in'].quantile(quan), EVTD_OneDay['t_out'].quantile(quan)
        Quants75['EStart'][z], Quants75['EEnd'][z] = EVTD_OneDay['EStart'].quantile(1-quan),EVTD_OneDay['EEnd'].quantile(1-quan)
        quan=0.95
        Quants95['t_in'][z], Quants95['t_out'][z] = EVTD_OneDay['t_in'].quantile(quan), EVTD_OneDay['t_out'].quantile(0.5)
        Quants95['EStart'][z], Quants95['EEnd'][z] = EVTD_OneDay['EStart'].quantile(1-quan),EVTD_OneDay['EEnd'].quantile(1-quan)
        
        d='yup'
        if Quants75['t_out'][z]<Quants75['t_in'][z]:
            d='nope'
            n=n+1
        if z<20 and d=='yup':
            plt.figure(z)
            for i in EVTD_OneDay.index:    
                plt.plot([EVTD_OneDay['t0'][i],EVTD_OneDay['t2'][i]],[EVTD_OneDay['EStart'][i],EVTD_OneDay['EEnd'][i]],marker='o', ms=2,linestyle='--',linewidth=0.2 )
    
            plt.plot([Quants75['t_in'][z],Quants75['t_out'][z]],[Quants75['EStart'][z],Quants75['EEnd'][z]],color='black',marker='o', ms=6,linestyle='-',linewidth=1.5,label='Q75')
            plt.plot([Quants95['t_in'][z],Quants95['t_out'][z]],[Quants95['EStart'][z],Quants95['EEnd'][z]],color='blue',marker='o', ms=6,linestyle='-',linewidth=1.5,label='Q95' )
            
            plt.legend()
        NewEVTDs[z]=EVTD_OneDay
    
    pickle_out = open("../Data/EV_75Quantile850EVs_wkd.pickle", "wb")
    pickle.dump(Quants75, pickle_out)
    pickle_out.close()
    
    pickle_out = open("../Data/EVTDs_850EVs_wkd.pickle", "wb")
    pickle.dump(NewEVs, pickle_out)
    pickle_out.close()
    
    pickle_out = open("../Data/EVs_850EVs_wkd.pickle", "wb")
    pickle.dump(NewEVs, pickle_out)
    pickle_out.close()
    Quants75=Quants75.drop(Quants75[Quants75['t_out']<Quants75['t_in']].index)
    return Quants75,n


Quants75,n=create_quants()
