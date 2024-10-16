# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 15:44:40 2024

@author: aless
"""



def PrintResults(Costs, risultato, Results, params):
    import pandas as pd

    Net_Present_Cost = pd.DataFrame(Costs['Net_Present_Cost_result'])
    Operation_Cost = pd.DataFrame(Costs['Operation_Cost_result'])
    LCOE = pd.DataFrame(Costs['lcoe_result'])
    year_selected = params['years_selected']

    if year_selected in Net_Present_Cost.index:
        npc = Net_Present_Cost.loc[year_selected].values
        npc = round(npc[0],2)
        print(f'\nNPC = {npc} USD')

    if year_selected in Operation_Cost.index:
        operation_cost = Operation_Cost.loc[year_selected].values
        operation_cost = round(operation_cost[0],2)
        print(f'Total Operation Cost = {operation_cost} USD')

    if year_selected in LCOE.index:
        lcoe = LCOE.loc[year_selected].values
        lcoe = round(lcoe[0],2)
        print(f'LCOE = {lcoe} USD/MWh')
        
        lost_load = float(risultato['LL'])
        lost_load = round(lost_load,2)
        print(f'Lost load = {lost_load} %')

        curtailment = float(risultato['CURT'])
        curtailment = round(curtailment,2)
        print(f'Energy curtailment = {curtailment} %')

    # renewable_penetration=float(Results['Renewable Penetration'].iloc[0,0])
    # print(f'Renewable Penetration = {round(renewable_penetration,2)} %')
    print("\n-----------------------------------------------------------------------------")


def ResultsSummary(params, Costs, emissioni, TimeSeries): 
    
    import os
    import pandas as pd
    
    print('Results: exporting economic results .')
    EnergySystemCost1                              = EnergySystemCost(params, Costs, emissioni)
    
    print('         exporting technical results .')
    EnergySystemSize1                              = EnergySystemSize(params)
    EnergyParams1, Renewable_Penetration           = EnergyParams(TimeSeries,params)

    current_directory = os.path.dirname(os.path.abspath(__file__))
    results_directory = os.path.join(os.path.dirname(current_directory),'Results', 'Results Summary.xlsx')

    results_folder = os.path.dirname(results_directory)
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    #Saving results    
    with pd.ExcelWriter(results_directory, engine='openpyxl') as writer:

        EnergySystemSize1.to_excel(writer, sheet_name='Size')
        EnergySystemCost1.to_excel(writer, sheet_name='Cost')
        Renewable_Penetration.to_excel(writer, sheet_name='Renewable_Penetration')
        EnergyParams1.to_excel(writer, sheet_name='Energy_parameters')


    Results = {
        'Costs': EnergySystemCost1,
        'Size': EnergySystemSize1,
        'Energy Parameters': EnergyParams1,
        'Renewable Penetration': Renewable_Penetration
    }
    
    return Results

def EnergyParams(TimeSeries, params):

    import pandas as pd
    
    #Importing parameters

    idx = pd.IndexSlice
    years = params['years']
    
    # Data preparation
    gen_load  = pd.DataFrame( columns=['Generators share','Value'])
    res_load  = pd.DataFrame( columns=['Renewable share','Value'])
    lost_load = pd.DataFrame( columns=['Lost load share','Value'])
    curt_load = pd.DataFrame( columns=['Curtailment share','Value'])
    res_pen   = pd.DataFrame( columns=['Renewables penetration','Value'])
    battery_usage = pd.DataFrame( columns=['Battery usage','Value'])  
    GEN_LOAD_over_years= pd.DataFrame()
    RES_LOAD_over_years= pd.DataFrame()
    LOST_LOAD_over_years= pd.DataFrame()
    CURT_LOAD_over_years= pd.DataFrame()
    RES_PEN_over_years= pd.DataFrame()
    BATTERY_USAGE_over_years= pd.DataFrame()
    for y in range(years):
        demand = 0
        curtailment = 0
        lost_load = 0
        renewables  = 0
        generators  = 0
        battery_out = 0
        demand += TimeSeries[y].loc[:,idx['Electric Demand',:,:]].sum().sum()  
        curtailment += TimeSeries[y].loc[:,idx['Curtailment',:,:]].sum().sum() 
        lost_load += TimeSeries[y].loc[:,idx['Lost Load',:,:]].sum().sum() 
        renewables  += TimeSeries[y].loc[:,idx['RES Production',:,:]].sum().sum() 
        generators  += TimeSeries[y].loc[:,idx['Generator Production',:,:]].sum().sum() 
        battery_out += TimeSeries[y].loc[:,idx['Battery Discharge',:,:]].sum().sum() 

        #Calculation
        GEN_LOAD = pd.DataFrame()
        gen_load  = pd.DataFrame([[ (generators/demand)*100]], columns=[ 'Generators share [%]']).T
        GEN_LOAD = pd.concat([GEN_LOAD, gen_load], axis=1).fillna(0)
        GEN_LOAD = GEN_LOAD.groupby(level=[0], axis=1, sort=False).sum()
        GEN_LOAD.columns= [f'Year {y}']
        GEN_LOAD_over_years = pd.concat([GEN_LOAD_over_years, GEN_LOAD], axis=1)

        RES_LOAD = pd.DataFrame()
        res_load  = pd.DataFrame([[ ((renewables-curtailment)/demand)*100]], columns=[ 'Renewable share [%]']).T
        RES_LOAD = pd.concat([RES_LOAD, res_load], axis=1).fillna(0)
        RES_LOAD = RES_LOAD.groupby(level=[0], axis=1, sort=False).sum()
        RES_LOAD.columns= [f'Year {y}']
        RES_LOAD_over_years = pd.concat([RES_LOAD_over_years, RES_LOAD], axis=1)

        CURT_LOAD = pd.DataFrame()
        curt_load = pd.DataFrame([[ (curtailment/(generators+renewables))*100]], columns=[ 'Curtailment share [%]']).T
        CURT_LOAD = pd.concat([CURT_LOAD, curt_load], axis=1).fillna(0)
        CURT_LOAD = CURT_LOAD.groupby(level=[0], axis=1, sort=False).sum()
        CURT_LOAD.columns= [f'Year {y}']
        CURT_LOAD_over_years = pd.concat([CURT_LOAD_over_years, CURT_LOAD], axis=1)

        LOST_LOAD = pd.DataFrame()
        lost_load = pd.DataFrame([[ (lost_load/demand)*100]], columns=[ 'Lost load share [%]']).T
        LOST_LOAD = pd.concat([LOST_LOAD, lost_load], axis=1).fillna(0)
        LOST_LOAD = LOST_LOAD.groupby(level=[0], axis=1, sort=False).sum()
        LOST_LOAD.columns= [f'Year {y}']
        LOST_LOAD_over_years = pd.concat([LOST_LOAD_over_years, LOST_LOAD], axis=1)

        RES_PEN = pd.DataFrame()
        res_pen   = pd.DataFrame([[(renewables/(renewables+generators))*100]], columns=[ 'Renewables penetration [%]']).T
        RES_PEN = pd.concat([RES_PEN, res_pen], axis=1).fillna(0)
        RES_PEN = RES_PEN.groupby(level=[0], axis=1, sort=False).sum()
        RES_PEN.columns= [f'Year {y}']
        RES_PEN_over_years = pd.concat([RES_PEN_over_years, RES_PEN], axis=1)

        BATTERY_USAGE = pd.DataFrame()
        battery_usage = pd.DataFrame([[ (battery_out/demand)*100]], columns=[ 'Battery usage [%]']).T
        BATTERY_USAGE = pd.concat([BATTERY_USAGE, battery_usage], axis=1).fillna(0)
        BATTERY_USAGE = BATTERY_USAGE.groupby(level=[0], axis=1, sort=False).sum()
        BATTERY_USAGE.columns= [f'Year {y}']
        BATTERY_USAGE_over_years = pd.concat([BATTERY_USAGE_over_years, BATTERY_USAGE], axis=1)
    
    # Concatenating
    EnergyParams = pd.concat([round(GEN_LOAD_over_years.astype(float),2),
                                round(RES_LOAD_over_years.astype(float),2),
                                round(RES_PEN_over_years.astype(float),2),
                                round(LOST_LOAD_over_years.astype(float),2),
                                round(CURT_LOAD_over_years.astype(float),2),
                                round(BATTERY_USAGE_over_years.astype(float),2)], axis=0)          

    return EnergyParams, RES_PEN_over_years

def EnergySystemCost(params, Costs, emissioni):

    import pandas as pd

    # Importing parameters
    Demand_df = pd.DataFrame(params['Demand'])
    periods = params['Periods']
    n_generators = (params['n_generators'])
    RES_Nominal_Capacity = pd.DataFrame(params['RES_Capacity'])
    RES_Specific_Investment_Cost = pd.DataFrame(params['RES_Investment'])
    RES_Specific_OM_Cost = pd.DataFrame(params['RES_OM'])
    Generator_Nominal_Capacity = pd.DataFrame(params['Generator_Nominal_Capacity'])
    Generator_Specific_Investment_Cost = pd.DataFrame(params['Generator_Investment'])
    Generator_Specific_OM_Cost = pd.DataFrame(params['Generator_OM'])
    Battery_Nominal_Capacity = params['Battery_Nominal_Capacity']
    Battery_Specific_Investment_Cost = params['Battery_Investment']
    Battery_Specific_OM_Cost = params['Battery_OM']
    RES_Names = pd.DataFrame(params['RES_names'])
    Generator_Names = pd.DataFrame(params['Generator_names'])
    Fuel_Names = pd.DataFrame(params['Fuel_names'])
    years = params['years']
    Net_Present_Cost_value = pd.DataFrame(Costs['Net_Present_Cost'])
    Operation_Maintenance_Cost = float(Costs['Operation_Cost'])
    Battery_Replacement_Cost = pd.DataFrame(Costs['Battery_Cost'])
    Lost_Load_Cost = pd.DataFrame(Costs['Lost_Load_Cost'])
    Total_Fuel_Cost = pd.DataFrame(Costs['Total_Fuel_Cost_Specific'])
    FUEL_emission = pd.DataFrame(emissioni['Fuel_emission'])
    CO2_emission = pd.DataFrame(emissioni['CO2_emission'])
    RES_emission_value = float(emissioni['RES_emission'])
    GEN_emission_value = float(emissioni['GEN_emission'])
    BESS_emission_value = float(emissioni['BESS_emission'])
    RES_Fixed_Costs_over_years = pd.DataFrame()
    BESS_Fixed_Costs_over_years = pd.DataFrame()
    Generator_Fixed_Costs_over_years = pd.DataFrame()
    Fixed_Costs_over_years = pd.DataFrame()
    Variable_Costs_over_years = pd.DataFrame()
    BESS_Replacement_Costs_over_years = pd.DataFrame()
    Fuel_Costs_over_years = pd.DataFrame()
    LostLoad_Costs_over_years = pd.DataFrame()
    CO2_out_over_years = pd.DataFrame()
    CO2_fuel_over_years = pd.DataFrame()
    RES_emission_over_years = pd.DataFrame()
    GEN_emission_over_years = pd.DataFrame()
    BESS_emission_over_years = pd.DataFrame()
    NPC_over_years = pd.DataFrame()
    LCOE_over_years = pd.DataFrame()

    RES_Names = RES_Names.transpose() 
    RES_Nominal_Capacity = RES_Nominal_Capacity.transpose()
    RES_Specific_Investment_Cost = RES_Specific_Investment_Cost.transpose()
    RES_Specific_OM_Cost = RES_Specific_OM_Cost.transpose()
    Generator_Names = Generator_Names.transpose()
    Generator_Nominal_Capacity = Generator_Nominal_Capacity.transpose()
    Generator_Specific_Investment_Cost = Generator_Specific_Investment_Cost.transpose()
    Generator_Specific_OM_Cost = Generator_Specific_OM_Cost.transpose()
    Fuel_Names = Fuel_Names.transpose()

    for y in range(years):

        "Renewable sources"    
        RES_Fixed_Cost = pd.DataFrame()
        for r in range(params['RES_Sources']):
            r_fc = 0
            r_fc += RES_Nominal_Capacity.iloc[0,r]*RES_Specific_Investment_Cost.iloc[0,r]*RES_Specific_OM_Cost.iloc[0,r]
            res_fc = pd.DataFrame([['Fixed cost', RES_Names.iloc[0,r], 'kUSD', r_fc/1e3]], columns=['Cost item', 'Component', 'Unit', f'Year {y}']).set_index(['Cost item', 'Component', 'Unit']) 
            RES_Fixed_Cost = pd.concat([RES_Fixed_Cost, res_fc], axis=1).fillna(0)
        RES_Fixed_Cost = RES_Fixed_Cost.groupby(level=[0], axis=1, sort=False).sum()
        RES_Fixed_Costs_over_years = pd.concat([RES_Fixed_Costs_over_years, RES_Fixed_Cost], axis=1)

        "Battery bank"
        BESS_Fixed_Cost = pd.DataFrame()
        b_fc = 0
        b_fc += Battery_Nominal_Capacity*Battery_Specific_Investment_Cost*Battery_Specific_OM_Cost
        bess_fc = pd.DataFrame([['Fixed cost', 'Battery bank', 'kUSD', b_fc/1e3]], columns=['Cost item', 'Component', 'Unit', f'Year {y}']).set_index(['Cost item', 'Component', 'Unit']) 
        BESS_Fixed_Cost = pd.concat([BESS_Fixed_Cost, bess_fc], axis=1).fillna(0) 
        BESS_Fixed_Cost = BESS_Fixed_Cost.groupby(level=[0], axis=1, sort=False).sum()
        BESS_Fixed_Costs_over_years = pd.concat([BESS_Fixed_Costs_over_years, BESS_Fixed_Cost], axis=1)
            
        "Generators"
        Generator_Fixed_Cost = pd.DataFrame()
        for g in range(n_generators):
            g_fc = 0
            g_fc += Generator_Nominal_Capacity.iloc[0,g]*Generator_Specific_Investment_Cost.iloc[0,g]*Generator_Specific_OM_Cost.iloc[0,g]
            gen_fc = pd.DataFrame([['Fixed cost', Generator_Names.iloc[0,g], 'kUSD', g_fc/1e3]], columns=['Cost item', 'Component', 'Unit', f'Year {y}']).set_index(['Cost item', 'Component', 'Unit']) 
            Generator_Fixed_Cost = pd.concat([Generator_Fixed_Cost, gen_fc], axis=1).fillna(0)
        Generator_Fixed_Cost = Generator_Fixed_Cost.groupby(level=[0], axis=1, sort=False).sum()
        Generator_Fixed_Costs_over_years = pd.concat([Generator_Fixed_Costs_over_years, Generator_Fixed_Cost], axis=1)
        
        "Total"
        Fixed_Costs = pd.DataFrame(['Total fixed O&M cost', 'System', 'kUSD', (Operation_Maintenance_Cost)/1e3]).T.set_index([0,1,2])
        Fixed_Costs.columns = [f'Year {y}']  
        Fixed_Costs_over_years = pd.concat([Fixed_Costs_over_years, Fixed_Costs], axis=1)

        # Variable costs 
        "Total"
        Variable_Costs = pd.DataFrame()
        Variable_Cost = pd.DataFrame(['Total variable O&M cost', 'System', 'kUSD', ( Net_Present_Cost_value.iloc[y,0] -  Operation_Maintenance_Cost)/1e3]).T
        Variable_Costs = pd.concat([Variable_Costs, Variable_Cost], axis=0)
        Variable_Costs = Variable_Costs.set_index([0,1,2])
        Variable_Costs.columns = [f'Year {y}']  
        Variable_Costs_over_years = pd.concat([Variable_Costs_over_years, Variable_Costs], axis=1)    

        "Replacement cost"
        BESS_Replacement_Cost = pd.DataFrame()
        BESS_Rep = pd.DataFrame(['Replacement cost', 'Battery bank', 'kUSD',  Battery_Replacement_Cost.iloc[y,0]/1e3]).T
        BESS_Replacement_Cost = pd.concat([BESS_Replacement_Cost, BESS_Rep], axis=0)
        BESS_Replacement_Cost = BESS_Replacement_Cost.set_index([0,1,2])
        BESS_Replacement_Cost.columns = [f'Year {y}']
        BESS_Replacement_Costs_over_years = pd.concat([BESS_Replacement_Costs_over_years, BESS_Replacement_Cost], axis=1)

        "Fuel cost" 
        Fuel_Cost = pd.DataFrame()
        for g in range(n_generators):   
            fc = pd.DataFrame([['Fuel cost', Fuel_Names.iloc[0,g], 'kUSD',  Total_Fuel_Cost.iloc[y,g]/1e3]], columns=['Cost item', 'Component', 'Unit', f'Year {y}']).set_index(['Cost item', 'Component', 'Unit'])
            Fuel_Cost = pd.concat([Fuel_Cost, fc], axis=0).fillna(0)
        Fuel_Costs_over_years = pd.concat([Fuel_Costs_over_years, Fuel_Cost], axis=1)

        "Lost load cost"
        LostLoad_Cost = pd.DataFrame()        
        LostLoad = pd.DataFrame(['Lost load cost', 'System', 'kUSD',  Lost_Load_Cost.iloc[y,0]/1e3]).T
        LostLoad_Cost = pd.concat([LostLoad_Cost, LostLoad], axis=0)
        LostLoad_Cost = LostLoad_Cost.set_index([0,1,2])
        LostLoad_Cost.columns = [f'Year {y}'] 
        LostLoad_Costs_over_years = pd.concat([LostLoad_Costs_over_years, LostLoad_Cost], axis=1)

        # Emission
        CO2_out = pd.DataFrame()  
        CO = pd.DataFrame(['TOTAL CO2 emission', 'System', 'ton',  CO2_emission.iloc[y,0]/1e3]).T
        CO2_out = pd.concat([CO2_out, CO], axis=0)
        CO2_out = CO2_out.set_index([0,1,2])
        CO2_out.columns = [f'Year {y}']
        CO2_out_over_years = pd.concat([CO2_out_over_years, CO2_out], axis=1)
        "Fuel emission"
        CO2_fuel = pd.DataFrame()  
        CO = pd.DataFrame(['Fuel CO2 emission', 'System', 'ton',  FUEL_emission.iloc[y,0]/1e3]).T
        CO2_fuel = pd.concat([CO2_fuel, CO], axis=0)
        CO2_fuel = CO2_fuel.set_index([0,1,2])
        CO2_fuel.columns = [f'Year {y}']
        CO2_fuel_over_years = pd.concat([CO2_fuel_over_years, CO2_fuel], axis=1)
        "RES emission"
        RES_emission = pd.DataFrame(['RES CO2 emission', 'RES', 'ton',  RES_emission_value/1e3]).T.set_index([0,1,2])
        RES_emission.columns = [f'Year {y}']
        RES_emission.index.names = ['Cost item', 'Component', 'Unit']
        RES_emission_over_years = pd.concat([RES_emission_over_years, RES_emission], axis=1)
        "Generator emission"
        GEN_emission = pd.DataFrame(['GEN CO2 emission', 'GEN', 'ton',  GEN_emission_value/1e3]).T.set_index([0,1,2])
        GEN_emission.columns = [f'Year {y}']
        GEN_emission.index.names = ['Cost item', 'Component', 'Unit']
        GEN_emission_over_years = pd.concat([GEN_emission_over_years, GEN_emission], axis=1)
        "Battery emission"
        BESS_emission = pd.DataFrame(['BESS CO2 emission', 'BESS', 'ton',  BESS_emission_value/1e3]).T.set_index([0,1,2])
        BESS_emission.columns = [f'Year {y}']
        BESS_emission.index.names = ['Cost item', 'Component', 'Unit'] 
        BESS_emission_over_years = pd.concat([BESS_emission_over_years, BESS_emission], axis=1)
        
        # Net present cost          
        NPC = pd.DataFrame()
        Net_Present_Cost = pd.DataFrame(['Net present cost ', 'System', 'kUSD', ( Net_Present_Cost_value.iloc[y,0])/1e3]).T
        NPC = pd.concat([NPC,Net_Present_Cost], axis=0)
        NPC = NPC.set_index([0,1,2])
        NPC.columns = [f'Year {y}']
        NPC_over_years = pd.concat([NPC_over_years, NPC], axis=1)

        #LCOE
        Demand = sum(Demand_df.iloc[t,y] for t in range(periods))
        LCOE = pd.DataFrame(['LCOE', 'USD/MWh', ((Net_Present_Cost_value.iloc[y,0])/Demand)*1e6]).T.set_index([0,1])
        LCOE.index.names = ['Cost item', 'Unit']
        LCOE.columns = [f'Year {y}']
        LCOE_over_years = pd.concat([LCOE_over_years, LCOE], axis=1)
    
    # Concatenating
    SystemCost = pd.concat([round(NPC_over_years.astype(float),3),
                            round(Fixed_Costs_over_years.astype(float),3),
                            round(Variable_Costs_over_years.astype(float),3),                          
                            round(LCOE_over_years.astype(float),3),
                            round(RES_Fixed_Costs_over_years.astype(float),3),
                            round(BESS_Fixed_Costs_over_years.astype(float),3),
                            round(Generator_Fixed_Costs_over_years.astype(float),3),
                            round(LostLoad_Costs_over_years.astype(float),3),
                            round(BESS_Replacement_Costs_over_years.astype(float),3),
                            round(Fuel_Costs_over_years.astype(float),3),
                            round(CO2_fuel_over_years.astype(float),3),
                            round(RES_emission_over_years.astype(float),3),
                            round(GEN_emission_over_years.astype(float),3),
                            round(BESS_emission_over_years.astype(float),3),
                            round(CO2_out_over_years.astype(float),3)], axis=0)

    return  SystemCost   


def EnergySystemSize(params):

    import pandas as pd

    # Importing parameters
    n_generators = (params['n_generators'])
    RES_Nominal_Capacity = pd.DataFrame(params['RES_Capacity'])
    Generator_Nominal_Capacity = pd.DataFrame(params['Generator_Nominal_Capacity'])
    Battery_Nominal_Capacity = params['Battery_Nominal_Capacity']
    RES_Names = pd.DataFrame(params['RES_names'])
    Generator_Names = pd.DataFrame(params['Generator_names'])
    
    "Renewable Sources"       
    RES_Size = pd.DataFrame()
    for r in range(params['RES_Sources']):
        r_size = RES_Nominal_Capacity.iloc[r,0]/1000
        res_size = pd.DataFrame([RES_Names.iloc[r,0], 'kW', r_size]).T.set_index([0,1])
        res_size.columns = ['Total']
        res_size.index.names = ['Component', 'Unit']
        RES_Size = pd.concat([RES_Size,res_size], axis=1).fillna(0)
    RES_Size = RES_Size.groupby(level=[0], axis=1, sort=False).sum()
    res_size_tot = RES_Size.sum(1).to_frame()
    res_size_tot.columns = ['Total']

    "Battery bank"
    BESS_Size = pd.DataFrame()
    bess_size = pd.DataFrame(['Battery bank', 'kWh', Battery_Nominal_Capacity/1e3]).T.set_index([0,1])
    bess_size.columns = ['Total']
    bess_size.index.names = ['Component', 'Unit']
    BESS_Size = pd.concat([BESS_Size, bess_size], axis=1).fillna(0)    
    BESS_Size = BESS_Size.groupby(level=[0], axis=1, sort=False).sum()
    bess_size_tot = BESS_Size.sum(1).to_frame()
    bess_size_tot.columns = ['Total']

    "Generators"
    Generator_Size = pd.DataFrame()
    for g in range(n_generators):
        gen_size = pd.DataFrame([Generator_Names.iloc[g,0], 'kW', Generator_Nominal_Capacity.iloc[g,0]/1e3]).T.set_index([0,1])
        gen_size.columns = ['Total']
        gen_size.index.names = ['Component', 'Unit']
        Generator_Size = pd.concat([Generator_Size, gen_size], axis=1).fillna(0)
    Generator_Size = Generator_Size.groupby(level=[0], axis=1, sort=False).sum()
    gen_size_tot = Generator_Size.sum(1).to_frame()
    gen_size_tot.columns = ['Total']
            
    # Concatenating
    SystemSize = pd.concat([round(RES_Size.astype(float),2),
                            round(BESS_Size.astype(float),2),
                            round(Generator_Size.astype(float),2)], axis=0).fillna('-')
        
    return SystemSize

# TimeSeries generation
def Time_Series(params,risultato,emissioni):

    import pandas as pd
    import os
    import numpy as np

    print('\nResults: exporting time-series...')
    #Importing parameters
    years = params['years']
    periods = params['Periods']
    index = pd.MultiIndex.from_product([range(years), range(periods)], names=['year', 'period'])
    Demand_df = pd.DataFrame(params['Demand'])
    RES_Energy_Production = pd.DataFrame(risultato['RES_Production'], index=index, columns=range(params['RES_Sources']))
    n_generators = (params['n_generators'])
    RES_Names = params['RES_names']
    Generator_Names = params['Generator_names']
    Fuel_Names = params['Fuel_names']
    Generator_Efficiency = pd.DataFrame(params['Generator_Efficiency'])
    Fuel_LHV = pd.DataFrame(params['Fuel_LHV'])
    StartDate = params['StartDate']
    Generator_Production = pd.DataFrame(risultato['Generator_Production'], index=index, columns=range(n_generators))
    Battery_Inflow = pd.DataFrame(risultato['Battery_Inflow'])
    Battery_Outflow = pd.DataFrame(risultato['Battery_Outflow'])
    Battery_Outflow = Battery_Outflow.clip(lower=0)
    Lost_Load = pd.DataFrame(risultato['Lost_Load'])
    Curtailment = pd.DataFrame(risultato['Energy_Curtailment'])
    Battery_SOC = pd.DataFrame(risultato['Battery_SOC'])
    FUEL_emission = pd.DataFrame(emissioni['Fuel_emission_specific'], index=index, columns=range(n_generators))
    gen_eff = pd.DataFrame(params['Gen_eff'])
    partial_load = pd.DataFrame(risultato['Partial_load'], index=index, columns=range(n_generators))
    Generator_Partial_Load = params['Generator_Partial_Load']
    
    indice = [0]*years

    date              = pd.to_datetime(StartDate, format='%d/%m/%Y %H:%M:%S')
    "Creating TimeSeries dictionary and exporting excel"
    TimeSeries = {}
        
    current_directory = os.path.dirname(os.path.abspath(__file__))
    results_directory = os.path.join(current_directory, '..', 'Results')
    results_2_path = os.path.join(results_directory, 'Time_Series.xlsx' )
    with pd.ExcelWriter(results_2_path) as writer:

        for y in range(years):

            flow_header      = []
            component_header = []
            unit_header      = []

            # Demand     
            TimeSeries[y] = pd.DataFrame()
            
            DEM = pd.DataFrame([Demand_df.iloc[t,y] for t in range(periods)])
            TimeSeries[y] = pd.concat([TimeSeries[y], DEM], axis=1)
            flow_header      += ['Electric Demand']
            component_header += ['']
            unit_header      += ['Wh']

            # Total Energy Production of RES    
            for r in range(params['RES_Sources']):
                RES = pd.DataFrame([RES_Energy_Production.loc[(y,t),r] for t in range(periods)])
                TimeSeries[y] = pd.concat([TimeSeries[y], RES], axis=1)
                flow_header      += ['RES Production']
                component_header += [RES_Names[r]]
                unit_header      += ['Wh']
                
            # Total Energy Production of the generator
            for g in range(n_generators):
                GEN = pd.DataFrame([Generator_Production.loc[(y,t),g] for t in range(periods)])
                TimeSeries[y] = pd.concat([TimeSeries[y], GEN], axis=1)
                flow_header      += ['Generator Production']
                component_header += [Generator_Names[g]]
                unit_header      += ['Wh']

            # Battery information        
            BESS_OUT         = pd.DataFrame([Battery_Outflow.iloc[t,y] for t in range(periods)])
            BESS_IN          = pd.DataFrame([Battery_Inflow.iloc[t,y] for t in range(periods)])
            LL               = pd.DataFrame([Lost_Load.iloc[t,y] for t in range(periods)])
            CURTAIL          = pd.DataFrame([Curtailment.iloc[t,y] for t in range(periods)])   
            TimeSeries[y] = pd.concat([TimeSeries[y], BESS_OUT, BESS_IN, LL, CURTAIL], axis=1) 
            flow_header      += ['Battery Charge','Battery Discharge','Lost Load','Curtailment'] 
            component_header += ['','','','']
            unit_header      += ['Wh','Wh','Wh','Wh']
                    
            # SOC of battery        
            SOC              = pd.DataFrame([Battery_SOC.loc[t,y] for t in range(periods)])
            TimeSeries[y] = pd.concat([TimeSeries[y], SOC], axis=1)
            flow_header      += ['Battery SOC']
            component_header += ['']
            unit_header      += ['Wh']

            if Generator_Partial_Load==1:

                # Fuel consumption and emission of generators without partial load 
                for g in range(n_generators):
                    FUEL = pd.DataFrame([Generator_Production.loc[(y,t),g]/Fuel_LHV.iloc[g,0]/(Generator_Efficiency.iloc[g,0]) for t in range(periods)])
                    FUEL.fillna(0, inplace=True) 
                    FUEL.replace([np.inf, -np.inf], 0, inplace=True)
                    TimeSeries[y] = pd.concat([TimeSeries[y], FUEL], axis=1)
                    flow_header      += ['Fuel Consumption']
                    component_header += [Fuel_Names[g]]
                    unit_header      += ['Lt']

            if Generator_Partial_Load==0:

                # Fuel consumption and emission of generators with partial load
                index = pd.MultiIndex.from_product([range(years), range(periods)], names=['year', 'period'])

                Generator_Efficiency = pd.DataFrame(0, index=index, columns=range(n_generators))
                      
                for g in range(n_generators):
                    for t in range(periods):
                        indice[y] = int(partial_load.loc[(y,t),g])
                        Generator_Efficiency.loc[(y,t),g] = gen_eff.iloc[indice[y], g+1]
                    FUEL = pd.DataFrame([Generator_Production.loc[(y,t),g]/Fuel_LHV.iloc[g,0]/(Generator_Efficiency.loc[(y,t),g]/100) for t in range(periods)])
                    FUEL.fillna(0, inplace=True) 
                    FUEL.replace([np.inf, -np.inf], 0, inplace=True)
                    TimeSeries[y] = pd.concat([TimeSeries[y], FUEL], axis=1)
                    flow_header      += ['Fuel Consumption']
                    component_header += [Fuel_Names[g]]
                    unit_header      += ['Lt']

            for g in range(n_generators):
                CO2 = pd.DataFrame([FUEL_emission.loc[(y,t),g] for t in range(periods)])
                TimeSeries[y] = pd.concat([TimeSeries[y], CO2], axis=1)
                flow_header      += ['CO2 emission']
                component_header += [Fuel_Names[g]]
                unit_header      += ['kg']                
                    
            TimeSeries[y].columns = pd.MultiIndex.from_arrays([flow_header, component_header, unit_header], names=['Flow','Component','Unit'])
            TimeSeries[y].index   = pd.date_range(start=date + pd.DateOffset(years=y), periods=periods, freq='H')
                
            round(TimeSeries[y],1).to_excel(writer, sheet_name=f'Year {y + 1}') #sheet_name='Year 0'
            
    return TimeSeries
