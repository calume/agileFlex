# Data Input Descriptors

This folder contains Scripts to process data inputs to the AGILE model
Data inputs include the following
- PV: London Datastore for 6 PV sites over ~400 days
- Smart Meter: London Datastore for ~50 customers over X days
- Heat Pump: London Datastore 
- Electric Vehicle: Electric nation

## PV 

The script 'PVLoad.py' is used to process PV data for the AGILE Model. The raw data can be found in 'HourlyPV.csv'.
The London DataStore PV data is used from: https://data.london.gov.uk/dataset/photovoltaic--pv--solar-panel-energy-generation-data
Hourly Data is used and interpolated to half hourly. (Only 4 months of data was available for 10-minutely and 1-minutely)

Data is available for the Following sites and Data ranges:

Site | Apparent capacity (kW) | Date Range
-----|------------------------|-----------
Forest Road | 3.00 | 2013-10-01 to 2014-10-03 (366 Days)                 
Suffolk Road | 0.50 | 2013-08-28 to 2014-11-09 (448 Days)
Bancroft Close | 3.50 | 2013-10-04 to 2014-11-17 (408 Days)
Alverston Close | 3.00 | 2013-11-06 to 2014-11-14 (372 Days)
Maple Drive East | 4.00 | 2013-08-21 to 2014-11-13 (448 Days)
YMCA | 0.45 | 2013-09-25 to 2014-11-19 (420 Days)

The script 'PVLoad.py' creates 2 pickle files with the data processed:
    
- 'PV_BySiteName.pickle' - Which contains output (kW and Normalised by capacity) datestamped with a dataframe for each site
- 'PV_Normalised.pickle' - Which has normalised output by season in rows of 48 half hours combined for all sites with timestamps removed.

The script 'PVLoad.py' also plots the data both by site and by season. Some of the displays are shown below.

### PV Data Visualisation

#### Timeseries by Site

![PVBySite](Visualisation_JPGs/PV_BySite.jpeg)

#### Daily profile by Season (all sites)

![PVSeason](Visualisation_JPGs/PV_Seasonal.jpeg)

#### Gaussian Mixture Models

Using the daily seasonal profiles above, Gaussian Mixture models can be fitted to the data to allow multivariate sampling.

The number of mixtures has been chosed by minimising the Aikaike Information Criterion, which leads to a large number of mixtures up to the limit of 60 chosen.

The means of the seasonal Gaussian mixture models can be seen below. The line weightings represent the weightings applied to each mixture (i.e. the probability that would be used for choosing one of the mixtures for sampling)

![PVSeason](Visualisation_JPGs/PV_MixtureModels.jpeg)

#Smart Meter

The London DataStore (or Low Carbon London (LCL) Smart Meter data is used from: https://data.london.gov.uk/dataset/smartmeter-energy-use-data-in-london-households
There is a data for 5,500 customers, A random 187 customers are chosen for sampling to keep data manageable size.
From Files:
-'Power-Networks-LCL-June2015(withAcornGps)v2_1.csv'
-'Power-Networks-LCL-June2015(withAcornGps)v2_2.csv'
-'Power-Networks-LCL-June2015(withAcornGps)v2_10.csv'
-'Power-Networks-LCL-June2015(withAcornGps)v2_11.csv'
-'Power-Networks-LCL-June2015(withAcornGps)v2_100.csv'
-'Power-Networks-LCL-June2015(withAcornGps)v2_101.csv'

Some example analysis of the data is found https://data.london.gov.uk/blog/electricity-consumption-in-a-sample-of-london-households/
Data is available for the Following 187 Households, by Acorn Group:

Acorn Group|Number of customers| Avg Days of Data (per customer)| Peak Demand (kW)| Average Daily Demand (kWh/day) | Average demand (kW)
-----------|-------------------|--------------------------------|------------------|-------------------------------|--------------------
Adversity | 55 | 662 | 7.75 | 15.99 | 0.33
Comfortable | 46 | 655 | 9.24 | 19.24 | 0.40
Affluent | 86 | 676 | 11.17 | 25.59 | 0.53

The script creates 3 pickle files with the data processed:
    
- "SM_DataFrame.pickle" - Smart meter raw data for 187 Smart meters (subset of the 5,500 LCL customers).Timestamped

- "SM_Summary.pickle" - Summary of Acorn Group, Date Ranges and Means/Peaks for each household

- "SM_Normalised.pickle" - Customers are combined into Seasonal (and weekday/weekend) daily profiles by ACorn Group

### SM Data Visualisation

#### Seasonal Mean Demand by Acorn Group

The daily mean demand (kW) profiles for the subset of 187 househoulds, categorised by Season, weekend/Weekday and AcornGroup is shown below:

![PVSeason](Visualisation_JPGs/SM_Consolidated.png)