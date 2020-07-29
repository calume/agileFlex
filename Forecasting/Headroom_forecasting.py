# -*- coding: utf-8 -*-
"""
Created on Thu May 02 13:48:06 2019

This python script produces forecasts of headroom calculated using OpenDSS. 

@author: Calum Edmunds
"""


######## Import packages
import scipy.io
import numpy as np
import pandas as pd

pd.options.mode.chained_assignment = None
from matplotlib import pyplot as plt
from datetime import datetime, timedelta, date, time
import datetime
import pickle
from sklearn.metrics import mean_absolute_error

smkeys = [
    "WinterWknd",
    "WinterWkd",
    "SpringWknd",
    "SpringWkd",
    "SummerWknd",
    "SummerWkd",
    "AutumnWknd",
    "AutumnWkd",
]

###----------------------- Load in Test data Set -------------##########

########- temperature data from https://power.larc.nasa.gov/data-access-viewer/
temp = pd.read_csv(
    "../../Data/heatpump/Grantham_Temp_Daily_20131101_20150301.csv", skiprows=16
)
radiation = pd.read_csv(
    "../../Data/NASA_POWER_AllSkyInsolation_01032014_13092014.csv", skiprows=10
)

radiation_W = pd.read_csv(
    "../../Data/NASA_POWER_AllSkyInsolation_01122013_01032014.csv", skiprows=10
)

temp = temp[29:118].append(temp[404:483])
radiation = radiation[40:-31]
radiation_W=radiation_W[:-1]
#temp=temp[395:483]
tempind = []
radind = []
radind_W=[]
for i in temp.index:
    tempind.append(
        datetime.datetime(
            int(temp["YEAR"][i]), int(temp["MO"][i]), int(temp["DY"][i]), 0
        )
    )

for i in radiation.index:
    radind.append(
        datetime.datetime(
            int(radiation["YEAR"][i]),
            int(radiation["MO"][i]),
            int(radiation["DY"][i]),
            0,
        )
    )

for i in radiation_W.index:
    radind_W.append(
        datetime.datetime(
            int(radiation_W["YEAR"][i]),
            int(radiation_W["MO"][i]),
            int(radiation_W["DY"][i]),
            0,
        )
    )

all_temp = temp["T2M"]
all_temp.index = tempind

all_rad = radiation["ALLSKY_SFC_SW_DWN"]
all_rad.index = radind

all_rad_W = radiation_W["ALLSKY_SFC_SW_DWN"]
all_rad_W.index = radind_W


plt.figure()
plt.hist(all_temp, bins=4)
plt.xlabel("Temperature (degC)")
plt.ylabel("Frequency")

plt.figure()
plt.hist(all_rad, bins=4)
plt.xlabel(" Summer All Sky Insolation (kW-hr/m^2/day)") # All Sky Insolation Incident on a Horizontal surface
plt.ylabel("Frequency")

plt.figure()
plt.hist(all_rad_W, bins=4)
plt.xlabel(" Winter All Sky Insolation (kW-hr/m^2/day)") # All Sky Insolation Incident on a Horizontal surface
plt.ylabel("Frequency")

###----------Winter Data------------------#####

pick_in = open("../../Data/Winter15HdRm_new.pickle", "rb")
Winter_HdRm = pickle.load(pick_in)

pick_in = open("../../Data/Winter14HdRm_new.pickle", "rb")
Winter14_HdRm = pickle.load(pick_in)

for i in Winter_HdRm.keys():
    Winter_HdRm[i]=Winter14_HdRm[i][:-1].append(Winter_HdRm[i][:-1])

pick_in = open("../../Data/Winter15Demand_delta.pickle", "rb")
WinterInputs = pickle.load(pick_in)

pick_in = open("../../Data/Winter14Demand_delta_new.pickle", "rb")
Winter14Inputs = pickle.load(pick_in)

for i in WinterInputs.keys():
    WinterInputs[i]=Winter14Inputs[i][:-1].append(WinterInputs[i][:-1])

###----------Summer Data------------------#####


pick_in = open("../../Data/Summer14Demand_delta_new.pickle", "rb")
SummerInputs = pickle.load(pick_in)

pick_in = open("../../Data/Summer14FtRm_new.pickle", "rb")
Summer_FtRm = pickle.load(pick_in)

