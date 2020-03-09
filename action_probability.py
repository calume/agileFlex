# -*- coding: utf-8 -*-
"""
Created on Thu May 02 13:48:06 2019
@author: Calum Edmunds
Scripts to calculate probability of flexibility providers or 'agents' being called 
"""

######## Importing the OpenDSS Engine and other packages #########
import pandas as pd

pd.options.mode.chained_assignment = None
import pickle
import datetime
import random
import numpy as np
from numpy.random import choice
from sensitivity import sensitivity
from runDSS import runDSS
from summary import summary
from actions import actions
import cloudpickle
import copy

######### Load in the list of loads from the DSS Loads.text File #########
LoadsIn = pd.read_csv(
    "Loads.txt",
    delimiter=" ",
    names=["New", "Load", "Phase", "Bus1", "kV", "kW", "PF", "Daily"],
)
LoadsIn["Phase"] = LoadsIn["Bus1"].str[-1:]

####### PV size distributions based on Gov FiT size distribution ########
PVcaplist = [1, 1.5, 2, 2.5, 3, 3.5, 4]
PVweights = [0.01, 0.08, 0.13, 0.15, 0.14, 0.12, 0.37]
PVcap = choice(PVcaplist, int(len(LoadsIn)), PVweights)

####### Load in Distributions of EV, SM, and HP demand as well as PV output ########

########### EV IN ##############
with open("JDEV_kde.cp.pkl", "rb") as f:
    EV_kde = cloudpickle.load(f)

###########  Smartmeter Data  ###############
with open("SM_kde.cp.pkl", "rb") as f:
    SM_kde = cloudpickle.load(f)
########### PV IN ##############

with open("PV_kde.cp.pkl", "rb") as f:
    PV_kde = cloudpickle.load(f)

########### HP IN ##############
with open("HP_kde.cp.pkl", "rb") as f:
    HP_kde = cloudpickle.load(f)

####### Optional Mixture Model distributions #####

pickle_in = open("SMDistsGMMChosen.pickle", "rb")
SM_GM = pickle.load(pickle_in)

pickle_in = open("SMDistsGMMWeights.pickle", "rb")
SM_GM = pickle.load(pickle_in)


######## Assign PV, Agent, EV Tags and Zone per Load Node ############
Flags = pd.DataFrame(
    0,
    index=(range(0, len(LoadsIn))),
    columns=["Feeder", "PV", "Agent", "EV", "SM", "HP", "Zone"],
)
Flags["Feeder"] = LoadsIn["Bus1"].str[6]


###### Randomly assing Smart Meters ########
K = list(SM_kde["WintWkndDists"].keys())
for i in Flags.index.tolist():
    Flags["SM"][i] = random.choice(K)

################ Assign EVs, HPs and Agents to active Feeder ############
Flags["EV"] = 1  # Every house has EV
Flags["Agent"] = 1  # Every house is an agent
Flags["PV"] = PVcap  # Every house has PV
K = list(HP_kde["WintWkndDists"].keys())
for i in Flags.index.tolist():  # Every house has a HP
    Flags["HP"][i] = random.choice(K)

# Flags['HP'][::2]=0  # Every 2nd house has a HP

################### Calculating Load for each Demand ############################

start_date = datetime.date(2018, 6, 1)
end_date = datetime.date(2018, 9, 1)
delta = datetime.timedelta(hours=1)
sims = pd.date_range(start_date, end_date, freq=delta)

P = {}
Gen = {}
P_Opt = {}
perc = 0.2
n = 0
PO = {}
GenO = {}
aa = {}
SMd = {}
SMC = {}
EVd = {}
PVd = {}
HPd = {}
UB = {}
LB = {}
CongSummary = {}
AgentSummary = {}
LoadBusByPhase = {}
#   for z in range(0,len(Flags)):
#       n=choice(range(0,len(SM[Flags['SM'][z]])), 1, p=SMW[Flags['SM'][z]])
#       SMC[z]=SM[Flags['SM'][z]][n]

