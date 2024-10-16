# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 15:44:40 2024

@author: aless
"""
def DispatchPlot(PlotDate,PlotTime,PlotResolution,PlotFormat,TimeSeries, params):
    
    import pandas as pd
    import os
    import math, numpy as np, matplotlib.pyplot as plt

    print('\nPlots: plotting energy dispatch...')
    
    fontaxis = 14
    fontlegend = 14
    
    idx = pd.IndexSlice
    
    # Importing parameters
    Delta_Time = params['Delta_Time']
    periods = params['Periods']
    RES_Names = pd.DataFrame(params['RES_names'])
    Generator_Names = pd.DataFrame(params['Generator_names'])
    n_generators = params['n_generators']
    Battery_Nominal_Capacity = params['Battery_Nominal_Capacity']
    Lost_Load_Color = params['Lost_Load_Color']
    Curtailment_Color = params['Curtailment_Color']
    RES_Colors = pd.DataFrame(params['RES_Colors'])
    Generator_Colors = pd.DataFrame(params['Generator_Colors'])
    BESS_Color = params['Battery_Color']
    StartDate = params['StartDate']
    PlotYear  = pd.to_datetime(PlotDate).year - pd.to_datetime(StartDate).year 
    # Importing Timeseries data
    pDay = 24/Delta_Time                       # Periods in a day

    foo = pd.date_range(start='2023-01-01',periods=periods,freq=('1h'))      # Find the position from which the plot will start in the Time_Series dataframe  
    reference_day = pd.to_datetime(PlotDate)
    
    time_diff = reference_day - foo[0]

    hours_in_foo = len(foo)

    index_reference_day = (time_diff // pd.Timedelta('1h')) % hours_in_foo

    Start_Plot1 = int(index_reference_day)

    End_Plot     = Start_Plot1 + PlotTime*pDay # Create the end of the plot position inside the time_series
    Series       = TimeSeries[PlotYear][Start_Plot1:int(End_Plot)] # Extract the data between the start and end position from the Time_Series
    Series.index = pd.date_range(start=PlotDate, periods=PlotTime*pDay, freq=('1h')) 

    y_RES = Series.loc[:, idx['RES Production', :, :]]

    y_BESS_out    = Series.loc[:,idx['Battery Discharge',:,:]]  
    y_BESS_in     = -1*Series.loc[:,idx['Battery Charge',:,:]]   
    y_Genset = Series.loc[:,idx['Generator Production',:,:]]
    y_LostLoad    = Series.loc[:,idx['Lost Load',:,:]]  
    y_Curtailment = -1*Series.loc[:,idx['Curtailment',:,:]]  
        
    y_Stacked_pos = []

    y_Stacked_pos.append(y_RES.copy())

    y_Stacked_pos.append(y_BESS_out.copy())  

    y_Stacked_pos.append(y_Genset.copy())
    
    y_Stacked_pos.append(y_LostLoad.copy())  

    y_Stacked_pos.append(y_Curtailment.copy()) 

    y_Stacked_neg = [y_BESS_in]
    
    y_Demand   = Series.loc[:,idx['Electric Demand',:,:]] 
    x_Plot = np.arange(len(y_Demand))
    y_BESS_SOC = Series.loc[:,idx['Battery SOC',:,:]] /Battery_Nominal_Capacity*100

    x_Plot = x_Plot.astype(float)
    
    y_stacked_values_pos = []
    for df in y_Stacked_pos:
        y_stacked_values_pos.append(df.iloc[:, 0].values.copy())
        if df.shape[1] > 1:
            y_stacked_values_pos.append(df.iloc[:, 1].values.copy())

    y_Stacked_values_neg = [df.iloc[:, 0] for df in y_Stacked_neg]

    # Plotting
    
    Colors_pos = []
    for r in range(params['RES_Sources']):
        Colors_pos.append('#'+RES_Colors.iloc[r,0])
    Colors_pos.append('#'+BESS_Color)  
    for g in range(n_generators):
        Colors_pos.append('#'+Generator_Colors.iloc[g,0])
    Colors_pos.append('#'+Lost_Load_Color)  
    Colors_pos.append('#'+Curtailment_Color)  

    Colors_neg = []
    Colors_neg = ['#'+BESS_Color]

    Labels_pos = []
    for r in range(params['RES_Sources']):
        Labels_pos += [RES_Names.iloc[r,0]]
    Labels_pos += ['Battery']  
    for g in range(n_generators):
        Labels_pos += [Generator_Names.iloc[g,0]]
    Labels_pos += ['Lost load']  
    Labels_pos += ['Curtailment'] 

    Labels_neg = []
    Labels_neg = ['_nolegend_'] 

    fig,ax1 = plt.subplots(nrows=1,ncols=1,figsize = (12,8))

    ax1.stackplot(x_Plot, y_stacked_values_pos, labels=Labels_pos, colors=Colors_pos, zorder=2)       
    ax1.stackplot(x_Plot, y_Stacked_values_neg, labels=Labels_neg, colors=Colors_neg, zorder=2)
    ax1.plot(x_Plot, y_Demand, linewidth=4, color='black', label='Demand', zorder=2)
    ax1.plot(x_Plot, np.zeros((len(x_Plot))), color='black', label='_nolegend_', zorder=2)

    ax1.set_xlabel('Time [Hours]', fontsize=fontaxis)
    ax1.set_ylabel('Power [W]', fontsize=fontaxis)
        
    "x axis"
    xticks_position = [0]
    xticks_position += [d*6-1 for d in range(1,PlotTime*4+1)]
            
    ax1.set_xticks(xticks_position)
    ax1.set_xlim(xmin=0)
    ax1.set_xlim(xmax=xticks_position[-1])
    ax1.margins(x=0)
        
    "primary y axis" 
    ax1.margins(y=0)
    ax1.grid(True, zorder=2) 
    
    "secondary y axis"
    if Battery_Nominal_Capacity >= 1:
        ax2=ax1.twinx()
        ax2.plot(x_Plot, y_BESS_SOC, '--', color='black', label='Battery state\nof charge', zorder=2)
        ax2.set_ylabel('Battery state of charge [%]', fontsize=fontaxis)

        ax2.set_yticks(np.arange(0,100.00000001,20))
        ax2.set_ylim(ymin=0)
        ax2.set_ylim(ymax=100.00000001)
        ax2.margins(y=0) 

    fig.legend(bbox_to_anchor=(1.19,0.98), ncol=1, fontsize=fontlegend, frameon=True)
    fig.tight_layout() 
    
    # Save plot
    current_directory = os.path.dirname(os.path.abspath(__file__))
    results_directory = os.path.join(current_directory, '..', 'Results/Plots')
    plot_path = os.path.join(results_directory, 'DispatchPlot.')
    fig.savefig(plot_path + PlotFormat, dpi=PlotResolution, bbox_inches='tight')

def SizePlot(params, Results, PlotResolution, PlotFormat):

    import pandas as pd
    import os
    import math, numpy as np, matplotlib.pyplot as plt

    print('       plotting components size...')
    fontticks = 18
    fontaxis = 20
    fontlegend = 18
    
    # Importing parameters
    RES_Names = pd.DataFrame(params['RES_names'])
    Generator_Names = pd.DataFrame(params['Generator_names'])
    n_generators = params['n_generators']
    RES_Colors = pd.DataFrame(params['RES_Colors'])
    Generator_Colors = pd.DataFrame(params['Generator_Colors'])
    BESS_Color = params['Battery_Color']


    # Single step or multiple steps
    fig, ax1 = plt.subplots(figsize=(20, 15))
    ax2 = ax1.twinx() 

    x_positions = np.arange(params['RES_Sources'] + n_generators + 1)
    x_ticks = []

    # Plotting for RES
    for r in range(params['RES_Sources']):
        ax1.bar(x_positions[r],
                Results['Size'].loc[pd.IndexSlice[RES_Names.iloc[r,0], :], 'Total'].values[0],
                color='#' + RES_Colors.iloc[r,0],
                edgecolor='black',
                label=RES_Names.iloc[r,0],
                zorder=3)
        x_ticks.append(RES_Names.iloc[r,0])

    # Plotting for Generators
    for g in range(n_generators):
        ax1.bar(x_positions[params['RES_Sources'] + g],
                Results['Size'].loc[pd.IndexSlice[Generator_Names.iloc[g,0], :], 'Total'].values[0],
                color='#' + Generator_Colors.iloc[g,0],
                edgecolor='black',
                label=Generator_Names.iloc[g,0],
                zorder=3)
        x_ticks.append(Generator_Names.iloc[g,0])

    # Plotting for Battery
    ax2.bar(x_positions[-1],
            Results['Size'].loc[pd.IndexSlice['Battery bank', :], 'Total'].values[0],
            color='#' + BESS_Color,
            edgecolor='black',
            label='Battery bank',
            zorder=3)
    x_ticks.append('Battery bank')

    # Set labels and ticks
    ax1.set_xlabel('Components', fontsize=fontaxis)
    ax1.set_ylabel('Installed capacity [kW]', fontsize=fontaxis)
    ax1.set_xticks(x_positions)
    ax1.set_xticklabels(x_ticks, fontsize=fontticks)
    ax1.margins(x=0.009)
    ax1.set_title('Mini-Grid Sizing [kW]', fontsize=fontaxis)

    ax2.set_ylabel('Installed capacity [kWh]', fontsize=fontaxis)
    ax2.set_xticks(x_positions)
    ax2.set_xticklabels(x_ticks, fontsize=fontticks)
    ax2.margins(x=0.009)

    # Set legend and save
    fig.legend(bbox_to_anchor=(1.19, 0.98), ncol=1, fontsize=fontlegend, frameon=True)
    fig.tight_layout()

    current_directory = os.path.dirname(os.path.abspath(__file__))
    results_directory = os.path.join(current_directory, '..', 'Results/Plots')
    plot_path = os.path.join(results_directory, 'SizePlot.' + PlotFormat)
    fig.savefig(plot_path, dpi=PlotResolution, bbox_inches='tight')
