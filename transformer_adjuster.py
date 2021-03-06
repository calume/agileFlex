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

networks=['network_18/']#,'network_5/','network_10/','network_17/','network_18/']
times = ["12:00", "16:00", "20:00", "24:00", "04:00", "08:00", "12:00"]
for N in networks:
#    TxAdjuster[N]=pd.DataFrame(columns=cases)

    pick_in = open("../Data/DumbRaw/"+N[:-1]+"_25PV50HPEV40_Trans_kVA.pickle", "rb")
    TransKVA_O_EV_dict = pickle.load(pick_in)
    
    TransKVA_O_EV=pd.Series(index=TransKVA_O_EV_dict.keys())   
    for i in TransKVA_O_EV_dict:
        TransKVA_O_EV[i]=TransKVA_O_EV_dict[i]
    
    pick_in = open("../Data/DumbRaw/"+N[:-1]+"_25PV50HPEV40_TransRatekVA.pickle", "rb")
    TransRateKVA = pickle.load(pick_in)
    
    pick_in = open("../Data/Upper/"+N+"validation/Winter14_V_Data.pickle", "rb")
    V_data = pickle.load(pick_in)
    
    pick_in = open("../Data/Raw/"+N[:-1]+"_50PV100HP_Trans_kVA.pickle", "rb")
    TransKVA_O_dict = pickle.load(pick_in)

    TransKVA_O=pd.Series(index=TransKVA_O_dict.keys())   
    for i in TransKVA_O_dict:
        TransKVA_O[i]=TransKVA_O_dict[i]

    tsamp=144
    dates=V_data['Trans_kVA'].index
    dailyrange = range(0, len(dates), tsamp)
    TxFlow_Opt = pd.DataFrame(index=dates[dailyrange], columns=range(0, tsamp),dtype=float)
    for d in TxFlow_Opt.index:
        mask = (V_data['Trans_kVA'].index >= d) & (V_data['Trans_kVA'].index < (d + timedelta(days=1)))
        TxFlow_Opt.loc[d] = -V_data['Trans_kVA'].loc[mask].values

    dates=TransKVA_O_EV.index
    dailyrange = range(0, len(dates), tsamp)
    TxFlow_Dumb = pd.DataFrame(index=dates[dailyrange], columns=range(0, tsamp),dtype=float)
    for d in TxFlow_Dumb.index:
        mask = (TransKVA_O_EV.index >= d) & (TransKVA_O_EV.index < (d + timedelta(days=1)))
        TxFlow_Dumb.loc[d] = -TransKVA_O_EV.loc[mask].values

    dates=TransKVA_O.index
    dailyrange = range(0, len(dates), tsamp)
    TxFlow_HP = pd.DataFrame(index=dates[dailyrange], columns=range(0, tsamp),dtype=float)
    for d in TxFlow_HP.index:
        mask = (TransKVA_O.index >= d) & (TransKVA_O.index < (d + timedelta(days=1)))
        TxFlow_HP.loc[d] = -TransKVA_O.loc[mask].values 
    
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
    lns1=ax1.plot(TxFlow_Opt.max().index, TxFlow_Opt.max(), linestyle='-',color=color, label="57% HP + \n72% Optimised EV")
    lns2=ax1.plot(TxFlow_Dumb.max().index, tx_max_dumb, linestyle=':', linewidth=1.5, color='green', label="50% HP + \n40% Dumb EV")
    lns3=ax1.plot(TxFlow_HP.max().index, tx_max_HP, linestyle='--', linewidth=1.5, color='blue', label="100% HP Only")
    lns4=ax1.plot(np.full(144,TransRateKVA),linestyle=':', linewidth=2, color='black', label="Tx Rating")
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_xlim(0,144)
    
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    
    color = 'tab:blue'
    ax2.set_ylabel('Price (p/kWh)', color=color)  # we already handled the x-label with ax1
    lns5=ax2.plot(prices.index, prices['cost(pounds/kwh)'].round(2)*100, color=color,linestyle="-.", label="Grid Price", linewidth=1)
    ax2.tick_params(axis='y', labelcolor=color)
    
    lns = lns1+lns2+lns3+lns4+lns5
    labs = [l.get_label() for l in lns]
    ax2.legend(lns, labs,fontsize=9,framealpha=0.6, bbox_to_anchor=(0, 1.3), loc='upper left', ncol=2)
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
