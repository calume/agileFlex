# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 16:39:22 2019

@author: qsb15202
"""
import opendssdirect as dss
import scipy.io
import numpy as np
import pandas as pd
from random import uniform
from random import seed
from opendssdirect.utils import run_command

pd.options.mode.chained_assignment = None
import timeit
from matplotlib import pyplot as plt
from datetime import datetime, timedelta, date, time
import os
import random
import csv
import pickle
import collections
import networkx as nx

# ------------ Network Pinch Point Summary Analysis and Visualisation---------##

#### This script takes network current and voltage data, and presents
#### which lines are overloaded and how frequently


def counts(network_summary, Coords, pinchClist):
    Chigh_allPeriods, Vhigh_allPeriods, Vlow_allPeriods = {}, {}, {}
    Chigh_count, Vhigh_count, Vlow_count = {}, {}, {}
    VHpinch = {}  # Will store the node with the highest voltage per phase/feeder
    for p in range(1, 4):
        VHpinch[p] = {}
        Chigh_count[p], Vhigh_count[p], Vlow_count[p] = [], [], []
        Chigh_allPeriods[p], Vhigh_allPeriods[p], Vlow_allPeriods[p] = [], [], []
        for i in network_summary:
            VHpinch[p][i] = {}
            if len(network_summary[i][p]["Chigh_lines"]) > 0:
                for item in network_summary[i][p]["Chigh_lines"]:
                    Chigh_allPeriods[p].append(item)
                Chigh_count[p] = collections.Counter(Chigh_allPeriods[p])

            if len(network_summary[i][p]["Vhigh_nodes"]) > 0:
                for item in network_summary[i][p]["Vhigh_nodes"]:
                    Vhigh_allPeriods[p].append(item)
                Vhigh_count[p] = collections.Counter(Vhigh_allPeriods[p])

                for f in range(1, len(pinchClist)+1):
                    AllCounts = pd.DataFrame()
                    AllCounts["node"] = Coords["Node"][
                        network_summary[i][p]["Vhigh_nodes"]
                    ]
                    AllCounts["voltage"] = network_summary[i][p]["Vhigh_vals"]
                    AllCounts = AllCounts[
                        AllCounts["node"].astype(str).str[0] == str(f)
                    ]
                    if len(AllCounts) > 0:
                        VHpinch[p][i][f] = AllCounts["node"][
                            AllCounts["node"] == AllCounts["node"].max()
                        ].index[0]

            if len(network_summary[i][p]["Vlow_nodes"]) > 0:
                for item in network_summary[i][p]["Vlow_nodes"]:
                    Vlow_allPeriods[p].append(item)
                Vlow_count[p] = collections.Counter(Vlow_allPeriods[p])

    return Chigh_count, Vhigh_count, Vlow_count, VHpinch
    ##--- The Chigh_count, Vhigh_count, Vlow_count tell us how often we have
    ##--- violations. they should be empty if the adjustments work.


###------ Thes spatial plots display locations of Violations---########
def plots(Network_Path, Chigh_count, Vhigh_count, Vlow_count, pinchClist,colors,k):
    Coords = pd.read_csv(str(Network_Path) + "/XY_Position.csv")
    Lines = pd.read_csv(
        str(Network_Path) + "/Lines.txt",
        delimiter=" ",
        names=["New", "Line", "Bus1", "Bus2", "phases", "Linecode", "Length", "Units"],
    )
    Lines.loc[-1] = ["New", "Trans", "Bus1=1", "Bus2=11", "1", "-", "-", "-"]
    Lines.index = Lines.index + 1  # shifting index
    Lines.sort_index(inplace=True)
    ##### Set Up NetworkX Graph from coordinates and network outputs ####
    G = nx.Graph()

    Edge = {}

    for index, value in Lines["Bus1"].items():
        Edge[index] = int(Lines["Bus1"][index][5:]), int(Lines["Bus2"][index][5:])

    pos = {}
    for index, value in Coords["Node"].items():
        pos[index] = float(Coords["X"][index]), int(Coords["Y"][index])

    pos = dict((Coords["Node"][key], value) for (key, value) in pos.items())

    G.add_nodes_from(Coords["Node"])
    G.add_edges_from(Edge.values())
    n = 1


    for p in range(1, 4):
                # --------- Add colors to nodes
        Coords["Color"]='red'
        for f in range(1, len(pinchClist)+1):
            Coords["Color"][Coords["Node"].astype(str).str[0] == str(f)] = colors[f-1]
        Coords["Color"].iloc[0] = "blue"
        Lines["Color"] = "white"
        Lines["width"] = 1
        Coords["size"] = 1
        # -------- Add colors to Current congested lines
        if len(Chigh_count[p]) > 0:
            Chigh_keys = [x + 1 for x in list(Chigh_count[p].keys())]
            Lines["Color"].iloc[Chigh_keys] = "blue"
            Lines["width"].iloc[Chigh_keys] = list(Chigh_count[p].values())

        # -------- Add colors to Voltage congested lines
        if len(Vhigh_count[p]) > 0:
            Vhigh_keys = [x for x in list(Vhigh_count[p].keys())]
            Coords["Color"].iloc[Vhigh_keys] = "black"
            Coords["size"].iloc[Vhigh_keys] = list(Vhigh_count[p].values())
            ##### Plot Currents for each Phase ####
        if len(Vlow_count[p]) > 0:
            Vlow_keys = [x for x in list(Vlow_count[p].keys())]
            Coords["Color"].iloc[Vlow_keys] = "black"
            Coords["size"].iloc[Vlow_keys] = list(Vlow_count[p].values())
            ##### Plot Currents for each Phase ####
        plt.figure('network plot, phase'+str(p)+k)
        # plt.figure(311+p)
        plt.title("Current + High/Low Voltage, Phase  " + str(p))
        nx.draw(
            G,
            pos,
            with_labels=False,
            width=Lines["width"] / max(Lines["width"]),
            node_size=Coords["size"] / max(Coords["size"]),
            node_color=Coords["Color"],
            edge_color=Lines["Color"],
            font_weight="bold",
        )
        plt.show()
        plt.tight_layout()
    n = n + 1

    return Coords


#######----------- This function returns headroom and footroom based on voltage power flow limits
def Headroom_calc(
    RateArray,
    VoltArray,
    All_VC,
    Flow,
    Trans_kVA,
    Customer_Summary,
    pinchClist,
    TransRatekVA,
    sims
):
         
    custph = {}
    Customer_Summary["feeder"] = Customer_Summary["Node"].astype(str).str[0]
    cs=[]
    for p in range(1, 4):
        custs = Customer_Summary[Customer_Summary["Phase"].astype(int) == (p)]
        custph[p] = {}
        for f in range(1, len(pinchClist)+1):
            custph[p][f] = custs[custs["feeder"].astype(int) == f]
            cs.append(str(p)+str(f))

    Txhdrm=pd.Series(index=sims.tolist())
    Headrm = pd.DataFrame(index=sims.tolist(), columns=cs)
    Footrm = pd.DataFrame(index=sims.tolist(), columns=cs)
    Rate = pd.DataFrame(index=sims.tolist(), columns=cs)
    Flag = pd.DataFrame(index=sims.tolist(), columns=cs)
    C_rate = pd.DataFrame(index=sims.tolist(), columns=cs)
    ###--- We go through every timestep modelled (sims) and calculate the Rate which is a minimum of
    ###--- C_rate (minimum of supply cable rating coverted to kVA) or V_rate which is the minimum voltage
    ###--- power flow limit calculated in voltage_headroom.py and stored for all zones in All_VC.pickle for each network
    for i in sims.tolist():
        Txhdrm[i] = TransRatekVA+Trans_kVA[i]
        print('hdrm calc ', i, round(TransRatekVA,1),'tx_flow',round(Trans_kVA[i],1),'tx_hdrm', round(Txhdrm[i],1))
        for p in range(1, 4):
            Vseries = pd.Series(VoltArray[i][:, p - 1])
            for f in range(1, len(pinchClist)+1):
                ###--- convert supply cable rating (RateArray)
                ###--- pinchClist is the list of supply cable numbers for each zone
                C_rate[str(p) + str(f)][i]= 0.9*RateArray[pinchClist[f - 1]] * Vseries[1] * 0.416 / (3 ** 0.5)
                if (str(p)+str(f)) in All_VC:
                    V_rate = All_VC[str(p)+str(f)]
                ###--- some zones have zero customers (zero power flow), in those cases there is no value in All_VC for that zone
                ###--- In which case V_rate is set to C_rate (but these zones are ignored in future analysis)
                else:
                    V_rate = C_rate[str(p) + str(f)][i]
                Rate[str(p) + str(f)][i] = min(C_rate[str(p) + str(f)][i],V_rate)
                ###--- Headroom and footroom are calculated as the difference between the rate and the supply cable power flow
                Headrm[str(p) + str(f)][i] = Rate[str(p) + str(f)][i]  - Flow[str(p) + str(f)][i] 
                Footrm[str(p) + str(f)][i] = Rate[str(p) + str(f)][i]  + Flow[str(p) + str(f)][i] 
                ###--- Flag simply stores a letter corresponding to the binding constraint
                if Rate[str(p) + str(f)][i] == C_rate[str(p) + str(f)][i] and Headrm[str(p) + str(f)][i]<0:
                    Flag[str(p) + str(f)][i]='c'  ##--- 'c' means cable rating (thermal)
                if Rate[str(p) + str(f)][i] == V_rate and Headrm[str(p) + str(f)][i]<0:
                    Flag[str(p) + str(f)][i]='v' ##--- 'v' means minimum voltage
        if Txhdrm[i]<0:
            Flag.loc[i]='t'  ##--- 't' means transformer (thermal)
        if sum(Headrm.loc[i]) > Txhdrm[i]:
            Headrm.loc[i]=Headrm.loc[i]+((Txhdrm[i]-Headrm.loc[i].sum())/len(Headrm.loc[i]))
            print(sum(Headrm.loc[i]),'Zonal Headroom reduced by transformer limit')

    return Headrm, Footrm, Txhdrm, Flag,C_rate


###---------- The secondary headroom, adjustments and per phase headrooms are shown
def plot_headroom(Headrm, Footrm, Flow, Rate, labels, pinchClist,InputsbyFP,genres,colors,k):
    # times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    plt.figure('Trans Headroom')
    plt.plot(
        Headrm[0].values,
        color=labels["col"],
        linewidth=1,
        linestyle=labels["style"],
        label=labels["label"],
    )
    plt.plot(
        InputsbyFP['demand'].sum(axis=1).values-genres.values,
        color='green',
        linewidth=1.5,
        linestyle=labels["style"],
        label='',
    )
    plt.plot(
        np.full(len(Headrm[0]), labels["TranskVA"]),
        color="red",
        linestyle="--",
        linewidth=0.5,
    )
    plt.plot(
        np.full(len(Headrm[0]), -labels["TranskVA"]),
        color="red",
        linestyle="--",
        linewidth=0.5,
    )
    plt.ylabel("Transformer Power Flow (kVA)")
    plt.title("Network 1 - Secondary Substation Headroom")
    plt.legend()
    plt.xlim([0, len(Headrm[0])])

    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.xticks(
        range(0, len(Headrm[0]), 24),
        Headrm[0].index.strftime("%d/%m %H:%M")[range(0, len(Headrm[0]), 24)],
    )

    plt.figure('Headroom'+k)
    plt.title("Headroom (at head supply branch) per phase and feeder")

    for p in range(1, 4):
        plt.subplot(310 + p)
        for f in range(1, len(pinchClist)+1):
            plt.plot(
                Flow[f][p].values,
                linewidth=1,
                # linestyle="--",
                label="Feeder " + str(f),
                color=colors[f - 1]
            )
            plt.plot(Rate[f][p].values/0.9, color="red", linestyle="--", linewidth=0.5)
            plt.plot(
                np.zeros(len(Headrm[0])), color="blue", linestyle="--", linewidth=0.5
            )
            plt.plot(-Rate[f][p].values/0.9, color="red", linestyle="--", linewidth=0.5)
        plt.title("Phase " + str(p))
        plt.ylabel("Power Flow (kW)")

        plt.xlim([0, len(Headrm[0])])
        plt.ylim([-200, 200])

        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(
            range(0, len(Headrm[0]), 24),
            Headrm[0].index.strftime("%d/%m %H:%M")[range(0, len(Headrm[0]), 24)],
        )

    axes = plt.gca()
    arrow_properties1 = dict(facecolor=sns.xkcd_rgb["pale red"], width=4, headwidth=8)
    arrow_properties2 = dict(facecolor=sns.xkcd_rgb["denim blue"], width=4, headwidth=8)

    plt.annotate(
        "", xy=(1, 75), xytext=(1, 0), arrowprops=arrow_properties1, fontsize=10
    )

    plt.annotate(
        "", xy=(1, -75), xytext=(1, 0), arrowprops=arrow_properties2, fontsize=10
    )

    style1 = dict(size=8, color=sns.xkcd_rgb["pale red"], weight="bold")
    style2 = dict(size=8, color=sns.xkcd_rgb["denim blue"], weight="bold")

    axes.text(1.5, 60, "Import Headroom", **style1)
    axes.text(1.5, -60, "Export Footroom", **style2)
    plt.legend()
    plt.tight_layout()


#######---------- Demand and PV adjustments are shown along with Heat pump and Smartmeter demand
def plot_flex(InputsbyFP,pinchClist,colors,k):

    # ------- PLot of demand and generation per feeder and phase
    
    # plt.figure('demand delta '+k)
    # for p in range(1, 4):
    #     plt.subplot(310 + p)
    #     for f in range(1, len(pinchClist)+1):
    #         if InputsbyFP["demand_delta"].sum().sum() != 0:
    #             plt.plot(
    #                 InputsbyFP["demand_delta"][str(p) + str(f)].values,
    #                 linewidth=1,
    #                 linestyle="-",
    #                 color=colors[f - 1],
    #                 label="Feeder " + str(f),
    #             )
    #         if InputsbyFP["pv_delta"].sum().sum() != 0:
    #             plt.plot(
    #                 -InputsbyFP["pv_delta"][str(p) + str(f)].values,
    #                 linewidth=1,
    #                 linestyle="--",
    #                 color=colors[f - 1],
    #                 #label="Feeder " + str(f),
    #             )
    #     plt.title("Phase " + str(p))
    #     plt.ylabel("Delta (kW)")

    #     plt.xlim([0, len(InputsbyFP["pv_delta"])])
    #     # plt.ylim([0, 5])

    #     plt.xticks(fontsize=8)
    #     plt.yticks(fontsize=8)
    #     plt.xticks(
    #         range(0, len(InputsbyFP["pv_delta"]), 24),
    #         InputsbyFP["pv_delta"].index.strftime("%d/%m %H:%M")[
    #             range(0, len(InputsbyFP["pv_delta"]), 24)
    #         ],
    #     )
    # plt.legend()
    # plt.tight_layout()

    # ----------- Plot of demands---------------#

    plt.figure('demands '+k)
    for p in range(1, 4):
        plt.subplot(310 + p)
        for f in range(1, len(pinchClist)+1):
            plt.plot(
                InputsbyFP["HP"][str(p) + str(f)].values,
                linewidth=1,
                linestyle="-",
                color=colors[f - 1],
                label="Feeder " + str(f),
            )
            plt.plot(
                InputsbyFP["SM"][str(p) + str(f)].values,
                linewidth=1,
                linestyle="--",
                color=colors[f - 1],
            )
        plt.title("HP and SM (--) Phase " + str(p))
        plt.ylabel("Demand (kW)")

        plt.xlim([0, len(InputsbyFP["HP"])])
        # plt.ylim([0, 5])

        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(
            range(0, len(InputsbyFP["HP"]), 24),
            InputsbyFP["HP"].index.strftime("%d/%m %H:%M")[
                range(0, len(InputsbyFP["HP"]), 24)
            ],
        )
    plt.legend()
    plt.tight_layout()
    
    # ----------- Plot of PV---------------#

    plt.figure('PV '+k)
    for p in range(1, 4):
        plt.subplot(310 + p)
        for f in range(1, len(pinchClist)+1):
            plt.plot(
                InputsbyFP["PV"][str(p) + str(f)].values,
                linewidth=1,
                linestyle="-",
                color=colors[f - 1],
                label="Feeder " + str(f),
            )

        plt.title("PV: Phase " + str(p))
        plt.ylabel("Output (kW)")

        plt.xlim([0, len(InputsbyFP["PV"])])
        # plt.ylim([0, 5])

        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(
            range(0, len(InputsbyFP["PV"]), 24),
            InputsbyFP["HP"].index.strftime("%d/%m %H:%M")[
                range(0, len(InputsbyFP["PV"]), 24)
            ],
        )
    plt.legend()
    plt.tight_layout()


####-------- Maximum voltage, Minimum Voltage and Current per zone are put in a dataframe (slow again) and plotted.
####---- for speed, Max voltage and Max Current are no longer stored as they werent needed

def calc_current_voltage(CurArray, VoltArray, Coords, Lines, RateArray,pinchClist,colors,sims):
    
    ###---- cs stores a list of all zones determined from pinchClist which is the 
    ###---- list of feeder supply cable numbers. For each feeder (f) there are 3 phases (p)
    cs=[]
    for p in range(1, 4):
        for f in range(1, len(pinchClist)+1):
            cs.append(str(p)+str(f))
    pinchVlist=pinchClist.copy()        
    pinchVlist.append(len(RateArray)-1)
    #print(pinchVlist)
#    Vmax = pd.DataFrame(
#        index=sims.tolist(),
#        columns=cs,
#    )
#    Vpinch = pd.DataFrame(
#        index=CurArray.keys(),
#        columns=cs,
#    )
    Vmin = pd.DataFrame(
        index=sims.tolist(),
        columns=cs,
    )
#    Cmax = pd.DataFrame(
#        index=CurArray.keys(),
#        columns=cs,
#    )
    C_Violations = pd.DataFrame(
        index=sims.tolist(),
        columns=cs,
    )
    for i in sims.tolist():
        print('vmin calc', i)
        for p in range(1, 4):

            for f in range(1, len(pinchClist)+1):
#                Cmax[str(p) + str(f)][i] = (
#                np.sign(Flow[str(p) + str(f)][i]) * CurArray[i][pinchClist[f - 1], p - 1]
#                )
                #Vmax[str(p) + str(f)][i] = VoltArray[i][Coords.index[Coords["Node"].astype(str).str[0] == str(f)].values,p - 1].max()
                Vmin[str(p) + str(f)][i] = VoltArray[i][
                    Coords.index[Coords["Node"].astype(str).str[0] == str(f)].values,
                    p - 1,
                ].min()
                curs=CurArray[i][Lines.index[Lines["Bus2"].astype(str).str[5] == str(f)].values,p - 1]
                rates=RateArray[Lines.index[Lines["Bus2"].astype(str).str[5] == str(f)].values]
                C_Violations[str(p) + str(f)][i] = sum(curs>rates)
    return Vmin, C_Violations

def plot_current_voltage(Vmax, Vmin, Cmax,RateArray,pinchClist, colors,N,k):
    # ------- PLot of maximum voltages per phase and feeder
    plt.figure(N+'Vmax '+k)
    for p in range(1, 4):
        plt.subplot(310 + p)
        for f in range(1, len(pinchClist)+1):
            plt.plot(
                Vmax[str(p) + str(f)].values,
                linewidth=1,
                linestyle="-",
                color=colors[f - 1],
                label="Feeder " + str(f),
            )
#            plt.plot(
#                Vpinch[str(p) + str(f)].values,
#                linewidth=1,
#                linestyle="--",
#                color=colors[f - 1],
#                # label="Feeder "+str(f),
#            )
        plt.plot(np.full(len(Vmax), 1.1), color="red", linestyle="--", linewidth=0.5)
        plt.title(N+"Phase " + str(p))
        plt.ylabel("Max Voltage (p.u.)")

        plt.xlim([0, len(Cmax)])
        plt.ylim([0.95, 1.15])

        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(
            range(0, len(Cmax), 24),
            Cmax.index.strftime("%d/%m %H:%M")[range(0, len(Cmax), 24)],
        )
    plt.legend()
    plt.tight_layout()

    # ------- PLot of minimum voltages per phase and feeder
    plt.figure(N+'Vmin '+k)
    for p in range(1, 4):
        plt.subplot(310 + p)
        for f in range(1, len(pinchClist)+1):
            plt.plot(
                Vmin[str(p) + str(f)].values,
                linewidth=1,
                linestyle="-",
                color=colors[f - 1],
                label="Feeder " + str(f),
            )
        plt.plot(np.full(len(Vmax), 0.9), color="red", linestyle="--", linewidth=0.5)
        plt.title(N+"Phase " + str(p))
        plt.ylabel("Min Voltage (p.u.)")

        plt.xlim([0, len(Cmax)])
        plt.ylim([0.85, 1])

        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(
            range(0, len(Cmax), 24),
            Cmax.index.strftime("%d/%m %H:%M")[range(0, len(Cmax), 24)],
        )
    plt.legend()
    plt.tight_layout()

    # ------- PLot of Current in supply branch per phase and feeder
    plt.figure(N+'Cmax '+k)
    for p in range(1, 4):
        plt.subplot(310 + p)
        for f in range(1, len(pinchClist)+1):
            plt.plot(
                Cmax[str(p) + str(f)].values,
                linewidth=1,
                linestyle="-",
                label="Feeder " + str(f),
                color=colors[f - 1]
            )
            plt.plot(
                np.full(len(Cmax), RateArray[pinchClist[f - 1]]),
                color="red",
                linestyle="--",
                linewidth=0.5,
            )
            plt.plot(
                np.full(len(Cmax), -RateArray[pinchClist[f - 1]]),
                color="red",
                linestyle="--",
                linewidth=0.5,
            )
        plt.title(N+"Phase " + str(p))
        plt.ylabel("Current (Amps)")

        plt.xlim([0, len(Cmax)])
        plt.ylim([-500, 500])

        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(
            range(0, len(Cmax), 24),
            Cmax.index.strftime("%d/%m %H:%M")[range(0, len(Cmax), 24)],
        )
    plt.legend()
    plt.tight_layout()




