#==================================================================
# runfile.py
# This is a top level script.
# EV charging scheduling problem
# ---Author---
# W. Bukhsh,
# wbukhsh@gmail.com
# OATS
# Copyright (c) 2019 by W. Bukhsh, Glasgow, Scotland
# OATS is distributed under the GNU GENERAL PUBLIC LICENSE v3. (see LICENSE file for details).
#==================================================================

from runcase import runcase
import logging
import pandas as pd
from matplotlib import pyplot as plt
from datetime import datetime

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='oatslog.log',
                    filemode='w')
logging.info("EV Scheduling log file")

#----------------------------------------------------------------------
def main(network):
    logging.info("Program started")
    #options
    opt=({'neos':False,\
    'solver':'cplex','charging_efficiency':0.88,'discharging_efficiency':0.88})
    # =====Test cases=====
    #give a path to the testcase file under the 'testcase' folder
    #testcase = 'SP53224_1bus.xlsx'
    #testcase = 'BaseEVDay_WG.xlsx'
    testcase = '/timeseries/EVDay01_mix'+network+'.xlsx'
    # testcase = 'case24_ieee_rts.xlsx'
    #testcase = 'case2.xlsx'
    # =====Model=====
    #specify a model to solve
    model ='EVScheduleV2G'
    # ==log==
    logging.info("Solver selected: "+opt['solver'])
    logging.info("Testcase selected: "+testcase)
    logging.info("Model selected: "+model)
    status=runcase(testcase,model,network,opt)
    logging.info("Done!")
    return status
#main('k_5')
# start=datetime.now()
# #main()
# end=datetime.now()
#print(end-start)

# gen=pd.read_excel('testcases/timeseries/EVDay01_mix.xlsx', sheet_name='genseries')
# genmin=pd.read_excel('testcases/timeseries/EVDay01_mix.xlsx', sheet_name='genmin')
# prices=pd.read_excel('testcases/timeseries/EVDay01_mix.xlsx', sheet_name='timeseriesGen')
# results=pd.read_excel('results/results.xlsx', sheet_name='EVs')
# costs=pd.read_excel('results/results.xlsx', sheet_name='summary')
# def plotDay(prices, gen, genmin):
#     ########-----------Plot Results----------#############
#     prices.index=prices['timeperiod']
#     prices=prices['cost(pounds/kwh)']
#     gen=gen['Grid'].rename('PG_Max')
#     genmin=genmin['Grid'].rename('PG_Min')
    
#     summary=pd.DataFrame(results.groupby(['Time period']).sum()['Charging(kW)'])
#     discharge=pd.DataFrame(results.groupby(['Time period']).sum()['Discharging(kW)'])
#     summary=summary.join(prices,how='outer')
#     summary=summary.join(gen,how='outer')
#     summary=summary.join(genmin,how='outer')
#     summary=summary.join(discharge,how='outer')
    
#     times = ['12:00','16:00','20:00','24:00','04:00','08:00','00:00']
#     fig, ax1 = plt.subplots()
    
#     color = 'tab:red'
#     ax1.set_xlabel('time')
#     ax1.set_ylabel('Charge (kWh)', color=color)
#     lns1=ax1.plot(summary.index, summary['Charging(kW)'], color=color, label="EV Charge")
#     lns5=ax1.plot(summary.index, summary['Charging(kW)']-summary['Discharging(kW)'], color='orange', label="Net EV Charge")
#     lns6=ax1.plot(summary.index, -summary['Discharging(kW)'], color=color, label="EV Discharge")
#     ax1.tick_params(axis='y', labelcolor=color)
    
#     lns2=ax1.plot(summary.index, summary['PG_Min'], color='black', linestyle=":", label="DSO Advance")
#     lns3=ax1.plot(summary.index, summary['PG_Max'], color='green', linestyle="--", label="Headroom")
    
#     ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    
#     color = 'tab:blue'
#     ax2.set_ylabel('Price (£/kWh)', color=color)  # we already handled the x-label with ax1
#     lns4=ax2.plot(summary.index, summary['cost(pounds/kwh)'], color=color, label="Grid+DSO Price")
#     ax2.tick_params(axis='y', labelcolor=color)
    
#     lns = lns1+lns2+lns3+lns4+lns5+lns6
#     labs = [l.get_label() for l in lns]
#     ax2.legend(lns, labs, loc=0)
    
#     fig.tight_layout()  # otherwise the right y-label is slightly clipped
#     #plt.xticks(range(0,144,24),times)
#     plt.show()

# plotDay(prices, gen, genmin)

# objective_total=(costs['Objective function value']).sum()
# print('Total is -£'+str(objective_total))
