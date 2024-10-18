# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 15:44:40 2024

@author: aless
"""


def Operation_Emission(params,risultato):

    import pandas as pd
    import numpy as np

    print('\nCalculating emission...')
    #Importing Data from params and risultato
    periods = params['Periods']
    years = params['years']
    index = pd.MultiIndex.from_product([range(years), range(periods)], names=['year', 'period'])
    n_generators = params['n_generators']
    RES_Nominal_Capacity = pd.DataFrame(params['RES_Capacity'])
    RES_Unit_CO2_emission = pd.DataFrame(params['RES_emission'])
    Generator_Unit_CO2_emission = pd.DataFrame(params['Generator_emission'])
    Fuel_LHV = pd.DataFrame(params['Fuel_LHV'])
    Generator_Efficiency = pd.DataFrame(params['Generator_Efficiency'])
    Fuel_Unit_CO2_Emission = pd.DataFrame(params['Fuel_Emission'])
    BESS_Unit_CO2_Emission = params['BESS_Emission']
    Generator_Nominal_Capacity = pd.DataFrame(params['Generator_Nominal_Capacity'])
    Battery_Nominal_Capacity = params['Battery_Nominal_Capacity']
    Generator_Production = pd.DataFrame(risultato['Generator_Production'], index=index, columns=range(n_generators))
    gen_eff = pd.DataFrame(params['Gen_eff'])
    partial_load = pd.DataFrame(risultato['Partial_load'], index=index, columns=range(n_generators))
    Generator_Partial_Load = params['Generator_Partial_Load']

    FUEL_emission = pd.DataFrame(0, index=index, columns=range(n_generators))
    
    CO2_emission = [0]*years
    FUEL_Emission = [0]*years
    indice = [0]*years

    for y in range(years):

        if Generator_Partial_Load==0:

            #Calculation emission without partial load
            RES_emission = np.sum( RES_Unit_CO2_emission.iloc[:,0].values* RES_Nominal_Capacity.iloc[:,0].values/1e3)
            GEN_emission = np.sum( Generator_Nominal_Capacity.iloc[:,0].values/1e3* Generator_Unit_CO2_emission.iloc[:,0].values)
            
            for t in range(periods):
                for g in range(n_generators):
                    FUEL_emission.loc[(y,t),g] =  Generator_Production.loc[(y,t),g]/ Fuel_LHV.iloc[g,0]/ (Generator_Efficiency.iloc[g,0])* Fuel_Unit_CO2_Emission.iloc[g,0]
                    FUEL_Emission[y] +=FUEL_emission.loc[(y,t),g]
            #FUEL_emission.fillna(0, inplace=True)
            #FUEL_emission.replace([np.inf, -np.inf], 0, inplace=True)
            BESS_emission =  Battery_Nominal_Capacity/1e3* BESS_Unit_CO2_Emission

        if Generator_Partial_Load==1:

            #Calculation emission with partial load
            Generator_Efficiency = pd.DataFrame(0, index=index, columns=range(n_generators))

            RES_emission = np.sum( RES_Unit_CO2_emission.iloc[:,0].values* RES_Nominal_Capacity.iloc[:,0].values/1e3)
            GEN_emission = np.sum( Generator_Nominal_Capacity.iloc[:,0].values/1e3* Generator_Unit_CO2_emission.iloc[:,0].values)
            
            for t in range(periods):
                for g in range(n_generators):
                    indice[y] = int(partial_load.loc[(y,t),g])
                    Generator_Efficiency.loc[(y,t),g] = gen_eff.iloc[indice[y], g+1]
                    if Generator_Efficiency.loc[(y,t),g]==0:
                        FUEL_emission.loc[(y,t),g] = 0
                    else:
                        FUEL_emission.loc[(y,t),g] =  Generator_Production.loc[(y,t),g]/ Fuel_LHV.iloc[g,0]/ (Generator_Efficiency.loc[(y,t),g]/100)* Fuel_Unit_CO2_Emission.iloc[g,0]
                    FUEL_Emission[y] +=FUEL_emission.loc[(y,t),g]
            #FUEL_emission.fillna(0, inplace=True)
            #FUEL_emission.replace([np.inf, -np.inf], 0, inplace=True)
            BESS_emission =  Battery_Nominal_Capacity/1e3* BESS_Unit_CO2_Emission

        CO2_emission[y] = ( RES_emission + GEN_emission + BESS_emission + FUEL_Emission[y])
    #FUEL_emission.fillna(0, inplace=True)
    #FUEL_emission.replace([np.inf, -np.inf], 0, inplace=True)

    emissioni = {
        'Fuel_emission_specific': FUEL_emission,
        'Fuel_emission': FUEL_Emission,
        'CO2_emission': CO2_emission,
        'RES_emission': RES_emission,
        'GEN_emission': GEN_emission,
        'BESS_emission': BESS_emission
    }

    return emissioni
