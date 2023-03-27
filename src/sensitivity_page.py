import streamlit as st
from typing import Dict
from dataclasses import fields
from src.scenario import Inputs
from src.pv_sizing import PVSizing
from src.sensitivity import Sensitivity
from src.scenario_page import display_scenario_results, create_excel_file

def format_sensitivity_inputs() -> Dict[str, str]:
    if 'inputs' not in st.session_state:
        inputs = Inputs()
    else:
        inputs = st.session_state.inputs
    format_dict = {}
    for var in fields(inputs):
        if var.name == 'pv_capacity' or var.name == 'currency':
            continue
        # Get variable
        input_var = getattr(inputs, var.name)
        name = input_var.name
        unit = input_var.unit

        format_dict[var.name] = f'{name} ({unit})'

    return format_dict

def deformat_sensitivity_inputs(dict: Dict[str, str]) -> Dict[str, str]:
    return {val: key for key, val in dict.items()}
    

def sensitivity_page():
    with st.form('sensitivity_form'):
                    
        with st.expander('**PV Capacity Sizing**', True):
            col1, col2 = st.columns(2)
            pv_sizing_var_min = col1.number_input(label='Minimum PV capacity (kWp)', key='pv_sizing_var_min', value=1.0, format='%f')    
            pv_sizing_var_max = col2.number_input(label='Maximum PV capacity (kWp)', key='pv_sizing_var_max', value=100_000.0, format='%f')
            
            col1, col2, col3 = st.columns((4,1,3))
            pv_sizing_steps = col1.number_input(label='Number of points', key='pv_sizing_steps', value=30, min_value=3, max_value=500,
                                                help='Number of points linearly interpolated between min and max. Increase for higher granularity.'
            )
            col3.write('\n')
            col3.write('\n')
            pv_sizing_log_scale = col3.checkbox(label='Log scale', key='pv_sizing_log_scale', value=True)

            col1, col2, col3 = st.columns((2,1,2))
            pv_sizing_btn = col2.form_submit_button('Run PV capacity sensitivity', type='primary')
            
        
        with st.expander('**Secondary sensitivity**', False):
            col1, col2, col3, col4 = st.columns((2,1,1,1))
            sensitivity_targets = list(format_sensitivity_inputs().values())[5:]
            sensitivity_target = col1.selectbox(label="Sensitivity target", key='sensitivity_target', options=sensitivity_targets)
            sensitivity_var_min = col2.number_input(label='Min', key='sensitivity_var_min', value=1.0, format='%f')
            sensitivity_var_max = col3.number_input(label='Max', key='sensitivity_var_max', value=10.0, format='%f')
            sensitivity_steps = col4.number_input(label='Number of points', key='sensitivity_steps', value=5, min_value=1, max_value=10)         

            col1, col2, col3 = st.columns((3,1,3))
            sensitivity_btn = col2.form_submit_button('Run sensitivity', type='primary')

    # Restore view with latest results
    # TODO: Add button to interact between the two views
    display = st.empty()
    if 'sensitivity' in st.session_state:
        with display:
            display_sensitivity()
    elif 'pv_sizing' in st.session_state:
        with display:
            display_pv_sizing()


    if pv_sizing_btn:
        display.empty()

        # returns dict[pv_capacity: pd.Dataframe(results)]
        run_pv_sizing_sensitivity(pv_sizing_var_min, pv_sizing_var_max, pv_sizing_steps, pv_sizing_log_scale)
        with display:
            display_pv_sizing()

    if sensitivity_btn:
        display.empty()

        # Reverse input formating to obtain variable name
        sensitivity_target= deformat_sensitivity_inputs(format_sensitivity_inputs())[sensitivity_target]
        run_sensitivity(sensitivity_target, sensitivity_var_min, sensitivity_var_max, sensitivity_steps)
        with display:
            display_sensitivity()

