#==================================================================
# EVSchedule.mod
# PYOMO model file
# This formulation uses the standard "DC" model of AC power flow equations
# ---Author---
# W. Bukhsh,
# wbukhsh@gmail.com
# OATS
# Copyright (c) 2017 by W Bukhsh, Glasgow, Scotland
# OATS is distributed under the GNU GENERAL PUBLIC LICENSE v3. (see LICENSE file for details).
#==================================================================

#==========Import==========
from __future__ import division
from pyomo.environ import *
#==========================

model = AbstractModel()

# --- SETS ---
model.B      = Set()  # set of buses, as a list of positive integers
model.G      = Set()  # set of generators, as a list of positive integers
model.D      = Set()  # set of demands, as a list of positive integers
model.L      = Set()  # set of lines, as a list of positive integers
model.TRANSF = Set()  # set of transformers, as a list of positive integers
model.SHUNT  = Set()  # set of shunts, as a list of positive integers
model.LE     = Set()  # line-to and from ends set (1,2)
model.b0     = Set(within=model.B)  # set of reference buses
model.T      = Set()  # set of time periods
model.TRed   = Set()  # set of time periods
model.EV     = Set()  # set of EVs
model.Window = Set()

model.EVWindow = Set(within=model.EV*model.Window)

model.EVFlexWindow       = Set(within = model.EV*model.Window*model.LE)
model.FlexTimes          = Set(within = model.EV*model.Window*model.T)
model.FlexTimesRed       = Set(within = model.EV*model.Window*model.T)
model.FlexTimesBoundary  = Set(within = model.EV*model.Window*model.T)
model.EVBoundaryStart    = Set(within = model.FlexTimes) #boundary conditions
model.EVBoundaryEnd      = Set(within = model.FlexTimes) #boundary conditions

model.SoCStart     = Param(model.EVBoundaryStart)
model.SoCEnd       = Param(model.EVBoundaryEnd)

# generators, buses, loads linked to each bus b
model.Gbs     = Set(within=model.B * model.G)    # set of generator-node mapping
model.Dbs     = Set(within=model.B * model.D)    # set of demand-node mapping
model.SHUNTbs = Set(within=model.B*model.SHUNT)  # set of shunt-node mapping
model.EVbs     = Set(within=model.B * model.EV)   # set of EV-node mapping

# --- parameters ---
# line matrix
model.A     = Param(model.L*model.LE)       # bus-line (node-arc) matrix
model.AT    = Param(model.TRANSF*model.LE)  # bus-transformer (node-arc) matrix

# demands
model.PD      = Param(model.D, model.T, within=Reals)  # real power demand at load d, p.u.
model.VOLL    = Param(model.D, within=Reals)
# generators
model.PGmax    = Param(model.G, model.T, within=Reals)# max real power of generator, p.u.
model.PGmin    = Param(model.G, model.T, within=Reals)# min real power of generator, p.u.
# model.RampUp   = Param(model.G, within=NonNegativeReals) # ramp up of generator g, p.u.
# model.RampDown = Param(model.G, within=NonNegativeReals) # ramp down of generator g, p.u.

# storage
model.PVUB          = Param(model.EV, within=NonNegativeReals)# max real power charging capacity
model.EVUB          = Param(model.EV, within=NonNegativeReals)# max energy capacity of the battery

model.RateCharge    = Param(model.EV, within=NonNegativeReals)# rate of charging of storage

# lines and transformer chracteristics and ratings
# model.SLmax  = Param(model.L, within=NonNegativeReals) # max real power limit on flow in a line, p.u.
# model.SLmaxT = Param(model.TRANSF, within=NonNegativeReals) # max real power limit on flow in line l, p.u.
# model.BL     = Param(model.L, within=Reals)  # susceptance of a line, p.u.
# model.BLT    = Param(model.TRANSF, within=Reals)  # susceptance of line l, p.u.

#emergency ratings
model.SLmax_E  = Param(model.L, within=NonNegativeReals) # max emergency real power limit on flow in a line, p.u.
model.SLmaxT_E = Param(model.TRANSF, within=NonNegativeReals) # max emergency real power limit on flow in a line, p.u.

# shunt
model.GB = Param(model.SHUNT, within=Reals) #  shunt conductance
model.BB = Param(model.SHUNT, within=Reals) #  shunt susceptance

# cost data
model.cost    = Param(model.G,model.T, within=NonNegativeReals)# generator cost coefficient c2 (*pG^2)

model.baseMVA = Param(within=NonNegativeReals)# base MVA

#constants
model.nT           = Param(within=NonNegativeReals) #total time horizon
model.ChargeEff    = Param(within=NonNegativeReals) #charging efficiency of V2G
model.DischargeEff = Param(within=NonNegativeReals) #discharging efficiency of V2G

