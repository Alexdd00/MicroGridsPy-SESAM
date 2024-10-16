# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 15:44:40 2024

@author: aless
"""

"Inizio codice TESI 19/03/2024 official"      #COMMENTARE OGNI RIGA

from collections import defaultdict
import re, time
import pandas as pd
import math, numpy as np, matplotlib.pyplot as plt
import urllib.parse, urllib.error
import csv
import sys
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from pandas import ExcelWriter
import warnings; warnings.simplefilter(action='ignore', category=FutureWarning)
from openpyxl import load_workbook
import os
from itertools import chain

def initialize():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    inputs_directory = os.path.join(current_directory, '..', 'Inputs')
    data_file_path = os.path.join(inputs_directory, 'Parameters_operation.dat')
    demand_file_path = os.path.join(inputs_directory, 'Demand.csv')
    res_file_path = os.path.join(inputs_directory, 'RES_Time_Series.csv')
    eff_file_path = os.path.join(inputs_directory, 'Efficiency.csv')
    temperature_file_path = os.path.join(inputs_directory, 'Temperature.csv')
    cap_file_path = os.path.join(inputs_directory, 'Newcapacity.csv')
    Data_import = open(data_file_path).readlines()

    Fuel_Specific_Start_Cost = []
    Generator_Efficiency = []
    Fuel_LHV = []
    RES_Specific_Investment_Cost = []
    RES_Specific_OM_Cost = []
    Generator_Specific_Investment_Cost = []
    Generator_Nominal_Capacity = []
    RES_Nominal_Capacity = []
    Generator_Specific_OM_Cost = []
    RES_Inverter_Efficiency = []
    FUEL_unit_CO2_emission = []
    GEN_unit_CO2_emission = []
    RES_unit_CO2_emission = []
    Generator_Colors = []
    RES_Colors = []
    RES_Names = []
    Generator_Names = []
    Fuel_Names = []
    Decad = []
    
    print('\nImporting parameters...')

    #Importing Data from parameters.dat
    for i in range(len(Data_import)):
        
        if "param: Periods" in Data_import[i]:
            n_periods = int((re.findall('\d+',Data_import[i])[0]))
        if "param: Generator_Types" in Data_import[i]:      
            n_generators = int((re.findall('\d+',Data_import[i])[0]))
        if "param: Fuel_Specific_Start_Cost" in Data_import[i]:
            for j in range(n_generators):
                Fuel_Specific_Start_Cost.append(float((re.findall("\d+\s+(\d+\.\d+|\d+)",Data_import[i+1+j])[0])))
        if "param: RES_Sources" in Data_import[i]:
            RES_Sources= int((re.findall('\d+',Data_import[i])[0]))
        if "param: Battery_Specific_Investment_Cost" in Data_import[i]:
            Battery_Specific_Investment_Cost = float((re.findall("\s+(\d+\.\d+|\d+)",Data_import[i])[0]))
        if "param: Battery_Specific_Electronic_Investment_Cost" in Data_import[i]:
            Battery_Specific_Electronic_Investment_Cost = float((re.findall("\s+(\d+\.\d+|\d+)",Data_import[i])[0]))
        if "param: Battery_Cycles" in Data_import[i]:
            Battery_Cycles = int((re.findall('\d+',Data_import[i])[0]))
        if "param: Battery_Depth_of_Discharge" in Data_import[i]:
            Battery_Depth_of_Discharge = float((re.findall("\s+(\d+\.\d+|\d+)",Data_import[i])[0]))
        if "param: Delta_Time" in Data_import[i]:
            Delta_Time = int((re.findall('\d+',Data_import[i])[0]))
        if "param: Battery_capacity_Real" in Data_import[i]:
            Battery_Nominal_Capacity = int((re.findall('\d+',Data_import[i])[0]))
        if "param: Generator_Efficiency" in Data_import[i]:
            for j in range(n_generators):
                Generator_Efficiency.append(float((re.findall("\d+\s+(\d+\.\d+|\d+)",Data_import[i+1+j])[0])))
        if "param: Fuel_LHV" in Data_import[i]:
            for j in range(n_generators):
                Fuel_LHV.append(int((re.findall("\d+\s+(\d+)",Data_import[i+1+j])[0])))
        if "param: RES_Specific_Investment_Cost" in Data_import[i]:
            for k in range(RES_Sources):
                RES_Specific_Investment_Cost.append(float((re.findall("\d+\s+(\d+\.\d+|\d+)",Data_import[i+1+k])[0]))) 
        if "param: RES_Specific_OM_Cost" in Data_import[i]:
            for k in range(RES_Sources):
                RES_Specific_OM_Cost.append(float((re.findall("\d+\s+(\d+\.\d+|\d+)",Data_import[i+1+k])[0])))
        if "param: Generator_Specific_Investment_Cost" in Data_import[i]:
            for j in range(n_generators):
                Generator_Specific_Investment_Cost.append(float((re.findall("\d+\s+(\d+\.\d+|\d+)",Data_import[i+1+j])[0])))
        if "param: Generator_Real_Capacity" in Data_import[i]:
            for j in range(n_generators):
                Generator_Nominal_Capacity.append(int((re.findall("\d+\s+(\d+)",Data_import[i+1+j])[0])))
        if "param: RES_Real_Capacity" in Data_import[i]:
            for k in range(RES_Sources):
                RES_Nominal_Capacity.append(int((re.findall("\d+\s+(\d+)",Data_import[i+1+k])[0])))
        if "param: Generator_Specific_OM_Cost" in Data_import[i]:
            for j in range(n_generators):
                Generator_Specific_OM_Cost.append(float((re.findall("\d+\s+(\d+\.\d+|\d+)",Data_import[i+1+j])[0])))
        if "param: Battery_Specific_OM_Cost" in Data_import[i]:
            Battery_Specific_OM_Cost = float((re.findall("\s+(\d+\.\d+|\d+)",Data_import[i])[0]))
        if "param: RES_Inverter_Efficiency" in Data_import[i]:
            for k in range(RES_Sources):
                RES_Inverter_Efficiency.append(float((re.findall("\d+\s+(\d+\.\d+|\d+)",Data_import[i+1+k])[0])))
        if "param: Lost_Load_Specific_Cost" in Data_import[i]:
            Lost_Load_Specific_Cost = int((re.findall('\d+',Data_import[i])[0]))
        if "param: Battery_Discharge_Battery_Efficiency" in Data_import[i]:
            Battery_Discharge_Battery_Efficiency = float((re.findall("\s+(\d+\.\d+|\d+)",Data_import[i])[0]))
        if "param: Battery_Initial_SOC" in Data_import[i]:
            Battery_Initial_SOC = float((re.findall("\s+(\d+\.\d+|\d+)",Data_import[i])[0]))
        if "param: Battery_Color" in Data_import[i]:
            Battery_Color = str((re.findall(r"'(.*?)'", Data_import[i]))[0])
        if "param: FUEL_unit_CO2_emission" in Data_import[i]:
            for j in range(n_generators):
                FUEL_unit_CO2_emission.append(float((re.findall("\d+\s+(\d+\.\d+|\d+)",Data_import[i+1+j])[0])))
        if "param: BESS_unit_CO2_emission" in Data_import[i]:
            BESS_unit_CO2_emission = int((re.findall('\d+',Data_import[i])[0]))
        if "param: Maximum_Battery_Charge_Time" in Data_import[i]:
            Maximum_Battery_Charge_Time = int((re.findall('\d+',Data_import[i])[0]))
        if "param: Maximum_Battery_Discharge_Time" in Data_import[i]:
            Maximum_Battery_Discharge_Time = int((re.findall('\d+',Data_import[i])[0]))
        if "param: GEN_unit_CO2_emission" in Data_import[i]:
            for j in range(n_generators):
                GEN_unit_CO2_emission.append(float((re.findall("\d+\s+(\d+\.\d+|\d+)",Data_import[i+1+j])[0])))
        if "param: RES_unit_CO2_emission" in Data_import[i]:
            for k in range(RES_Sources):
                RES_unit_CO2_emission.append(float((re.findall("\d+\s+(\d+\.\d+|\d+)",Data_import[i+1+k])[0])))
        if "param: Battery_Charge_Battery_Efficiency" in Data_import[i]:
            Battery_Charge_Battery_Efficiency = float((re.findall("\s+(\d+\.\d+|\d+)",Data_import[i])[0]))
        if "param: StartDate" in Data_import[i]:
            start_date_match = re.findall(r"'(.*?)'", Data_import[i])
        if "param: Curtailment_Color" in Data_import[i]:
            Curtailment_Color = str((re.findall(r"'(.*?)'", Data_import[i]))[0])
        if "param: Lost_Load_Color" in Data_import[i]:
            Lost_Load_Color = str((re.findall(r"'(.*?)'", Data_import[i]))[0])
        if "param: Generator_Colors" in Data_import[i]:
            for j in range(n_generators):
                Generator_Colors.append(str((re.findall(r"'(.*?)'", Data_import[i+1+j]))[0]))
        if "param: RES_Colors" in Data_import[i]:
            for k in range(RES_Sources):
                RES_Colors.append(str((re.findall(r"'(.*?)'", Data_import[i+1+k]))[0]))       
        if "param: RES_Names" in Data_import[i]:
            for k in range(RES_Sources):
                RES_Names.append(str((re.findall(r"'(.*?)'", Data_import[i+1+k]))))       
        if "param: Generator_Names" in Data_import[i]:
            for j in range(n_generators):
                Generator_Names.append(str((re.findall(r"'(.*?)'", Data_import[i+1+j]))))
        if "param: Fuel_Names" in Data_import[i]:
            for j in range(n_generators):
                Fuel_Names.append(str((re.findall(r"'(.*?)'", Data_import[i+1+j]))))
        if "param: Years" in Data_import[i]:
            years = int((re.findall('\d+',Data_import[i])[0])) 
        if "param: Decad" in Data_import[i]:
            for k in range(RES_Sources):
                Decad.append(float((re.findall("\d+\s+(\d+\.\d+|\d+)",Data_import[i+1+k])[0])))
        if "param: Mode " in Data_import[i]:
            mode = int((re.findall('\d+',Data_import[i])[0]))
        if "param: Generator_Partial_Load" in Data_import[i]:
            Generator_Partial_Load = int((re.findall('\d+',Data_import[i])[0]))
        if "param: Degradation_RES" in Data_import[i]:
            Degradation_RES = int((re.findall('\d+',Data_import[i])[0]))
        if "param: Degradation_BESS" in Data_import[i]:
            Degradation_BESS = int((re.findall('\d+',Data_import[i])[0]))
        if "param: Yea_selected" in Data_import[i]:
            year_selected = int((re.findall('\d+',Data_import[i])[0]))
        if "param: Battery_Technology" in Data_import[i]:
            Battery_Type = int((re.findall('\d+',Data_import[i])[0]))
        if "param: Battery_Iterative_Replacement" in Data_import[i]:
            Battery_Iterative_Replacement = int((re.findall('\d+',Data_import[i])[0]))
        if "param: Battery_Replacement_Year"  in Data_import[i]:
            Battery_Replacement_Year = int((re.findall('\d+',Data_import[i])[0]))
    
    periods = n_periods
    StartDate = str(start_date_match[0])
    Battery_Inflow = pd.DataFrame([[0]*years for _ in range(periods)])
    Battery_Outflow = pd.DataFrame([[0]*years for _ in range(periods)])
    #print(mode)

    #Importing Demand
    Demand = pd.read_csv(demand_file_path, delimiter=';', decimal='.', header=0)
    Demand = Demand.dropna(how='all', axis=1)
    Demand = Demand.iloc[:, 1:]
    Demand = pd.DataFrame(Demand)

    #Importing Renewable Time Series capacity factor
    Renewable_Energy = pd.read_csv(res_file_path, delimiter=';', decimal='.', header=0)
    RES_Energy_Production = pd.DataFrame(np.zeros((periods, RES_Sources)))
    
    #Importing Efficiency generator
    Generator_effic = pd.read_csv(eff_file_path, delimiter=';', decimal=',', header=0)
    Gen_eff = pd.DataFrame(Generator_effic)

    #Importing additional capacity of RES
    add_capacity = pd.read_csv(cap_file_path, delimiter=';', decimal=',', header=0)
    add_cap = pd.DataFrame(add_capacity)
    #print(add_cap)

    #Scaled value of partial generator curve
    scale_factor = [0]*n_generators
    basic_value =[0]*n_generators
    for g in range(n_generators):
        basic_value[g] = Gen_eff.iloc[100, (g+1)]
        scale_factor[g] = Generator_Efficiency[g]*100 / basic_value[g]

    for g in range(n_generators):
        Gen_eff.iloc[:,(g+1)] = Gen_eff.iloc[:, (g+1)] * scale_factor[g]

    #Real capacity
    RES_capacity = pd.DataFrame([[RES_Nominal_Capacity[r]]*years for r in range(RES_Sources)])
    for y in range(1, years):
        for r in range(RES_Sources):
            RES_capacity.iloc[r, y] = RES_capacity.iloc[r, y-1] + add_cap.iloc[r, y+1]
            #print(RES_capacity)




    if Degradation_RES==1:

        #Calculating RES production with decad
        index = pd.MultiIndex.from_product([range(years), range(periods)], names=['year', 'period'])

        RES_Energy_Production = pd.DataFrame(0, index=index, columns=range(RES_Sources))

        for y in range(years):
            for t in range(periods):
                for r in range(RES_Sources):
                    RES_Energy_Production.loc[(y,t), r] = ((RES_capacity.iloc[r,y]) * Renewable_Energy.iloc[t, (r+1)] * RES_Inverter_Efficiency[r]*(1-Decad[r])**(y))
                    #RES_Energy_Production.loc[(y,t), r] = ((RES_Nominal_Capacity[r] ) * Renewable_Energy.iloc[t, (r+1)] * RES_Inverter_Efficiency[r]*(1-Decad[r])**(y))
    if Degradation_RES==0:

        index = pd.MultiIndex.from_product([range(years), range(periods)], names=['year', 'period'])

        RES_Energy_Production = pd.DataFrame(0, index=index, columns=range(RES_Sources))

        #Calculating RES production without decad
        for y in range(years):
            for t in range(periods):
                for r in range(RES_Sources):
                    #print(RES_capacity)
                    RES_Energy_Production.loc[(y,t), r] = ((RES_capacity.iloc[r,y]) * Renewable_Energy.iloc[t, (r+1)] * RES_Inverter_Efficiency[r])

    #Calculating generator production
    Generator_Energy_Production = pd.DataFrame([[1]*n_generators for _ in range(periods)])
    Generator_Production = pd.DataFrame([[0]*n_generators for _ in range(periods)])

    for t in range(periods):
        for j in range(n_generators):
            Generator_Production.iloc[t,j]=Generator_Nominal_Capacity[j]*Generator_Energy_Production.iloc[t,j]

    #Calculating SOC
    Battery_SOC = pd.DataFrame([[0]*years for _ in range(periods)])
    for y in range(years):
        for t in range(periods):
            if t==0: 
                Battery_SOC.iloc[t,y] =  Battery_Nominal_Capacity* Battery_Initial_SOC -  (Battery_Outflow.iloc[t,y]/ Battery_Discharge_Battery_Efficiency) +  (Battery_Inflow.iloc[t,y]* Battery_Charge_Battery_Efficiency)  
            else:  
                Battery_SOC.iloc[t,y] =  Battery_SOC.iloc[(t-1),y] -  (Battery_Outflow.iloc[t,y]/ Battery_Discharge_Battery_Efficiency) +  (Battery_Inflow.iloc[t,y]* Battery_Charge_Battery_Efficiency)    

    #Calculating Battery replacement cost
    Unitary_Battery_Replacement_Cost = (Battery_Specific_Investment_Cost-Battery_Specific_Electronic_Investment_Cost)/(Battery_Cycles*2*Battery_Depth_of_Discharge)


    Battery_DoD = Battery_Depth_of_Discharge

    if Degradation_BESS == 1: #initialize coefficients for battery degradation model
        
        temperature = pd.read_csv(temperature_file_path, delimiter=';', decimal='.', header=0)
        
        T_amb = temperature['1'].tolist()
        
        T_amb = [T_amb for _ in range(years)]
        
        T_amb_ = list(chain(*T_amb))
        
        Tamb = [y / 10 for y in T_amb_]
        
        z = (Battery_DoD*10)-2
        Alpha = []; Beta = []
        for x in Tamb:
            if Battery_Type==1: # 1=LFP
                cycle_coefficient = 6400/Battery_Cycles
                if Battery_DoD==0.8:
                    Alpha.append(3.446908*10**(-10)*(x**3)+1.240398*10**(-9)*(x**2)+1.053498*10**(-8)*(x)+1.970248*10**(-8))
                    Beta.append((6.337047*10**(-7)*(x**3)-2.869914*10**(-6)*(x**2)+9.192472*10**(-6)*(x)+3.861381*10**(-6))*cycle_coefficient)
                elif Battery_DoD==0.9:
                    Alpha.append(3.446908*10**(-10)*(x**3)+1.240398*10**(-9)*(x**2)+1.053498*10**(-8)*(x)+1.970248*10**(-8))
                    Beta.append((6.070837*10**(-7)*(x**3)-2.769339*10**(-6)*(x**2)+8.701044*10**(-6)*(x)+3.423667*10**(-6))*cycle_coefficient)
                elif Battery_DoD==0.7:
                    Alpha.append(4.485623*10**(-10)*(x**3)+1.614189*10**(-9)*(x**2)+1.370967*10**(-8)*(x)+2.563976*10**(-8))
                    Beta.append((7.549737*10**(-7)*(x**3)-3.721425*10**(-6)*(x**2)+1.167026*10**(-5)*(x)+3.269498*10**(-6))*cycle_coefficient)
                elif Battery_DoD==0.6:
                    Alpha.append(4.485623*10**(-10)*(x**3)+1.614189*10**(-9)*(x**2)+1.370967*10**(-8)*(x)+2.563976*10**(-8))
                    Beta.append((8.528446*10**(-7)*(x**3)-4.189309*10**(-6)*(x**2)+1.323273*10**(-5)*(x)+3.85312*10**(-6))*cycle_coefficient)
                elif Battery_DoD==0.5:
                    Alpha.append(4.485623*10**(-10)*(x**3)+1.614189*10**(-9)*(x**2)+1.370967*10**(-8)*(x)+2.563976*10**(-8))
                    Beta.append((9.085917*10**(-7)*(x**3)-4.051845*10**(-6)*(x**2)+1.32569*10**(-5)*(x)+6.130398*10**(-6))*cycle_coefficient)
            elif Battery_Type==2: # 2=NMC
                cycle_coefficient = 5000/Battery_Cycles
                if Battery_DoD==0.8:
                    Alpha.append(8.32382*10**(-11)*(x**3)+8.912264*10**(-10)*(x**2)+6.706961*10**(-9)*(x)+1.814235*10**(-8))    
                    Beta.append((1.403785*10**(-6)*(x**3)-4.530322*10**(-6)*(x**2)+1.324309*10**(-5)*(x)-2.212139*10**(-6))*cycle_coefficient)
                elif Battery_DoD==0.9:
                    Alpha.append(8.32382*10**(-11)*(x**3)+8.912264*10**(-10)*(x**2)+6.706961*10**(-9)*(x)+1.814235*10**(-8))
                    Beta.append((1.326799*10**(-6)*(x**3)-4.21017*10**(-6)*(x**2)+1.256349*10**(-5)*(x)-1.862879*10**(-6))*cycle_coefficient)
                elif Battery_DoD==0.7:
                    Alpha.append(9.208524*10**(-11)*(x**3)+9.854044*10**(-10)*(x**2)+7.418433*10**(-9)*(x)+2.006416*10**(-8))
                    Beta.append((1.543396*10**(-6)*(x**3)-5.03352*10**(-6)*(x**2)+1.451821*10**(-5)*(x)-2.625175*10**(-6))*cycle_coefficient)
                elif Battery_DoD==0.6:
                    Alpha.append(9.208524*10**(-11)*(x**3)+9.854044*10**(-10)*(x**2)+7.418433*10**(-9)*(x)+2.006416*10**(-8))
                    Beta.append((1.746515*10**(-6)*(x**3)-5.739906*10**(-6)*(x**2)+1.640342*10**(-5)*(x)-3.106159*10**(-6))*cycle_coefficient)
                elif Battery_DoD==0.5:
                    Alpha.append(9.208524*10**(-11)*(x**3)+9.854044*10**(-10)*(x**2)+7.418433*10**(-9)*(x)+2.006416*10**(-8))
                    Beta.append((2.044415*10**(-6)*(x**3)-6.759912*10**(-6)*(x**2)+1.917865*10**(-5)*(x)-3.760983*10**(-6))*cycle_coefficient)
            elif Battery_Type==3: # 3=Lead Acid
                    cycle_coefficient = 3000/Battery_Cycles
                    Alpha.append(2.283105*10**(-6))
                    Beta.append((-1.012639*10**(-7)*(z**3)+1.534911*10**(-6)*(z**2)-8.427153*10**(-6)*(z)+2.813216*10**(-5))*cycle_coefficient)
        
        Alpha.append(Alpha[len(Alpha)-1])
        Beta.append(Beta[len(Beta)-1])


    if Degradation_BESS==0:
        Alpha= 0
        Beta = 0

    #Exporting Data
    params = {
        'Battery_Inflow' : Battery_Inflow,
        'Battery_Outflow' : Battery_Outflow,
        'RES_Energy_Production' : RES_Energy_Production,
        'Generator_Production' : Generator_Production,
        'Demand' : Demand,
        'Battery_SOC' : Battery_SOC,
        'RES_Sources' : RES_Sources,
        'Battery_Nominal_Capacity' : Battery_Nominal_Capacity,
        'Battery_Depth_of_Discharge' : Battery_Depth_of_Discharge,
        'n_generators' : n_generators,
        'Delta_Time' : Delta_Time,
        'Generator_Energy_Production' : Generator_Energy_Production,
        'Generator_Nominal_Capacity' : Generator_Nominal_Capacity,
        'Maximum_Battery_Charge_Time' : Maximum_Battery_Charge_Time,
        'Maximum_Battery_Discharge_Time' : Maximum_Battery_Discharge_Time,
        'Periods': periods,
        'RES_Capacity': RES_Nominal_Capacity,
        'RES_Investment': RES_Specific_Investment_Cost,
        'RES_OM': RES_Specific_OM_Cost,
        'Generator_Investment': Generator_Specific_Investment_Cost,
        'Generator_OM': Generator_Specific_OM_Cost,
        'Battery_Investment': Battery_Specific_Investment_Cost,
        'Battery_OM': Battery_Specific_OM_Cost,
        'Unitary_Battery_Replacement': Unitary_Battery_Replacement_Cost,
        'RES_emission': RES_unit_CO2_emission,
        'Generator_emission': GEN_unit_CO2_emission,
        'Fuel_LHV': Fuel_LHV,
        'Generator_Efficiency': Generator_Efficiency,
        'Fuel_Emission': FUEL_unit_CO2_emission,
        'BESS_Emission': BESS_unit_CO2_emission,
        'Lost_Load_Specific_Cost': Lost_Load_Specific_Cost,
        'RES_names': RES_Names,
        'Generator_names': Generator_Names,
        'Fuel_names': Fuel_Names,
        'StartDate': StartDate,
        'Lost_Load_Color': Lost_Load_Color,
        'Curtailment_Color': Curtailment_Color,
        'RES_Colors': RES_Colors,
        'Generator_Colors': Generator_Colors,
        'Battery_Color': Battery_Color,
        'Fuel_Specific_Cost': Fuel_Specific_Start_Cost,
        'Gen_eff': Gen_eff,
        'years': years,
        'Generator_Partial_Load': Generator_Partial_Load,
        'years_selected': year_selected,
        'Degradation_BESS': Degradation_BESS,
        'Battery_Initial_SOC': Battery_Initial_SOC,
        'Battery_Iterative_Replacement': Battery_Iterative_Replacement,
        'Battery_Replacement_Year': Battery_Replacement_Year,
        'Alpha': Alpha,
        'Beta': Beta,
        'mode': mode
    }

    return params
