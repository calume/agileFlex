# -*- coding: utf-8 -*-
"""
Created on Wed March 18 13:49:06 2020

This script produces a plot of the test feeder (Feeder1 from LVNS) and Network 1 which includes Feeder1 and 3 others

From:  https://www.enwl.co.uk/zero-carbon/innovation/smaller-projects/low-carbon-networks-fund/low-voltage-network-solutions/

The feeder has 55 customers spread across the 3 phases. Flexibility is assigned as per Acorn Group.

- Affluent: are assumed to be full adopters of Low carbon technologies, all have Heat Pumps, Electric Vehicles, PV and Home Batteries.
- Comfortable: half of these are assumed to have PV and all are assumed to have solar.
- Adversity: are assumed to not have any low carbon technologies (LCTs) due high capital costs required.

@author: qsb15202
"""


import pandas as pd
import networkx as nx
from matplotlib import pyplot as plt
import pickle
import matplotlib.image as mpimg
from matplotlib.offsetbox import TextArea, DrawingArea, OffsetImage, AnnotationBbox
#from arcgis.gis import GIS

pd.options.mode.chained_assignment = None
from tabulate import tabulate
from numpy.random import choice

# ------------------------Define Network Agents----------------------------
def customer_summary(Network_Path,Case):
    # ---------------Load Network Data-----------------------------

    Coords = pd.read_csv(str(Network_Path) + "/XY_Position.csv")
    Lines = pd.read_csv(
        str(Network_Path) + "/Lines.txt",
        delimiter=" ",
        names=["New", "Line", "Bus1", "Bus2", "phases", "Linecode", "Length", "Units"],
    )
    Lines = Lines[Lines["Line"].map(len) > 5]
    Lines.reset_index(drop=True, inplace=True)
    Loads = pd.read_csv(
        str(Network_Path) + "/Loads.txt",
        delimiter=" ",
        names=["New", "Load", "Phases", "Bus1", "kV", "kW", "PF", "Daily"],
    )

    # The PV distribution of PV capacities has been calculated from the distribution of installed PV capacities with Feed in tariffs.

    # pvcaplist = [1, 1.5, 2, 2.5, 3, 3.5, 4]
    # weights = [0.01, 0.08, 0.13, 0.15, 0.14, 0.12, 0.37]
    # pvlist=choice(pvcaplist, 1000, weights)
    
    pick_in = open("Test_Network/pvcaplist.pickle", "rb")
    pvcaplist = pickle.load(pick_in)

    
    LoadsByAcorn = {}
    LoadsByAcorn["Affluent"] = list(range(1,int(len(Loads)/3)))
    LoadsByAcorn["Comfortable"] = list(range(1, int(len(Loads)/3)))
    LoadsByAcorn["Adversity"] = list(range(1, int(len(Loads)/3)))

    Customer_Summary = pd.DataFrame(
        0,
        index=(range(0, len(Loads))),
        columns=[
            "ID",
            "Node",
            "Agent",
            "Acorn_Group",
            "X",
            "Y",
            "Phase",
            "Feeder",
            "EV_ID",
            "PV_kW",
            "Heat_Pump_Flag",
            "Color",
        ],
    )

    
    Customer_Summary["ID"] = Loads.index + 1
    Customer_Summary["Node"] = Loads["Bus1"].str[5:-2].astype(int)
    Customer_Summary["Phase"] = Loads["Bus1"].str[-1]
    Customer_Summary["Feeder"] = Loads["Load"].str[9]
    Customer_Summary['zone']=0
    for i in Customer_Summary.index:
        Customer_Summary['zone'].loc[i]=str(Customer_Summary['Phase'][i])+str(Customer_Summary['Feeder'][i])

    Customer_Summary["Agent"][Customer_Summary["Acorn_Group"] == "Affluent"] = 1
    Customer_Summary["EV_ID"][Customer_Summary["Acorn_Group"] == "Affluent"] = 0
    for j in Customer_Summary['zone'].unique():
        if Case[4:]=='25HP':
            Cslice=Customer_Summary[Customer_Summary['zone']==j].index[::4]
            Customer_Summary["Acorn_Group"].loc[Cslice] = "Adversity"
            Cslice=Customer_Summary[Customer_Summary['zone']==j].index[2::4]
            Customer_Summary["Acorn_Group"].loc[Cslice] = "Comfortable" 
            Cslice=Customer_Summary[Customer_Summary['zone']==j].index[3::4]
            Customer_Summary["Acorn_Group"].loc[Cslice] = "Comfortable"             
            Cslice=Customer_Summary[Customer_Summary['zone']==j].index[1::4]
            Customer_Summary["Acorn_Group"].loc[Cslice] = "Affluent"   
    
        if Case[4:]=='50HP':
            Cslice=Customer_Summary[Customer_Summary['zone']==j].index[::4]
            Customer_Summary["Acorn_Group"].loc[Cslice] = "Adversity" 
            Cslice=Customer_Summary[Customer_Summary['zone']==j].index[2::4]
            Customer_Summary["Acorn_Group"].loc[Cslice] = "Comfortable"             
            Cslice=Customer_Summary[Customer_Summary['zone']==j].index[1::2]
            Customer_Summary["Acorn_Group"].loc[Cslice] = "Affluent"   

        if Case[4:]=='75HP':
            Cslice=Customer_Summary[Customer_Summary['zone']==j].index[::8]
            Customer_Summary["Acorn_Group"].loc[Cslice] = "Adversity" 
            Cslice=Customer_Summary[Customer_Summary['zone']==j].index[4::8]
            Customer_Summary["Acorn_Group"].loc[Cslice] = "Comfortable"             
            Cslice=Customer_Summary[Customer_Summary['zone']==j].index[1::4]
            Customer_Summary["Acorn_Group"].loc[Cslice] = "Affluent"  
            Cslice=Customer_Summary[Customer_Summary['zone']==j].index[2::4]
            Customer_Summary["Acorn_Group"].loc[Cslice] = "Affluent"  
            Cslice=Customer_Summary[Customer_Summary['zone']==j].index[3::4]
            Customer_Summary["Acorn_Group"].loc[Cslice] = "Affluent"  
        
        if Case[5:]=='100HP' or Case[4:]=='100HP':
            Customer_Summary["Acorn_Group"] = "Affluent"
    
    Customer_Summary["PV_kW"][Customer_Summary["Acorn_Group"] == "Affluent"] = pvcaplist[0:sum(Customer_Summary["Acorn_Group"] == "Affluent")]
    Customer_Summary["Heat_Pump_Flag"][Customer_Summary["Acorn_Group"] == "Affluent"] = 1

    for j in Customer_Summary['zone'].unique():
        if Case[:4]=='00PV':
            Customer_Summary["PV_kW"]=0
        if Case=='25PV50HP' or Case=='50PV100HP':
            affs_in=Customer_Summary[Customer_Summary['zone']==j]
            Customer_Summary["PV_kW"].loc[affs_in.index]=0
            affs_in=Customer_Summary[Customer_Summary['zone']==j]
            affs=affs_in["PV_kW"][affs_in["Acorn_Group"] == "Affluent"]
            affs[::2] = pvcaplist[0:len(affs[::2])]
            Customer_Summary["PV_kW"].loc[affs.index]=affs
            
        if Case=='25PV75HP':
            affs_in=Customer_Summary[Customer_Summary['zone']==j]
            Customer_Summary["PV_kW"].loc[affs_in.index]=0
            affs_in=Customer_Summary[Customer_Summary['zone']==j]
            affs=affs_in["PV_kW"][affs_in["Acorn_Group"] == "Affluent"]
            affs[::3] = pvcaplist[0:len(affs[::3])]
            Customer_Summary["PV_kW"].loc[affs.index]=affs        
                    
    acorns = ["Affluent", "Comfortable", "Adversity"]
    colors = ["green", "#17becf", "black"]

    for i in range(0, 3):
        Customer_Summary["Color"][
            Customer_Summary["Acorn_Group"] == acorns[i]
        ] = colors[i]
    fcolor = ["red", "yellow", "blue", "orange", "green", "#17becf", "black","grey","purple"]
    Coords["Node_Color"] = "red"
    for i in Customer_Summary['Feeder'].unique():
        Coords["Node_Color"][Coords["Node"].astype(str).str[0] == i] = fcolor[int(i)-1]
    Coords["Node_Color"].iloc[0] = "blue"
    return Customer_Summary, Coords, Lines, Loads