# === Pre-contigency variables ===
# --- control variables ---
model.pG    = Var(model.G, model.T, domain= Reals)  #real power generation
model.pD    = Var(model.D, model.T, domain= Reals) #real power demand delivered
model.alpha = Var(model.D, model.T, domain= NonNegativeReals) #propotion of real power demand delivered


model.pEVCharge       = Var(model.FlexTimes, domain= NonNegativeReals)  #real power charging
model.pEVDischarge    = Var(model.FlexTimes, domain= NonNegativeReals)  #real power discharging

model.SoC    = Var(model.FlexTimes, domain= Reals)  #State of charge
# --- state variables ---
model.deltaL   = Var(model.L, model.T, domain= Reals) # angle difference across lines
model.deltaLT  = Var(model.TRANSF, model.T, domain= Reals) # angle difference across transformers
model.delta    = Var(model.B, model.T, domain= Reals, initialize=0.0) # voltage phase angle at bus b, rad
model.pL       = Var(model.L, model.T, domain= Reals) # real power injected at b onto line l, p.u.
model.pLT      = Var(model.TRANSF, model.T, domain= Reals) # real power injected at b onto transformer line l, p.u.

model.eps      = Var(domain= NonNegativeReals) # slack

# --- costs
model.CostTP  = Var(model.T) # Objective function component for pre-contingency operation

# --- cost function ---
def objective(model):
    #obj = sum(model.FPreCont[t] for t in model.T)
    obj = sum(model.CostTP[t] for t in model.T)
    return obj
model.OBJ = Objective(rule=objective, sense=minimize)

# --- cost components of the objective function ---
def precontingency_cost(model,t):
    return model.CostTP[t] == sum(model.cost[g,t]*model.baseMVA*model.pG[g,t] for g in model.G)\
    +sum(model.baseMVA*model.VOLL[d]*(1-model.alpha[d,t])*model.PD[d,t] for d in model.D)+10000*model.eps
model.precontingency_cost_const = Constraint(model.T,rule=precontingency_cost)

# --- Kirchoff's current law Definition at each bus b ---
def KCL_def(model, b,t):
    return sum(model.pG[g,t] for g in model.G if (b,g) in model.Gbs) +\
    sum(model.pEVDischarge[c,w,t]-model.pEVCharge[c,w,t] for (c,w) in model.EVWindow if (b,c) in model.EVbs if (c,w,t) in model.FlexTimes) == \
    sum(model.pD[d,t] for d in model.D if (b,d) in model.Dbs)
    # sum(model.pL[l,t] for l in model.L if model.A[l,1]==b)- \
    # sum(model.pL[l,t] for l in model.L if model.A[l,2]==b)+\
    # sum(model.pLT[l,t] for l in model.TRANSF if model.AT[l,1]==b)- \
    # sum(model.pLT[l,t] for l in model.TRANSF if model.AT[l,2]==b)+\
    # sum(model.GB[s] for s in model.SHUNT if (b,s) in model.SHUNTbs)
# the next line creates one KCL constraint for each bus
model.KCL_const = Constraint(model.B, model.T, rule=KCL_def)

# # --- Kirchoff's voltage law on each line and transformer---
# def KVL_line_def(model,l,t):
#     return model.pL[l,t] == (-model.BL[l])*model.deltaL[l,t]
# def KVL_trans_def(model,l,t):
#     return model.pLT[l,t] == (-model.BLT[l])*model.deltaLT[l,t]
# #the next two lines creates KVL constraints for each line and transformer, respectively.
# model.KVL_line_const     = Constraint(model.L, model.T, rule=KVL_line_def)
# model.KVL_trans_const    = Constraint(model.TRANSF, model.T, rule=KVL_trans_def)

# --- demand model ---
def demand_model(model,d,t):
    return model.pD[d,t] == model.alpha[d,t]*model.PD[d,t]
def demand_LS_bound_Max(model,d,t):
    return model.alpha[d,t] <= 1
#the next two lines creates constraints for demand model
model.demandmodelC = Constraint(model.D, model.T, rule=demand_model)
model.demandalphaC = Constraint(model.D, model.T, rule=demand_LS_bound_Max)


# --- EV charging model ---
def EV_SoC(model,c,w,t):
    return model.SoC[c,w,t] == 1/6*(model.ChargeEff*model.pEVCharge[c,w,t-1] - (1/model.DischargeEff)*model.pEVDischarge[c,w,t-1]) + model.SoC[c,w,t-1]
model.EVmodel = Constraint(model.FlexTimesRed,rule=EV_SoC)


def EV_SoCBoundary1(model,c,w,t):
    return model.SoC[c,w,t] == model.SoCStart[c,w,t]