for i in sims.tolist():
    print(i)
    P[i] = np.zeros(len(Flags))
    Gen[i] = np.zeros(len(Flags))
    Currents = {}
    Voltages = {}
    Loads = {}
    Rates = {}
    CLmax = {}
    SMd[i] = np.zeros(len(Flags))
    EVd[i] = np.zeros(len(Flags))
    PVd[i] = np.zeros(len(Flags))
    HPd[i] = np.zeros(len(Flags))
    UB[i] = np.zeros(len(Flags))
    LB[i] = np.zeros(len(Flags))
    if (i.weekday() >= 5) & (i.weekday() <= 6):  ###Weekend######
        EV = EV_kde  # ['WkndDists']
        if (i.month == 12) | (i.month <= 2):  # Dec-Feb
            SM = SM_kde["WintWkndDists"]
            # SMW=SM_GM['WintWkndDists']
            HP = HP_kde["WintWkndDists"]
            PV = PV_kde["WintDists"]
        if (i.month >= 3) & (i.month <= 5):  # Mar-May
            SM = SM_kde["SpringWkndDists"]
            # SMW=SM_GM['SpringWkndDists']
            HP = HP_kde["SpringWkndDists"]
            PV = PV_kde["SpringDists"]
        if (i.month >= 6) & (i.month <= 8):  # Jun-Aug
            SM = SM_kde["SummerWkndDists"]
            # SMW=SM_GM['SummerWkndDists']
            HP = HP_kde["SummerWkndDists"]
            PV = PV_kde["SummerDists"]
        if (i.month >= 9) & (i.month <= 11):  # Sept-Nov
            SM = SM_kde["AutumnWkndDists"]
            # SMW=SM_GM['AutumnWkndDists']
            HP = HP_kde["AutumnWkndDists"]
            PV = PV_kde["AutumnDists"]
    if (i.weekday() >= 0) & (i.weekday() <= 4):  ##Weekday######
        EV = EV_kde  # ['WkdDists']
        if (i.month == 12) | (i.month <= 2):  # Dec-Feb
            SM = SM_kde["WintWkdDists"]
            # SMW=SM_GM['WintWkdDists']
            HP = HP_kde["WintWkdDists"]
            PV = PV_kde["WintDists"]
        if (i.month >= 3) & (i.month <= 5):  # Mar-May
            SM = SM_kde["SpringWkdDists"]
            # SMW=SM_GM['SpringWkdDists']
            HP = HP_kde["SpringWkdDists"]
            PV = PV_kde["SpringDists"]
        if (i.month >= 6) & (i.month <= 8):  # Jun-Aug
            SM = SM_kde["SummerWkdDists"]
            # SMW=SM_GM['SummerWkdDists']
            HP = HP_kde["SummerWkdDists"]
            PV = PV_kde["SummerDists"]
        if (i.month >= 9) & (i.month <= 11):  # Sept-Nov
            SM = SM_kde["AutumnWkdDists"]
            # SMW=SM_GM['AutumnWkdDists']
            HP = HP_kde["AutumnWkdDists"]
            PV = PV_kde["AutumnDists"]

    if PV[i.hour] != 0:
        samp = max(PV[i.hour].resample(1), 0)
    for z in range(0, len(Flags)):
        SMd[i][z] = max(SM[Flags["SM"][z]][i.hour].resample(1), 0)
        EVd[i][z] = max(EV[i.hour].resample(1), 0) * Flags["EV"][z]
        if Flags["HP"][z] == 0:
            HPd[i][z] = 0
        else:
            HPd[i][z] = max(HP[Flags["HP"][z]][i.hour].resample(1), 0)
        if PV[i.hour] == 0:
            PVd[i][z] = 0
        else:
            PVd[i][z] = samp * Flags["PV"][z]

        P[i][z] = SMd[i][z] + EVd[i][z] + HPd[i][z]
        Gen[i][z] = PVd[i][z]
        UB[i][z] = (
            int(not (Flags["Agent"][z])) * Gen[i][z]
        )  # Which equates to SMd[i][z]+HPd[i][z]+EVd[i][z]
        LB[i][z] = P[i][z] + Flags["Agent"][z] * (
            -EVd[i][z] - HPd[i][z]
        )  # Which equates to  SMd[i][z]-PVd[i][z]

    u = 0 * P[i]
    ug = 0 * Gen[i]

    P[i][np.isnan(P[i])] = 0
    PO[i] = copy.copy(P[i])
    GenO[i] = copy.copy(Gen[i])
    ###### Run DSS for initial network state ###########
    n = 1
    (
        Loadarray,
        CurArray,
        VoltArray,
        RateArray,
        CurMaxInit,
        VmaxInit,
        VminInit,
        Locationsi,
    ) = runDSS(P[i], Gen[i], u, ug)

    ## Run Sensitivity ###

    (
        Violperphase,
        VmaxFlagInit,
        VminFlagInit,
        ThermalFlagInit,
        n,
        Locations,
    ) = sensitivity(
        LoadsIn,
        P[i],
        Gen[i],
        Loadarray,
        CurArray,
        VoltArray,
        RateArray,
        CurMaxInit,
        VmaxInit,
        VminInit,
        n,
    )

    ### Generate LoadBus Summary  #######

    LoadBusByPhase[i] = summary(
        LoadsIn,
        Violperphase,
        CurMaxInit,
        VmaxInit,
        VminInit,
        P[i],
        Gen[i],
        PO[i],
        LB[i],
        UB[i],
    )

    P[i], Gen[i], LoadBusByPhase[i] = actions(
        P[i],
        Gen[i],
        LB[i],
        UB[i],
        PVd[i],
        EVd[i],
        HPd[i],
        u,
        ug,
        n,
        LoadBusByPhase[i],
        CurMaxInit,
        VmaxInit,
        VminInit,
        LoadsIn,
        PO[i],
    )

    CongSummary[i] = {}
    for p in range(0, 3):
        CongSummary[i][p] = {}
        CongSummary[i][p]["Voltages"] = Locationsi["Voltages"][p]
        CongSummary[i][p]["Currents"] = Locationsi["Current"][p]
        CongSummary[i][p]["Headroom"] = Locationsi["Hdrm"][p]
        if ThermalFlagInit[p] == True:
            CongSummary[i][p]["ThermalLineNos"] = Locationsi["Cmax"][p]
        if VmaxFlagInit[p] == True:
            CongSummary[i][p]["VhighBusNos"] = Locationsi["Vmax"][p]
        if VminFlagInit[p] == True:
            CongSummary[i][p]["VlowBusNos"] = Locationsi["Vmin"][p]

    ###### Create summary of agent actions ###########
    AgentSummary[i] = pd.DataFrame(
        index=range(0, len(LoadsIn)),
        columns=[
            "Bus",
            "Phase",
            "BaseDemand",
            "EV",
            "PV",
            "HP",
            "LoadSetPoint",
            "DemLB",
            "GenLB",
            "DemAdjust",
            "FinalDem",
            "FinalGen",
            "GenAdjust",
        ],
    )
    AgentSummary[i]["Bus"] = LoadsIn["Bus1"].str[5:-2]
    AgentSummary[i]["Phase"] = LoadsIn["Phase"]
    AgentSummary[i]["BaseDemand"] = SMd[i]
    AgentSummary[i]["EV"] = EVd[i]
    AgentSummary[i]["PV"] = PVd[i]
    AgentSummary[i]["HP"] = HPd[i]
    AgentSummary[i]["LoadSetPoint"] = PO[i]
    AgentSummary[i]["DemLB"] = LB[i]
    AgentSummary[i]["GenLB"] = UB[i]
    AgentSummary[i]["DemAdjust"] = P[i] - PO[i]
    AgentSummary[i]["FinalDem"] = P[i]
    AgentSummary[i]["FinalGen"] = Gen[i]
    AgentSummary[i]["GenAdjust"] = Gen[i] - GenO[i]

pickle_out = open("AgentSummarySummerFeed2_100PV.pickle", "wb")
pickle.dump(AgentSummary, pickle_out)
pickle_out.close()

pickle_out = open("CongSummarySummerFeed2_100PV.pickle", "wb")
pickle.dump(CongSummary, pickle_out)
pickle_out.close()
