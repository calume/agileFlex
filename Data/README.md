# Data Input Descriptors

This folder contains Scripts to process data inputs to the AGILE model
Data inputs include the following
- PV: London Datastore for 6 PV sites over ~400 days
- Smart Meter: London Datastore for 187 customers over ~650 days
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

![PVBySite](Visualisation/PV_BySite.jpeg)

#### Daily profile by Season (all sites)

![PVSeason](Visualisation/PV_Seasonal.jpeg)

#### Gaussian Mixture Models

Using the daily seasonal profiles above, Gaussian Mixture models can be fitted to the data to allow multivariate sampling.

The number of mixtures has been chosed by minimising the Aikaike Information Criterion, which leads to a large number of mixtures up to the limit of 60 chosen.

The means of the seasonal Gaussian mixture models can be seen below. The line weightings represent the weightings applied to each mixture (i.e. the probability of each mixture being chosen for sampling)

![PVSeason](Visualisation/PV_MixtureModels.jpeg)

## Smart Meter

The London DataStore (or Low Carbon London (LCL)) Smart Meter data is used from: https://data.london.gov.uk/dataset/smartmeter-energy-use-data-in-london-households .

There is a data for 5,500 customers, a random 185 customers are chosen for sampling to keep data manageable size.
From Files:
- 'Power-Networks-LCL-June2015(withAcornGps)v2_1.csv'
- 'Power-Networks-LCL-June2015(withAcornGps)v2_2.csv'
- 'Power-Networks-LCL-June2015(withAcornGps)v2_10.csv'
- 'Power-Networks-LCL-June2015(withAcornGps)v2_11.csv'
- 'Power-Networks-LCL-June2015(withAcornGps)v2_100.csv'
- 'Power-Networks-LCL-June2015(withAcornGps)v2_101.csv'

Some example analysis of the data is found https://data.london.gov.uk/blog/electricity-consumption-in-a-sample-of-london-households/ .
The data for the 185 Households used in Agile is summarised below, by Acorn Group:

Acorn Group|Number of customers| Avg Days of Data (per customer)| Peak Demand (kW)| Average Daily Demand (kWh/day) | Average demand (kW)
-----------|-------------------|--------------------------------|------------------|-------------------------------|--------------------
Adversity | 57 | 662 | 7.75 | 15.99 | 0.33
Comfortable | 46 | 655 | 9.24 | 19.24 | 0.40
Affluent | 86 | 676 | 11.17 | 25.59 | 0.53

The script creates 3 pickle files with the data processed:
    
- "SM_DataFrame.pickle" - Smart meter raw data for 185 Smart meters (subset of the 5,500 LCL customers).Timestamped

- "SM_Summary.pickle" - Summary of Acorn Group, Date Ranges and Means/Peaks for each household

- "SM_Normalised.pickle" - Customers are combined into Seasonal (and weekday/weekend) daily profiles by ACorn Group

### SM Data Visualisation

#### Seasonal Mean Demand by Acorn Group

The daily mean demand (kW) profiles for the subset of 185 househoulds, categorised by Season, weekend/weekday and Acorn Group (Adversity, Comfortable, Affluent) is shown below:

![PVSeason](Visualisation/SM_Consolidated.png)

#### Customers with storage heating
From Inspection there are unexpected peaks in the winter demand from midnight till around 4am. This suggests controlled storage heating and/or water heating.
As Heat pump demand is to be added to customers base load, it is important to separate customers with electric heating, so that
heat demand is not added twice to any customers.

Some of the Customers with the highest overnight and 4pm demand are shown below. These are all Affluent type customers with very high annual demands, 
amongst the highest of the sample set, of up to 30,000 kWh/year. As a reference, the Ofgem Typical Domestic Consumption Values (TCVD) for a high user 
of electricity on Economy 7 Tariff (as customers with storage heating typically are), is 7,100 kWh/year.

![PVSeason](Visualisation/SM_Heating.png)

y axis is demand in kW, y labels are the customer ID

#### Demand profiles with high overnight demand removed

Customers with demands above 2000kWh/year in the hours of midnight to 2am were removed. This removed 23 customer profiles with 162 remaining.

3 Adversity and 20 Affluent customers were removed. The remaining customers are summarised as follows;

Acorn Group|Number of customers| Avg Days of Data (per customer)| Peak Demand (kW)| Average Daily Demand (kWh/day) | Average demand (kW)
-----------|-------------------|--------------------------------|------------------|-------------------------------|--------------------
Adversity | 54 | 662 | 7.51 | 15.25 | 0.32
Comfortable | 46 | 655 | 9.24 | 19.24 | 0.40
Affluent | 66 | 666 | 9.16 | 17.88 | 0.37

As can be seen from the table above and the mean daily demand profiles below. There is now little difference between Affluent and Comfortable customers in terms of demand.

In fact Comfortable customers now have a higher average daily demand and peak. This highlights the significant effect the 20 high demand Affluent customers had on the averaged data.

![PVSeason](Visualisation/SM_Consolidated_NH.png)
