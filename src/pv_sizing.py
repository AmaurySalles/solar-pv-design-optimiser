import numpy as np
import pandas as pd
import math
import plotly.express as px
from typing import Dict, List
from src.scenario import Scenario, Inputs

import plotly.graph_objects as go

class PVSizing():

    def __init__(self, inputs:Inputs, var_min:float, var_max:float, steps:int=20, log_scale=True):
        self.inputs = inputs
        self.log_scale = log_scale
        self.pv_range = self.generate_pv_range(var_min, var_max, steps, log_scale)
        self.scenario = self.run_pv_sensitivity()
        self.data = self.aggregate_data()
        self.best_result = self.highest_npv()

    def generate_pv_range(self, var_min, var_max, steps, log_scale=True) -> np.array:
        if log_scale:
            log_delta = math.log10(var_max - var_min)
            pv_range = np.logspace(start=0, stop=log_delta, num=steps)
        else:
            pv_range = np.linspace(start=var_min, stop=var_max, num=steps)
        self.pv_range = pv_range
        return pv_range

    def run_pv_sensitivity(self) -> Dict[int, Scenario]:
        all_scenario = {}
        for capacity in self.pv_range:
            self.inputs.pv_capacity.value = round(capacity)
            scenario = Scenario(self.inputs)
            all_scenario[round(capacity)] = scenario
        self.scenario=all_scenario
        return self.scenario

    def aggregate_data(self) -> pd.DataFrame:
        agg_data = pd.DataFrame()
        for pv_capacity, scenarii in self.scenario.items():
            agg_data = pd.concat([agg_data, scenarii.data])
        self.data = agg_data
        return self.data
    
    def highest_npv(self):
        highest_npv_scenario = pd.to_numeric(self.data['npv']).idxmax()
        return self.scenario[highest_npv_scenario]

    def graph(self, graph_var: List[str], units: str):
        
        var_title_maping={
            'pv_self_cons': 'PV Self-consumption',
            'pv_utilisation': 'PV Utilisation',
            'npv':'NPV',
            'lcoe': 'LCOE',
            'blcoe': 'Blended LCOE',
            'irr': 'IRR'
        }

        fig = go.Figure()
        for i, var in enumerate(graph_var):
            colors = ['#6c93b3', '#c38c98','#F6D992', '#8CC3B7', '#B78CC3', '#B38C6C']
            fig.add_traces(go.Scatter(
                x=self.data.index,
                y=self.data[var],
                name=var_title_maping[var],
                mode='lines',
                line=dict(color=colors[i % len(colors)])
            ))
            fig.add_traces(go.Scatter(
                x=[self.best_result.pv_capacity.value],
                y=[self.data.loc[self.best_result.pv_capacity.value, var]],
                mode='markers',
                name=var_title_maping[var],
                showlegend=False,
                marker=dict(color=colors[i % len(colors)], size=10),
            ))

        # Y-lims
        max_val = self.data[graph_var].max().max() * 1.2 # x1.2 to include max value within axis limit
        fig.update_yaxes(range=[0, max_val]) # range starts at 0 because not interested in negative results
        
        title=''.join([f'{var_title_maping[var]} & ' for var in graph_var]).strip('& ')
        fig.update_layout(title=title, legend_title=dict(text='Params'))
        fig.update_xaxes(type='log', title='PV Capacity (kWp)')
        fig.update_yaxes(title=f'{units}')

        return fig