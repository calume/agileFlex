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
    pickin = open("../../Data/HP_DistsConsolidated.pickle", "rb")
    Load_Data = pickle.load(pickin)

    # GMModels={}
    GMChosen = {}
    GMWeights = {}
    AIC = {}  # The Akaike Information Criteria is to be minimised to reduce overfitting
    AICmean = {}
    nmix = {}
    GMModels = {}

    nm = 80  # number of mixtures

    for k in Distkeys:
        AIC[k] = np.empty([3, nm])
        AIC[k] = np.full_like(AIC[k], np.nan)
        AICmean[k] = pd.Series(index=range(2, nm))
        GMModels[k] = {}
        Load_Data[k] = Load_Data[k].replace(np.nan, 0)
        Load_Data[k] = np.log(Load_Data[k] + np.finfo(float).eps)
        # for i in range(2, nm):
        mix = mixture.GaussianMixture(
            n_components=nm, covariance_type="diag", reg_covar=0.1
        )
        for j in range(0, 3):
            GMModels[k][nm - 1] = mix.fit(Load_Data[k])
            AIC[k][j, nm - 1] = GMModels[k][nm - 1].aic(Load_Data[k])
        AICmean[k][nm - 1] = AIC[k][:, nm - 1].mean()
        # nmix[k] = AICmean[k].idxmin()
        GMChosen[k] = np.exp(GMModels[k][nm - 1].means_)
        GMChosen[k][GMChosen[k] < 0.02] = 0
        GMWeights[k] = GMModels[k][nm - 1].weights_

    pickle_out = open("../../Data/HP_DistsGMMChosen.pickle", "wb")  # means
    pickle.dump(GMChosen, pickle_out)
    pickle_out.close()

    pickle_out = open("../../Data/HP_DistsGMMWeights.pickle", "wb")  # weights
    pickle.dump(GMWeights, pickle_out)
    pickle_out.close()


# mixtures()
# ---------------------- Visualisation of the Mixture models----------------


def mix_Visualisation():
    pickin = open("../../Data/HP_DistsGMMChosen.pickle", "rb")
    GMChosen = pickle.load(pickin)
    pickin = open("../../Data/HP_DistsGMMWeights.pickle", "rb")
    GMWeights = pickle.load(pickin)
    pickin = open("../../Data/HP_DistsConsolidated.pickle", "rb")
    HP_DistsConsolidated = pickle.load(pickin)

    Seasons = ["Winter", "Spring", "Summer", "Autumn"]
    times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    n = 1
    r = 0
    # By Season
    for item in GMChosen:

        print(len(GMChosen[item]))
        plt.subplot(420 + n)
        q = 0
        for i in GMChosen[item]:
            plt.plot(i, linewidth=(GMWeights[item][q] ** 0.5 / GMWeights[item].max()))
            q = q + 1
        plt.plot(
            HP_DistsConsolidated[item].mean(),
            color="black",
            linewidth=1,
            linestyle="--",
            label="Mean",
        )
        # plt.plot(HP_DistsConsolidated[item].max(),color="green", linewidth=0.5, linestyle="--", label="Max")
        plt.plot(
            HP_DistsConsolidated[item].quantile(0.95),
            color="blue",
            linewidth=1,
            linestyle="--",
            label="95th Percentile",
        )
        plt.xlim([0, 47])
        plt.ylim([0, 5])
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(range(0, 47, 8), times)
        if n == 1:
            plt.legend(fontsize=7)
            plt.title("Weekend (Sat-Sun)", fontsize=9, fontweight="bold")
        if n == 2:
            plt.title("Week Day (Mon-Fri)", fontsize=9, fontweight="bold")
        if n % 2 == 1:
            plt.ylabel(Seasons[r], rotation=15, fontsize=9, fontweight="bold")
            r = r + 1
        n = n + 1
        plt.tight_layout()


mix_Visualisation()
