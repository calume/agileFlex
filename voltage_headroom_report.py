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

networks=['network_1/','network_5/','network_17/','network_18/']
Y=14
Cases=['00PV00HP','00PV25HP','25PV50HP','25PV75HP','50PV100HP']#,'25PV25HP','50PV50HP','75PV75HP','100PV100HP']
#for Y in [14,15]:

VlowPerc={}
ChighPerc={}
Y=14
c=0
cols = ["grey","#9467bd", "#ff7f0e","#d62728"] 
mk=['+','x','o','s']
style = ["--", ":", "-.", "--","-"]
times = ["0% HP", "25% HP", "50% HP","75% HP", "100%HP"]
allvmins={}
allchigh={}
allcusts={}
transmax={}
TransPerc={}
TransCusts=pd.Series(index=networks)
times2 = ["00:00", "06:00", "12:00", "18:00"]
paths="../Data/Upper/"
s=6
VlowAllZone=pd.DataFrame(index=networks, columns=Cases)
ChighAllZone=pd.DataFrame(index=networks, columns=Cases)
for N in networks:
    
    AllVmin=pd.DataFrame()
    VlowPerc[N]=pd.DataFrame()
    ChighPerc[N]=pd.DataFrame()
    TransPerc[N]=pd.Series(dtype=float)
    AllPflow=pd.DataFrame()

    pick_in = open("../Data/Raw/"+N[:-1]+'_00PV00HP_TransRatekVA.pickle', "rb")
    TransRateKVA = pickle.load(pick_in)
    
    for C in Cases:

        pick_in = open("../Data/Raw/"+N[:-1]+'_'+C+"_Trans_kVA.pickle", "rb")
        TransKVA = pickle.load(pick_in)
        
        TransKVA_S=pd.Series(index=TransKVA.keys())
        for i in TransKVA.keys():
            TransKVA_S[i]=TransKVA[i]
            
        pick_in = open("../Data/"+N+"Customer_Summary"+C+str(Y)+".pickle", "rb")
        Customer_Summary= pickle.load(pick_in)   
        TransCusts[N]=len(Customer_Summary)
        
        pick_in = open("../Data/"+N+C+"_C_Violations.pickle", "rb")
        C_Violations = pickle.load(pick_in)
        
        pick_in = open("../Data/"+N+C+"_Vmin_DF.pickle", "rb")
        V_min = pickle.load(pick_in)
        

        VlowPerc[N]['nCusts']=0
        for k in V_min.columns:
            VlowPerc[N]['nCusts'][k]=len(Customer_Summary[Customer_Summary['zone']==k])
            if k[1]=='1':
                C_Violations[k]=0
        ##### Count Vmins < 0.9 and 0.94 ################
        VlowPerc[N][C]=round((V_min<0.9).sum()/len(V_min.index)*100,2)   
        TransPerc[N][C]=round((abs(TransKVA_S)>TransRateKVA).sum()/len(TransKVA_S.index)*100,2)   
        ChighPerc[N][C]=round((C_Violations>0).sum()/len(C_Violations.index)*100,2) 
        VlowAllZone[C][N]=sum((V_min<0.9).sum(axis=1)>0)/len(V_min)*100
        ChighAllZone[C][N]=sum(C_Violations.sum(axis=1)>0)/len(V_min)*100
    o=0

    for h in VlowPerc[N].columns[1:]:
        if c==0:
            allvmins[h]=[]
            allcusts[h]=[]
        allvmins[h].extend(VlowPerc[N][h].values)
        allcusts[h].extend(VlowPerc[N]['nCusts'].values)
   
    plt.plot(VlowPerc[N]['nCusts'],VlowPerc[N]['50PV100HP'], markersize=s, fillstyle='none', marker=mk[c], color=cols[c],linestyle = 'None')
    c=c+1



plt.grid(linewidth=0.2)
custom=[Line2D([0],[0], marker=mk[0], markersize=s,color=cols[0], fillstyle='none', label='Network 1',linestyle = 'None'),
        Line2D([0],[0], marker=mk[1], markersize=s,color=cols[1], fillstyle='none', label='Network 5',linestyle = 'None'),
        #Line2D([0],[0], marker=mk[2], markersize=s,color=cols[2], fillstyle='none', label='Network 10',linestyle = 'None'),
        Line2D([0],[0], marker=mk[2], markersize=s,color=cols[2], fillstyle='none', label='Network 17',linestyle = 'None'),
        Line2D([0],[0], marker=mk[3], markersize=s,color=cols[3], fillstyle='none', label='Network 18',linestyle = 'None')]
    
leg2=plt.legend(handles=custom,loc='upper left',fontsize=12)
plt.gca().add_artist(leg2)
plt.xlabel('Number of Customers (per zone)',fontsize=12)
plt.ylabel('% of timesteps with Voltage < 216 V',fontsize=12)

