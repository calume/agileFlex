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
networks=['network_1/','network_5/','network_10/','network_18/']
#networks=['network_17/']
Cases=['00PV00HP','00PV25HP','25PV50HP']#,'25PV75HP','50PV100HP']
#Cases=['25PV75HP','50PV100HP']
EVPens=[10,20,30,40]

#networks=['network_18/']#,'network_5/','network_10/','network_17/','network_18/']
Y=14
#Cases=['00PV00HP','00PV25HP','25PV50HP','25PV75HP','50PV100HP']#,'25PV25HP','50PV50HP','75PV75HP','100PV100HP']


VlowPerc={}
ChighPerc={}
TransPerc={}
Y=14
c=0
cols = ["grey","#9467bd", "#bcbd22","#ff7f0e","#d62728"] 
mk=['+','x','o','s']
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

VlowAllZone={}
ChighAllZone={}
s=6
for C in Cases:
    VlowAllZone[C]=pd.DataFrame(index=EVPens, columns=networks)
    ChighAllZone[C]=pd.DataFrame(index=EVPens, columns=networks)
CP='00PV25HP'
for N in networks:
    pick_in = open("../Data/DumbRaw/"+N[:-1]+'_00PV00HPEV10_TransRatekVA.pickle', "rb")
    TransRateKVA = pickle.load(pick_in)   
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
            pick_in = open("../Data/Dumb/"+N+C+'EV'+str(E)+"_Vmin_DF.pickle", "rb")
            V_min = pickle.load(pick_in)
            
            pick_in = open("../Data/Dumb/"+N+C+'EV'+str(E)+"_C_Violations.pickle", "rb")
            C_Violations = pickle.load(pick_in)
            
            pick_in = open("../Data/DumbRaw/"+N[:-1]+'_'+C+'EV'+str(E)+"_Trans_kVA.pickle", "rb")
            TransKVA = pickle.load(pick_in)
            
            TransKVA_S=pd.Series(index=TransKVA.keys())
            for i in TransKVA.keys():
                TransKVA_S[i]=-TransKVA[i]
                
            ##### Count Vmins < 0.9 and 0.94 ################
            VlowPerc[N][C][E]=round((V_min<0.9).sum()/len(V_min.index)*100,2)   
            TransPerc[N][C]['All'][E]=round((abs(TransKVA_S)>TransRateKVA).sum()/len(TransKVA_S.index)*100,2)   
            ChighPerc[N][C][E]=round((C_Violations>0).sum()/len(C_Violations.index)*100,2)
            VlowAllZone[C][N][E]=sum((V_min<0.9).sum(axis=1)>0)/len(V_min)*100
            ChighAllZone[C][N][E]=sum(C_Violations.sum(axis=1)>0)/len(V_min)*100
            oks[N][C][E]=ChighPerc[N][C][E]
            for k in VlowPerc[N][C][E].index:
                oks[N][C][E][k]=(VlowPerc[N][C][E][k]==0) and (TransPerc[N][C]['All'][E]<=0.5) and (ChighPerc[N][C][E][k]<0.5)
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
        plt.plot(zcusts[h],VlowPerc[N][CP][40].loc[h], markersize=s, fillstyle='none', marker=mk[c], color=cols[c],linestyle = 'None')
    c=c+1

plt.grid(linewidth=0.2)
custom=[Line2D([0],[0], marker=mk[0], markersize=s,color=cols[0], fillstyle='none', label='Network 1',linestyle = 'None'),
        Line2D([0],[0], marker=mk[1], markersize=s,color=cols[1], fillstyle='none', label='Network 5',linestyle = 'None'),
        #Line2D([0],[0], marker=mk[2], markersize=s,color=cols[2], fillstyle='none', label='Network 10',linestyle = 'None'),
        Line2D([0],[0], marker=mk[2], markersize=s,color=cols[2], fillstyle='none', label='Network 17',linestyle = 'None'),
        Line2D([0],[0], marker=mk[3], markersize=s,color=cols[3], fillstyle='none', label='Network 18',linestyle = 'None')]
    
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
        plt.plot(zcusts[h],ChighPerc[N][CP][40].loc[h], markersize=s, fillstyle='none', marker=mk[c], color=cols[c],linestyle = 'None')
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
     transmax[N]=[]
     for n in range(0,24):
         # transmins.append(TransKVA_S.loc[TransKVA_S.index.hour==n].min())
         # transmedian.append(np.quantile(TransKVA_S.loc[TransKVA_S.index.hour==n],0.5))
         transmax[N].append(abs(TransKVA_S).loc[TransKVA_S.index.hour==n].max())
    
     plt.plot(transmax[N],label=N[:-1],color=cols[u],linestyle=style[u])
     u=u+1
plt.plot(np.full(24,800), label='Tx Rating (kVA)',color='black',linewidth=0.5,linestyle=':')
plt.ylabel('Max Transformer Power Flow (kVA)')
plt.legend(fontsize=9,)
plt.grid(linewidth=0.2)
plt.xlim([0, 23])
plt.xticks(range(0,24,6),times2)


plt.figure()

#mk=['+','x','o','2']
lbls=['Network 1','Network 5','Network 17','Network 18']
cases = ["10", "20","30", "40"]
styles=[':','--','-']

s=6
plt.subplot(3,1,1)
c=0
for N in networks:
    plt.plot(VlowAllZone[CP][N],marker=mk[c],color=cols[c],markersize=s, fillstyle='none', label=lbls[c],linestyle='none')
    c=c+1
    plt.xticks(TransPerc[N][CP].index,labels=cases)
    plt.grid(linewidth=0.2)
    plt.legend(framealpha=1,bbox_to_anchor=(0, 1.6), loc='upper left', ncol=2)
    plt.ylabel('Low Voltage',fontsize=12)
    plt.ylim(-0.5,100)
    plt.yscale('symlog')
    
plt.subplot(3,1,2)
c=0
for N in networks:
    plt.plot(ChighAllZone[CP][N],marker=mk[c],markersize=s,color=cols[c], fillstyle='none', label=lbls[c],linestyle='none')
    #plt.errorbar(ChighPerc[N].columns,ChighPerc[N].mean(),ChighPerc[N].mean()-ChighPerc[N].max(),uplims=True, marker=mk[c],fmt='.k', color=cols[c], ecolor=cols[c], lw=1, capsize=3)
    c=c+1
    plt.xticks(TransPerc[N][CP].index,labels=cases)
    plt.grid(linewidth=0.2)
    plt.ylabel('Cable',fontsize=12)
    plt.ylim(-0.5,100)
    plt.yscale('symlog')

plt.subplot(3,1,3)
c=0
for N in networks:
    plt.plot(TransPerc[N][CP],marker=mk[c],markersize=s,color=cols[c], fillstyle='none', label=lbls[c],linestyle='none')
    c=c+1
    plt.xticks(TransPerc[N][CP].index,labels=cases)
    plt.grid(linewidth=0.2)
    plt.xlabel('% EV Penetration',fontsize=12)
    plt.ylabel('Transformer',fontsize=12)
    plt.ylim(-0.5,100)
    plt.yscale('symlog')

        