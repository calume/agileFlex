# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 11:31:31 2020

@author: CalumEdmunds
"""
import pickle
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None
from matplotlib import pyplot as plt
from datetime import datetime, timedelta, date, time
import datetime

start_date = date(2014, 1, 4)
end_date = date(2014, 1, 5)

delta_halfhours = timedelta(hours=0.5)
dt = pd.date_range(start_date, end_date, freq=delta_halfhours)[:-1]

pick_in = open("../../Data/Winter14Inputs.pickle", "rb")
WinterInputs = pickle.load(pick_in)

pick_in = open("../../Data/Winter14HdRm.pickle", "rb")
Winter_HdRm = pickle.load(pick_in)

Summary_DF={}

for i in WinterInputs['HP'].columns:
    Summary_DF[i[1]+i[0]]=pd.DataFrame(index=dt, columns=['HP','SM','PV','Headroom','Footroom','Advance' ])
    for z in Summary_DF[i[1]+i[0]].columns[0:3]:
        Summary_DF[i[1]+i[0]][z]=WinterInputs[z][i][dt]
    Summary_DF[i[1]+i[0]]['Headroom']=Winter_HdRm[int(i[1])][int(i[0])][dt]
    Summary_DF[i[1]+i[0]]['Advance']=-WinterInputs['demand_delta'][i][dt]
    Summary_DF[i[1]+i[0]]['Footroom']=90-Summary_DF[i[1]+i[0]]['Headroom']
    
    Summary_DF[i[1]+i[0]].to_csv(str(i[1]+i[0])+'.csv')