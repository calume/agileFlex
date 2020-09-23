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

# ------------ Network Voltage Headroom calculation---------##

#### This script takes network current and voltage data, and plots
#### the relationship between minimum voltage and current at the pinch point

#def voltage_headroom(Pflow,Vmin):

networks=['network_1/']#,'network_10/','network_5/','network_18/','network_17/']
Y=14
Cases=['00PV00HP','00PV25HP','25PV50HP','25PV75HP','50PV100HP']#,'25PV25HP','50PV50HP','75PV75HP','100PV100HP']
All_VC_Limits={}
#for Y in [14,15]:
pick_in = open("../Data/All_VC_Limits0.94.pickle", "rb")
All_VC = pickle.load(pick_in)
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
times2 = ["00:00", "06:00", "12:00", "18:00"]
for N in networks:
    AllVmin=pd.DataFrame()
    VlowPerc[N]=pd.DataFrame()
    ChighPerc[N]=pd.DataFrame()
    AllPflow=pd.DataFrame()
    for C in Cases:
        pick_in = open("../Data/"+N+"Customer_Summary"+C+str(Y)+".pickle", "rb")
        Customer_Summary= pickle.load(pick_in)   

        pick_in = open("../Data/"+N+C+"Winter"+str(Y)+"_V_Data.pickle", "rb")
        #pick_in = open("../Data/"+N+"validation/Winter"+str(Y)+"_V_Data.pickle", "rb")
        V_data = pickle.load(pick_in)

        VlowPerc[N]['nCusts']=0
        for k in V_data['Vmin'].columns:
            VlowPerc[N]['nCusts'][k]=len(Customer_Summary[Customer_Summary['zone']==k])
        
        ##### Count Vmins < 0.9 and 0.94 ################
        VlowPerc[N][C]=round((V_data['Vmin']<0.9).sum()/len(V_data['Vmin'].index)*100,2)   
        
        ChighPerc[N][C]=round((V_data['C_Violations']>0).sum()/len(V_data['C_Violations'].index)*100,2) 


        cs=[]
        for p in range(1, 4):
            for f in range(1, len(V_data['Flow'].keys())+1):
                cs.append(str(p)+str(f))         
        Pflow = pd.DataFrame(index=V_data['Vmin'].index,columns=cs)  
        for p in range(1,4):
            for f in range(1, len(V_data['Flow'].keys())+1):
                Pflow[str(p)+str(f)]=V_data['Flow'][f][p]
    
        AllVmin=AllVmin.append(V_data['Vmin'])
        AllPflow=AllPflow.append(Pflow)
            
        trues=round(AllPflow.sum(),3)>0
        trues=trues[trues].index
         
        VC_Fits=pd.DataFrame(columns=['m','c'], index=trues)
        VC_Limit=pd.Series(index=trues, dtype=float)
        
        C=np.arange(0,100,step=10)
            
        #######only include with Data
        #plt.figure()
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
plt.grid(linewidth=0.2)
custom=[Line2D([0],[0], marker='o', color="grey",fillstyle='full', markerfacecolor='grey', label='Network 1',linestyle = 'None'),
        Line2D([0],[0], marker='o', color="#9467bd",fillstyle='left', markerfacecolor='#9467bd', label='Network 10',linestyle = 'None'),
        Line2D([0],[0], marker='o', color="#bcbd22",fillstyle='bottom', markerfacecolor='#bcbd22', label='Network 5',linestyle = 'None'),
        Line2D([0],[0], marker='o', color="#ff7f0e",fillstyle='right', markerfacecolor='#ff7f0e', label='Network 18',linestyle = 'None'),
        Line2D([0],[0], marker='o', color="#d62728",fillstyle='none', label='Network 17',linestyle = 'None')]

