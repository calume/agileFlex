# -*- coding: utf-8 -*-
"""
Created on Thu Sep 24 14:16:25 2020

@author: CalumEdmunds
"""

from congestion_probability_batch import runbatch
from voltage_headroom import voltage_limits
from headroom_forecasting import headroom_percentiles
from zonal_summary import EVRealiser

from congestion_probability_validation import runvalid

networks=['network_1/']#,'network_5/','network_10/','network_17/','network_18/']
Cases=['00PV00HP']#,'00PV25HP','25PV50HP','25PV75HP','50PV100HP']

Voltage_data=runbatch(networks,Cases,'Post')
#voltage_limits(networks,Cases)
# nHPs_Final=headroom_percentiles(networks,Cases)
# EVRealiser(networks)
# runvalid(networks)