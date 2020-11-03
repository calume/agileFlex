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

networks=['network_1/','network_5/','network_10/','network_17/','network_18/']
Y=14
Cases=['00PV00HP','00PV25HP','25PV50HP','25PV75HP','50PV100HP']#,'25PV25HP','50PV50HP','75PV75HP','100PV100HP']
All_VC_Limits={}
#for Y in [14,15]:

VlowPerc={}
ChighPerc={}
Y=14
c=0
cols = ["grey","#9467bd", "#bcbd22","#ff7f0e","#d62728"] 
mk=['o','^','*','P','s']
style = ["--", ":", "-.", "--","-"]
fills = ["full", "left", "bottom", "right","none"]
times = ["0% HP", "25% HP", "50% HP","75% HP", "100%HP"]
allvmins={}
allchigh={}
allcusts={}
transmax={}
TransPerc={}
TransCusts=pd.Series(index=networks)
times2 = ["00:00", "06:00", "12:00", "18:00"]
paths="../Data/Upper/"

for N in networks:
    pick_in = open(paths+N+"All_VC_Limits.pickle", "rb")
    All_VC = pickle.load(pick_in)
    
    AllVmin=pd.DataFrame()
    VlowPerc[N]=pd.DataFrame()
    ChighPerc[N]=pd.DataFrame()
    TransPerc[N]=pd.Series(dtype=float)
    AllPflow=pd.DataFrame()
    
    for C in Cases:

        pick_in = open("../Data/Raw/"+N[:-1]+'_'+C+"_Trans_kVA.pickle", "rb")
        TransKVA = pickle.load(pick_in)
        
        pick_in = open("../Data/Raw/"+N[:-1]+'_'+C+"_TransRatekVA.pickle", "rb")
        TransRateKVA = pickle.load(pick_in)
        
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
        
        pick_in = open("../Data/"+N+C+"_PFlow_DF.pickle", "rb")
        Flow = pickle.load(pick_in)

        VlowPerc[N]['nCusts']=0
        for k in V_min.columns:
            VlowPerc[N]['nCusts'][k]=len(Customer_Summary[Customer_Summary['zone']==k])
            if k[1]=='1':
                C_Violations[k]=0
        ##### Count Vmins < 0.9 and 0.94 ################
        VlowPerc[N][C]=round((V_min<0.9).sum()/len(V_min.index)*100,2)   
        TransPerc[N][C]=round((abs(TransKVA_S)>TransRateKVA).sum()/len(TransKVA_S.index)*100,2)   
        #ChighPerc[N][C]=round(C_Violations.sum()/len(C_Violations),2) 
        ChighPerc[N][C]=round((C_Violations>0).sum()/len(C_Violations.index)*100,2) 

    o=0
    
    for h in VlowPerc[N].columns[1:]:
        if c==0:
            allvmins[h]=[]
            allcusts[h]=[]
        allvmins[h].extend(VlowPerc[N][h].values)
        allcusts[h].extend(VlowPerc[N]['nCusts'].values)
        if N!='network_17/':
            plt.plot(VlowPerc[N]['nCusts'],VlowPerc[N][h], marker=mk[o], fillstyle=fills[c], color=cols[c],linestyle = 'None')
            o=o+1
        if N =='network_17/':
            plt.plot(VlowPerc[N]['nCusts'],VlowPerc[N][h], marker=mk[o], fillstyle=fills[c], color=cols[c], label=times[o],linestyle = 'None')
            o=o+1
    c=c+1

plt.grid(linewidth=0.2)
custom=[Line2D([0],[0], marker='o', color="grey",fillstyle='full', markerfacecolor='grey', label='Network 1',linestyle = 'None'),
        Line2D([0],[0], marker='o', color="#9467bd",fillstyle='left', markerfacecolor='#9467bd', label='Network 10',linestyle = 'None'),
        Line2D([0],[0], marker='o', color="#bcbd22",fillstyle='bottom', markerfacecolor='#bcbd22', label='Network 5',linestyle = 'None'),
        Line2D([0],[0], marker='o', color="#ff7f0e",fillstyle='right', markerfacecolor='#ff7f0e', label='Network 18',linestyle = 'None'),
        Line2D([0],[0], marker='o', color="#d62728",fillstyle='none', label='Network 17',linestyle = 'None')]
    
leg2=plt.legend(handles=custom,loc=6,fontsize=12)
plt.gca().add_artist(leg2)
plt.legend(fontsize=12)
plt.xlabel('Number of Customers',fontsize=12)
plt.ylabel('% of timesteps with Voltage < 216 V',fontsize=12)