pick_in = open("../../Data/Summer14HdRm_new.pickle", "rb")
Summer_Hdrm = pickle.load(pick_in)

########---------Convert Headroom to feeder+phase column dataframe
Headrm_DF = pd.DataFrame(
    index=Winter_HdRm[1].index,
    columns=["11", "12", "13", "14", "21", "22", "23", "24", "31", "32", "33", "34",],
)

for p in range(1, 4):
    for f in range(1, 5):
        Headrm_DF[str(p) + str(f)] = Winter_HdRm[f][p]

Footrm_DF = pd.DataFrame(
    index=Summer_FtRm[1].index,
    columns=["11", "12", "13", "14", "21", "22", "23", "24", "31", "32", "33", "34",],
)

SmrHeadrm_DF = pd.DataFrame(
    index=Summer_Hdrm[1].index,
    columns=["11", "12", "13", "14", "21", "22", "23", "24", "31", "32", "33", "34",],
)


for p in range(1, 4):
    for f in range(1, 5):
        Headrm_DF[str(p) + str(f)] = Winter_HdRm[f][p]
        Footrm_DF[str(p) + str(f)] = Summer_FtRm[f][p]
        SmrHeadrm_DF[str(p) + str(f)] = Summer_Hdrm[f][p]

#########---------Convert to daily timeseries--------

summer_dates = SummerInputs.index[:-1]
winter_dates = Headrm_DF.index[:-1]
wkd_dates = (winter_dates.weekday >= 0) & (winter_dates.weekday <= 4)
wknd_dates = (winter_dates.weekday >= 5) & (winter_dates.weekday <= 6)
wkd_dates = winter_dates[wkd_dates]
wknd_dates = winter_dates[wknd_dates]

wkd_temps = all_temp[wkd_dates[range(0, len(wkd_dates), 48)]]
wknd_temps = all_temp[wknd_dates[range(0, len(wknd_dates), 48)]]

Settings = {}
Settings["summer Ftrm"] = {
    "min": -25,
    "max": 75,
    "Q": "P5-",
    "Title": " Summer Footroom ",
    "units": " kW-hr/m^2/day ",
    "min/max": "min",
    "dates": summer_dates,
    "data": Footrm_DF[:-1],
    "temps": all_rad,
    "negative": 'Dont'
}

Settings["summer Hdrm"] = {
    "min": -25,
    "max": 75,
    "Q": "P5-",
    "Title": " Summer Headroom ",
    "units": " kW-hr/m^2/day ",
    "min/max": "min",
    "dates": summer_dates,
    "data": SmrHeadrm_DF[:-1],
    "temps": all_rad,
    "negative": 'Dont'
}

Settings["summer pv"] = {
    "min": 0,
    "max": 25,
    "Q": "P95-",
    "Title": " Summer PV Adjust ",
    "units": " kW-hr/m^2/day ",
    "min/max": "max",
    "dates": summer_dates,
    "data": SummerInputs[:-1],
    "temps": all_rad,
    "negative": True
}

Settings["winter Hdrm"] = {
    "min": -30,
    "max": 100,
    "Q": "P5-",
    "Title": " Winter Headroom ",
    "units": "deg C",#" kW-hr/m^2/day ",
    "min/max": "min",
    "dates": winter_dates,
    "data": Headrm_DF,
    "temps": all_temp,
    "negative": 'Dont'
}

Settings["winter demand"] = {
    "min": 0,
    "max": 30,
    "Q": "P95-",
    "Title": " Winter demand turn-down ",
    "units": " degC ",
    "min/max": "max",
    "dates": winter_dates,
    "data": WinterInputs[:-1]*-1,
    "temps": all_temp,
    "negative": False
}

#Settings["winter pv"] = {
#    "min": -15,
#    "max": 0,
#    "Q": "P95-",
#    "Title": " Winter pv turn-down ",
#    "units": " kW-hr/m^2/day  ",
#    "min/max": "min",
#    "dates": winter_dates,
#    "data": WinterInputs['pv_delta'][:-1],
#    "temps": all_rad_W,
#    "negative": True
#}


