# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 14:59:41 2019

@author: qsb15202
"""
#samp=[26,27,30,31,45,47,48,51,70,71,74,76,77,78,79,80,81,82,85,86,87,89,90,91,92,93,94,95,97,98,99,100,101,102,103,113,124,125,158,159,164,180,194,195,209,210,221,222,229,230,231,244,250,253,254,255,256,257,262,263,264,265,266,275,277,285,286,287,288,295,296,297,299,329,332,335,336,337,350]

import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

testdirect = "testcases/timeseries/Idealised"
#
#fact=[1,5,10,20,30,40,50]
fact=[10,50,100,250,500,750,1000]


#########This commented stuff was used to generate TotWindCurt.csv and TotWindRedFrac.csv #############

#tmin=0
#tmax=112
##at
#TotWindCurt = pd.DataFrame(columns=range(tmin,tmax),index=[0])
#TotWindRedFrac = pd.DataFrame(columns=range(tmin,tmax),index=fact)
#TotWindGen= pd.DataFrame(columns=range(tmin,tmax),index=[0])
#
#for i in range(tmin,tmax):
#   genseries = pd.read_excel(str(testdirect)+'/EVDay'+str(i)+'10.xlsx', sheet_name="genseries")
#   TotWindCurt[i] = sum(genseries['Wind'][0:143])
#   windgen = pd.read_csv('results/Idealised/windgen'+str(i)+'.csv',usecols=([1,2,3,4,5,6,7]))
#   TotWindRedFrac[i][fact]=windgen.iloc[0:143].sum()/TotWindCurt[i].values
#
#TotWindCurt.to_csv('results/IdealisedTotWindCurt.csv', header=True, index=True)
#TotWindRedFrac.to_csv('results/IdealisedTotWindRedFrac.csv', header=True, index=True)
#
##### Ignore commented stuff above unless you do additional runs #######################

TotWindCurt=pd.read_csv('results/RoutineTotWindCurt.csv', index_col=0)
TotWindRedFrac=pd.read_csv('results/RoutineTotWindRedFrac.csv', index_col=0)

TotWindCurtI=pd.read_csv('results/IdealisedTotWindCurt.csv', index_col=0)
TotWindRedFracI=pd.read_csv('results/IdealisedTotWindRedFrac.csv', index_col=0)


totred=pd.Series(index=fact)
totredI=pd.Series(index=fact)

for i in range(0,len(fact)):
   tot=TotWindCurt*TotWindRedFrac.iloc[i]
   totI=TotWindCurtI*TotWindRedFracI.iloc[i]
   totred[fact[i]]=tot.sum(axis=1)/TotWindCurt.sum(axis=1)*100
   totredI[fact[i]]=totI.sum(axis=1)/TotWindCurtI.sum(axis=1)*100
   
plt.plot(totred, label="routine")
plt.plot(totredI, label="idealised")
plt.xlabel("1,000 cars")
plt.ylabel("% reduction in curtailment")
plt.legend()
axes = plt.gca()
axes.set_ylim(0,100)

### Focus on days with no Soakage  ####
#
#EVcharge=pd.read_csv('results/EVChargekWh6.csv', index_col=0)
#gen6 = pd.read_excel(str(testdirect)+'/EVDay61.xlsx', sheet_name="genseries")
#gen5 = pd.read_excel(str(testdirect)+'/EVDay51.xlsx', sheet_name="genseries")
#plt.figure(2)
#plt.plot(gen5['Wind'])
#plt.plot(gen6['Wind'])