def run_pv_sizing_sensitivity(pv_sizing_var_min, pv_sizing_var_max, pv_sizing_steps, pv_sizing_log_scale):
    pv_sizing = PVSizing(
        st.session_state.inputs,
        var_min=pv_sizing_var_min, 
        var_max=pv_sizing_var_max, 
        steps=pv_sizing_steps, 
        log_scale=pv_sizing_log_scale
    )
    if "pv_sizing" not in st.session_state:
        st.session_state['pv_sizing'] = pv_sizing
    else:
        st.session_state.pv_sizing = pv_sizing

    st.write(f'##### **PV Capacity**: `{pv_sizing.best_result.pv_capacity.value:,.0f} kWp`')
    # Create summary spreadsheet for checks
    st.session_state.inputs.pv_capacity.value = pv_sizing.best_result.pv_capacity.value
    excel_file_path = create_excel_file(st.session_state.inputs, pv_sizing.best_result)

    if "best_scenario_excel" not in st.session_state:
        st.session_state['best_scenario_excel'] = excel_file_path
    else:
        st.session_state.best_scenario_excel = excel_file_path


def run_sensitivity(sensitivity_objective:str, sensitivity_var_min:float, sensitivity_var_max:float, sensitivity_steps:int):

    sensitivity = Sensitivity(st.session_state.inputs,
                              variable=sensitivity_objective,
                              var_min=sensitivity_var_min,
                              var_max=sensitivity_var_max, 
                              steps=sensitivity_steps,
                              pv_var_min=st.session_state.pv_sizing_var_min,
                              pv_var_max=st.session_state.pv_sizing_var_max,
                              pv_steps=st.session_state.pv_sizing_steps,
                              pv_log_scale=st.session_state.pv_sizing_log_scale,
        )

    if "sensitivity" not in st.session_state:
        st.session_state['sensitivity'] = sensitivity
    else:
        st.session_state.sensitivity = sensitivity

def display_pv_sizing():
    with st.container():
        col1, col2, col3 = st.columns((2,1,2))
        col1.write('## Best Scenario')
        best_scenario = st.session_state.pv_sizing.best_result
        col2.write('\n')
        col2.write('\n')
        col2.write(f'##### **PV Capacity**: `{best_scenario.pv_capacity.value:,.0f} kWp`')
        with col3:
            col31, col32, col33 = col3.columns(3)
            col32.write('\n')
            with open(st.session_state.best_scenario_excel, "rb") as f:
                btn = col32.download_button(
                    label="Download Best Scenario",
                    data=f,
                    file_name=st.session_state.best_scenario_excel.name
                )

        display_scenario_results(best_scenario)
        
        pv_sizing = st.session_state.pv_sizing

        col1, col2 = st.columns((3,2))
        with col1:
            st.plotly_chart(pv_sizing.graph(graph_var=['pv_self_cons','pv_utilisation'], 
                                            units='%'), 
                            use_container_width=True)
            st.plotly_chart(pv_sizing.graph(graph_var=['lcoe','blcoe'], 
                                            units=f'{st.session_state.currency}/kWh'), 
                            use_container_width=True)

        with col2:
            st.plotly_chart(pv_sizing.graph(graph_var=['npv'], 
                                            units=st.session_state.currency), 
                            use_container_width=True)        
            st.plotly_chart(pv_sizing.graph(graph_var=['irr'], 
                                            units='%'), 
                            use_container_width=True)

def display_sensitivity(): 
    sensitivity = st.session_state.sensitivity
    
    col1, col2 = st.columns((3,2))
    with col1:
        st.plotly_chart(sensitivity.graph(graph_var=['pv_self_cons','pv_utilisation'], 
                                        units='Percentage (%)'), 
                        use_container_width=True)
        st.plotly_chart(sensitivity.graph(graph_var=['lcoe','blcoe'], 
                                        units=f'{st.session_state.currency}/kWh'), 
                        use_container_width=True)

    with col2:
        st.plotly_chart(sensitivity.graph(graph_var=['npv'], 
                                        units=st.session_state.currency), 
                        use_container_width=True)        
        st.plotly_chart(sensitivity.graph(graph_var=['irr'], 
                                        units='Percentage (%)'), 
                        use_container_width=True)
