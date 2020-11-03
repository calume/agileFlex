# -*- coding: utf-8 -*-
"""
Created on Tue Oct  6 14:40:46 2020

@author: CalumEdmunds
"""

import numpy as np
import pandas as pd
import pickle
from matplotlib import pyplot as plt
from datetime import datetime, timedelta, date, time

TxAdjuster={}

networks=['network_5/']#,'network_5/','network_10/','network_17/','network_18/']
times = ["12:00", "16:00", "20:00", "24:00", "04:00", "08:00", "12:00"]
for N in networks:
#    TxAdjuster[N]=pd.DataFrame(columns=cases)
    pick_in = open("../Data/Upper/perc0.02/"+N+"validation/Winter14_V_Data.pickle", "rb")
    V_data = pickle.load(pick_in)
    
    pick_in = open("../Data/Dumb/"+N+"25PV50HPEV50Winter14_V_Data.pickle", "rb")
    V_data_O_EV = pickle.load(pick_in)

    pick_in = open("../Data/"+N+"50PV100HPWinter14_V_Data.pickle", "rb")
    V_data_O = pickle.load(pick_in)


    tsamp=144
    dates=V_data['Trans_kVA'].index
    dailyrange = range(0, len(dates), tsamp)
    TxFlow_Opt = pd.DataFrame(index=dates[dailyrange], columns=range(0, tsamp),dtype=float)
    for d in TxFlow_Opt.index:
        mask = (V_data['Trans_kVA'].index >= d) & (V_data['Trans_kVA'].index < (d + timedelta(days=1)))
        TxFlow_Opt.loc[d] = V_data['Trans_kVA'].loc[mask].values

    dates=V_data_O_EV['Trans_kVA'].index
    dailyrange = range(0, len(dates), tsamp)
    TxFlow_Dumb = pd.DataFrame(index=dates[dailyrange], columns=range(0, tsamp),dtype=float)
    for d in TxFlow_Dumb.index:
        mask = (V_data_O_EV['Trans_kVA'].index >= d) & (V_data_O_EV['Trans_kVA'].index < (d + timedelta(days=1)))
        TxFlow_Dumb.loc[d] = -V_data_O_EV['Trans_kVA'].loc[mask].values

    dates=V_data_O['Trans_kVA'].index
    dailyrange = range(0, len(dates), tsamp)
    TxFlow_HP = pd.DataFrame(index=dates[dailyrange], columns=range(0, tsamp),dtype=float)
    for d in TxFlow_HP.index:
        mask = (V_data_O['Trans_kVA'].index >= d) & (V_data_O['Trans_kVA'].index < (d + timedelta(days=1)))
        TxFlow_HP.loc[d] = -V_data_O['Trans_kVA'].loc[mask].values 
    
#    TxAdjuster=TxFlow.max()
#    TxAdjuster[TxAdjuster<=800]=0
#    TxAdjuster[TxAdjuster>800]=TxAdjuster[TxAdjuster>800]-800
    tx_max_dumb=TxFlow_Dumb.max()[74:].append(TxFlow_Dumb.max()[:74])
    tx_max_HP=TxFlow_HP.max()[74:].append(TxFlow_HP.max()[:74])
    
    optfile='testcases/timeseries/EVDay01_mix10.xlsx'     
    prices=pd.read_excel(optfile, sheet_name='timeseriesGen')
    fig, ax1 = plt.subplots()
    fig.canvas.set_window_title(N)
    color = 'tab:red'
    #ax1.set_xlabel('time',,fontsize=9)
    ax1.set_ylabel('Max Tx apparent power flow (kVA)', color=color)
    lns1=ax1.plot(TxFlow_Opt.max().index, TxFlow_Opt.max(), linestyle='-',color=color, label="76% HP + \n82% Optimised EV")
    lns2=ax1.plot(TxFlow_Dumb.max().index, tx_max_dumb, linestyle=':', linewidth=1.5, color='green', label="50% HP + \n50% Dumb EV")
    lns3=ax1.plot(TxFlow_HP.max().index, tx_max_HP, linestyle='--', linewidth=1.5, color='blue', label="100% HP Only")
    lns4=ax1.plot(np.full(144,800),linestyle=':', linewidth=0.5, color='black', label="Tx Rating")
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_xlim(0,144)
    
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    
    color = 'tab:blue'
    ax2.set_ylabel('Price (p/kWh)', color=color)  # we already handled the x-label with ax1
    lns5=ax2.plot(prices.index, prices['cost(pounds/kwh)'].round(2)*100, color=color,linestyle="-.", label="Grid Price", linewidth=1)
    ax2.tick_params(axis='y', labelcolor=color)
    
    lns = lns1+lns2+lns3+lns4+lns5
    labs = [l.get_label() for l in lns]
    ax2.legend(lns, labs,loc=0,fontsize=9,framealpha=0.6)
    ax2.set_xlim(0,144)
    plt.xticks(range(0,168,24),times)
    
    #plt.ylim([0, 4])
    ax1.grid(linewidth=0.2)
    # plt.yticks([0,0.5,1,1.5])
    plt.xticks(range(0,tsamp+24,int(tsamp/6)),times)
    plt.tight_layout()

pickle_out = open("txnetwork18.pickle", "wb")
pickle.dump(TxAdjuster, pickle_out)
pickle_out.close()
