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
from arcgis.gis import GIS

pd.options.mode.chained_assignment = None
from tabulate import tabulate
from numpy.random import choice

# ------------------------Define Network Agents----------------------------
def customer_summary(Network_Path):
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

    pvcaplist = [1, 1.5, 2, 2.5, 3, 3.5, 4]
    weights = [0.01, 0.08, 0.13, 0.15, 0.14, 0.12, 0.37]

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
            "Home_Battery_kW",
            "Home_Battery_kWh",
            "EV_Charger_Size_kW",
            "EV_Battery_Size_kWh",
            "PV_kW",
            "Heat_Pump_Flag",
            "Color",
        ],
    )
    Customer_Summary["ID"] = Loads.index + 1
    Customer_Summary["Node"] = Loads["Bus1"].str[5:-2].astype(int)
    Customer_Summary["Acorn_Group"][int(len(Loads)/(3/2)):int(len(Loads))] = "Adversity"
    Customer_Summary["Acorn_Group"][int(len(Loads)/3):int(len(Loads)/(3/2))] = "Comfortable"
    Customer_Summary["Acorn_Group"][0:int(len(Loads)/3)] = "Affluent"
    Customer_Summary["Acorn_Group"] = "Affluent"     # Worst case of everyone with all LCTs
    Customer_Summary["Phase"] = Loads["Bus1"].str[-1]
    Customer_Summary["Feeder"] = Loads["Load"].str[9]
    Customer_Summary["Agent"][Customer_Summary["Acorn_Group"] == "Affluent"] = 1
    Customer_Summary["Home_Battery_kW"][
        Customer_Summary["Acorn_Group"] == "Affluent"
    ] = 5
    Customer_Summary["Home_Battery_kWh"][
        Customer_Summary["Acorn_Group"] == "Affluent"
    ] = 13.5
    Customer_Summary["EV_Charger_Size_kW"][
        Customer_Summary["Acorn_Group"] == "Affluent"
    ] = 7.4
    Customer_Summary["EV_Battery_Size_kWh"][
        Customer_Summary["Acorn_Group"] == "Affluent"
    ] = 40
    MoreComfortable = Customer_Summary["PV_kW"][
        Customer_Summary["Acorn_Group"] == "Comfortable"
    ].index[: int(sum(Customer_Summary["Acorn_Group"] == "Comfortable") / 2)]
    Customer_Summary["PV_kW"][Customer_Summary["Acorn_Group"] == "Affluent"] = choice(
        pvcaplist, int(sum(Customer_Summary["Acorn_Group"] == "Affluent")), weights
    )  # Every house has PV
    Customer_Summary["PV_kW"][MoreComfortable] = choice(
        pvcaplist,
        int(sum(Customer_Summary["Acorn_Group"] == "Comfortable") / 2),
        weights,
    )
    Customer_Summary["Heat_Pump_Flag"][
        Customer_Summary["Acorn_Group"] == "Affluent"
    ] = 1
    Customer_Summary["Heat_Pump_Flag"][
        Customer_Summary["Acorn_Group"] == "Comfortable"
    ] = 1

    acorns = ["Affluent", "Comfortable", "Adversity"]
    colors = ["green", "#17becf", "black"]

    for i in range(0, 3):
        Customer_Summary["Color"][
            Customer_Summary["Acorn_Group"] == acorns[i]
        ] = colors[i]

    Coords["Node_Color"] = "red"
    if Network_Path == "Network1":
        Coords["Node_Color"][Coords["Node"].astype(str).str[0] == "2"] = "yellow"
        Coords["Node_Color"][Coords["Node"].astype(str).str[0] == "3"] = "blue"
        Coords["Node_Color"][Coords["Node"].astype(str).str[0] == "4"] = "orange"
        Coords["Node_Color"].iloc[0] = "blue"
    return Customer_Summary, Coords, Lines, Loads


# ------------------- Plot the network with icons for each LCT type