c=0
plt.figure()
for N in networks:
    o=0
    plt.plot(VlowPerc[N]['nCusts'],ChighPerc[N]['50PV100HP'], markersize=s, fillstyle='none', marker=mk[c], color=cols[c],linestyle = 'None')
    c=c+1

plt.grid(linewidth=0.2)
leg2=plt.legend(handles=custom,loc='upper left',fontsize=12)
plt.gca().add_artist(leg2)
plt.xlabel('Number of Customers (per zone)',fontsize=12)
plt.ylabel('% of timesteps with thermal violations',fontsize=12)
#plt.ylabel('Avg Number of Current Violations per Timestep',fontsize=12)


summary=pd.DataFrame(index=VlowPerc[N].columns[1:].append(pd.Index(['Total'])))
bycusts={}
FullSum=pd.DataFrame(index=networks, columns=['HPs','Total Customers'])
replace={}
ReplaceSum=pd.DataFrame(index=VlowPerc[N].columns[1:].append(pd.Index(['Total'])),columns=networks)
probzones={}
for N in networks:
    replace[N]=pd.DataFrame(index=VlowPerc[N].columns[1:], columns=VlowPerc[N].index)    
    for r in replace[N].index:
        for c in replace[N].columns:
            replace[N][c][r] = (VlowPerc[N][r][c]>0) or (ChighPerc[N][r][c]>0) #or (TransPerc[N][r]>0)
        ReplaceSum[N].loc[r]=(replace[N].loc[r]>0).sum(axis=0)
    probzones[N]={}
    probzones[N]['LV']=VlowPerc[N]['00PV00HP'][VlowPerc[N]['00PV00HP']>0]
    probzones[N]['HC']=ChighPerc[N]['00PV00HP'][ChighPerc[N]['00PV00HP']>0]
    bycusts[N]=pd.Series(index=VlowPerc[N].index)
    summary[N]=(VlowPerc[N][VlowPerc[N].columns[1:]]>0).sum()
    summary[N].loc['Total']=len(VlowPerc[N])
    
#    for k in summary[N].index[:-1]:
#        summary[N][k]['Total']= summary[N][k].sum()
#        summary[N][k]=str(int(summary[N][k]))+' ('+str((ChighPerc[N]>0.01).sum()[k])+')'
#        summary[N][k]['Total']= str(summary[N][k]['Total'])+' ('+str((ChighPerc[N]>0.01).sum()[k].sum())+')'
    #plt.xticks(VlowPerc[N].columns,times)
    
    for h in VlowPerc[N].index:
        
        ########-----------Check Voltage Violations
        if len(VlowPerc[N].loc[h][VlowPerc[N].loc[h]<0.5])>0:
            C=VlowPerc[N].loc[h][VlowPerc[N].loc[h]<0.5].index[-1]
        else:
            C='00PV00HP'
        pick_in = open("../Data/"+N+"Customer_Summary"+C+str(Y)+".pickle", "rb")
        Customer_Summary= pickle.load(pick_in)   
        Vsum=sum(Customer_Summary[Customer_Summary['zone']==h]['Heat_Pump_Flag']>0)
        
        ########---------- Check Current Violations
        if len(ChighPerc[N].loc[h][ChighPerc[N].loc[h]<0.5])>0:
            C=ChighPerc[N].loc[h][ChighPerc[N].loc[h]<0.5].index[-1]
        else:
            C='00PV00HP'
        pick_in = open("../Data/"+N+"Customer_Summary"+C+str(Y)+".pickle", "rb")
        Customer_Summary= pickle.load(pick_in)   
        Csum=sum(Customer_Summary[Customer_Summary['zone']==h]['Heat_Pump_Flag']>0) 
        
        #########--------- Check Transformer Violations
        if len(TransPerc[N][TransPerc[N]<0.5])>0:
            C=TransPerc[N][TransPerc[N]<0.5].index[-1]        
        else:
            C='00PV00HP'
            
        pick_in = open("../Data/"+N+"Customer_Summary"+C+str(Y)+".pickle", "rb")
        Customer_Summary= pickle.load(pick_in)   
        Tsum=sum(Customer_Summary[Customer_Summary['zone']==h]['Heat_Pump_Flag']>0) 
        
        bycusts[N][h]=min(Vsum,Csum,Tsum)
    
    FullSum['HPs'][N]=bycusts[N].sum()
    FullSum['Total Customers'][N]=len(Customer_Summary)
FullSum.append(pd.Series(FullSum.sum(),name='Total'))

pickle_out = open("../Data/Problem_Zones.pickle", "wb")
pickle.dump(probzones, pickle_out)
pickle_out.close()   
        