leg2=plt.legend(handles=custom,loc=6,fontsize=12)
plt.gca().add_artist(leg2)
# plt.plot([35,35],[0,100], linewidth=1, linestyle='-', color='black')#,label='0% HP Limit')
# plt.plot([21,21],[0,50], linewidth=1, linestyle='--', color='black')#,label='25% HP Limit')
# plt.plot([13,13],[0,25], linewidth=1, linestyle=':', color='black')#,label='50% HP Limit')
plt.legend(fontsize=12)
plt.xlabel('Number of Customers',fontsize=12)
plt.ylabel('% of timesteps with Voltage < 216 V',fontsize=12)

plt.figure()
for N in networks:
    for h in ChighPerc[N].columns:
        if c==0:
            allchigh[h]=[]
        allvmins[h].extend(ChighPerc[N][h].values)
        if N!='network_17/':
            plt.plot(VlowPerc[N]['nCusts'],ChighPerc[N][h], marker=mk[o], fillstyle=fills[c], color=cols[c],linestyle = 'None')
            o=o+1
        if N =='network_17/':
            plt.plot(VlowPerc[N]['nCusts'],ChighPerc[N][h], marker=mk[o], fillstyle=fills[c], color=cols[c], label=times[o],linestyle = 'None')
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
plt.ylabel('% of timesteps with thermal violation',fontsize=12)



# for n in allcusts:
#     allvmins[n]=np.array(allvmins[n]).astype(float)
#     allcusts[n]=np.array(allcusts[n]).astype(float)
#     print(n, allcusts[n][allvmins[n]>0].min())

# summary=pd.DataFrame(index=VlowPerc[N].columns[1:].append(pd.Index(['Total'])))
# for N in networks:
#     summary[N]=(VlowPerc[N][VlowPerc[N].columns[1:]]>0).sum()
#     summary[N].loc['Total']=len(VlowPerc[N])
#     #plt.xticks(VlowPerc[N].columns,times)

#     for i in trues:#V_data['Pflow'].columns:
#         x=AllPflow[i].astype(float).values
#         y=AllVmin[i].astype(float).values
# #        data , x_e, y_e = np.histogram2d( x, y, bins = 30, density = True )
# #        z = interpn( ( 0.5*(x_e[1:] + x_e[:-1]) , 0.5*(y_e[1:]+y_e[:-1]) ) , data , np.vstack([x,y]).T , method = "splinef2d", bounds_error = False)
# #        z[np.where(np.isnan(z))] = 0.0
# #        plt.figure(i)
# #        idx = z.argsort()
# #        x, y, z = x[idx], y[idx], z[idx]
# #        plt.scatter( x, y, c=z,s=1)
# #    
# #        norm = Normalize(vmin = np.min(z), vmax = np.max(z))
# #        cbar = plt.colorbar(cm.ScalarMappable(norm = norm))
# #        cbar.ax.set_ylabel('Density')

#         VC_Fits.loc[i]['m'],VC_Fits.loc[i]['c']=np.polyfit(x,y,1)
#         #plt.plot(C,C*VC_Fits.loc[i]['m']+VC_Fits.loc[i]['c'], linewidth=0.5)
#         V_lim=0.9
#         V_lim_u=0.9
#         VC_Limit[i]=(V_lim_u-VC_Fits.loc[i]['c'])/VC_Fits.loc[i]['m']
#         if y.min() >0.9:
#             VC_Limit[i]=VC_Limit[i]*0.8
#         unders=y[x<VC_Limit[i]]
#         if sum(unders[unders<V_lim_u])>0:
#             VC_Limit[i]=x[y<=V_lim_u].min()
#         #VC_Limit[i]=All_VC[N][i]
#         # if (len(y[y<V_lim_u])/len(y)*100) <5:
#         #     VC_Limit[i]=(V_lim_u-VC_Fits.loc[i]['c'])/VC_Fits.loc[i]['m']
#         unders_n=y[x<VC_Limit[i]]
#         prob=len(unders_n[unders_n<V_lim_u])/len(unders_n)*100
#         print(str(i)+', % Probability of <0.94 p.u at Flow<VCmin '+str(prob))
#         # q=0.35
#         # prob_lim=0.5
#         # if N=='network_17/' and i=='27':
#         #     prob_lim=1
#         # while prob>prob_lim:
#         #     VC_Limit[i]=np.quantile(x[(y<=V_lim_u)&(y>=V_lim)],q)
#         #     unders_n=y[x<VC_Limit[i]]
#         #     prob=len(unders_n[unders_n<0.94])/len(unders_n)*100
#         #     q=q-0.001
# #        plt.plot([0,VC_Limit[i]*2],[V_lim,V_lim], linewidth=0.5)
# #        plt.plot([0,VC_Limit[i]*2],[0.9,0.9], linewidth=0.5, linestyle=':', color='black')
# #        plt.plot([VC_Limit[i],VC_Limit[i]],[0.88,1], linewidth=0.7)
# #        plt.title('Network/Zone '+N+i)
# #        plt.xlabel('Supply Power (kVA)')
# #        plt.ylabel('Min Voltage (Amps)')
# #        plt.ylim(0.88,1)
#         print(str(i)+', % Probability of <0.9 p.u at Flow<VCmin '+str(prob))
#     All_VC_Limits[N]=VC_Limit

