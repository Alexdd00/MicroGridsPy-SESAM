# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 15:44:40 2024

@author: aless
"""

from line_profiler import LineProfiler

#@profile
def Operation(params):

    import pandas as pd
    import numpy as np

    #Importing Data from params
    mode = params['mode']
    years = params['years']
    periods = params['Periods']
    index = pd.MultiIndex.from_product([range(years), range(periods)], names=['year', 'period'])
    
    Generator_Production_df = pd.DataFrame(params['Generator_Production'])
    RES_Energy_Production_dfa = pd.DataFrame(params['RES_Energy_Production'], index=index, columns=range(params['RES_Sources']))
    RES_Energy_Production_df = pd.DataFrame(0, index=index, columns=[0])
    
    Battery_SOC_df = pd.DataFrame(params['Battery_SOC'])
    Demand_df = pd.DataFrame(params['Demand'])
    for y in range(years):
        for t in range(periods):
            RES_Energy_Production_df.loc[(y,t),0] = sum((RES_Energy_Production_dfa.loc[(y,t),r]) for r in range(params['RES_Sources']))

    blocks = [RES_Energy_Production_df[i*periods:(i+1)*periods] for i in range(years)]

    RES_Energy_Production_df_reshaped = np.column_stack(blocks)
    RES_Energy_Production_dfu = pd.DataFrame(RES_Energy_Production_df_reshaped)

    Energy_Curtailment = [0]*len(params['RES_Energy_Production'])
    Lost_Load = [0]*len(params['RES_Energy_Production'])
    Maximum_Generator_Energy_1 = pd.DataFrame([[0]*params['n_generators'] for _ in range(len(params['RES_Energy_Production']))])
    Minimum_Generator_Energy = pd.DataFrame([[0]*params['n_generators'] for _ in range(len(params['RES_Energy_Production']))])
    Battery_Nominal_Capacity = params['Battery_Nominal_Capacity']
    Battery_Depth_of_Discharge = params['Battery_Depth_of_Discharge']
    Maximum_Battery_Charge_Time = params['Maximum_Battery_Charge_Time']
    Maximum_Battery_Discharge_Time = params['Maximum_Battery_Discharge_Time']
    Battery_Inflow1 = pd.DataFrame(params['Battery_Inflow'])
    Battery_Outflow1 = pd.DataFrame(params['Battery_Outflow'])
    Delta_Time = params['Delta_Time']
    n_generators = params['n_generators']
    Generator_Nominal_Capacity = params['Generator_Nominal_Capacity']
    res_columns = [f'RES{r+1}' for r in range(params['RES_Sources'])] + [f'Generator{i+1}' for i in range(n_generators)] + ['SOC','Lost_Load', 'Energy_Curtailment', 'Total_Energy_Production','Battery']
    res = pd.DataFrame(columns=res_columns)
    
    Degradation_BESS = params['Degradation_BESS']
    Battery_Initial_SOC = params['Battery_Initial_SOC']
    Battery_Iterative_Replacement = params['Battery_Iterative_Replacement']
    Battery_Replacement_Year = params['Battery_Replacement_Year']
    Energy_Curtailment = pd.DataFrame([[0]*years for _ in range(periods)])
    Lost_Load = pd.DataFrame([[0]*years for _ in range(periods)])
    Battery_Inflow = pd.DataFrame([[0]*years for _ in range(periods)])
    Battery_Outflow = pd.DataFrame([[0]*years for _ in range(periods)])
    Battery_Bank_Energy_Exchange = pd.DataFrame([[0]*years for _ in range(periods)])
    Battery_Bank_Energy = pd.DataFrame([[0]*years for _ in range(periods)])
    years_selected = params['years_selected']
    total_value = periods*years
    if Degradation_BESS==1:
        alpha = params['Alpha'][:total_value]
        beta = params['Beta'][:total_value]
        #index = pd.MultiIndex.from_product([range(years), range(periods)], names=['year', 'period'])

        array_alpha = np.array(alpha)
        array_beta = np.array(beta)

        array_reshaped_alpha = array_alpha.reshape(periods, years)
        array_reshaped_beta = array_beta.reshape(periods, years)

        alfa = pd.DataFrame(array_reshaped_alpha)
        bieta = pd.DataFrame(array_reshaped_beta)

    Generator_energies = pd.DataFrame(0, index=index, columns=range(n_generators))
    Battery_Inflow2 = pd.DataFrame([[0]*years for _ in range(periods)])
    Battery_Outflow2 = pd.DataFrame([[0]*years for _ in range(periods)])

    print('\nSimulating operation mode...')
    #print(mode)

    #Creation of constraints
    for y in range(years):
        
        for t in range(periods):
            
            if t==0 and y==0:
                Battery_Outflow.iloc[t,y] = Battery_Outflow1.iloc[t,y]
                Battery_Inflow.iloc[t,y] = Battery_Inflow1.iloc[t,y]
            if t==0 and y!=0:
                Battery_Outflow2.iloc[t,y] = Battery_Outflow.iloc[(periods-1),(y-1)]
                Battery_Inflow2.iloc[t,y] = Battery_Inflow.iloc[(periods-1),(y-1)]
                Battery_SOC_df.iloc[t,y] = Battery_SOC_df.iloc[(periods-1),(y-1)]
            if t != 0:
                Battery_Outflow2.iloc[t,y] = Battery_Outflow.iloc[(t-1),y]
                Battery_Inflow2.iloc[t,y] = Battery_Inflow.iloc[(t-1),y]
                Battery_SOC_df.iloc[t,y] = Battery_SOC_df.iloc[(t-1),y]


            if Degradation_BESS == 1:
                Battery_Bank_Energy_Exchange.iloc[t,y] = -Battery_Outflow2.iloc[t,y] + Battery_Inflow2.iloc[t,y] 
                
                if t == 0 and y == 0:
                    Battery_Bank_Energy.iloc[t,y] = ( Battery_Nominal_Capacity* Battery_Initial_SOC-(alfa.iloc[t,y]*  Battery_Bank_Energy.iloc[t,y]) -(bieta.iloc[t,y]*Battery_Bank_Energy_Exchange.iloc[t,y])) 
                if t != 0 and y == 0:
                    Battery_Bank_Energy.iloc[t,y] = ( Battery_Bank_Energy.iloc[(t-1),y]-(alfa.iloc[t,y]*Battery_Bank_Energy.iloc[(t-1),y])-(bieta.iloc[t,y]*Battery_Bank_Energy_Exchange.iloc[t,y]))
                if t == 0 and y != 0:
                    if   Battery_Iterative_Replacement == 1 and y ==  Battery_Replacement_Year:
                        Battery_Bank_Energy.iloc[t,y] =  Battery_Nominal_Capacity
                    else:
                        Battery_Bank_Energy.iloc[t,y] = ( Battery_Bank_Energy.iloc[(periods-1),(y-1)]-alfa.iloc[t,y]*  Battery_Bank_Energy.iloc[t,y] -bieta.iloc[t,y]*Battery_Bank_Energy_Exchange.iloc[t,y])
                if t !=0 and y != 0: 
                    Battery_Bank_Energy.iloc[t,y] = ( Battery_Bank_Energy.iloc[(t-1),y]-(alfa.iloc[t,y]*Battery_Bank_Energy.iloc[(t-1),y])-(bieta.iloc[t,y]*Battery_Bank_Energy_Exchange.iloc[t,y]))
                

            if Degradation_BESS == 1:
                Demand_higher_RES = Demand_df.iloc[t, y] > RES_Energy_Production_dfu.iloc[t, y]
                Demand_lower_RES = Demand_df.iloc[t,y] < RES_Energy_Production_dfu.iloc[t, y]
                Demand_equal_RES = Demand_df.iloc[t, y] == RES_Energy_Production_dfu.iloc[t, y]
                Minimum_Charge = Battery_SOC_df.iloc[t, y] >= Battery_Bank_Energy.iloc[t,y]*(1- Battery_Depth_of_Discharge) #Degradation
                if t==0:
                    Maximum_Charge = Battery_SOC_df.iloc[t, y] <= Battery_Bank_Energy.iloc[t,y]
                    Max_Power_Battery_Charge = Battery_Outflow2.iloc[t,y] ==  Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time #Degradation DA CONTROLLARE
                    Max_Power_Battery_Discharge = Battery_Inflow2.iloc[t,y] ==  Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Discharge_Time #Degradation DA CONTROLLARE TUTTI I t-1 PERCHè ORA 0 NON VALIDO
                    Max_Bat_in = Battery_Outflow2.iloc[t,y] <=  (Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time)* Delta_Time #Degradation DA CONTROLARE
                    Battery_Single_Flow_Discharge = Battery_Inflow2.iloc[t,y] <= (Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Discharge_Time)* Delta_Time
                if t!=0:
                    Maximum_Charge = Battery_SOC_df.iloc[t, y] <= Battery_Bank_Energy.iloc[(t-1),y] #Degradation
                    Max_Power_Battery_Charge = Battery_Outflow2.iloc[t,y] ==  Battery_Bank_Energy.iloc[(t-1),y]/ Maximum_Battery_Charge_Time #Degradation DA CONTROLLARE
                    Max_Power_Battery_Discharge = Battery_Inflow2.iloc[t,y] ==  Battery_Bank_Energy.iloc[(t-1),y]/ Maximum_Battery_Discharge_Time #Degradation DA CONTROLLARE TUTTI I t-1 PERCHè ORA 0 NON VALIDO
                    Max_Bat_in = Battery_Outflow2.iloc[t,y] <=  (Battery_Bank_Energy.iloc[(t-1),y]/ Maximum_Battery_Charge_Time)* Delta_Time #Degradation DA CONTROLARE
                    Battery_Single_Flow_Discharge = Battery_Inflow2.iloc[t,y] <= (Battery_Bank_Energy.iloc[(t-1),y]/ Maximum_Battery_Discharge_Time)* Delta_Time #Degradation 
                Full_batt = Battery_SOC_df.iloc[t, y] <= Battery_Bank_Energy.iloc[t,y]*(1- Battery_Depth_of_Discharge) #Degradation
                Full_batt2 = Battery_SOC_df.iloc[t, y] >= (Battery_Bank_Energy.iloc[t,y] - 0.2) #Degradation 
                Max_Bat_out = Battery_Inflow2.iloc[t,y] <=  Demand_df.iloc[t,y]
                Battery_Single_Flow_Charge = Battery_Outflow2.iloc[t,y] <= 0

            if Degradation_BESS == 0:
                Demand_higher_RES = Demand_df.iloc[t, y] > RES_Energy_Production_dfu.iloc[t, y]
                Demand_lower_RES = Demand_df.iloc[t,y] < RES_Energy_Production_dfu.iloc[t, y]
                Demand_equal_RES = Demand_df.iloc[t, y] == RES_Energy_Production_dfu.iloc[t, y]
                Minimum_Charge = Battery_SOC_df.iloc[t, y] >= Battery_Nominal_Capacity*(1- Battery_Depth_of_Discharge) #Degradation
                Maximum_Charge = Battery_SOC_df.iloc[t, y] <= Battery_Nominal_Capacity #Degradation
                Full_batt = Battery_SOC_df.iloc[t, y] <= Battery_Nominal_Capacity*(1- Battery_Depth_of_Discharge) #Degradation
                Full_batt2 = Battery_SOC_df.iloc[t, y] >= Battery_Nominal_Capacity #Degradation
                Max_Power_Battery_Charge = Battery_Outflow.iloc[t,y] ==  Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time #Degradation
                Max_Power_Battery_Discharge = Battery_Inflow.iloc[t,y] ==  Battery_Nominal_Capacity/ Maximum_Battery_Discharge_Time #Degradation
                Max_Bat_in = Battery_Outflow.iloc[t,y] <=  (Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time)* Delta_Time #Degradation
                Max_Bat_out = Battery_Inflow.iloc[t,y] <=  Demand_df.iloc[t,y]
                Battery_Single_Flow_Discharge = Battery_Inflow.iloc[t,y] <= (Battery_Nominal_Capacity/ Maximum_Battery_Discharge_Time)* Delta_Time #Degradation
                Battery_Single_Flow_Charge = Battery_Outflow.iloc[t,y] <= 0

            for g in range(n_generators):
                Maximum_Generator_Energy_1.iloc[t,g] = Generator_Production_df.iloc[t,g] <=  Generator_Nominal_Capacity[g]* Delta_Time 
                Minimum_Generator_Energy.iloc[t,g] = Generator_Production_df.iloc[t,g] >= 0

            
            #Simulation core Cycle Charging
            if mode == 1:
                if Demand_equal_RES:
                    res_row = {'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': 0, 'Energy_Curtailment': 0, 'Total_Energy_Production': RES_Energy_Production_dfu.iloc[t, y], 'Battery': Battery_SOC_df.iloc[t,y]}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    for g in range(n_generators):
                        res_row[f'Generator{g+1}'] = 0
                    res = res.append(res_row, ignore_index=True)
                
                    
                elif Demand_higher_RES and Minimum_Charge and Maximum_Charge and (Max_Power_Battery_Discharge or Max_Bat_out or Battery_Single_Flow_Discharge):
                    if Degradation_BESS == 1:
                        if ((Demand_df.iloc[t,y] - RES_Energy_Production_dfu.iloc[t, y]) > (Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Discharge_Time)) and (Battery_SOC_df.iloc[t,y] > (Battery_Bank_Energy.iloc[t,y]*(1- Battery_Depth_of_Discharge)+(Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Discharge_Time))) :
                            Battery_Inflow.iloc[t,y] = Battery_Bank_Energy.iloc[t,y]/Maximum_Battery_Discharge_Time
                        else:
                            Battery_Inflow.iloc[t,y] = min((Demand_df.iloc[t,y]-RES_Energy_Production_dfu.iloc[t, y]), (Battery_SOC_df.iloc[t,y]-(Battery_Bank_Energy.iloc[t,y]*(1- Battery_Depth_of_Discharge))))
                        Battery_SOC_df.iloc[t,y] = max(Battery_SOC_df.iloc[t,y] - Battery_Inflow.iloc[t,y], (Battery_Bank_Energy.iloc[t,y]*(1- Battery_Depth_of_Discharge)))
                        
                    if Degradation_BESS == 0:
                        if ((Demand_df.iloc[t,y] - RES_Energy_Production_dfu.iloc[t, y]) > (Battery_Nominal_Capacity/ Maximum_Battery_Discharge_Time)) and (Battery_SOC_df.iloc[t,y] > (Battery_Nominal_Capacity*(1- Battery_Depth_of_Discharge)+(Battery_Nominal_Capacity/ Maximum_Battery_Discharge_Time))) :
                            Battery_Inflow.iloc[t,y] = Battery_Nominal_Capacity/Maximum_Battery_Discharge_Time
                        else:
                            Battery_Inflow.iloc[t,y] = min((Demand_df.iloc[t,y]-RES_Energy_Production_dfu.iloc[t, y]), (Battery_SOC_df.iloc[t,y]-(Battery_Nominal_Capacity*(1- Battery_Depth_of_Discharge))))
                        Battery_SOC_df.iloc[t,y] = max(Battery_SOC_df.iloc[t,y] - Battery_Inflow.iloc[t,y], (Battery_Nominal_Capacity*(1- Battery_Depth_of_Discharge)))
                    res_energy = (RES_Energy_Production_dfu.iloc[t, y] + Battery_Inflow.iloc[t,y])
                    #DA QUA INIZIA LA PARTE DI CYCLE CHARGING
                    if (res_energy - Demand_df.iloc[t,y]) < (-0.1) or Full_batt:   #res_energy < Demand_df.iloc[t,y] IL PROBLEMA è LA TOLLERANZA, ora messa a 0.1 però devo stringere di più forse , metto tolleranza a 1 watt
                        for g in range(n_generators):

                            Generator_Production = (Generator_Production_df.iloc[t,g])
                            
                            res_energy += Generator_Production
                            Generator_energies.loc[(y,t),g] = Generator_Production
                            if res_energy > Demand_df.iloc[t,y]:  #QUA DEVO AGGIUNGERE LE BATTERIE CHE SI RICARICANO
                                if Degradation_BESS == 1:
                                   if ((res_energy - Demand_df.iloc[t,y]) > (Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time)) and (Battery_SOC_df.iloc[t,y] < (Battery_Bank_Energy.iloc[t,y]-(Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time))) :
                                      Battery_Outflow.iloc[t,y] = Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time
                                   else:    
                                        Battery_Outflow.iloc[t,y] = min((res_energy - Demand_df.iloc[t,y]), (Battery_Bank_Energy.iloc[t,y]-Battery_SOC_df.iloc[t,y]))
                                   Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow.iloc[t,y],Battery_Bank_Energy.iloc[t,y])
                                if Degradation_BESS == 0:
                                   if ((res_energy - Demand_df.iloc[t,y]) > (Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time)) and (Battery_SOC_df.iloc[t,y] < (Battery_Nominal_Capacity-(Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time))) :
                                      Battery_Outflow.iloc[t,y] = Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time
                                   else:    
                                      Battery_Outflow.iloc[t,y] = min((res_energy - Demand_df.iloc[t,y]), (Battery_Nominal_Capacity-Battery_SOC_df.iloc[t,y]))
                                   Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow.iloc[t,y],Battery_Nominal_Capacity)
                                res_energy -= Battery_Outflow.iloc[t,y]
                                    # if res_energy > Demand_df.iloc[t,y] or Full_batt2:
                                    #     Energy_Curtailment.iloc[t,y] = res_energy - Demand_df.iloc[t,y]
                                    #     res_energy -= Energy_Curtailment.iloc[t,y]
                                if res_energy > Demand_df.iloc[t,y] or Full_batt2:
                                    Generator_Produ = res_energy - Demand_df.iloc[t,y]
                                    Generator_Production -= Generator_Produ
                                    res_energy -= Generator_Produ
                                    Generator_energies.loc[(y,t),g] = Generator_Production
                                res_row = {'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': 0, 'Energy_Curtailment': Energy_Curtailment.iloc[t,y], 'Total_Energy_Production': res_energy, 'Battery': -Battery_Outflow.iloc[t,y]}
                                for r in range(params['RES_Sources']):
                                    res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                                for g in range(n_generators):
                                    res_row[f'Generator{g+1}'] = 0
                                res = res.append(res_row, ignore_index=True)
                                break         

                        if res_energy < Demand_df.iloc[t,y]:
                            Lost_Load.iloc[t,y] = max(Demand_df.iloc[t,y]-res_energy, 0)
                            res_energy += Lost_Load.iloc[t,y]
                    res_row={'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': Lost_Load.iloc[t,y], 'Energy_Curtailment': 0, 'Total_Energy_Production': res_energy, 'Battery':Battery_Inflow.iloc[t,y]}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    for g in range(n_generators):
                        res_row[f'Generator{g+1}'] = Generator_energies.loc[(y,t),g]
                    res = res.append(res_row, ignore_index=True)
                
                elif Demand_higher_RES and Full_batt:
                    Lost_Load.iloc[t,y] = Demand_df.iloc[t, y] - RES_Energy_Production_dfu.iloc[t, y]
                    res_energy += Lost_Load.iloc[t,y]
                    res_row={'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': Lost_Load.iloc[t,y], 'Energy_Curtailment': 0, 'Total_Energy_Production': res_energy, 'Battery':0}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    res = res.append(res_row, ignore_index=True)
                    
                elif Demand_lower_RES and Full_batt2:
                    if Degradation_BESS == 1:
                        Battery_Outflow.iloc[t,y] = min((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]), (Battery_Bank_Energy.iloc[t,y]-Battery_SOC_df.iloc[t,y]))
                        Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow.iloc[t,y],Battery_Bank_Energy.iloc[t,y])
                    if Degradation_BESS == 0:
                        Battery_Outflow.iloc[t,y] = min((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]), (Battery_Nominal_Capacity-Battery_SOC_df.iloc[t,y]))
                        Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow.iloc[t,y],Battery_Nominal_Capacity)
                    res_energy = RES_Energy_Production_dfu.iloc[t, y]
                    Energy_Curtailment.iloc[t,y] = RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]
                    res_energy -= Energy_Curtailment.iloc[t,y]
                    res_row = {'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': 0, 'Energy_Curtailment': Energy_Curtailment.iloc[t,y], 'Total_Energy_Production': res_energy, 'Battery': 0}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                        for g in range(n_generators):
                            res_row[f'Generator{g+1}'] = 0
                    res = res.append(res_row, ignore_index=True)
                    
                elif Demand_lower_RES and Minimum_Charge and Maximum_Charge and (Max_Power_Battery_Charge or Max_Bat_in or Battery_Single_Flow_Charge):
                    if Degradation_BESS == 1:
                        if ((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]) > (Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time)) and (Battery_SOC_df.iloc[t,y] < (Battery_Bank_Energy.iloc[t,y]-(Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time))) :
                            Battery_Outflow.iloc[t,y] = Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time
                        else:    
                            Battery_Outflow.iloc[t,y] = min((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]), (Battery_Bank_Energy.iloc[t,y]-Battery_SOC_df.iloc[t,y]))
                        Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow.iloc[t,y],Battery_Bank_Energy.iloc[t,y])
                    if Degradation_BESS == 0:
                        if ((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]) > (Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time)) and (Battery_SOC_df.iloc[t,y] < (Battery_Nominal_Capacity-(Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time))) :
                            Battery_Outflow.iloc[t,y] = Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time
                        else:    
                            Battery_Outflow.iloc[t,y] = min((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]), (Battery_Nominal_Capacity-Battery_SOC_df.iloc[t,y]))
                        Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow.iloc[t,y],Battery_Nominal_Capacity)
                    res_energy = (RES_Energy_Production_dfu.iloc[t, y] - Battery_Outflow.iloc[t,y])
                    if res_energy > Demand_df.iloc[t,y] or Full_batt2:
                        Energy_Curtailment.iloc[t,y] = res_energy - Demand_df.iloc[t,y]
                        res_energy -= Energy_Curtailment.iloc[t,y]
                    res_row = {'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': 0, 'Energy_Curtailment': Energy_Curtailment.iloc[t,y], 'Total_Energy_Production': res_energy, 'Battery': -Battery_Outflow.iloc[t,y]}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    for g in range(n_generators):
                        res_row[f'Generator{g+1}'] = 0
                    res = res.append(res_row, ignore_index=True)
                    
                else:
                    res_row = {'SOC': 0, 'Lost_Load': 0, 'Energy_Curtailment': 0, 'Total_Energy_Production': Demand_df.iloc[t,y], 'Battery': 'Error'}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    res = res.append(res_row, ignore_index=True)
                    print('errore: nessun caso valido')
                



            #Simulation core Load Following
            if mode == 0:
                if Demand_equal_RES:
                    res_row = {'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': 0, 'Energy_Curtailment': 0, 'Total_Energy_Production': RES_Energy_Production_dfu.iloc[t, y], 'Battery': Battery_SOC_df.iloc[t,y]}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    for g in range(n_generators):
                        res_row[f'Generator{g+1}'] = 0
                    res = res.append(res_row, ignore_index=True)
                
                    
                elif Demand_higher_RES and Minimum_Charge and Maximum_Charge and (Max_Power_Battery_Discharge or Max_Bat_out or Battery_Single_Flow_Discharge):
                    if Degradation_BESS == 1:
                        if ((Demand_df.iloc[t,y] - RES_Energy_Production_dfu.iloc[t, y]) > (Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Discharge_Time)) and (Battery_SOC_df.iloc[t,y] > (Battery_Bank_Energy.iloc[t,y]*(1- Battery_Depth_of_Discharge)+(Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Discharge_Time))) :
                            Battery_Inflow.iloc[t,y] = Battery_Bank_Energy.iloc[t,y]/Maximum_Battery_Discharge_Time
                        else:
                            Battery_Inflow.iloc[t,y] = min((Demand_df.iloc[t,y]-RES_Energy_Production_dfu.iloc[t, y]), (Battery_SOC_df.iloc[t,y]-(Battery_Bank_Energy.iloc[t,y]*(1- Battery_Depth_of_Discharge))))
                        Battery_SOC_df.iloc[t,y] = max(Battery_SOC_df.iloc[t,y] - Battery_Inflow.iloc[t,y], (Battery_Bank_Energy.iloc[t,y]*(1- Battery_Depth_of_Discharge)))
                        
                    if Degradation_BESS == 0:
                        if ((Demand_df.iloc[t,y] - RES_Energy_Production_dfu.iloc[t, y]) > (Battery_Nominal_Capacity/ Maximum_Battery_Discharge_Time)) and (Battery_SOC_df.iloc[t,y] > (Battery_Nominal_Capacity*(1- Battery_Depth_of_Discharge)+(Battery_Nominal_Capacity/ Maximum_Battery_Discharge_Time))) :
                            Battery_Inflow.iloc[t,y] = Battery_Nominal_Capacity/Maximum_Battery_Discharge_Time
                        else:
                            Battery_Inflow.iloc[t,y] = min((Demand_df.iloc[t,y]-RES_Energy_Production_dfu.iloc[t, y]), (Battery_SOC_df.iloc[t,y]-(Battery_Nominal_Capacity*(1- Battery_Depth_of_Discharge))))
                        Battery_SOC_df.iloc[t,y] = max(Battery_SOC_df.iloc[t,y] - Battery_Inflow.iloc[t,y], (Battery_Nominal_Capacity*(1- Battery_Depth_of_Discharge)))
                    res_energy = (RES_Energy_Production_dfu.iloc[t, y] + Battery_Inflow.iloc[t,y])
                    if res_energy < Demand_df.iloc[t,y] or Full_batt:
                        for g in range(n_generators):
                            Generator_Production = min(Demand_df.iloc[t, y] - res_energy, Generator_Production_df.iloc[t, g])
                            res_energy += Generator_Production
                            Generator_energies.loc[(y,t),g] = Generator_Production
                            if res_energy >= Demand_df.iloc[t,y]:
                                break

                        if res_energy < Demand_df.iloc[t,y]:
                            Lost_Load.iloc[t,y] = max(Demand_df.iloc[t,y]-res_energy, 0)
                            res_energy += Lost_Load.iloc[t,y]
                    res_row={'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': Lost_Load.iloc[t,y], 'Energy_Curtailment': 0, 'Total_Energy_Production': res_energy, 'Battery':Battery_Inflow.iloc[t,y]}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    for g in range(n_generators):
                        res_row[f'Generator{g+1}'] = Generator_energies.loc[(y,t),g]
                    res = res.append(res_row, ignore_index=True)
                
                elif Demand_higher_RES and Full_batt:
                    Lost_Load.iloc[t,y] = Demand_df.iloc[t, y] - RES_Energy_Production_dfu.iloc[t, y]
                    res_energy += Lost_Load.iloc[t,y]
                    res_row={'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': Lost_Load.iloc[t,y], 'Energy_Curtailment': 0, 'Total_Energy_Production': res_energy, 'Battery':0}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    res = res.append(res_row, ignore_index=True)
                    
                elif Demand_lower_RES and Full_batt2:
                    if Degradation_BESS == 1:
                        Battery_Outflow.iloc[t,y] = min((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]), (Battery_Bank_Energy.iloc[t,y]-Battery_SOC_df.iloc[t,y]))
                        Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow.iloc[t,y],Battery_Bank_Energy.iloc[t,y])
                    if Degradation_BESS == 0:
                        Battery_Outflow.iloc[t,y] = min((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]), (Battery_Nominal_Capacity-Battery_SOC_df.iloc[t,y]))
                        Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow.iloc[t,y],Battery_Nominal_Capacity)
                    res_energy = RES_Energy_Production_dfu.iloc[t, y]
                    Energy_Curtailment.iloc[t,y] = RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]
                    res_energy -= Energy_Curtailment.iloc[t,y]
                    res_row = {'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': 0, 'Energy_Curtailment': Energy_Curtailment.iloc[t,y], 'Total_Energy_Production': res_energy, 'Battery': 0}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                        for g in range(n_generators):
                            res_row[f'Generator{g+1}'] = 0
                    res = res.append(res_row, ignore_index=True)
                    
                elif Demand_lower_RES and Minimum_Charge and Maximum_Charge and (Max_Power_Battery_Charge or Max_Bat_in or Battery_Single_Flow_Charge):
                    if Degradation_BESS == 1:
                        if ((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]) > (Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time)) and (Battery_SOC_df.iloc[t,y] < (Battery_Bank_Energy.iloc[t,y]-(Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time))) :
                            Battery_Outflow.iloc[t,y] = Battery_Bank_Energy.iloc[t,y]/ Maximum_Battery_Charge_Time
                        else:    
                            Battery_Outflow.iloc[t,y] = min((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]), (Battery_Bank_Energy.iloc[t,y]-Battery_SOC_df.iloc[t,y]))
                        Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow.iloc[t,y],Battery_Bank_Energy.iloc[t,y])
                    if Degradation_BESS == 0:
                        if ((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]) > (Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time)) and (Battery_SOC_df.iloc[t,y] < (Battery_Nominal_Capacity-(Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time))) :
                            Battery_Outflow.iloc[t,y] = Battery_Nominal_Capacity/ Maximum_Battery_Charge_Time
                        else:    
                            Battery_Outflow.iloc[t,y] = min((RES_Energy_Production_dfu.iloc[t, y] - Demand_df.iloc[t,y]), (Battery_Nominal_Capacity-Battery_SOC_df.iloc[t,y]))
                        Battery_SOC_df.iloc[t,y] = min(Battery_SOC_df.iloc[t,y] + Battery_Outflow.iloc[t,y],Battery_Nominal_Capacity)
                    res_energy = (RES_Energy_Production_dfu.iloc[t, y] - Battery_Outflow.iloc[t,y])
                    if res_energy > Demand_df.iloc[t,y] or Full_batt2:
                        Energy_Curtailment.iloc[t,y] = res_energy - Demand_df.iloc[t,y]
                        res_energy -= Energy_Curtailment.iloc[t,y]
                    res_row = {'SOC':Battery_SOC_df.iloc[t,y], 'Lost_Load': 0, 'Energy_Curtailment': Energy_Curtailment.iloc[t,y], 'Total_Energy_Production': res_energy, 'Battery': -Battery_Outflow.iloc[t,y]}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    for g in range(n_generators):
                        res_row[f'Generator{g+1}'] = 0
                    res = res.append(res_row, ignore_index=True)
                    
                else:
                    res_row = {'SOC': 0, 'Lost_Load': 0, 'Energy_Curtailment': 0, 'Total_Energy_Production': Demand_df.iloc[t,y], 'Battery': 'Error'}
                    for r in range(params['RES_Sources']):
                        res_row[f'RES{r+1}'] = RES_Energy_Production_dfa.loc[(y,t),r]
                    res = res.append(res_row, ignore_index=True)
                    print('errore: nessun caso valido')
                
            ...
    
    #res_df = pd.DataFrame(res)
    #Battery_Outflow_df = pd.DataFrame(Battery_Outflow) 
    #Battery_Bank_Energy_df = pd.DataFrame(Battery_Bank_Energy)
    
    
    #Energy_Curtailment_df = pd.DataFrame(Energy_Curtailment)
    #Lost_Load_df = pd.DataFrame(Lost_Load)
    #Battery_Inflow_df = pd.DataFrame(Battery_Inflow) 
    #Battery_SOC_dfa = pd.DataFrame(Battery_SOC_df)
    
    #index = pd.MultiIndex.from_product([range(years), range(periods)], names=['year', 'period'])

    partial_load = pd.DataFrame(0, index=index, columns=range(n_generators))
    load = pd.DataFrame(0, index=index, columns=range(n_generators))
    for y in range(years):
        for t in range(periods):
            for g in range(n_generators):
                load.loc[(y,t),g] = 100*Generator_energies.loc[(y,t),g]/(Generator_Nominal_Capacity[g])
                partial_load.loc[(y,t),g] = load.loc[(y,t),g].round(0)

    for y in range(years):
        if y==years_selected:
            lost= sum(Lost_Load.iloc[t,y] for t in range(periods))*100/sum(Demand_df.iloc[t,y] for t in range(periods))
            curt= sum(Energy_Curtailment.iloc[t,y] for t in range(periods))*100/sum(Demand_df.iloc[t,y] for t in range(periods))
    
    #Exporting data
    risultato={
        'Battery_Outflow':Battery_Outflow,
        'Battery_Inflow':Battery_Inflow,
        'Energy_Curtailment':Energy_Curtailment,
        'Lost_Load':Lost_Load,
        'res':res,
        'Generator_Production':Generator_energies,
        'RES_Production':RES_Energy_Production_dfa,
        'Battery_SOC': Battery_SOC_df,
        'Partial_load': partial_load,
        'LL': lost,
        'CURT': curt
    }
    return  risultato
