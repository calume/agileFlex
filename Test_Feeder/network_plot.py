import pandas as pd
import networkx as nx
from matplotlib import pyplot as plt
import pickle
from numpy.random import choice

Feeder='Feed1'
Coords = pd.read_csv(str(Feeder)+"/XY_Position.csv")
Lines = pd.read_csv(str(Feeder)+"/Lines.txt",delimiter=' ', names=['New','Line','Bus1','Bus2','phases','Linecode','Length','Units'] )
Lines = Lines[Lines['Line'].map(len) > 5]
Lines.reset_index(drop=True, inplace=True)
Loads = pd.read_csv(str(Feeder)+"/Loads.txt",delimiter=' ', names=['New','Load','Phases','Bus1','kV','kW','PF','Daily'] )

#------------Define Network Agents[[[[[[[[[[[[[[[]]]]]]]]]]]]]]]

pvcaplist=[1,1.5,2,2.5,3,3.5,4]
weights=[.01,.08,.13,.15,.14,.12,.37]

LoadsByAcorn={}
LoadsByAcorn['Affluent']=list(range(1,18))
LoadsByAcorn['Comfortable']=list(range(1,18))
LoadsByAcorn['Adversity']=list(range(1,18))

for i in LoadsByAcorn['Affluent']:    
    PVcap=choice(pvcaplist, int(len(LoadsByAcorn['Affluent'])), weights)

Customer_Summary=pd.DataFrame(0, index=(range(0,len(Loads))), columns=['ID','Node','Agent','Acorn_Group','Phase','Home_Battery_kW','Home_Battery_kWh','EV_Charger_Size_kW','EV_Battery_Size_kWh','PV_kW','Heat_Pump_kW'])
Customer_Summary['ID']=Loads.index+1
Customer_Summary['Node']=Loads['Bus1'].str[5:-2].astype(int)
Customer_Summary['Agent'][Customer_Summary['Acorn_Group']=='Affluent']=1
Customer_Summary['Acorn_Group'][0:18]='Affluent'
Customer_Summary['Acorn_Group'][18:30]='Comfortable'
Customer_Summary['Acorn_Group'][30:]='Adversity'
Customer_Summary['Phase']=Loads['Bus1'].str[-1]
Customer_Summary['Home_Battery_kW'][Customer_Summary['Acorn_Group']=='Affluent']= 5
Customer_Summary['Home_Battery_kWh'][Customer_Summary['Acorn_Group']=='Affluent']= 13.5
Customer_Summary['EV_Charger_Size_kW'][Customer_Summary['Acorn_Group']=='Affluent']= 7.4
Customer_Summary['EV_Battery_Size_kWh'][Customer_Summary['Acorn_Group']=='Affluent']= 40
Customer_Summary['PV_kW'][Customer_Summary['Acorn_Group']=='Affluent']= choice(pvcaplist, int(sum(Customer_Summary['Acorn_Group']=='Affluent')), weights)   # Every house has PV
Customer_Summary['Heat_Pump_kW'][Customer_Summary['Acorn_Group']=='Affluent']=5
Customer_Summary['Heat_Pump_kW'][Customer_Summary['Acorn_Group']=='Comfortable']=4

def Network_plot(Coords,Lines,Loads):
   ##### Set Up NetworkX Graph from coordinates and network outputs ####

   G = nx.Graph()
   
   Edge={}
   
   for index, value in Lines['Bus1'].items():
       Edge[index] = int(Lines['Bus1'][index][5:]),int(Lines['Bus2'][index][5:])
   
   pos={}
   for index, value in Coords['Node'].items():
       pos[index] = float(Coords['X'][index]),int(Coords['Y'][index])
   
   pos = dict((Coords['Node'][key], value) for (key, value) in pos.items())
   
   G.add_nodes_from(Coords['Node'])
   G.add_edges_from(Edge.values())
   
   ##### Plot Currents for each Phase ####
   Loads['X']=0
   Loads['Y']=0
   Loads['X'].astype(float)
   Loads['Y'].astype(float)
   plt.figure(1)
   nx.draw(G, pos, with_labels=False, width=2, node_size=3, font_weight='bold')
   for i in Loads.index:
       Loads['X'][i]=Coords['X'][Coords['Node']==int(Loads['Bus1'][i][5:-2])].astype(float)+2
       Loads['Y'][i]=Coords['Y'][Coords['Node']==int(Loads['Bus1'][i][5:-2])].astype(float)
       plt.annotate(i+1, (Loads['X'][i], Loads['Y'][i]),fontsize=12,color="blue",)

   plt.show()
   

Network_plot(Coords,Lines,Loads)
