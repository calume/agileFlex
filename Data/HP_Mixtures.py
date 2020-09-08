# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 17:00:40 2020

This Script creates Gaussian Mixture Models (GMMs) of PV output for sampling

The script outputs 2 pickle files which contains dictionaries of the GMMs
'PVDistsGMMChosen.pickle' contains the means for each mixture
'PVDistsGMMChosen.pickle' contains the weights for each mixture

Created by Calum Edmunds

"""
import pandas as pd
import pickle
import numpy as np
import matplotlib.pyplot as plt

pd.options.mode.chained_assignment = None
from sklearn import mixture

# from PV_Load import SM_Visualisation

# --------------------- Do the Multivariate bit --------------------

Distkeys = [
    "WinterWknd",
    "WinterWkd",
    "SpringWknd",
    "SpringWkd",
    "SummerWknd",
    "SummerWkd",
    "AutumnWknd",
    "AutumnWkd",
]


def mixtures():
    pickin = open("../../Data/HP_DistsConsolidated_10min_pad.pickle", "rb")
    Load_Data = pickle.load(pickin)

    # GMModels={}
    GMChosen = {}
    GMWeights = {}
    AIC = {}  # The Akaike Information Criteria is to be minimised to reduce overfitting
    AICmean = {}
    nmix = {}
    GMModels = {}

    nm = 20  # number of mixtures

    AIC = np.empty([3, nm])
    AIC = np.full_like(AIC, np.nan)
    AICmean = pd.Series(index=range(2, nm))
    GMModels = {}
    Load_Data = Load_Data.replace(np.nan, 0)
    Load_Data = np.log(Load_Data + np.finfo(float).eps)
    # for i in range(2, nm):
    mix = mixture.GaussianMixture(
        n_components=nm, covariance_type="diag", reg_covar=0.1
    )
    for j in range(0, 3):
        GMModels[nm - 1] = mix.fit(Load_Data)
        AIC[j, nm - 1] = GMModels[nm - 1].aic(Load_Data)
    AICmean[nm - 1] = AIC[:, nm - 1].mean()
    # nmix = AICmean.idxmin()
    GMChosen = np.exp(GMModels[nm - 1].means_)
    GMChosen[GMChosen < 0.02] = 0
    GMWeights = GMModels[nm - 1].weights_

    pickle_out = open("../../Data/HP_DistsGMMChosen.pickle", "wb")  # means
    pickle.dump(GMChosen, pickle_out)
    pickle_out.close()

    pickle_out = open("../../Data/HP_DistsGMMWeights.pickle", "wb")  # weights
    pickle.dump(GMWeights, pickle_out)
    pickle_out.close()


##mixtures()
# ---------------------- Visualisation of the Mixture models----------------

tsamp=144
def mix_Visualisation():
    pickin = open("../../Data/HP_DistsGMMChosen.pickle", "rb")
    GMChosen = pickle.load(pickin)
    pickin = open("../../Data/HP_DistsGMMWeights.pickle", "rb")
    GMWeights = pickle.load(pickin)
    pickin = open("../../Data/HP_DistsConsolidated_10min_pad.pickle", "rb")
    HP_DistsConsolidated = pickle.load(pickin)

    Seasons = ["Winter", "Spring", "Summer", "Autumn"]
    times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    n = 1
    r = 0
    # By Season
    print(len(GMChosen))
    q = 0
    for i in GMChosen:
        plt.plot(i, linewidth=(GMWeights[q] ** 0.5 / GMWeights.max()))
        q = q + 1
    # plt.plot(
    #     HP_DistsConsolidated.mean(),
    #     color="black",
    #     linewidth=1,
    #     linestyle="--",
    #     label="Mean",
    # )
    # plt.plot(HP_DistsConsolidated.max(),color="green", linewidth=0.5, linestyle="--", label="Max")
    # plt.plot(
    #     HP_DistsConsolidated.quantile(0.95),
    #     color="blue",
    #     linewidth=1,
    #     linestyle="--",
    #     label="95th Percentile",
    # )
    plt.xlim([0, tsamp-1])
    plt.ylim([0, 1.5])
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.xticks(range(0,tsamp+24,int(tsamp/6)),times)
    plt.xlabel("Mean Daily Demand (kWh/day)", fontsize=9)
    plt.tight_layout()


mix_Visualisation()
