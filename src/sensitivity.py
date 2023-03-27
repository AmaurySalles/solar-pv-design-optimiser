import numpy as np
import pandas as pd

from typing import List, Dict
from dataclasses import fields
from src.pv_sizing import PVSizing
from src.scenario import Inputs

import plotly.express as px
import plotly.graph_objects as go

class Sensitivity():
    def __init__(self, inputs:Inputs, variable:str, var_min:float, var_max:float, steps:int, 
                pv_var_min: int, pv_var_max:int, pv_steps:int, pv_log_scale:bool=True):
        self.inputs = inputs
        self.variable = variable
        self.var_min = var_min
        self.var_max = var_max
        self.variable_range = np.linspace(start=var_min, stop=var_max, num=steps)
        self.pv_var_min = pv_var_min
        self.pv_var_max = pv_var_max
        self.pv_steps = pv_steps
        self.pv_log_scale = pv_log_scale
        self.pv_sizing = self.run_sensitivity()

    def run_sensitivity(self) -> Dict[str, pd.DataFrame]:
        results = {}
        # Find variable to edit
        for input_var in fields(self.inputs):
            if input_var.name == self.variable:
                # Get variable
                input_var = getattr(self.inputs, input_var.name)
                for sensitivity_val in self.variable_range:
                    # Round unit & unformat percentages (to decimal point)
                    sensitivity_val = round(sensitivity_val, 4)
                    if input_var.unit == '%':
                        sensitivity_val /= 100
                    # Update input with regard to variable
                    input_var.value = sensitivity_val
                    # Run scenario with modified input
                    pv_sizing = PVSizing(
                        self.inputs,
                        var_min=self.pv_var_min, 
                        var_max=self.pv_var_max, 
                        steps=self.pv_steps, 
                        log_scale=self.pv_log_scale
                    )
                    results[sensitivity_val] = pv_sizing
        self.pv_sizing = results
        return self.pv_sizing

    def highest_npv(self):
        return self.data.loc[pd.to_numeric(self.data['npv']).idxmax(), :]

    def graph_data(self, graph_var:str) -> pd.DataFrame:
        graph_data = pd.DataFrame()
        for sensitivity_val in self.pv_sizing:
            graph_data.loc[sensitivity_val,:] = self.pv_sizing[sensitivity_val].data.loc[:, graph_var]
        self.graph_data = graph_data
        return self.graph_data

    def graph(self, graph_var: List[str], units: str) -> go.Figure:

        graph_var_title_maping={
            'pv_self_cons': 'PV Self-consumption',
            'pv_utilisation': 'PV Utilisation',
            'npv':'NPV',
            'lcoe': 'LCOE',
            'blcoe': 'Blended LCOE',
            'irr': 'IRR'
        }
        variable_title_maping = {}
        for var in fields(self.inputs):
            if var.name == self.variable:
                input_var = getattr(self.inputs, var.name)
                variable_title_maping[var.name] = f"{input_var.name} ({input_var.unit})"

        fig = go.Figure()
        
        for i, sensitivity_var in enumerate(self.pv_sizing):
            for j, var in enumerate(graph_var):
                # The enumaration is done solely to select colours for chart
                # i.e. keeping lines & markers of same colours for each sensitivity_var
                # and differentiating between two (max) graph variables (e.g. LCOE and BLCOE)
                if j == 0:   
                    colors = ['#6c93b3', '#c38c98','#F6D992', '#8CC3B7', '#B78CC3', '#B38C6C']
                elif j== 1:  # Secondary set of colours, slightly darker than 
                    colors = ['#486d8b','#a95a6b', '#f0c04b','#5aa998', '#985aa9', '#8b6648']
                
                if len(graph_var) > 1:
                    if input_var.unit == '%':
                        name = f'{round(sensitivity_var * 100, 4)} - {graph_var_title_maping[var]}'
                    else:
                        name = f'{round(sensitivity_var, 4)} - {graph_var_title_maping[var]}'
                else:
                    if input_var.unit == '%':
                        name = f'{round(sensitivity_var * 100,4)}'
                    else:
                        name = f'{round(sensitivity_var, 4)}'
                
                graph_data = self.pv_sizing[sensitivity_var]

                fig.add_traces(go.Scatter(
                    x=graph_data.data.index,
                    y=graph_data.data[var],
                    name=name,
                    mode='lines',
                    line=dict(color=colors[i % len(colors)])
                ))
                best_result_x = graph_data.best_result.pv_capacity.value
                best_result_y = graph_data.data.loc[best_result_x, var]
                fig.add_traces(go.Scatter(
                    x=[best_result_x],
                    y=[best_result_y],
                    mode='markers',
                    name=name,
                    showlegend=False,
                    marker=dict(color=colors[i % len(colors)], size=10),
                ))
        
        # Y-axis limits
        max_values = []
        for sensitivity_val in self.pv_sizing:
            max_values.append(self.pv_sizing[sensitivity_val].data[var].max().max())
        max_val = np.max(max_values) * 1.2 # x1.2 to include max value within axis limit
        fig.update_yaxes(range=[0, max_val]) # range starts at 0 because not interested in negative results
        
        var_title = ''.join([f'{graph_var_title_maping[var]} & ' for var in graph_var]).strip('& ') 
        main_title = var_title + f' vs {variable_title_maping[self.variable]}'
        fig.update_layout(title=main_title, legend_title=dict(text=variable_title_maping[self.variable]))
        fig.update_xaxes(type='log', title='PV Capacity (kWp)')
        fig.update_yaxes(title=f'{var_title} \n({units})')

        return fig

    
