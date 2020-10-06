# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 16:39:22 2019

@author: qsb15202
"""
import scipy.io
import numpy as np
import pandas as pd
import pickle
from matplotlib import pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize 
from scipy.interpolate import interpn
from matplotlib.lines import Line2D
pd.options.mode.chained_assignment = None

# ------------ Network Voltage Headroom calculation---------##

#### This script takes network current and voltage data, and plots
#### the relationship between minimum voltage and current at the pinch point

#def voltage_headroom(Pflow,Vmin):

## Network 17 done up to 25HP and 30EV
networks=['network_1/','network_5/','network_10/','network_17/','network_18/']
#networks=['network_17/']
Cases=['00PV00HP','00PV25HP']#,'25PV50HP']#,'25PV75HP','50PV100HP']
#Cases=['25PV75HP','50PV100HP']
EVPens=[10,20,30,40]

#networks=['network_18/']#,'network_5/','network_10/','network_17/','network_18/']
Y=14
#Cases=['00PV00HP','00PV25HP','25PV50HP','25PV75HP','50PV100HP']#,'25PV25HP','50PV50HP','75PV75HP','100PV100HP']
All_VC_Limits={}
#for Y in [14,15]:
pick_in = open("../Data/All_VC_Limits.pickle", "rb")
All_VC = pickle.load(pick_in)
VlowPerc={}
ChighPerc={}
TransPerc={}
Y=14
c=0
cols = ["grey","#9467bd", "#bcbd22","#ff7f0e","#d62728"] 
mk=['o','^','*','P','s']
style = ["--", ":", "-.", "--","-"]
fills = ["full", "left", "bottom", "right","none"]
times = ["0% HP", "25% HP", "50% HP","75% HP", "100%HP"]
times2 = ["00:00", "06:00", "12:00", "18:00"]
oks={}
allvmins={}
allchigh={}
allcusts={}
maxEVs=pd.DataFrame(index=Cases, columns=networks)
maxi={}
ncusts=pd.Series(index=networks)
for N in networks:
    o=0
    oks[N]={}
    VlowPerc[N]={}
    ChighPerc[N]={}
    TransPerc[N]={}
    AllPflow=[]
    maxi[N]=pd.DataFrame(columns=Cases)
    for C in Cases:
        
        oks[N][C]=pd.DataFrame(columns=EVPens)
        VlowPerc[N][C]=pd.DataFrame(columns=EVPens)
        ChighPerc[N][C]=pd.DataFrame(columns=EVPens)
        TransPerc[N][C]=pd.DataFrame(index=EVPens,columns=['All'])
        pick_in = open("../Data/"+N+"Customer_Summary"+C+str(Y)+".pickle", "rb")
        Customer_Summary= pickle.load(pick_in)  
        ncusts[N]=len(Customer_Summary)
        for E in EVPens:
            pick_in = open("../Data/Dumb/"+N+C+'EV'+str(E)+"Winter"+str(Y)+"_V_Data.pickle", "rb")
            V_data = pickle.load(pick_in)
            ##### Count Vmins < 0.9 and 0.94 ################
            VlowPerc[N][C][E]=round((V_data['Vmin']<0.9).sum()/len(V_data['Vmin'].index)*100,2)   
            TransPerc[N][C]['All'][E]=round((abs(V_data['Trans_kVA'])>800).sum()/len(V_data['Trans_kVA'].index)*100,2)   
            ChighPerc[N][C][E]=round((V_data['C_Violations']>0).sum()/len(V_data['C_Violations'].index)*100,2) 
            oks[N][C][E]=ChighPerc[N][C][E]
            for k in VlowPerc[N][C][E].index:
                oks[N][C][E][k]=(VlowPerc[N][C][E][k]==0) and (TransPerc[N][C]['All'][E]==0) and (ChighPerc[N][C][E][k]==0)
            maxi[N][C]=VlowPerc[N][C][10]
        for k in VlowPerc[N][C].index:
            if len(oks[N][C].loc[k][oks[N][C].loc[k]==True])>0:
                maxi[N][C][k]=oks[N][C].loc[k][oks[N][C].loc[k]==True][-1:].index[0]
            else:
                maxi[N][C][k]=0
                
        evflags=np.zeros(len(Customer_Summary))

        for k in VlowPerc[N][C].index:
            if maxi[N][C][k]>0:
                idx=Customer_Summary[Customer_Summary['zone']==k].index[::(int(100/maxi[N][C][k]))]
                evflags[idx]=1
            else:
                idx=Customer_Summary[Customer_Summary['zone']==k].index
                evflags[idx]=0
        
        maxEVs[N][C]=sum(evflags)
        maxEVs.loc['Total']=ncusts
        maxEVs[N][C]=str(maxEVs[N][C])+' ('+str(round(maxEVs[N][C]/maxEVs[N]['Total']*100,1))+'%)'
    
    zcusts=pd.Series(index=VlowPerc[N][C].index)
    for h in VlowPerc[N][C].index:
        pick_in = open("../Data/"+N+"Customer_Summary00PV00HP14.pickle", "rb")
        Customer_Summary= pickle.load(pick_in) 
        zcusts[h]=len(Customer_Summary[Customer_Summary['zone']==h])
        plt.plot(zcusts[h],VlowPerc[N]['00PV25HP'][40].loc[h], marker=mk[c], fillstyle=fills[c], color=cols[c],linestyle = 'None')
    c=c+1

plt.grid(linewidth=0.2)
custom=[Line2D([0],[0], marker='o', color="grey",fillstyle='full', markerfacecolor='grey', label='Network 1',linestyle = 'None'),
        Line2D([0],[0], marker='^', color="#9467bd",fillstyle='left', markerfacecolor='#9467bd', label='Network 5',linestyle = 'None'),
        Line2D([0],[0], marker='*', color="#bcbd22",fillstyle='bottom', markerfacecolor='#bcbd22', label='Network 10',linestyle = 'None'),
        Line2D([0],[0], marker='P', color="#ff7f0e",fillstyle='right', markerfacecolor='#ff7f0e', label='Network 17',linestyle = 'None'),
        Line2D([0],[0], marker='s', color="#d62728",fillstyle='none', label='Network 18',linestyle = 'None')]

leg2=plt.legend(handles=custom,loc=2,fontsize=12)
plt.gca().add_artist(leg2)
plt.xlabel('Number of Customers',fontsize=12)
plt.ylabel('% of timesteps with Voltage < 216 V',fontsize=12)

######----------------------Current PLot--------------------############

c=0
plt.figure()
for N in networks:
    pick_in = open("../Data/"+N+"Customer_Summary00PV00HP14.pickle", "rb")
    Customer_Summary= pickle.load(pick_in) 
    zcusts=pd.Series(index=ChighPerc[N][C].index)
    for h in ChighPerc[N][C].index:
        zcusts[h]=len(Customer_Summary[Customer_Summary['zone']==h])
        plt.plot(zcusts[h],ChighPerc[N]['00PV25HP'][40].loc[h], marker=mk[c], fillstyle=fills[c], color=cols[c],linestyle = 'None')
    c=c+1

plt.grid(linewidth=0.2)
leg2=plt.legend(handles=custom,loc=2,fontsize=12)
plt.gca().add_artist(leg2)
plt.xlabel('Number of Customers',fontsize=12)
plt.ylabel('% of timesteps with thermal violations',fontsize=12)

maxEVs=maxEVs.transpose()

###########---------------Transformer PLot------------##############
transmax={}
plt.figure()
u=0
for N in networks:
     pick_in = open("../Data/Dumb/"+N+"00PV25HPEV40Winter14_V_Data.pickle", "rb")
     V_data = pickle.load(pick_in)

     transmax[N]=[]
     for n in range(0,24):
         # transmins.append(V_data['Trans_kVA'].loc[V_data['Trans_kVA'].index.hour==n].min())
         # transmedian.append(np.quantile(V_data['Trans_kVA'].loc[V_data['Trans_kVA'].index.hour==n],0.5))
         transmax[N].append(abs(V_data['Trans_kVA']).loc[V_data['Trans_kVA'].index.hour==n].max())
    
     plt.plot(transmax[N],label=N[:-1],color=cols[u],linestyle=style[u])
     u=u+1
plt.plot(np.full(24,800), label='Tx Rating (kVA)',color='black',linewidth=0.5,linestyle=':')
plt.ylabel('Max Transformer Power Flow (kVA)')
plt.legend(fontsize=9,)
plt.grid(linewidth=0.2)
plt.xlim([0, 23])
plt.xticks(range(0,24,6),times2)