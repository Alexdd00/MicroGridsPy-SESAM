# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 15:44:40 2024

@author: aless
"""

"Costs"

def Operation_Cost(params,risultato):

    import pandas as pd
    import numpy as np

    print('\nCalculating cost...')

    #Importing Data from params and risultato
    Demand_df = pd.DataFrame(params['Demand'])
    periods = params['Periods']
    years = params['years']
    index = pd.MultiIndex.from_product([range(years), range(periods)], names=['year', 'period'])
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
    Unitary_Battery_Replacement_Cost = params['Unitary_Battery_Replacement']
    Lost_Load_Specific_Cost = params['Lost_Load_Specific_Cost']
    Generator_Production = pd.DataFrame(risultato['Generator_Production'], index=index, columns=range(n_generators))
    Battery_Inflow = risultato['Battery_Inflow']
    Battery_Outflow = risultato['Battery_Outflow']
    # Battery_Inflow = pd.DataFrame(risultato['Battery_Inflow'])
    # Battery_Outflow = pd.DataFrame(risultato['Battery_Outflow'])
    Lost_Load = pd.DataFrame(risultato['Lost_Load'])
    Fuel_LHV = pd.DataFrame(params['Fuel_LHV'])
    Fuel_Specific_Start_Cost = pd.DataFrame(params['Fuel_Specific_Cost'])
    gen_eff = pd.DataFrame(params['Gen_eff'])
    partial_load = pd.DataFrame(risultato['Partial_load'], index=index, columns=range(n_generators))
    Generator_Efficiency = pd.DataFrame(params['Generator_Efficiency'])
    Generator_Partial_Load = params['Generator_Partial_Load']
    
    years_selected = params['years_selected']
    Battery_cost_in = [0]*years
    Battery_cost_out = [0]*years
    Battery_Replacement_Cost = [0]*years 
    Lost_Load_Cost = [0]*years 
    indice = [0]*years
    Fuel_Cost = [0]*years
    Net_Present_Cost = [0]*years
    Demand = [0]*years
    LCOE = [0]*years
    Net_present_Cost_result = [0]*years
    Operation_Cost_result = [0]*years
    Total_Fuel_Cost = pd.DataFrame([[0]*n_generators for _ in range(years)])
    

    for y in range(years):

        #Calculation total O&M costs
        OyM_Ren = np.sum(( RES_Nominal_Capacity.iloc[:,0].values* RES_Specific_Investment_Cost.iloc[:,0].values* RES_Specific_OM_Cost.iloc[:,0].values))    
        OyM_Gen = np.sum(( Generator_Nominal_Capacity.iloc[:,0].values* Generator_Specific_Investment_Cost.iloc[:,0].values* Generator_Specific_OM_Cost.iloc[:,0].values))
        OyM_Bat = (Battery_Nominal_Capacity* Battery_Specific_Investment_Cost* Battery_Specific_OM_Cost)
        Operation_Maintenance_Cost = OyM_Ren + OyM_Gen + OyM_Bat

        #Calculation battery cost
 
        Battery_cost_in[y] = np.sum( Battery_Inflow.iloc[:,y].values* Unitary_Battery_Replacement_Cost)
        Battery_cost_out[y] = np.sum( Battery_Outflow.iloc[:,y].values* Unitary_Battery_Replacement_Cost)
        Battery_Replacement_Cost[y] = Battery_cost_out[y] + Battery_cost_in[y]

        #Calculation Lost Load cost
                
        Lost_Load_Cost[y] = np.sum( Lost_Load.iloc[:,y]* Lost_Load_Specific_Cost)

        if Generator_Partial_Load==0:

            #Calculating marginal cost of generators without partial load
            Generator_Marginal_Cost = pd.DataFrame([0]*n_generators)
            for g in range(n_generators):
                Generator_Marginal_Cost.iloc[g,0] = Fuel_Specific_Start_Cost.iloc[g,0]/(Fuel_LHV.iloc[g,0]*Generator_Efficiency.iloc[g,0]) 
            
            for g in range(n_generators):
                Total_Fuel_Cost.iloc[y,g] = sum( Generator_Production.loc[(y,t),g] * Generator_Marginal_Cost.iloc[g,0] for t in range(periods))
            Fuel_Cost[y] = np.sum( Total_Fuel_Cost.iloc[y,:].values)

        if Generator_Partial_Load==1:
            
            #Calculating marginal cost of generators with partial load
            #index = pd.MultiIndex.from_product([range(years), range(periods)], names=['year', 'period'])

            Generator_Efficiency = pd.DataFrame(0, index=index, columns=range(n_generators))
            Generator_Marginal_Cost = pd.DataFrame(0, index=index, columns=range(n_generators))
            
            for t in range(periods):
                for g in range(n_generators):
                    indice[y] = int(partial_load.loc[(y,t),g])
                    Generator_Efficiency.loc[(y,t),g] = gen_eff.iloc[indice[y], g+1]
                    if Generator_Efficiency.loc[(y,t),g]==0:
                        Generator_Marginal_Cost.loc[(y,t),g] = 0   
                    else:
                        Generator_Marginal_Cost.loc[(y,t),g] = Fuel_Specific_Start_Cost.iloc[g,0]/(Fuel_LHV.iloc[g,0]*Generator_Efficiency.loc[(y,t),g]/100)
            #Generator_Marginal_Cost.replace([np.inf, -np.inf], 0, inplace=True)


            #Calculation fuel costs
            for g in range(n_generators):
                Total_Fuel_Cost.iloc[y,g] = sum( Generator_Production.loc[(y,t),g] * Generator_Marginal_Cost.loc[(y,t),g] for t in range(periods))
            Fuel_Cost[y] = np.sum( Total_Fuel_Cost.iloc[y,:].values)

        #Calculation Net Present Cost
        
        Net_Present_Cost[y] = Operation_Maintenance_Cost + Battery_Replacement_Cost[y] + Lost_Load_Cost[y] + Fuel_Cost[y]

        if y==years_selected:
            Demand[y] = np.sum(Demand_df.iloc[:,y].values)
            LCOE[y] = ((Net_Present_Cost[y])/Demand[y])*1e6
            Net_present_Cost_result[y] = Operation_Maintenance_Cost + Battery_Replacement_Cost[y] + Lost_Load_Cost[y] + Fuel_Cost[y]
            Operation_Cost_result[y] = OyM_Ren + OyM_Gen + OyM_Bat + Fuel_Cost[y]
        

    Costs={
        'Net_Present_Cost': Net_Present_Cost,
        'Net_Present_Cost_result': Net_present_Cost_result,
        'Operation_Cost': Operation_Maintenance_Cost,
        'Operation_Cost_result': Operation_Cost_result,
        'Battery_Cost': Battery_Replacement_Cost,
        'Lost_Load_Cost': Lost_Load_Cost,
        'Fuel_Cost': Fuel_Cost,
        'lcoe_result': LCOE,
        'Total_Fuel_Cost_Specific': Total_Fuel_Cost
    }

    return Costs
