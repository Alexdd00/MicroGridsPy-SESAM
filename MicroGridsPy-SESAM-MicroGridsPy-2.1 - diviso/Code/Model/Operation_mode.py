
import time
from Operation_mode_SENZAGRID_ottimizzato import initialize
from Operation_func import Operation
#from prova_ottimo import Operation
from Operation_costo import Operation_Cost
from Operation_emissioni import Operation_Emission
from Operation_plotti import DispatchPlot, SizePlot
from Operation_result import PrintResults, ResultsSummary, Time_Series

start = time.time()         # Start time counter
params = initialize()
#%
risultato = Operation(params)
#%
Costs = Operation_Cost(params,risultato)
emissioni = Operation_Emission(params,risultato)

#% Results

TimeSeries       = Time_Series(params,risultato,emissioni)
#%
Results          = ResultsSummary(params, Costs, emissioni, TimeSeries) 

#% Plot and print-out
PlotScenario = 1                     # Plot scenario
PlotDate = '01/03/2024 00:00:00'     # Month-Day-Year. 
PlotTime = 4                         # Number of days to be shown in the plot
PlotFormat = 'png'                   # Desired extension of the saved file (Valid formats: png, svg, pdf)
PlotResolution = 400                 # Plot resolution in dpi (useful only for .png files, .svg and .pdf output a vector plot)

DispatchPlot(PlotDate,PlotTime,PlotResolution,PlotFormat,TimeSeries, params)
SizePlot(params, Results, PlotResolution, PlotFormat)

PrintResults(Costs, risultato, Results, params)  


#% Timing
end = time.time()
elapsed = end - start
print('\n\nModel run complete (overall time: ',round(elapsed,0),'s,',round(elapsed/60,1),' m)\n')