# ------------------- Plot the network with icons for each LCT type


def Network_plot(Coords, Lines, Loads, Customer_Summary):
    acorns = ["Affluent", "Comfortable", "Adversity"]
    #colors = []
    ####  Import Icons
    EV_Icon = mpimg.imread("Feed1/EVIcon2.png")
    EVbox = OffsetImage(EV_Icon, zoom=0.3)

    HP_Icon = mpimg.imread("Feed1/HeatPump.png")
    HPbox = OffsetImage(HP_Icon, zoom=0.25)

    powerwall_Icon = mpimg.imread("Feed1/powerwall.png")
    powerwallbox = OffsetImage(powerwall_Icon, zoom=0.3)

    PV_Icon = mpimg.imread("Feed1/PV_Icon.png")
    PVbox = OffsetImage(PV_Icon, zoom=0.25)

    House = mpimg.imread("Feed1/house.png")
    Housebox = OffsetImage(House, zoom=0.1)

    Substation = mpimg.imread("Feed1/substation.png")
    Substationbox = OffsetImage(Substation, zoom=0.3)

    G = nx.Graph()
    ##### Set Up NetworkX Graph from coordinates and network outputs ####
    Edge = {}

    for index, value in Lines["Bus1"].items():
        Edge[index] = int(Lines["Bus1"][index][5:]), int(Lines["Bus2"][index][5:])

    pos = {}
    for index, value in Coords["Node"].items():
        pos[index] = float(Coords["X"][index]), int(Coords["Y"][index])

    pos = dict((Coords["Node"][key], value) for (key, value) in pos.items())

    G.add_nodes_from(Coords["Node"])
    G.add_edges_from(Edge.values())

    ##### network and icons ####
    fig, ax = plt.subplots()
    nx.draw(
        G, pos, with_labels=False, width=0.5, node_size=1.5, node_color=Coords["Node_Color"]
    )
    for i in Loads.index:
        Customer_Summary["X"][i] = Coords["X"][
            Coords["Node"] == int(Loads["Bus1"][i][5:-2])
        ].astype(float)
        Customer_Summary["Y"][i] = Coords["Y"][
            Coords["Node"] == int(Loads["Bus1"][i][5:-2])
        ].astype(float)
        # plt.annotate(
        #     i + 1,
        #     (Customer_Summary["X"][i] + 2, Customer_Summary["Y"][i] + 5),
        #     fontsize=10,
        #     color=Customer_Summary["Color"][i],
        #     # weight="bold",
        # )
        if Customer_Summary["PV_kW"][i] > 0:
            ab = AnnotationBbox(
                PVbox,
                [Customer_Summary["X"][i], Customer_Summary["Y"][i]],
                frameon=False,
                pad=0,
            )
            ax.add_artist(ab)
        if Customer_Summary["EV_ID"][i] > 0:
            ab = AnnotationBbox(
                EVbox,
                [Customer_Summary["X"][i], Customer_Summary["Y"][i] - 5],
                frameon=False,
                pad=0,
            )
            ax.add_artist(ab)
        if Customer_Summary["Acorn_Group"][i] == "Adversity":
            ab = AnnotationBbox(
                Housebox,
                [Customer_Summary["X"][i], Customer_Summary["Y"][i]],
                frameon=False,
                pad=0,
            )
            ax.add_artist(ab)
        if (
            Customer_Summary["Acorn_Group"][i] == "Comfortable"
            and Customer_Summary["PV_kW"][i] == 0
        ):
            ab = AnnotationBbox(
                Housebox,
                [Customer_Summary["X"][i], Customer_Summary["Y"][i]],
                frameon=False,
                pad=0,
            )
            ax.add_artist(ab)
        # if Customer_Summary["Home_Battery_kW"][i] > 0:
        #     ab = AnnotationBbox(
        #         powerwallbox,
        #         [Customer_Summary["X"][i] + 3, Customer_Summary["Y"][i]],
        #         frameon=False,
        #         pad=0,
        #     )
            ax.add_artist(ab)
        if Customer_Summary["Heat_Pump_Flag"][i] > 0:
            ab = AnnotationBbox(
                HPbox,
                [Customer_Summary["X"][i] - 4, Customer_Summary["Y"][i] - 1],
                frameon=False,
                pad=0,
            )
            ax.add_artist(ab)
        offset = [0, 6, 12, 18, 24, 30,36,42,48,54]
    # plt.annotate("Acorn Group", (480, 445), fontsize=10, color="black", weight="bold")
    # for i in range(0, 3):
    #     plt.annotate(
    #         acorns[i],
    #         (480, 435 - offset[i] * 3),
    #         fontsize=9,
    #         color=colors[i],
    #         weight="bold",
    #     )
    fcolor = ["red", "yellow", "blue", "orange", "green", "#17becf", "black","grey","purple"]
    plt.annotate("Feeder", (480, 315), fontsize=10, color="black", weight="bold")
    for i in Customer_Summary['Feeder'].unique().astype(int):
        plt.annotate(
            i,
            (480, 305 - offset[i] * 3),
            fontsize=9,
            color=fcolor[i-1],
            weight="bold",
        )

    boxes = [PVbox, HPbox, Housebox, Substationbox]
    intros = [
        "PV Owner",
        "Heat Pump Owner",
        "No LCTs",
        "Secondary Substation",
    ]
    plt.annotate("Legend", (500, 415), fontsize=10, color="black", weight="bold")
    for i in range(0, 4):
        plt.annotate(intros[i], (515, 400 - offset[i] * 3), fontsize=9, color="black")
        ab = AnnotationBbox(boxes[i], [500, (400 - offset[i] * 3)], frameon=False, pad=0)
        ax.add_artist(ab)

    ab = AnnotationBbox(boxes[3], [Coords['X'][0], Coords['Y'][0]], frameon=False, pad=0)
    ax.add_artist(ab)

    plt.show()
    plt.tight_layout()


# Case='00PV25HP'
# Network='network_5/'
# Network_Path = "Test_Network/condensed"+str(Network)
# Y=14

# Customer_Summary,Coords, Lines,Loads = customer_summary(Network,Case)
# Network_plot(Coords, Lines, Loads,Customer_Summary)
# Customer_Summary.style.hide_index()
# print(
#     tabulate(
#         Customer_Summary.drop(columns="Color"),
#         tablefmt="pipe",
#         headers="keys",
#         showindex=False,
#     )
# )
