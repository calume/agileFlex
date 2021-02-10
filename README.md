# Agile Flex

## Prerequisites

- [Python 3.7]
- See the requirements.txt file

## Overall Project Description

We start with some data of PV, Heat Pump and Smartmeter Data (See Data folder). Then we do load flows using OpenDSS.
Then we estimate the headroom and Optimise EVs around the remaining headroom. Finally we validate the results with more load flows and recalculate the headroom.

Megaloader is the top level script loading in functions from other scripts. The overall running order is as follows:
    
1. Create customer data (based on Cases) for all Networks 
---- raw_input_data() function within congestion_probability_batch.py
    
2. Power flow then is run using PV, Smartmeter (SM) and heat pump (HP) data for all cases 
---- do_loadflows(sims) function within congestion_probability_batch.py

3. The zonal minimum voltage and zonal supply cable power flow is determined 
---- calc_current_voltage function (in crunch_results_batch.py) within congestion_probability_batch.py
    
4. Using the resulting zonal power flows and minimum voltages, Power flow limits are estimated per zone
---- voltage_limits(networks,Cases,paths) function

5. Headroom and footroom are calculated for each timestep
----  Headroom_calc function (in crunch_results_batch.py) called from post_process() within congestion_probability_batch.py

6. Daily profiles of headroom and footroom are calculated, number of EVs and HPs are also calculated and saved in pickle files
---- headroom_percentiles function within headroom_forecasting.py runs
    ---- percentiles() creates daily profiles
    ---- HP_vs_Headroom() calculates headroom
    ---- EV numbers are estimated per zone based on daily headroom
    ---- HP cases are assigned (based on headroom) and new customer summaries created
    
7. Calculate number of optimised EVs (10 successful attempts).
---- EVRealiser function within zonal_summary.py

8. Do EV optimisation for successful EV number. Then validate using congestion_probability_validation.py
--Load flow is run and headroom is re-calculated for comparison
----- EVRealiser function within zonal_summary.py (with flag to say its not 10 attempts, but 2 instead)
----- runvalid within congestion_probability_validation.py 
-----------runvalid calls save_outputs, post_process from congestion_probability_batch.py


============== Required Data Folder Structure ==================

Data/network_X/       ------------ Stores calculated Zonal Vmin, Pflow and C Violations
Data/Raw              -------------Stores the raw data (input dataframes of demand and output results of current, Voltage Arrays)
Data/Upper/           -------------Stores the calculated nEVs and HPs (assigned cases)
-----Upper/network_X/ -------------Stores calculated headrooms, both as timeseries and daily profiles. Also stores All_VC_limits.pickle which is the Power flow limit for minimum voltage
Data/Validation       -------------Stores validation results arrays
Data/Validation/network_X/ --------Stores new headrooms for validation results 