model.EVmodelSoCStart = Constraint(model.EVBoundaryStart,rule=EV_SoCBoundary1)

def EV_SoCBoundary2(model,c,w,t):
    return model.SoC[c,w,t] == model.SoCEnd[c,w,t]*0.97
model.EVmodelSoCEnd = Constraint(model.EVBoundaryEnd,rule=EV_SoCBoundary2)

def EV_ChargeCapUB1(model,c,w,t):
    return model.pEVCharge[c,w,t] <= model.PVUB[c]

def EV_ChargeCapUB2(model,c,w,t):
    return model.pEVDischarge[c,w,t] <= model.PVUB[c]

def EV_ChargeCap2(model,c,w,t):
    # return model.SoC[c,w,t]<=model.EVUB[c]
    return model.pEVCharge[c,w,t] <= (1.0/0.201)*model.PVUB[c]/model.EVUB[c]*(1.001*model.EVUB[c]-model.SoC[c,w,t])+model.eps



model.EV_ChargeCapConst1 = Constraint(model.FlexTimes,rule=EV_ChargeCapUB1)
model.EV_ChargeCapConst2 = Constraint(model.FlexTimes,rule=EV_ChargeCapUB2)
model.EV_ChargeCapConst3 = Constraint(model.FlexTimes,rule=EV_ChargeCap2)

# --- generator power limits ---
def Real_Power_Max(model,g,t):
    return model.pG[g,t] <= model.PGmax[g,t]
def Real_Power_Min(model,g,t):
    return model.pG[g,t] >= model.PGmin[g,t]
#the next two lines creates generation bounds for each generator.
model.PGmaxC = Constraint(model.G, model.T, rule=Real_Power_Max)
model.PGminC = Constraint(model.G, model.T, rule=Real_Power_Min)

# # --- line power limits ---
# def line_lim1_def(model,l,t):
#     return model.pL[l,t] <= model.SLmax[l]
# def line_lim2_def(model,l,t):
#     return model.pL[l,t] >= -model.SLmax[l]
# #the next two lines creates line flow constraints for each line.
# model.line_lim1 = Constraint(model.L, model.T, rule=line_lim1_def)
# model.line_lim2 = Constraint(model.L, model.T, rule=line_lim2_def)

# # --- power flow limits on transformer lines---
# def transf_lim1_def(model,l,t):
#     return model.pLT[l,t] <= model.SLmaxT[l]
# def transf_lim2_def(model,l,t):
#     return model.pLT[l,t] >= -model.SLmaxT[l]
# #the next two lines creates line flow constraints for each transformer.
# model.transf_lim1 = Constraint(model.TRANSF, model.T, rule=transf_lim1_def)
# model.transf_lim2 = Constraint(model.TRANSF, model.T, rule=transf_lim2_def)

# # --- phase angle constraints ---
# def phase_angle_diff1(model,l,t):
#     return model.deltaL[l,t] == model.delta[model.A[l,1],t] - \
#     model.delta[model.A[l,2],t]
# model.phase_diff1 = Constraint(model.L, model.T, rule=phase_angle_diff1)

# # --- phase angle constraints ---
# def phase_angle_diff2(model,l,t):
#     return model.deltaLT[l,t] == model.delta[model.AT[l,1],t] - \
#     model.delta[model.AT[l,2],t]
# model.phase_diff2 = Constraint(model.TRANSF, model.T, rule=phase_angle_diff2)

# # --- reference bus constraint ---
# def ref_bus_def(model,b,t):
#     return model.delta[b,t]==0
# model.refbus = Constraint(model.b0, model.T, rule=ref_bus_def)


# #======Constraints fixing last time period charging======
def fix_pcharge(model,c,w,t):
    return model.pEVCharge[c,w,t] == 0
def fix_pdischarge(model,c,w,t):
    return model.pEVDischarge[c,w,t] == 0

model.ChargingBoundaryConst     = Constraint(model.FlexTimesBoundary, rule=fix_pcharge)
model.DischargingBoundaryConst  = Constraint(model.FlexTimesBoundary, rule=fix_pdischarge)

#
# #======Constraints linking time periods======
# #generation
# def generation_temporal_link_rampUp_def(model,g,t):
#     return model.pG[g,t]-model.pG[g,t-1]<=model.RampUp[g]
# def generation_temporal_link_rampDown_def(model,g,t):
#     return model.pG[g,t]-model.pG[g,t-1]>=-model.RampDown[g]
# model.generation_temporal_link_rampUp_const   = Constraint(model.G,model.TRed, rule=generation_temporal_link_rampUp_def)
# model.generation_temporal_link_rampDown_const = Constraint(model.G,model.TRed, rule=generation_temporal_link_rampDown_def)