c=0
plt.figure()
for N in networks:
    o=0
    for h in ChighPerc[N].columns:
        if c==0:
            allchigh[h]=[]
        #allvmins[h].extend(ChighPerc[N][h].values)
        if N!='network_17/':
            plt.plot(VlowPerc[N]['nCusts'],ChighPerc[N][h], marker=mk[o], fillstyle=fills[c], color=cols[c],linestyle = 'None')
            o=o+1
        if N =='network_17/':
            plt.plot(VlowPerc[N]['nCusts'],ChighPerc[N][h], marker=mk[o], fillstyle=fills[c], color=cols[c], label=times[o],linestyle = 'None')
            o=o+1
    c=c+1

plt.grid(linewidth=0.2)
leg2=plt.legend(handles=custom,loc=6,fontsize=12)
plt.gca().add_artist(leg2)
plt.legend(fontsize=12)
plt.xlabel('Number of Customers',fontsize=12)
plt.ylabel('% of timesteps with thermal violations',fontsize=12)
#plt.ylabel('Avg Number of Current Violations per Timestep',fontsize=12)



for n in allcusts:
    allvmins[n]=np.array(allvmins[n]).astype(float)
    allcusts[n]=np.array(allcusts[n]).astype(float)
    print(n, allcusts[n][allvmins[n]>0].min())

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
            replace[N][c][r] = (VlowPerc[N][r][c]>0) or (ChighPerc[N][r][c]>0)
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
        if len(VlowPerc[N].loc[h][VlowPerc[N].loc[h]==0])>0:
            C=VlowPerc[N].loc[h][VlowPerc[N].loc[h]==0].index[-1]
        else:
            C='00PV00HP'
        pick_in = open("../Data/"+N+"Customer_Summary"+C+str(Y)+".pickle", "rb")
        Customer_Summary= pickle.load(pick_in)   
        Vsum=sum(Customer_Summary[Customer_Summary['zone']==h]['Heat_Pump_Flag']>0)
        
        if len(ChighPerc[N].loc[h][ChighPerc[N].loc[h]==0])>0:
            C=ChighPerc[N].loc[h][ChighPerc[N].loc[h]==0].index[-1]
        else:
            C='00PV00HP'
        pick_in = open("../Data/"+N+"Customer_Summary"+C+str(Y)+".pickle", "rb")
        Customer_Summary= pickle.load(pick_in)   
        Csum=sum(Customer_Summary[Customer_Summary['zone']==h]['Heat_Pump_Flag']>0) 
        bycusts[N][h]=min(Vsum,Csum)
    
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

# plt.figure()

# c=0
# for N in networks:
#     o=0
#     for C in Cases:
#         if N!='network_17/':
#             plt.plot(TransCusts[N],TransPerc[N][C], marker=mk[o], fillstyle=fills[c], color=cols[c],linestyle = 'None')
#             o=o+1
#         if N =='network_17/':
#             plt.plot(TransCusts[N],TransPerc[N][C], marker=mk[o], fillstyle=fills[c], color=cols[c],label=times[o],linestyle = 'None')
#             o=o+1
#     c=c+1

# plt.grid(linewidth=0.2)
# custom=[Line2D([0],[0], marker='o', color="grey",fillstyle='full', markerfacecolor='grey', label='Network 1',linestyle = 'None'),
#         Line2D([0],[0], marker='o', color="#9467bd",fillstyle='left', markerfacecolor='#9467bd', label='Network 10',linestyle = 'None'),
#         Line2D([0],[0], marker='o', color="#bcbd22",fillstyle='bottom', markerfacecolor='#bcbd22', label='Network 5',linestyle = 'None'),
#         Line2D([0],[0], marker='o', color="#ff7f0e",fillstyle='right', markerfacecolor='#ff7f0e', label='Network 18',linestyle = 'None'),
#         Line2D([0],[0], marker='o', color="#d62728",fillstyle='none', label='Network 17',linestyle = 'None')]
# leg2=plt.legend(handles=custom,loc=10,fontsize=9)
# plt.gca().add_artist(leg2)
# plt.legend(fontsize=9)
# plt.xscale('log')
# #plt.yscale('log')
# plt.xlabel('Number of Customers (log scale)',fontsize=10)
# plt.ylabel('% of timesteps with Tx thermal violations',fontsize=10)