#Author Calum Edmunds
#To run time series

import pandas as pd
import numpy as np
from datetime import datetime
#from runfile import main

windcurt = pd.read_csv('ScotWindVolumeJune18toEndMay19.csv')
windcurt=windcurt.fillna(0)

National = pd.read_csv('National_Actual.csv')
NatCarb=pd.DataFrame(index=range(0,17600), columns=['1'])

##### Get national carbon intensity June 18 to end of June 19####
NatCarb = National.iloc[0][1:].T.astype(float)

for index, row in National.iterrows():
   if 365 > index > 0:
      NatCarb = NatCarb.append(National.iloc[index][1:].T, ignore_index=True)

NatCarb=NatCarb[24:-24]
windTot=windcurt[24:-24]
NatCarb=NatCarb.reset_index(drop=True)
windTot=windTot.reset_index(drop=True)

##### Get Whitelees Curtailment, June 18 to end of June 19 ####

whiltot = (windTot['T_WHILW-1']+windTot['T_WHILW-2'])*-2   #### Converting from negative MWh into positive MW
    
NatCarb = np.interp(np.linspace(0,17472,52414),range(0,17472),NatCarb.values.astype(float))
whiltot = np.interp(np.linspace(0,17472,52414),range(0,17472),whiltot.values.astype(float))

testdirect = "testcases/timeseries"

from shutil import copyfile
from openpyxl import load_workbook

start=datetime.now()
pd.options.mode.chained_assignment = None



#samp=random.sample(range(365),100)
#samp=[213,13,285,87,164,257,31,327,176,243,146,281,20,123,130,47,328,302,28,154,57,93,128,114,78,147,193,293,96,346,237,231,0,52,207,113,259,112,134,108,184,171,218,188,253,236,2,58,312,190,204,72,162,301,229,288,11,133,339,12,279,239,217,313,140,357,82,127,120,135,250,41,79,139,32,264,286,209,45,333,183,309,351,22,238,161,321,67,340,226,337,115,156,167,308,187,263,83,132,119]
#samp=[26,27,30,31,45,47,48,51,70,71,74,76,77,78,79,80,81,82,85,86,87,89,90,91,92,93,94,95,97,98,99,100,101,102,103,113,124,125,158,159,164,180,194,195,209,210,221,222,229,230,231,244,250,253,254,255,256,257,262,263,264,265,266,275,277,285,286,287,288,295,296,297,299,329,332,335,336,337,350]
samp = [55,  56,  57,  58,  59,  60,  61,  75,  76,  77,  78,  81,  83,
        86, 100, 101, 103, 104, 106, 107, 108, 109, 110, 111, 112, 114,
       115, 116, 117, 119, 120, 121, 122, 123, 124, 125, 127, 128, 129,
       130, 131, 132, 133, 136, 137, 143, 144, 145, 154, 155, 165, 172,
       180, 184, 188, 189, 194, 196, 199, 210, 213, 224, 225, 227, 228,
       238, 239, 240, 246, 247, 251, 252, 253, 257, 259, 260, 261, 263,
       264, 265, 267, 274, 277, 279, 280, 282, 283, 284, 285, 286, 287,
       288, 292, 293, 294, 295, 296, 305, 307, 315, 316, 317, 318, 319,
       325, 326, 327, 328, 329, 358, 359, 362]
fact=[1,5,10,25,50,75,100]
tmin=0
tmax=len(samp)

WindCurtRed = pd.DataFrame(columns=range(tmin,tmax),index=fact)
CarbIntpkWh = pd.DataFrame(columns=range(tmin,tmax),index=fact)
windgen = pd.DataFrame(columns=fact,index=(range(0,144)))
gridgen = pd.DataFrame(columns=fact,index=(range(0,144)))
EVChargekW = pd.DataFrame(columns=fact, index=(range(0,144)))


