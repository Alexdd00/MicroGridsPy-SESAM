# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 15:44:40 2024

Author: aless
"""

import pandas as pd
import numpy as np

def Operation(params):

    # Importing Data from params
    mode = params['mode']
    years = params['years']
    periods = params['Periods']
    index = pd.MultiIndex.from_product([range(years), range(periods)], names=['year', 'period'])
    
    Generator_Production_df = pd.DataFrame(params['Generator_Production'])
    RES_Energy_Production_dfa = pd.DataFrame(params['RES_Energy_Production'], index=index, columns=range(params['RES_Sources']))
    
    # Vectorized operation to sum RES energy production
    RES_Energy_Production_df = RES_Energy_Production_dfa.sum(axis=1).unstack(level=0).T
    
    Battery_SOC_df = pd.DataFrame(params['Battery_SOC'])
    Demand_df = pd.DataFrame(params['Demand'])
    
    # Reshape RES_Energy_Production_df
    RES_Energy_Production_df_reshaped = RES_Energy_Production_df.values.T
    RES_Energy_Production_dfu = pd.DataFrame(RES_Energy_Production_df_reshaped)
    
    # Initialize DataFrames and lists
    Energy_Curtailment_df = pd.DataFrame(0, index=range(periods), columns=range(years))
    Lost_Load_df = pd.DataFrame(0, index=range(periods), columns=range(years))
    Maximum_Generator_Energy_1 = pd.DataFrame(0, index=range(len(params['RES_Energy_Production'])), columns=range(params['n_generators']))
    Minimum_Generator_Energy = pd.DataFrame(0, index=range(len(params['RES_Energy_Production'])), columns=range(params['n_generators']))
    
    Battery_Nominal_Capacity = params['Battery_Nominal_Capacity']
    Battery_Depth_of_Discharge = params['Battery_Depth_of_Discharge']
    Maximum_Battery_Charge_Time = params['Maximum_Battery_Charge_Time']
    Maximum_Battery_Discharge_Time = params['Maximum_Battery_Discharge_Time']
    
    Battery_Inflow1 = pd.DataFrame(params['Battery_Inflow'])
    Battery_Outflow1 = pd.DataFrame(params['Battery_Outflow'])
    
    Delta_Time = params['Delta_Time']
    n_generators = params['n_generators']
    Generator_Nominal_Capacity = params['Generator_Nominal_Capacity']
    res_columns = [f'RES{r+1}' for r in range(params['RES_Sources'])] + [f'Generator{i+1}' for i in range(n_generators)] + ['SOC', 'Lost_Load', 'Energy_Curtailment', 'Total_Energy_Production', 'Battery']
    res_df = pd.DataFrame(columns=res_columns)
    
    Degradation_BESS = params['Degradation_BESS']
    Battery_Initial_SOC = params['Battery_Initial_SOC']
    Battery_Iterative_Replacement = params['Battery_Iterative_Replacement']
    Battery_Replacement_Year = params['Battery_Replacement_Year']
    
    Battery_Inflow_df = pd.DataFrame(0, index=range(periods), columns=range(years))
    Battery_Outflow_df = pd.DataFrame(0, index=range(periods), columns=range(years))
    Battery_Bank_Energy_Exchange = pd.DataFrame(0, index=range(periods), columns=range(years))
    Battery_Bank_Energy = pd.DataFrame(0, index=range(periods), columns=range(years))
    
    years_selected = params['years_selected']
    total_value = periods * years
    
    if Degradation_BESS == 1:
        alpha = np.array(params['Alpha'][:total_value]).reshape(periods, years)
        beta = np.array(params['Beta'][:total_value]).reshape(periods, years)
        
        alfa = pd.DataFrame(alpha)
        bieta = pd.DataFrame(beta)
    
    Generator_energies = pd.DataFrame(0, index=index, columns=range(n_generators))
    
    print('\nSimulating operation mode...')
    #print(mode)

    # Creation of constraints
    Battery_Outflow_df.iloc[0, 0] = Battery_Outflow1.iloc[0, 0]
    Battery_Inflow_df.iloc[0, 0] = Battery_Inflow1.iloc[0, 0]
    
    Battery_Outflow_df.iloc[0, 1:] = Battery_Outflow_df.iloc[periods-1, :-1].values
    Battery_Inflow_df.iloc[0, 1:] = Battery_Inflow_df.iloc[periods-1, :-1].values
    Battery_SOC_df.iloc[0, 1:] = Battery_SOC_df.iloc[periods-1, :-1].values
    
    for y in range(years):
        for t in range(periods):
            if t != 0:
                Battery_Outflow_df.iloc[t, y] = Battery_Outflow_df.iloc[t-1, y]
                Battery_Inflow_df.iloc[t, y] = Battery_Inflow_df.iloc[t-1, y]
                Battery_SOC_df.iloc[t, y] = Battery_SOC_df.iloc[t-1, y]
            
            if Degradation_BESS == 1:
                Battery_Bank_Energy_Exchange.iloc[t, y] = -Battery_Outflow_df.iloc[t, y] + Battery_Inflow_df.iloc[t, y]
                
                if t == 0 and y == 0:
                    Battery_Bank_Energy.iloc[t, y] = (Battery_Nominal_Capacity * Battery_Initial_SOC - (alfa.iloc[t, y] * Battery_Bank_Energy.iloc[t, y]) - (bieta.iloc[t, y] * Battery_Bank_Energy_Exchange.iloc[t, y]))
                elif t != 0 and y == 0:
                    Battery_Bank_Energy.iloc[t, y] = (Battery_Bank_Energy.iloc[t-1, y] - (alfa.iloc[t, y] * Battery_Bank_Energy.iloc[t-1, y]) - (bieta.iloc[t, y] * Battery_Bank_Energy_Exchange.iloc[t, y]))
                elif t == 0 and y != 0:
                    if Battery_Iterative_Replacement == 1 and y == Battery_Replacement_Year:
                        Battery_Bank_Energy.iloc[t, y] = Battery_Nominal_Capacity * Battery_Initial_SOC
                    else:
                        Battery_Bank_Energy.iloc[t, y] = Battery_Bank_Energy.iloc[periods-1, y-1]
                else:
                    Battery_Bank_Energy.iloc[t, y] = (Battery_Bank_Energy.iloc[t-1, y] - (alfa.iloc[t, y] * Battery_Bank_Energy.iloc[t-1, y]) - (bieta.iloc[t, y] * Battery_Bank_Energy_Exchange.iloc[t, y]))
            
            if Degradation_BESS == 1:
                Demand_higher_RES = Demand_df.iloc[t, y] > RES_Energy_Production_dfu.iloc[t, y]
                Demand_lower_RES = Demand_df.iloc[t,y] < RES_Energy_Production_dfu.iloc[t, y]
                Demand_equal_RES = Demand_df.iloc[t, y] == RES_Energy_Production_dfu.iloc[t, y]
                Minimum_Charge = Battery_SOC_df.iloc[t, y] >= Battery_Bank_Energy.iloc[t,y]*(1- Battery_Depth_of_Discharge) #Degradation
                if t==0:
                    Maximum_Charge = Battery_SOC_df.iloc[t, y] <= Battery_Bank_Energy.iloc[t,y]
                    Max_Power_Battery_Charge = Battery_Outflow_df.iloc[t,y] ==  Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time #Degradation DA CONTROLLARE
                    Max_Power_Battery_Discharge = Battery_Inflow_df.iloc[t,y] ==  Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Discharge_Time #Degradation DA CONTROLLARE TUTTI I t-1 PERCHè ORA 0 NON VALIDO
                    Max_Bat_in = Battery_Outflow_df.iloc[t,y] <=  (Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time)* Delta_Time #Degradation DA CONTROLARE
                    Battery_Single_Flow_Discharge = Battery_Inflow_df.iloc[t,y] <= (Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Discharge_Time)* Delta_Time
                if t!=0:
                    Maximum_Charge = Battery_SOC_df.iloc[t, y] <= Battery_Bank_Energy.iloc[(t-1),y] #Degradation
                    Max_Power_Battery_Charge = Battery_Outflow_df.iloc[t,y] ==  Battery_Bank_Energy.iloc[(t-1),y]/ Maximum_Battery_Charge_Time #Degradation DA CONTROLLARE
                    Max_Power_Battery_Discharge = Battery_Inflow_df.iloc[t,y] ==  Battery_Bank_Energy.iloc[(t-1),y]/ Maximum_Battery_Discharge_Time #Degradation DA CONTROLLARE TUTTI I t-1 PERCHè ORA 0 NON VALIDO
                    Max_Bat_in = Battery_Outflow_df.iloc[t,y] <=  (Battery_Bank_Energy.iloc[(t-1),y]/ Maximum_Battery_Charge_Time)* Delta_Time #Degradation DA CONTROLARE
                    Battery_Single_Flow_Discharge = Battery_Inflow_df.iloc[t,y] <= (Battery_Bank_Energy.iloc[(t-1),y]/ Maximum_Battery_Discharge_Time)* Delta_Time #Degradation 
                Full_batt = Battery_SOC_df.iloc[t, y] <= Battery_Bank_Energy.iloc[t,y]*(1- Battery_Depth_of_Discharge) #Degradation
                Full_batt2 = Battery_SOC_df.iloc[t, y] >= (Battery_Bank_Energy.iloc[t,y] - 0.2) #Degradation 
                Max_Bat_out = Battery_Inflow_df.iloc[t,y] <=  Demand_df.iloc[t,y]
                Battery_Single_Flow_Charge = Battery_Outflow_df.iloc[t,y] <= 0

            if Degradation_BESS == 0:
                Demand_higher_RES = Demand_df.iloc[t, y] > RES_Energy_Production_dfu.iloc[t, y]
                Demand_lower_RES = Demand_df.iloc[t,y] < RES_Energy_Production_dfu.iloc[t, y]
                Demand_equal_RES = Demand_df.iloc[t, y] == RES_Energy_Production_dfu.iloc[t, y]
                Minimum_Charge = Battery_SOC_df.iloc[t, y] >= Battery_Nominal_Capacity*(1- Battery_Depth_of_Discharge) #Degradation
                Maximum_Charge = Battery_SOC_df.iloc[t, y] <= Battery_Nominal_Capacity #Degradation
                Full_batt = Battery_SOC_df.iloc[t, y] <= Battery_Nominal_Capacity*(1- Battery_Depth_of_Discharge) #Degradation
                Full_batt2 = Battery_SOC_df.iloc[t, y] >= Battery_Nominal_Capacity #Degradation
                Max_Power_Battery_Charge = Battery_Outflow_df.iloc[t,y] ==  Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time #Degradation
                Max_Power_Battery_Discharge = Battery_Inflow_df.iloc[t,y] ==  Battery_Nominal_Capacity/ Maximum_Battery_Discharge_Time #Degradation
                Max_Bat_in = Battery_Outflow_df.iloc[t,y] <=  (Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time)* Delta_Time #Degradation
                Max_Bat_out = Battery_Inflow_df.iloc[t,y] <=  Demand_df.iloc[t,y]
                Battery_Single_Flow_Discharge = Battery_Inflow_df.iloc[t,y] <= (Battery_Nominal_Capacity/ Maximum_Battery_Discharge_Time)* Delta_Time #Degradation
                Battery_Single_Flow_Charge = Battery_Outflow_df.iloc[t,y] <= 0
            
            for g in range(n_generators):
                Maximum_Generator_Energy_1.iloc[t, g] = Generator_Production_df.iloc[t, g] <= Generator_Nominal_Capacity[g] * Delta_Time
                Minimum_Generator_Energy.iloc[t, g] = Generator_Production_df.iloc[t, g] >= 0
            
            #Simulation core Cycle Charging
            if mode == 1:
                if Demand_equal_RES:
                    res_row = {'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': 0, 'Energy_Curtailment': 0, 'Total_Energy_Production': RES_Energy_Production_dfu.iloc[t, y], 'Battery': Battery_SOC_df.iloc[t,y]}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    for g in range(n_generators):
                        res_row[f'Generator{g+1}'] = 0
                    res_df = res_df.append(res_row, ignore_index=True)
                
                    
                elif Demand_higher_RES and Minimum_Charge and Maximum_Charge and (Max_Power_Battery_Discharge or Max_Bat_out or Battery_Single_Flow_Discharge):
                    if Degradation_BESS == 1:
                        if ((Demand_df.iloc[t,y] - RES_Energy_Production_dfu.iloc[t, y]) > (Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Discharge_Time)) and (Battery_SOC_df.iloc[t,y] > (Battery_Bank_Energy.iloc[t,y]*(1- Battery_Depth_of_Discharge)+(Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Discharge_Time))) :
                            Battery_Inflow_df.iloc[t,y] = Battery_Bank_Energy.iloc[t,y]/Maximum_Battery_Discharge_Time
                        else:
                            Battery_Inflow_df.iloc[t,y] = min((Demand_df.iloc[t,y]-RES_Energy_Production_dfu.iloc[t, y]), (Battery_SOC_df.iloc[t,y]-(Battery_Bank_Energy.iloc[t,y]*(1- Battery_Depth_of_Discharge))))
                        Battery_SOC_df.iloc[t,y] = max(Battery_SOC_df.iloc[t,y] - Battery_Inflow_df.iloc[t,y], (Battery_Bank_Energy.iloc[t,y]*(1- Battery_Depth_of_Discharge)))
                        
                    if Degradation_BESS == 0:
                        if ((Demand_df.iloc[t,y] - RES_Energy_Production_dfu.iloc[t, y]) > (Battery_Nominal_Capacity/ Maximum_Battery_Discharge_Time)) and (Battery_SOC_df.iloc[t,y] > (Battery_Nominal_Capacity*(1- Battery_Depth_of_Discharge)+(Battery_Nominal_Capacity/ Maximum_Battery_Discharge_Time))) :
                            Battery_Inflow_df.iloc[t,y] = Battery_Nominal_Capacity/Maximum_Battery_Discharge_Time
                        else:
                            Battery_Inflow_df.iloc[t,y] = min((Demand_df.iloc[t,y]-RES_Energy_Production_dfu.iloc[t, y]), (Battery_SOC_df.iloc[t,y]-(Battery_Nominal_Capacity*(1- Battery_Depth_of_Discharge))))
                        Battery_SOC_df.iloc[t,y] = max(Battery_SOC_df.iloc[t,y] - Battery_Inflow_df.iloc[t,y], (Battery_Nominal_Capacity*(1- Battery_Depth_of_Discharge)))
                    res_energy = (RES_Energy_Production_dfu.iloc[t, y] + Battery_Inflow_df.iloc[t,y])
                    #DA QUA INIZIA LA PARTE DI CYCLE CHARGING
                    if (res_energy - Demand_df.iloc[t,y]) < (-0.1) or Full_batt:   #res_energy < Demand_df.iloc[t,y] IL PROBLEMA è LA TOLLERANZA, ora messa a 0.1 però devo stringere di più forse , metto tolleranza a 1 watt
                        for g in range(n_generators):

                            Generator_Production = (Generator_Production_df.iloc[t,g])
                            
                            res_energy += Generator_Production
                            Generator_energies.loc[(y,t),g] = Generator_Production
                            if res_energy > Demand_df.iloc[t,y]:  #QUA DEVO AGGIUNGERE LE BATTERIE CHE SI RICARICANO
                                if Degradation_BESS == 1:
                                   if ((res_energy - Demand_df.iloc[t,y]) > (Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time)) and (Battery_SOC_df.iloc[t,y] < (Battery_Bank_Energy.iloc[t,y]-(Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time))) :
                                      Battery_Outflow_df.iloc[t,y] = Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time
                                   else:    
                                        Battery_Outflow_df.iloc[t,y] = min((res_energy - Demand_df.iloc[t,y]), (Battery_Bank_Energy.iloc[t,y]-Battery_SOC_df.iloc[t,y]))
                                   Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow_df.iloc[t,y],Battery_Bank_Energy.iloc[t,y])
                                if Degradation_BESS == 0:
                                   if ((res_energy - Demand_df.iloc[t,y]) > (Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time)) and (Battery_SOC_df.iloc[t,y] < (Battery_Nominal_Capacity-(Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time))) :
                                      Battery_Outflow_df.iloc[t,y] = Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time
                                   else:    
                                      Battery_Outflow_df.iloc[t,y] = min((res_energy - Demand_df.iloc[t,y]), (Battery_Nominal_Capacity-Battery_SOC_df.iloc[t,y]))
                                   Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow_df.iloc[t,y],Battery_Nominal_Capacity)
                                res_energy -= Battery_Outflow_df.iloc[t,y]
                                    # if res_energy > Demand_df.iloc[t,y] or Full_batt2:
                                    #     Energy_Curtailment_df.iloc[t,y] = res_energy - Demand_df.iloc[t,y]
                                    #     res_energy -= Energy_Curtailment_df.iloc[t,y]
                                if res_energy > Demand_df.iloc[t,y] or Full_batt2:
                                    Generator_Produ = res_energy - Demand_df.iloc[t,y]
                                    Generator_Production -= Generator_Produ
                                    res_energy -= Generator_Produ
                                    Generator_energies.loc[(y,t),g] = Generator_Production
                                res_row = {'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': 0, 'Energy_Curtailment': Energy_Curtailment_df.iloc[t,y], 'Total_Energy_Production': res_energy, 'Battery': -Battery_Outflow_df.iloc[t,y]}
                                for r in range(params['RES_Sources']):
                                    res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                                for g in range(n_generators):
                                    res_row[f'Generator{g+1}'] = 0
                                res_df = res_df.append(res_row, ignore_index=True)
                                break         

                        if res_energy < Demand_df.iloc[t,y]:
                            Lost_Load_df.iloc[t,y] = max(Demand_df.iloc[t,y]-res_energy, 0)
                            res_energy += Lost_Load_df.iloc[t,y]
                    res_row={'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': Lost_Load_df.iloc[t,y], 'Energy_Curtailment': 0, 'Total_Energy_Production': res_energy, 'Battery':Battery_Inflow_df.iloc[t,y]}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    for g in range(n_generators):
                        res_row[f'Generator{g+1}'] = Generator_energies.loc[(y,t),g]
                    res_df = res_df.append(res_row, ignore_index=True)
                
                elif Demand_higher_RES and Full_batt:
                    Lost_Load_df.iloc[t,y] = Demand_df.iloc[t, y] - RES_Energy_Production_dfu.iloc[t, y]
                    res_energy += Lost_Load_df.iloc[t,y]
                    res_row={'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': Lost_Load_df.iloc[t,y], 'Energy_Curtailment': 0, 'Total_Energy_Production': res_energy, 'Battery':0}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    res_df = res_df.append(res_row, ignore_index=True)
                    
                elif Demand_lower_RES and Full_batt2:
                    if Degradation_BESS == 1:
                        Battery_Outflow_df.iloc[t,y] = min((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]), (Battery_Bank_Energy.iloc[t,y]-Battery_SOC_df.iloc[t,y]))
                        Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow_df.iloc[t,y],Battery_Bank_Energy.iloc[t,y])
                    if Degradation_BESS == 0:
                        Battery_Outflow_df.iloc[t,y] = min((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]), (Battery_Nominal_Capacity-Battery_SOC_df.iloc[t,y]))
                        Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow_df.iloc[t,y],Battery_Nominal_Capacity)
                    res_energy = RES_Energy_Production_dfu.iloc[t, y]
                    Energy_Curtailment_df.iloc[t,y] = RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]
                    res_energy -= Energy_Curtailment_df.iloc[t,y]
                    res_row = {'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': 0, 'Energy_Curtailment': Energy_Curtailment_df.iloc[t,y], 'Total_Energy_Production': res_energy, 'Battery': 0}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                        for g in range(n_generators):
                            res_row[f'Generator{g+1}'] = 0
                    res_df = res_df.append(res_row, ignore_index=True)
                    
                elif Demand_lower_RES and Minimum_Charge and Maximum_Charge and (Max_Power_Battery_Charge or Max_Bat_in or Battery_Single_Flow_Charge):
                    if Degradation_BESS == 1:
                        if ((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]) > (Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time)) and (Battery_SOC_df.iloc[t,y] < (Battery_Bank_Energy.iloc[t,y]-(Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time))) :
                            Battery_Outflow_df.iloc[t,y] = Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time
                        else:    
                            Battery_Outflow_df.iloc[t,y] = min((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]), (Battery_Bank_Energy.iloc[t,y]-Battery_SOC_df.iloc[t,y]))
                        Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow_df.iloc[t,y],Battery_Bank_Energy.iloc[t,y])
                    if Degradation_BESS == 0:
                        if ((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]) > (Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time)) and (Battery_SOC_df.iloc[t,y] < (Battery_Nominal_Capacity-(Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time))) :
                            Battery_Outflow_df.iloc[t,y] = Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time
                        else:    
                            Battery_Outflow_df.iloc[t,y] = min((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]), (Battery_Nominal_Capacity-Battery_SOC_df.iloc[t,y]))
                        Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow_df.iloc[t,y],Battery_Nominal_Capacity)
                    res_energy = (RES_Energy_Production_dfu.iloc[t, y] - Battery_Outflow_df.iloc[t,y])
                    if res_energy > Demand_df.iloc[t,y] or Full_batt2:
                        Energy_Curtailment_df.iloc[t,y] = res_energy - Demand_df.iloc[t,y]
                        res_energy -= Energy_Curtailment_df.iloc[t,y]
                    res_row = {'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': 0, 'Energy_Curtailment': Energy_Curtailment_df.iloc[t,y], 'Total_Energy_Production': res_energy, 'Battery': -Battery_Outflow_df.iloc[t,y]}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    for g in range(n_generators):
                        res_row[f'Generator{g+1}'] = 0
                    res_df = res_df.append(res_row, ignore_index=True)
                    
                else:
                    res_row = {'SOC': 0, 'Lost_Load': 0, 'Energy_Curtailment': 0, 'Total_Energy_Production': Demand_df.iloc[t,y], 'Battery': 'Error'}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    res_df = res_df.append(res_row, ignore_index=True)
                    print('errore: nessun caso valido')
                



            #Simulation core Load Following
            if mode == 0:
                if Demand_equal_RES:
                    res_row = {'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': 0, 'Energy_Curtailment': 0, 'Total_Energy_Production': RES_Energy_Production_dfu.iloc[t, y], 'Battery': Battery_SOC_df.iloc[t,y]}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    for g in range(n_generators):
                        res_row[f'Generator{g+1}'] = 0
                    res_df = res_df.append(res_row, ignore_index=True)
                
                    
                elif Demand_higher_RES and Minimum_Charge and Maximum_Charge and (Max_Power_Battery_Discharge or Max_Bat_out or Battery_Single_Flow_Discharge):
                    if Degradation_BESS == 1:
                        if ((Demand_df.iloc[t,y] - RES_Energy_Production_dfu.iloc[t, y]) > (Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Discharge_Time)) and (Battery_SOC_df.iloc[t,y] > (Battery_Bank_Energy.iloc[t,y]*(1- Battery_Depth_of_Discharge)+(Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Discharge_Time))) :
                            Battery_Inflow_df.iloc[t,y] = Battery_Bank_Energy.iloc[t,y]/Maximum_Battery_Discharge_Time
                        else:
                            Battery_Inflow_df.iloc[t,y] = min((Demand_df.iloc[t,y]-RES_Energy_Production_dfu.iloc[t, y]), (Battery_SOC_df.iloc[t,y]-(Battery_Bank_Energy.iloc[t,y]*(1- Battery_Depth_of_Discharge))))
                        Battery_SOC_df.iloc[t,y] = max(Battery_SOC_df.iloc[t,y] - Battery_Inflow_df.iloc[t,y], (Battery_Bank_Energy.iloc[t,y]*(1- Battery_Depth_of_Discharge)))
                        
                    if Degradation_BESS == 0:
                        if ((Demand_df.iloc[t,y] - RES_Energy_Production_dfu.iloc[t, y]) > (Battery_Nominal_Capacity/ Maximum_Battery_Discharge_Time)) and (Battery_SOC_df.iloc[t,y] > (Battery_Nominal_Capacity*(1- Battery_Depth_of_Discharge)+(Battery_Nominal_Capacity/ Maximum_Battery_Discharge_Time))) :
                            Battery_Inflow_df.iloc[t,y] = Battery_Nominal_Capacity/Maximum_Battery_Discharge_Time
                        else:
                            Battery_Inflow_df.iloc[t,y] = min((Demand_df.iloc[t,y]-RES_Energy_Production_dfu.iloc[t, y]), (Battery_SOC_df.iloc[t,y]-(Battery_Nominal_Capacity*(1- Battery_Depth_of_Discharge))))
                        Battery_SOC_df.iloc[t,y] = max(Battery_SOC_df.iloc[t,y] - Battery_Inflow_df.iloc[t,y], (Battery_Nominal_Capacity*(1- Battery_Depth_of_Discharge)))
                    res_energy = (RES_Energy_Production_dfu.iloc[t, y] + Battery_Inflow_df.iloc[t,y])
                    if res_energy < Demand_df.iloc[t,y] or Full_batt:
                        for g in range(n_generators):
                            Generator_Production = min(Demand_df.iloc[t, y] - res_energy, Generator_Production_df.iloc[t, g])
                            res_energy += Generator_Production
                            Generator_energies.loc[(y,t),g] = Generator_Production
                            if res_energy >= Demand_df.iloc[t,y]:
                                break

                        if res_energy < Demand_df.iloc[t,y]:
                            Lost_Load_df.iloc[t,y] = max(Demand_df.iloc[t,y]-res_energy, 0)
                            res_energy += Lost_Load_df.iloc[t,y]
                    res_row={'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': Lost_Load_df.iloc[t,y], 'Energy_Curtailment': 0, 'Total_Energy_Production': res_energy, 'Battery':Battery_Inflow_df.iloc[t,y]}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    for g in range(n_generators):
                        res_row[f'Generator{g+1}'] = Generator_energies.loc[(y,t),g]
                    res_df = res_df.append(res_row, ignore_index=True)
                
                elif Demand_higher_RES and Full_batt:
                    Lost_Load_df.iloc[t,y] = Demand_df.iloc[t, y] - RES_Energy_Production_dfu.iloc[t, y]
                    res_energy += Lost_Load_df.iloc[t,y]
                    res_row={'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': Lost_Load_df.iloc[t,y], 'Energy_Curtailment': 0, 'Total_Energy_Production': res_energy, 'Battery':0}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    res_df = res_df.append(res_row, ignore_index=True)
                    
                elif Demand_lower_RES and Full_batt2:
                    if Degradation_BESS == 1:
                        Battery_Outflow_df.iloc[t,y] = min((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]), (Battery_Bank_Energy.iloc[t,y]-Battery_SOC_df.iloc[t,y]))
                        Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow_df.iloc[t,y],Battery_Bank_Energy.iloc[t,y])
                    if Degradation_BESS == 0:
                        Battery_Outflow_df.iloc[t,y] = min((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]), (Battery_Nominal_Capacity-Battery_SOC_df.iloc[t,y]))
                        Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow_df.iloc[t,y],Battery_Nominal_Capacity)
                    res_energy = RES_Energy_Production_dfu.iloc[t, y]
                    Energy_Curtailment_df.iloc[t,y] = RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]
                    res_energy -= Energy_Curtailment_df.iloc[t,y]
                    res_row = {'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': 0, 'Energy_Curtailment': Energy_Curtailment_df.iloc[t,y], 'Total_Energy_Production': res_energy, 'Battery': 0}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                        for g in range(n_generators):
                            res_row[f'Generator{g+1}'] = 0
                    res_df = res_df.append(res_row, ignore_index=True)
                    
                elif Demand_lower_RES and Minimum_Charge and Maximum_Charge and (Max_Power_Battery_Charge or Max_Bat_in or Battery_Single_Flow_Charge):
                    if Degradation_BESS == 1:
                        if ((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]) > (Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time)) and (Battery_SOC_df.iloc[t,y] < (Battery_Bank_Energy.iloc[t,y]-(Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time))) :
                            Battery_Outflow_df.iloc[t,y] = Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time
                        else:    
                            Battery_Outflow_df.iloc[t,y] = min((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]), (Battery_Bank_Energy.iloc[t,y]-Battery_SOC_df.iloc[t,y]))
                        Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow_df.iloc[t,y],Battery_Bank_Energy.iloc[t,y])
                    if Degradation_BESS == 0:
                        if ((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]) > (Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time)) and (Battery_SOC_df.iloc[t,y] < (Battery_Nominal_Capacity-(Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time))) :
                            Battery_Outflow_df.iloc[t,y] = Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time
                        else:    
                            Battery_Outflow_df.iloc[t,y] = min((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]), (Battery_Nominal_Capacity-Battery_SOC_df.iloc[t,y]))
                        Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow_df.iloc[t,y],Battery_Nominal_Capacity)
                    res_energy = (RES_Energy_Production_dfu.iloc[t, y] - Battery_Outflow_df.iloc[t,y])
                    if res_energy > Demand_df.iloc[t,y] or Full_batt2:
                        Energy_Curtailment_df.iloc[t,y] = res_energy - Demand_df.iloc[t,y]
                        res_energy -= Energy_Curtailment_df.iloc[t,y]
                    res_row = {'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': 0, 'Energy_Curtailment': Energy_Curtailment_df.iloc[t,y], 'Total_Energy_Production': res_energy, 'Battery': -Battery_Outflow_df.iloc[t,y]}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    for g in range(n_generators):
                        res_row[f'Generator{g+1}'] = 0
                    res_df = res_df.append(res_row, ignore_index=True)
                    
                else:
                    res_row = {'SOC': 0, 'Lost_Load': 0, 'Energy_Curtailment': 0, 'Total_Energy_Production': Demand_df.iloc[t,y], 'Battery': 'Error'}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    res_df = res_df.append(res_row, ignore_index=True)
                    print('errore: nessun caso valido')
    
    # Calculate partial load and load
    load = 100 * Generator_energies.div(Generator_Nominal_Capacity, axis=1)
    partial_load = load.round(0)
    
    # Calculate lost load and energy curtailment for selected years
    lost = (Lost_Load_df.sum(axis=0) * 100 / Demand_df.sum(axis=0)).loc[years_selected]
    curt = (Energy_Curtailment_df.sum(axis=0) * 100 / Demand_df.sum(axis=0)).loc[years_selected]
    
    # Exporting data
    risultato = {
    'Battery_Outflow': Battery_Outflow_df,
    'Battery_Inflow': Battery_Inflow_df,
    'Energy_Curtailment': Energy_Curtailment_df,
    'Lost_Load': Lost_Load_df,
    'res': res_df,
    'Generator_Production': Generator_energies,
    'RES_Production': RES_Energy_Production_dfa,
    'Battery_SOC': Battery_SOC_df,
    'Partial_load': partial_load,
    'LL': lost,
    'CURT': curt
    }
    return  risultato