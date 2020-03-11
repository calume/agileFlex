# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 17:00:40 2020

This Script creates Gaussian Mixture Models for sampling

"""
import pandas as pd
import pickle
import numpy as np
import time
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
from datetime import datetime, timedelta, date, time
import datetime
import matplotlib.dates as mdates
from matplotlib.ticker import LinearLocator, FormatStrFormatter
from matplotlib import cm
import scipy as sp
from scipy import optimize
from numpy import exp
from scipy.stats import boxcox
from scipy.stats import gaussian_kde
from statsmodels.nonparametric.kde import KDEUnivariate
import cloudpickle
pd.options.mode.chained_assignment = None 
from sklearn import mixture

################# Do the Multivariate bit ######################
Distkeys=['WintDists', 'SpringDists','SummerDists','AutumnDists']
pickin= open("Pickle/PV_Normalised.pickle","rb")
PVW = pickle.load(pickin)
aa=PVW

#GMModels={}
GMChosen={}
GMWeights={}
BIC = {}
BICmean={}
nmix={}
GMModels={}
nm=40 #number of mixtures

for k in Distkeys:
    GMChosen[k]={}
    GMWeights[k]={}
    nmix[k]={}   
    BIC[k] = np.empty([3,nm])
    BIC[k] = np.full_like(BIC[k],np.nan)
    BICmean[k]=pd.Series(index=range(2,nm))
    GMModels[k]={}
    PVW[k]=PVW[k].astype(float)
    #PVW[k]=PVW[k][0:-sum(PVW[k][47].isna())]
    PVW[k]=PVW[k].replace(np.nan,0)
    PVW[k]=np.log(PVW[k]+np.finfo(float).eps)
    for i in range(2,nm):
       mix= mixture.GaussianMixture(n_components=i, covariance_type='diag', reg_covar=0.1)
       for j in range(0,3):
           GMModels[k][i]=mix.fit(PVW[k])
           BIC[k][j,i]= GMModels[k][i].bic(PVW[k])
       BICmean[k][i]=BIC[k][:,i].mean()
    nmix[k]=BICmean[k].idxmin()
    GMChosen[k]=np.exp(GMModels[k][nmix[k]].means_)
    GMChosen[k][GMChosen[k]<0.02]=0
    GMWeights[k]=GMModels[k][nmix[k]].weights_

#pickle_out = open("PVDistsGMMChosen.pickle","wb")
#pickle.dump(GMChosen, pickle_out)
#pickle_out.close()
#
#pickle_out = open("PVDistsGMMWeights.pickle","wb")
#pickle.dump(GMWeights, pickle_out)
#pickle_out.close()
#
#pickin= open("PVDistsGMMChosen.pickle","rb")
#GMChosen = pickle.load(pickin)
#
#pickin= open("PVDistsGMMWeights.pickle","rb")
#GMWeights = pickle.load(pickin)

plt.figure(1)
# By Season
n = 1
Seasons = ["Winter ", "Spring ", "Summer ", "Autumn "]
for item in GMChosen:
    print(len(GMChosen[item]))
    plt.subplot(220 + n)
    plt.title(Seasons[n - 1]+str(len(GMChosen[item]))+" mixtures", fontsize=9)
    q=0
    for i in GMChosen[item]:
        plt.plot(i, linewidth=(3*GMWeights[item][q]/GMWeights[item].max()))
        q=q+1
    plt.xlabel("Settlement Period (half hourly)", fontsize=8)
    plt.ylabel("Output(fraction of capacity)", fontsize=8)
    plt.ylim(top=1)
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    n = n + 1
    
#plt.figure(2)
## By Season
#n = 1
#Seasons = ["Winter", "Spring", "Summer", "Autumn"]
#for item in GMChosen:
#    plt.subplot(220 + n)
#    plt.title(Seasons[n - 1], fontsize=9)
#    q=0
#    for i in range(0,100):
#        plt.plot(np.exp(GMModels[item][nmix[item]].sample()[0]), linewidth=0.8)
#        q=q+1
#    plt.xlabel("Settlement Period (half hourly)", fontsize=8)
#    plt.ylabel("Output(fraction of capacity)", fontsize=8)
#    plt.xticks(fontsize=8)
#    plt.yticks(fontsize=8)
#    n = n + 1