def Network_plot(Coords, Lines, Loads):
    acorns = ["Affluent", "Comfortable", "Adversity"]
    colors = ["green", "#17becf", "black"]
    ####  Import Icons
    EV_Icon = mpimg.imread("Feed1/EVIcon2.png")
    EVbox = OffsetImage(EV_Icon, zoom=0.3)

    HP_Icon = mpimg.imread("Feed1/HeatPump.png")
    HPbox = OffsetImage(HP_Icon, zoom=0.3)

    powerwall_Icon = mpimg.imread("Feed1/powerwall.png")
    powerwallbox = OffsetImage(powerwall_Icon, zoom=0.3)

    PV_Icon = mpimg.imread("Feed1/PV_Icon.png")
    PVbox = OffsetImage(PV_Icon, zoom=0.3)

    House = mpimg.imread("Feed1/house.png")
    Housebox = OffsetImage(House, zoom=0.15)

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
        G, pos, with_labels=False, width=1, node_size=2, node_color=Coords["Node_Color"]
    )
    for i in Loads.index:
        Customer_Summary["X"][i] = Coords["X"][
            Coords["Node"] == int(Loads["Bus1"][i][5:-2])
        ].astype(float)
        Customer_Summary["Y"][i] = Coords["Y"][
            Coords["Node"] == int(Loads["Bus1"][i][5:-2])
        ].astype(float)
        plt.annotate(
            i + 1,
            (Customer_Summary["X"][i] + 2, Customer_Summary["Y"][i] + 5),
            fontsize=10,
            color=Customer_Summary["Color"][i],
            # weight="bold",
        )
        if Customer_Summary["PV_kW"][i] > 0:
            ab = AnnotationBbox(
                PVbox,
                [Customer_Summary["X"][i], Customer_Summary["Y"][i]],
                frameon=False,
                pad=0,
            )
            ax.add_artist(ab)
        if Customer_Summary["EV_Charger_Size_kW"][i] > 0:
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
        if Customer_Summary["Home_Battery_kW"][i] > 0:
            ab = AnnotationBbox(
                powerwallbox,
                [Customer_Summary["X"][i] + 3, Customer_Summary["Y"][i]],
                frameon=False,
                pad=0,
            )
            ax.add_artist(ab)
        if Customer_Summary["Heat_Pump_Flag"][i] > 0:
            ab = AnnotationBbox(
                HPbox,
                [Customer_Summary["X"][i] - 4, Customer_Summary["Y"][i] - 1],
                frameon=False,
                pad=0,
            )
            ax.add_artist(ab)
        offset = [0, 6, 12, 18, 24, 30]
    plt.annotate("Acorn Group", (480, 445), fontsize=10, color="black", weight="bold")
    for i in range(0, 3):
        plt.annotate(
            acorns[i],
            (480, 435 - offset[i] * 3),
            fontsize=9,
            color=colors[i],
            weight="bold",
        )
    fcolor = ["red", "yellow", "blue", "orange"]
    plt.annotate("Feeder", (480, 315), fontsize=10, color="black", weight="bold")
    for i in range(0, 4):
        plt.annotate(
            i + 1,
            (480, 305 - offset[i] * 3),
            fontsize=9,
            color=fcolor[i],
            weight="bold",
        )

    boxes = [PVbox, EVbox, powerwallbox, HPbox, Housebox, Substationbox]
    intros = [
        "PV Owner",
        "EV Owner",
        "Home Battery Owner",
        "Heat Pump Owner",
        "Non-Agent",
        "Secondary Substation",
    ]
    plt.annotate("Legend", (25, 165), fontsize=10, color="black", weight="bold")
    for i in range(0, 6):
        plt.annotate(intros[i], (30, 154 - offset[i] * 3), fontsize=9, color="black")
        ab = AnnotationBbox(boxes[i], [25, (154 - offset[i] * 3)], frameon=False, pad=0)
        ax.add_artist(ab)

    ab = AnnotationBbox(boxes[5], [360, 163], frameon=False, pad=0)
    ax.add_artist(ab)

    plt.show()
    plt.tight_layout()



#Feeder = "Network1"
#Customer_Summary,Coords, Lines,Loads = customer_summary(Feeder)
#Network_plot(Coords, Lines, Loads)
#Customer_Summary.style.hide_index()
#print(
#    tabulate(
#        Customer_Summary.drop(columns="Color"),
#        tablefmt="pipe",
#        headers="keys",
#        showindex=False,
#    )
# )