for i in range(tmin,tmax):
    for k in range(0,len(fact)):
       print(fact[k])
       print(i)
       copyfile('testcases/BaseEVDay_WG.xlsx', str(testdirect)+'/EVDay'+str(i)+str(fact[k])+'.xlsx')
       
       ##### Read in the Carbon Intensity Data to the OATS sheet ######
       timeseriesGen = pd.read_excel(str(testdirect)+'/EVDay'+str(i)+str(fact[k])+'.xlsx', sheet_name="timeseriesGen")
       genseries = pd.read_excel(str(testdirect)+'/EVDay'+str(i)+str(fact[k])+'.xlsx', sheet_name="genseries")
       
       gridrows = timeseriesGen[timeseriesGen['name']=='GridConnection_58'].index
       timeseriesGen['cost(pounds/kwh)'][gridrows] = NatCarb[samp[i]*144:(samp[i]+1)*144]
   
       #### Input Curtailment as wind generation available ####
       genseries['Wind'] = whiltot[samp[i]*144:(samp[i]+1)*144]*1000 #converted from MW to kW
       genseries['Wind'] = round(genseries['Wind'].fillna(0),1)
       ##### Load EV and Load Profiles  #######
       
       EVsTravelDiary = pd.read_csv(str(testdirect)+'/Routine_10000EVTD.csv')
       EVs = pd.read_csv(str(testdirect)+'/Routine_10000EV.csv')
       ### For scaling up number of EVs
       #EVs['busname']=1
       EVs['capacity(kW)']=EVs['capacity(kW)']*fact[k]
       EVs['battery(kWh)']=EVs['battery(kWh)']*fact[k]
       EVs['chargingrate(MW/hr)']=EVs['chargingrate(MW/hr)']*fact[k]
       
       EVsTravelDiary['EStart']=EVsTravelDiary['EStart']*fact[k]
       EVsTravelDiary['EEnd']=EVsTravelDiary['EEnd']*fact[k]
       ####  Write to copied sheet
       
       book = load_workbook(str(testdirect)+'/EVDay'+str(i)+str(fact[k])+'.xlsx')
       
       writer = pd.ExcelWriter(str(testdirect)+'/EVDay'+str(i)+str(fact[k])+'.xlsx', engine='openpyxl')
       writer.book = book
       writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
   
       EVsTravelDiary.to_excel(writer, "EVsTravelDiary", columns=None, header=True, index=False, startrow=0)
       #timeseries.to_excel(writer, "timeseries", columns=None, header=True, index=False, startrow=0)
       timeseriesGen.to_excel(writer, "timeseriesGen", columns=None, header=True, index=False, startrow=0)
       genseries.to_excel(writer, "genseries", columns=None, header=True, index=False, startrow=0)
       EVs.to_excel(writer, "EVs", columns=None, header=True, index=False, startrow=0)
   
       writer.save()
       #Write to D    
   
       #Run optimisation for batch
       try:
          main('timeseries/EVDay'+str(i)+str(fact[k])+'.xlsx')
              #Write Transmission results
          summarydata = pd.read_csv('results/summary.csv')
          generatordata = pd.read_csv('results/generator.csv')
          copyfile('results/generator.csv', 'results/generator'+str(i)+str(fact[k])+'.csv')
          copyfile('results/summary.csv', 'results/summary'+str(i)+str(fact[k])+'.csv')
          
          EVChargekW[fact[k]] = summarydata['Conventional generation (kW)'].round(4)  - summarydata['Demand (kW)'].round(4)
          
          windgen[fact[k]] = generatordata[generatordata['busname']=='Wind']['pG(kW)'].reset_index(drop=True)
          gridgen[fact[k]] = generatordata[generatordata['busname']=='GridConnection_58']['pG(kW)'].reset_index(drop=True)
          
          WindCurtRed[i].iloc[k] = sum(windgen[fact[k]])
          
          CarbIntpkWh[i].iloc[k] = sum((gridgen) * 
                     timeseriesGen[timeseriesGen['name']=='GridConnection_58']['cost(pounds/kwh)']) / sum(EVChargekW[fact[k]])
      
       except:
          print('Fail on'+str(fact[k]))    
    gridgen.to_csv('results/gridgen'+str(i)+'.csv', header=True, index=True)
    windgen.to_csv('results/windgen'+str(i)+'.csv', header=True, index=True)
    EVChargekW.to_csv('results/EVChargekWh'+str(i)+'.csv', header=True, index=True)

CarbIntpkWh.to_csv('results/CarbIntpkWh.csv', header=True, index=True)
WindCurtRed.to_csv('results/WindCurtRed.csv', header=True, index=True)
   
end=datetime.now()
print(end-start)