# ########==============Histogram of number of costomers per zone=============#######

# # all_means=allcusts['00PV00HP']
# # histo, binz = np.histogram(all_means, bins=range(0, int(max(all_means))+15, 5))
# # fig, ax = plt.subplots(figsize=(5, 4))
# # ax.bar(binz[:-1], histo, width=5, align="edge")
# # ax.set_xlim(left=0,right=100)
# # ax.set_ylabel("Frequency", fontsize=11)
# # ax.set_xlabel("Number of customers per zone", fontsize=11)
# # for t in ax.xaxis.get_majorticklabels():
# #     t.set_fontsize(11)
# # for t in ax.yaxis.get_majorticklabels():
# #     t.set_fontsize(11)
# # plt.plot([np.quantile(all_means,0.5),np.quantile(all_means,0.5)],[0,max(histo)], linewidth=1, color='black', label='Median')
# # plt.plot([np.quantile(all_means,0.75),np.quantile(all_means,0.75)],[0,max(histo)], linewidth=1,linestyle='--', color='orange', label='Q75')
# # plt.plot([np.quantile(all_means,0.95),np.quantile(all_means,0.95)],[0,max(histo)], linewidth=1,linestyle=':', color='red', label='Q95')
# # plt.grid(linewidth=0.2)
# # plt.legend()
# # plt.tight_layout()

plt.figure()
u=0
for N in networks:
    pick_in = open("../Data/Raw/"+N[:-1]+"_50PV100HP_Trans_kVA.pickle", "rb")
    TransKVA = pickle.load(pick_in)
    TransKVA_S=pd.Series(index=TransKVA.keys())
    for i in TransKVA.keys():
        TransKVA_S[i]=TransKVA[i]

    transmax[N]=[]
    for n in range(0,24):
         # transmins.append(TransKVA_S.loc[TransKVA_S.index.hour==n].min())
         # transmedian.append(np.quantile(TransKVA_S.loc[TransKVA_S.index.hour==n],0.5))
        transmax[N].append(abs(TransKVA_S).loc[TransKVA_S.index.hour==n].max())
    
    plt.plot(transmax[N],label=N[:-1],color=cols[u],linestyle=style[u])
    u=u+1
#plt.plot(np.full(24,800), label='Tx Rating (kVA)',color='black',linewidth=0.5,linestyle=':')
plt.ylabel('Max Transformer Power Flow (kVA)')
plt.legend(fontsize=9,)
plt.grid(linewidth=0.2)
plt.xlim([0, 23])
plt.xticks(range(0,24,6),times2)

plt.figure()

#mk=['+','x','o','2']
networks=['network_1/','network_5/','network_17/','network_18/']
lbls=['Network 1','Network 5','Network 17','Network 18']
cases = ["0", "25", "50","75", "100"]
styles=[':','--','-']
c=0

plt.subplot(3,1,1)
c=0
for N in networks:
    plt.plot(VlowAllZone.loc[N],marker=mk[c],color=cols[c],markersize=s, fillstyle='none', label=lbls[c],linestyle='none')
    c=c+1
    plt.xticks(TransPerc[N].index,labels=cases)
    plt.grid(linewidth=0.2)
    plt.legend(framealpha=1,bbox_to_anchor=(0, 1.6), loc='upper left', ncol=2)
    plt.ylabel('Low Voltage',fontsize=12)
    plt.ylim(-0.5,110)
    plt.yscale('symlog')
    
plt.subplot(3,1,2)
c=0
for N in networks:
    plt.plot(ChighAllZone.loc[N],marker=mk[c],markersize=s,color=cols[c], fillstyle='none', label=lbls[c],linestyle='none')
    #plt.errorbar(ChighPerc[N].columns,ChighPerc[N].mean(),ChighPerc[N].mean()-ChighPerc[N].max(),uplims=True, marker=mk[c],fmt='.k', color=cols[c], ecolor=cols[c], lw=1, capsize=3)
    c=c+1
    plt.xticks(TransPerc[N].index,labels=cases)
    plt.grid(linewidth=0.2)
    plt.ylabel('Cable',fontsize=12)
    plt.ylim(-0.5,110)
    plt.yscale('symlog')

plt.subplot(3,1,3)
c=0
for N in networks:
    plt.plot(TransPerc[N],marker=mk[c],markersize=s,color=cols[c], fillstyle='none', label=lbls[c],linestyle='none')
    c=c+1
    plt.xticks(TransPerc[N].index,labels=cases)
    plt.grid(linewidth=0.2)
    plt.xlabel('% HP Penetration',fontsize=12)
    plt.ylabel('Transformer',fontsize=12)
    plt.ylim(-0.5,110)
    plt.yscale('symlog')

        