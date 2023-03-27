import streamlit as st

from src.optimiser import PlatypusOptimiser, ScipyOptimiser
from src.scenario import Scenario, Variable



OBJECTIVE_OPTIONS = [
    'LCOE',
    'BLCOE',
    'IRR',
    'NPV',
    'PV self_per',
    'PV util_per',
    'LPBP',
]

            
def optimiser_page():
    with st.form('optimiser_form'):

        # Input / Scenario form header
        col1, col2 = st.columns((4,1))
        with col1:
            st.write('## Optimiser')
        with col2:
            st.write(' ')
            run_optimiser = st.form_submit_button('Run', type='primary')

        col1, col2 = st.columns((3,2))
        with col1:
            optimiser_type = col1.radio(label='Type', options=["Min","Max","Goal-Seek"], horizontal=True)
        with col2:
            to_value = st.number_input(label='Goal-seek value', min_value=0.0)
        
        objective = st.selectbox(label='Objective',
                                    options=OBJECTIVE_OPTIONS)

        variable = st.selectbox(label='By changing',
                                options=[var.name for var in Variable])

        # Once form submitted
        if run_optimiser:
            
            ## Platypus optimiser ###
            if 'scenario' not in st.session_state:
                st.session_state['scenario'] = create_scenario()
            else: # Update
                st.session_state.scenario = create_scenario()

            if 'optimiser' not in st.session_state:
                st.session_state['optimiser'] = PlatypusOptimiser(st.session_state.scenario)
            else:
                st.session_state.optimiser = PlatypusOptimiser(st.session_state.scenario)


            ### Scipy Optimiser ###

            # if 'objective' not in st.session_state:
            #     st.session_state['objective'] = objective
            # if 'optimiser_type' not in st.session_state:
            #     st.session_state['optimiser_type'] = optimiser_type
            # if 'variable' not in st.session_state:
            #     st.session_state['variable'] = variable
            # if 'to_value' not in st.session_state:
            #     st.session_state['to_value'] = to_value

            # optimiser = ScipyOptimiser(scenario=st.session_state.scenario,
            #             objective=st.session_state.objective,
            #             optimisation=st.session_state.optimiser_type,
            #             variable=st.session_state.variable,
            #             init_value=1000,
            #             to_value=st.session_state.to_value
            # )

            # if "optimiser" not in st.session_state:
            #     st.session_state['optimiser'] = optimiser
            # else:
            #     st.session_state.optimiser = optimiser            


if __name__ == "__main__":
    optimiser_form()
