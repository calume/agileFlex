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
from PV_Load import PV_Visualisation

# --------------------- Do the Multivariate bit --------------------


def mixtures():
    Distkeys = ["WintDists", "SpringDists", "SummerDists", "AutumnDists"]
    pickin = open("Pickle/PV_Normalised.pickle", "rb")
    PVW = pickle.load(pickin)

    # GMModels={}
    GMChosen = {}
    GMWeights = {}
    AIC = (
        {}
    )  # The Akaike Information Criteria is to be minimised to prevent overfitting
    AICmean = {}
    nmix = {}
    GMModels = {}
    nm = 60  # number of mixtures

    for k in Distkeys:
        GMChosen[k] = {}
        GMWeights[k] = {}
        nmix[k] = {}
        AIC[k] = np.empty([3, nm])
        AIC[k] = np.full_like(AIC[k], np.nan)
        AICmean[k] = pd.Series(index=range(2, nm))
        GMModels[k] = {}
        PVW[k] = PVW[k].replace(np.nan, 0)
        PVW[k] = np.log(PVW[k] + np.finfo(float).eps)
        for i in range(2, nm):
            mix = mixture.GaussianMixture(
                n_components=i, covariance_type="diag", reg_covar=0.1
            )
            for j in range(0, 3):
                GMModels[k][i] = mix.fit(PVW[k])
                AIC[k][j, i] = GMModels[k][i].aic(PVW[k])
            AICmean[k][i] = AIC[k][:, i].mean()
        nmix[k] = AICmean[k].idxmin()
        GMChosen[k] = np.exp(GMModels[k][nmix[k]].means_)
        GMChosen[k][GMChosen[k] < 0.02] = 0
        GMWeights[k] = GMModels[k][nmix[k]].weights_

    pickle_out = open("Pickle/PVDistsGMMChosen.pickle", "wb")  # means
    pickle.dump(GMChosen, pickle_out)
    pickle_out.close()

    pickle_out = open("Pickle/PVDistsGMMWeights.pickle", "wb")  # weights
    pickle.dump(GMWeights, pickle_out)
    pickle_out.close()


# ---------------------- Visualisation of the Mixture models----------------
#'qrts' is loaded from 'PV_Load.py' which contains the mean and maximum of input distributions
# These are to be overlaid on the mixture model plots to show how good an approximation


def mix_Visualisation():
    qrts = PV_Visualisation()  # This will also print the outputs from PV_Load
    pickin = open("Pickle/PVDistsGMMChosen.pickle", "rb")
    GMChosen = pickle.load(pickin)

    pickin = open("Pickle/PVDistsGMMWeights.pickle", "rb")
    GMWeights = pickle.load(pickin)

    plt.figure(3)
    # By Season
    n = 1
    Seasons = ["Winter ", "Spring ", "Summer ", "Autumn "]
    for item in GMChosen:
        print(len(GMChosen[item]))
        plt.subplot(220 + n)
        plt.title(Seasons[n - 1] + str(len(GMChosen[item])) + " mixtures", fontsize=9)
        q = 0
        for i in GMChosen[item]:
            plt.plot(
                i, linewidth=(1.5 * GMWeights[item][q] ** 0.5 / GMWeights[item].max())
            )
            q = q + 1
        plt.xlabel("Settlement Period (half hourly)", fontsize=8)
        plt.ylabel("Output(fraction of capacity)", fontsize=8)
        plt.ylim(top=1)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        n = n + 1

    ########## To overlay the raw data mean and max over the mixtures
    i = 1
    for item in qrts:
        n = 0
        plt.subplot(220 + i)
        plt.plot(
            qrts[item]["mean"],
            color="black",
            linewidth=0.8,
            label="mean",
            linestyle="--",
        )
        plt.plot(
            qrts[item]["max"], color="green", linewidth=0.5, label="max", linestyle="--"
        )
        n = n + 1
        plt.legend(fontsize=8)
        i = i + 1
    plt.tight_layout()


mix_Visualisation()
