# -*- coding: utf-8 -*-
"""
Created on Fri Jul 31 12:37:10 2020

@author: CalumEdmunds
"""
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None
from datetime import timedelta, date, datetime
import pickle
import matplotlib.pyplot as plt



start_date = date(2013, 12, 1)
end_date = date(2013, 12, 2)
sims_halfhours = pd.date_range(start_date, end_date, freq=timedelta(hours=0.5))
sims_tenminutes = pd.date_range(start_date, end_date, freq=timedelta(minutes=10))
sims_twominutes = pd.date_range(start_date, end_date, freq=timedelta(minutes=2))

pick_in = open("../Data/HP_DataFrame_2mins_week.pickle", "rb")
HP_DataFrame = pickle.load(pick_in)
HP_DataFrame_two = HP_DataFrame.loc[sims_twominutes]
HP_reduced = HP_DataFrame_two.reindex(sims_twominutes.tolist()).count()> (0.9*len(sims_twominutes))
HP_reduced=HP_reduced[HP_reduced].index
HP_DataFrame_two=HP_DataFrame_two[HP_reduced]

HP_DataFrame_ten = HP_DataFrame_two.resample('10T').max()

#pick_in = open("../Data/HP_DataFrame_10mins_week.pickle", "rb")
#HP_DataFrame = pickle.load(pick_in)
#HP_DataFrame_ten = HP_DataFrame.loc[sims_tenminutes]
#HP_reduced = HP_DataFrame_ten.reindex(sims_tenminutes.tolist()).count()> (0.9*len(sims_tenminutes))
#HP_reduced=HP_reduced[HP_reduced].index
#HP_DataFrame_ten=HP_DataFrame_ten[HP_reduced]

pick_in = open("../Data/HP_DataFrame_hh_mean.pickle", "rb")
HP_DataFrame = pickle.load(pick_in)
HP_DataFrame_hh = HP_DataFrame.loc[sims_halfhours]
HP_reduced = HP_DataFrame_hh.reindex(sims_halfhours.tolist()).count()> (0.9*len(sims_halfhours))
HP_reduced=HP_reduced[HP_reduced].index
HP_DataFrame_hh=HP_DataFrame_hh[HP_reduced]

for i in HP_DataFrame_ten.columns[16:17]:
    plt.figure()
    plt.plot(HP_DataFrame_two[i], linestyle=":", color='black', label='Two Minutes')
    plt.plot(HP_DataFrame_ten[i], linestyle="--", color='blue', label='Ten Minutes')
    plt.plot(HP_DataFrame_hh[i], linestyle="-", color='green', label='Half Hours')
    plt.legend()
    plt.ylabel('Heat Pump Demand (kW)')