# """ Note on Vlimits"""
# """ Say 2% drop acceptable, that is 383.2V which is 0.921 p.u."""
# """ Minimum for UK appliances is 216.2 V P-N, which is 374.47 V P-P and 0.9 p.u (for 416 V base)"""

# # pickle_out = open("../Data/All_VC_Limits.pickle", "wb")
# # pickle.dump(All_VC_Limits, pickle_out)
# # pickle_out.close()   

# all_means=allcusts['00PV00HP']
# histo, binz = np.histogram(all_means, bins=range(0, int(max(all_means))+15, 5))
# fig, ax = plt.subplots(figsize=(5, 4))
# ax.bar(binz[:-1], histo, width=5, align="edge")
# ax.set_xlim(left=0,right=100)
# ax.set_ylabel("Frequency", fontsize=11)
# ax.set_xlabel("Number of customers per zone", fontsize=11)
# for t in ax.xaxis.get_majorticklabels():
#     t.set_fontsize(11)
# for t in ax.yaxis.get_majorticklabels():
#     t.set_fontsize(11)
# plt.plot([np.quantile(all_means,0.5),np.quantile(all_means,0.5)],[0,max(histo)], linewidth=1, color='black', label='Median')
# plt.plot([np.quantile(all_means,0.75),np.quantile(all_means,0.75)],[0,max(histo)], linewidth=1,linestyle='--', color='orange', label='Q75')
# plt.plot([np.quantile(all_means,0.95),np.quantile(all_means,0.95)],[0,max(histo)], linewidth=1,linestyle=':', color='red', label='Q95')
# plt.grid(linewidth=0.2)
# plt.legend()
# plt.tight_layout()
labs=times[1:]
u=0
for N in networks:
    for C in Cases[1:]:
        pick_in = open("../Data/"+N+C+"Winter"+str(Y)+"_V_Data.pickle", "rb")
        V_data = pickle.load(pick_in)

        transmax[C]=[]
        for n in range(0,24):
            # transmins.append(V_data['Trans_kVA'].loc[V_data['Trans_kVA'].index.hour==n].min())
            # transmedian.append(np.quantile(V_data['Trans_kVA'].loc[V_data['Trans_kVA'].index.hour==n],0.5))
            transmax[C].append(V_data['Trans_kVA'].loc[V_data['Trans_kVA'].index.hour==n].max())
        
        plt.plot(transmax[C],label=labs[u],color=cols[u],linestyle=style[u])
        u=u+1
    plt.plot(np.full(24,800), label='Tx Rating (kVA)')
    plt.ylabel('Max Transformer Power Flow (kVA)')
    plt.legend()
    plt.grid(linewidth=0.2)
    plt.xlim([0, 23])
    plt.xticks(range(0,24,6),times2)
    
            