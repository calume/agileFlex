import pandas as pd
import networkx as nx
import pickle
from matplotlib import pyplot as plt

def plots(Network_Path,VoltArray,CurArray,RateArray):
    Volts={}
    Currents={}
    Coords = pd.read_csv(str(Network_Path)+'/XY_Position.csv')
    Lines = pd.read_csv(str(Network_Path)+'/Lines.txt',delimiter=' ', names=['New','Line','Bus1','Bus2','phases','Linecode','Length','Units'] )
    Lines.loc[-1]=['New','Trans','Bus1=1','Bus2=11','1','-','-','-']
    Lines.index = Lines.index + 1  # shifting index
    Lines.sort_index(inplace=True) 
    #Lines = Lines[Lines['Line'].map(len) > 5]
    #Lines.reset_index(drop=True, inplace=True)
    n=1
    for p in range(0,3):
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
       
       cmap = plt.cm.YlOrRd
       edge_cmap = plt.cm.cool
       
       Volts[p] = VoltArray[:,p].tolist()
       
       Currents[p] = (CurArray[:,p]/RateArray).tolist()
       Currents[p][:0]=[TransKVA_sum/DSSTransformers.kVA()]
    
       ##### Plot Currents for each Phase ####
    
       plt.figure(n)
       #plt.figure(311+p)
       plt.title('Current (A) - Phase ' +str(p+1))
       nx.draw(G, pos, edge_color=Currents[p],with_labels=False, width=2, node_size=1, font_weight='bold', edge_cmap=edge_cmap)
       sm = plt.cm.ScalarMappable(cmap=edge_cmap, norm=plt.Normalize(vmin=min(Currents[p]),vmax=max(Currents[p])))
       sm._A = []
       plt.colorbar(sm,ticks=[min(Currents[p]),(max(Currents[p])+min(Currents[p]))/2, max(Currents[p])])
       plt.show()
       n=n+1
       ############ Plot Voltages for each Phase ############
       plt.figure(n)
       #plt.subplot(311+p)
       plt.title('Voltages (p.u.) - Phase '+str(p+1))
       nx.draw(G, pos, node_color=Volts[p],with_labels=False, width=1, node_size=7, font_weight='bold', cmap=cmap)
       sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=min(Volts[p]),vmax=max(Volts[p])))
       sm._A = []
       plt.colorbar(sm,ticks=[min(Volts[p]),(max(Volts[p])+min(Volts[p]))/2, max(Volts[p])])
       plt.show()
       n=n+1
