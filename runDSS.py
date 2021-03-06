# -*- coding: utf-8 -*-
"""
Created on Fri Aug  2 11:54:13 2019

@author: qsb15202
"""
######## Importing the OpenDSS Engine  #########

import opendssdirect as dss
import numpy as np
import pandas as pd
import pickle
from opendssdirect.utils import run_command

pd.options.mode.chained_assignment = None

### Set up DSS Commands ####

DSSCircuit = dss.Circuit
DSSLoads = dss.Loads
DSSBus = dss.Bus
DSSLines = dss.Lines
DSSGens = dss.Generators
DSSTransformers = dss.Transformers

####----- For each Load a generator is created to allow PV to be added
def create_gens(Network_Path):
    LoadsIn = pd.read_csv(
        str(Network_Path) + "Loads.txt",
        delimiter=" ",
        names=["New", "Load", "Phases", "Bus1", "kV", "kW", "PF", "Daily"],
    )
    GensIn = pd.read_csv(
        str(Network_Path) + "Generators.txt",
        delimiter=" ",
        index_col=False,
        names=["New", "Generator", "Bus1", "kV", "kW", "PF"],
    )

    GensIn["Generator"][0] = "Generator.GEN" + str(LoadsIn["Load"][0][9:])
    GensIn["Bus1"][0] = LoadsIn["Bus1"][0]
    for i in LoadsIn.index[1:]:
        print(i)
        GensIn = GensIn.append(GensIn.iloc[i - 1], ignore_index=True)
        GensIn["Generator"][i] = "Generator.GEN" + str(LoadsIn["Load"][i][9:])
        GensIn["Bus1"][i] = LoadsIn["Bus1"][i]

    GensIn.to_csv(
        str(Network_Path) + "Generators.txt", sep=" ", index=False, header=False
    )

####### Compile the OpenDSS file using the Master.txt directory#########
def runDSS(Network_Path, demand, pv,ev):
      
    dss.Basic.ClearAll()
    dss.Basic.Start(0)

    Voltages = {}
    Currents = {}
    Powers = {}
    Rates = {}
    
    run_command("Redirect ./" + str(Network_Path) + "Master.dss")
    ################### Calculating Load for each Demand ############################
    iterations=100
    v_delta=0
    c=0
    print(sum(pv))
    while iterations==100 and v_delta<0.05:
        iLoad = DSSLoads.First()
        while iLoad > 0:
            DSSLoads.kW(demand[iLoad - 1])
            if ev[iLoad - 1]>0:
                kva=(demand[iLoad - 1]-ev[iLoad - 1])/0.95+ev[iLoad - 1]/0.98
                DSSLoads.kvar((kva**2-demand[iLoad - 1]**2)**0.5)
            ##print(DSSLoads.kW(),'kW',DSSLoads.kvar(),'kvar',DSSLoads.PF())
            DSSLoads.Vmaxpu(50)
            DSSLoads.Vminpu(0.02)
            DSSLoads.kV(0.24)
            iLoad = DSSLoads.Next()
            if c>3:
                DSSLoads.Model(2)
        ################### Calculating Gen for each Demand ############################
        iGen = DSSGens.First()
        
        while iGen > 0:
            DSSGens.kV(0.24+v_delta)
            DSSGens.kW(pv[iGen - 1])
            DSSGens.PF(1)
            DSSGens.Vmaxpu(50)
            DSSGens.Vminpu(0.02)
            DSSGens.Phases(1)
            DSSGens.Model(1)
            if pv[iGen - 1]>0:
                DSSGens.Model(3)
            iGen = DSSGens.Next()

        ######### Solve the Circuit ############
        dss.Solution.Mode(0)
        dss.Solution.Convergence(0.0001)
        dss.Solution.MaxIterations(100)
        dss.Solution.Solve()
        dss.Monitors.SampleAll()
        iterations=dss.Solution.Iterations()
        print(iterations)
        v_delta=v_delta+0.01
        c=c+1
        
    ############-----Export Results-------------------------#################
        
    iGen = DSSGens.First()
    genres=[]
    while iGen > 0:
        #print(DSSGens.kV())
        genres.append(DSSGens.kW())
        iGen = DSSGens.Next()
    genres=sum(genres)
    ########## Export Voltages ###########
    bvs = list(DSSCircuit.AllBusMagPu())
    Voltages = bvs[0::3], bvs[1::3], bvs[2::3]
    VoltArray = np.zeros((len(Voltages[0]), 3))
    for i in range(0, 3):
        VoltArray[:, i] = np.array(Voltages[i], dtype=float)
    ########## Export Current and Power ###########
    i_Line = DSSLines.First()
    while i_Line > 0:
        curs = list(dss.CktElement.CurrentsMagAng())
        Currents[i_Line] = curs[0], curs[2], curs[4]
    
        ### Powers() is a complex power, we store the KVAr Apparent Power
        pows = list(dss.CktElement.Powers())
        Powers[i_Line] = (
            np.sign(pows[0]) * (pows[0] ** 2 + pows[1] ** 2) ** 0.5,
            np.sign(pows[2]) * (pows[2] ** 2 + pows[3] ** 2) ** 0.5,
            np.sign(pows[4]) * (pows[4] ** 2 + pows[5] ** 2) ** 0.5,
        )      
       
        Rates[i_Line] = dss.CktElement.NormalAmps()
        i_Line = DSSLines.Next()
    
    ########## Store as Arrays ############
    CurArray = np.array(list(Currents.values()), dtype=float)
    PowArray = np.array(list(Powers.values()), dtype=float)
    Losses = dss.Circuit.Losses()[0] / 1000
    RateArray = np.array(list(Rates.values()), dtype=float)
    TranskVA = np.sign(dss.Circuit.TotalPower()[0]) * (dss.Circuit.TotalPower()[0] ** 2 + dss.Circuit.TotalPower()[1] ** 2) ** 0.5
    TransRatekVA = DSSTransformers.kVA()
    converged=dss.Solution.Converged()
    return CurArray, VoltArray, PowArray, Losses, TranskVA, RateArray, TransRatekVA,genres,converged

###------- Using the network outputs (voltage and current) from Opendss
###------- network summary is generated including overvoltage and current locations

            

# from feedbackplot import plots
# plots(Network_Path,VoltArray,CurArray,RateArray)