def advance_forecast(settings):
    dailyrange = {}
    DailyDelta = {}
    DailyByBin = {}
    cols = ["#9467bd","#bcbd22", "#ff7f0e", "#d62728"]
    times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    r = 0
    tempLabels = range(1, 5)
    # TempBins=pd.cut(settings['temps'],bins=[2.06254,3.935,5.8,7.665,9.53], labels=tempLabels, retbins=True)
    TempBins = pd.cut(settings['temps'], bins=4, labels=tempLabels, retbins=True)
    plt.figure(
        str(settings["Title"])
        + str(settings["Q"][:-1])
        + " (kWs) vs Settlement Period"
    )
    if settings["negative"]==True:
        tempLabels=tempLabels[::-1]
        cols = cols[::-1]
    for c in settings['data'].columns:
        dailyrange = range(0, len(settings['dates']), 48)
    
        DailyDelta[c] = pd.DataFrame(index=settings['dates'][dailyrange], columns=range(0, 48))
    
        for d in DailyDelta[c].index:
            mask = (settings['data'][c].index >= d) & (settings['data'][c].index < (d + timedelta(days=1)))
            DailyDelta[c].loc[d] = settings['data'][c].loc[mask].values
    
        datesBinned = {}
        DailyByBin[c] = {}
        n = 0
        r = r + 1
        plt.tight_layout()
        plt.subplot(3, 4, r)
        if r < 5:
            plt.title("Feeder - " + str(r))
        if r % 2 != 0:
            plt.ylabel("Phase " + str(c[0]))
        plt.plot(np.full(47, 0), color="red", linestyle="--", linewidth=0.5)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(range(0,47,8),times)
        for z in tempLabels:
            datesBinned[z] = TempBins[0][TempBins[0] == z].index
            DailyByBin[c][z] = pd.DataFrame(index=datesBinned[z], columns=range(0, 48))
            DailyByBin[c]["P95-" + str(z)] = pd.Series(index=range(0, 48))
            DailyByBin[c]["P5-" + str(z)] = pd.Series(index=range(0, 48))
            DailyByBin[c]["Median-" + str(z)] = pd.Series(index=range(0, 48))
            for i in datesBinned[z]:
                DailyByBin[c][z].loc[i] = DailyDelta[c].loc[i].values
            for p in range(0, 48):
                DailyByBin[c]["P95-" + str(z)][p] = DailyByBin[c][z][p].quantile(0.95)
                DailyByBin[c]["P5-" + str(z)][p] = DailyByBin[c][z][p].quantile(0.05)
                DailyByBin[c]["Median-" + str(z)][p] = DailyByBin[c][z][p].quantile(0.5)
            lbl = (
                str(round(TempBins[1][z - 1], 1))
                + " - "
                + str(round(TempBins[1][z], 1))
                + str(settings["units"])
            )
            y = DailyByBin[c][str(settings["Q"]) + str(z)].values
            plt.plot(y, linewidth=1, color=cols[n], label=lbl)
            if settings["negative"]!= 'Dont':
                plt.fill_between(range(0,48),0,y, facecolor=cols[n])
            #plt.plot(DailyByBin[c]['Median-'+str(z)].values, linewidth=1, linestyle='--', label=lbl)
            # plt.plot(DailyByBin[c]['Median'+str(z)].values, linewidth=1, linestyle='--')
            plt.ylim(settings["min"], settings["max"])
            plt.xlim(0, 47)
            n = n + 1
            plt.tight_layout()
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    plt.tight_layout()
    plt.legend()
    plt.figure('Daily '+str(settings["units"]) + " vs " +str(settings["min/max"])+str(settings["Title"]))
    u = 0
    for c in settings['data'].columns:
        print(u)
        u = u + 1
        plt.subplot(3, 4, u)
        if u < 5:
            plt.title("Feeder - " + str(u))
        if u == 1 or u == 5 or u == 9:
            plt.ylabel("Phase " + str(c[0]))
        if settings["min/max"] == "min":
            vals = DailyDelta[c].min(axis=1).values
        if settings["min/max"] == "max":
            vals = DailyDelta[c].max(axis=1).values
        plt.scatter(settings['temps'].values, vals, s=0.8)
        plt.tight_layout()
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    plt.tight_layout()
    return DailyByBin, DailyDelta

DailyByBin, DailyDelta = advance_forecast(Settings["winter Hdrm"])

#pickle_out = open("../../Data/Network1SummerHdrm.pickle", "wb")
#pickle.dump(DailyByBin, pickle_out)
#pickle_out.close()