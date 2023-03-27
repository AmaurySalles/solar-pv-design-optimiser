import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from src.scenario import Inputs, Scenario


def scenario_page():

    with st.form('scenario_form'):

        # Form input fields
        with st.expander('**Hourly Profile Inputs**', True):
            col1, col2, col3 = st.columns(3)
            load_file = col1.file_uploader(
                    label='Load Profile (_kWh/hr_)',
                    help="Upload the _annual hourly load (kWh)_ profile under a 'csv' format.",
                    type='csv')

            ref_yield_file = col2.file_uploader(
                    label='Reference Yield Profile (_kWh/hr_)',
                    help="Upload the _annual hourly profile_ of the _reference PV system \
                        (kWh)_ under a 'csv' format.",
                    type='csv')

            ref_pv_capacity = col3.number_input(
                label="Reference yield PV system capacity _(kWp)_",
                key='ref_pv_capacity',
                value=10_000,
                min_value=1,
                max_value=9_999_999,
                step=1,
                format='%g')

            postproc_losses = col3.number_input(  label="Post-processing losses _(%)_",
                                                help="Post processing loss applied on typical in-house EYAs,\
                                                        following modelisation on PVsyst.",
                                                key="postproc_losses",
                                                min_value=0.0,
                                                max_value=100.0,
                                                value=3.0,
                                                step=0.1)

        with st.expander('**Scenario Params**', True):
            col1, col2, col3 = st.columns(3)
            currency = col1.selectbox(label="Currency", options=['USD','EUR','GBP'], key='currency')
            study_period = col2.number_input(label="Study Period (_years_)",
                            key="study_period",
                            value=25,
                            min_value=1,
                            max_value=50,
                            step=1)
            
            discount_rate = col3.number_input(label="Discount Rate (_% p.a._)",
                            key="discount_rate",
                            value=4.0,
                            min_value=0.0,
                            max_value=100.0,
                            step=0.1)

        with st.expander('**PV System Params**', True):
            col1, col2 = st.columns(2)
            pv_capacity = col1.number_input(label="PV System Capacity (_kWp_)",
                                            key="pv_capacity",
                                            value=1_000,
                                            min_value=1,
                                            max_value=1_000_000,
                                            step=1,
                                            format='%d')
            degradation_rate = col2.number_input(label="Degradation Rate (_% p.a._)",
                                                key="degradation_rate",
                                                value=0.5,
                                                min_value=0.0,
                                                max_value=100.0,
                                                step=0.1)

        with st.expander('**Financial Params**'):
            col1, col2 = st.columns(2)
            devex = col1.number_input(label="Development Costs (DevEx) (_currency_/kWp)",
                                            key="devex",
                                            value=0.0,
                                            min_value=0.0,
                                            step=0.1,
                                            format='%f')
            capex = col1.number_input(label="Capital Costs (CapEx) (_currency_/kWp)",
                                            key="capex",
                                            value=700,
                                            min_value=0,
                                            step=1,
                                            format='%d')
            opex = col2.number_input(label="Operating Costs (OpEx) per annum (_currency/kWp p.a._)",
                                            key="opex",
                                            value=15.0,
                                            min_value=0.0,
                                            step=0.1,
                                            format='%f')
            opex_increase = col2.number_input(label="OPEX Increase (_% p.a._)",
                                            key="opex_increase",
                                            value=0.0,
                                            min_value=0.0,
                                            max_value=100.0,
                                            step=0.1,
                                            format='%f')
        
            col1, col2, col3 = st.columns(3)
            loan = col1.number_input(label="Loan Portion (_% of investment_)", 
                                     key='loan',
                                     value=0.0,
                                     min_value=0.0,
                                     max_value=100.0,
                                     step=0.1)
            
            loan_period = col2.number_input(label="Loan Period (_years_)",
                                            key="loan_period",
                                            value=10,
                                            min_value=0,
                                            max_value=100,
                                            step=1)
            
            loan_rate = col3.number_input(label="Interest Rate (_% p.a._)",
                                          key="loan_rate",
                                          value=2.0,
                                          min_value=0.0,
                                          max_value=100.0,
                                          step=0.1)

        with st.expander('**Electricity Market Params**'):
            col1, col2 = st.columns(2)
            import_tariff = col1.number_input(label="**Import Tariff** (_currency/kWh_)",
                                            key="import_tariff",
                                            value=0.1,
                                            min_value=0.0,
                                            step=0.001,
                                            format='%f')
            export_tariff = col2.number_input(label="**Export Tariff** (_currency/kWh_)",
                                            key="export_tariff",
                                            value=0.05,
                                            min_value=0.0,
                                            step=0.001,
                                            format='%f')
            import_increase = col1.number_input(label="**Import Tariff Increase** (_% p.a._)",
                                            key="import_increase",
                                            value=0.0,
                                            min_value=0.0,
                                            max_value=100.0,
                                            step=0.1,
                                            format='%f')
            export_increase = col2.number_input(label="**Export Tariff Increase** (_% p.a._)",
                                            key="export_increase",
                                            value=0.0,
                                            min_value=0.0,
                                            max_value=100.0,
                                            step=0.1,
                                            format='%f')
        
        col1, col2, col3 = st.columns((3,1,3))
        with col2:
            st.write('\n')
            save_input_btn = st.form_submit_button('Save & View Results', type='primary')

    display = st.empty()
    if 'scenario' in st.session_state:
        with display:
            display_scenario()

    if save_input_btn:
        display.empty()
        try:
            input_loads = pd.read_csv(load_file, index_col=0, parse_dates=True, dayfirst=True)
            ref_yield = pd.read_csv(ref_yield_file, skiprows=9, index_col=0, parse_dates=True,
                                                dayfirst=True, encoding='latin-1')
            ref_yield = ref_yield.iloc[1:].copy().astype(float) # Remove unit row
        except Exception:
            st.error("Could not upload 'csv' file. Check file path & retry.")
        
        inputs = Inputs(
            load=input_loads,
            ref_yield=ref_yield,
            # Reference yield parameters
            ref_capacity = ref_pv_capacity,
            postproc_losses = postproc_losses / 100, # % input
            ref_specific_yield= None, # Will be instantiated automatically
            # Scenario parameters
            study_period = study_period,
            discount_rate = discount_rate / 100, # % input
            # PV system parameters
            pv_capacity = pv_capacity,
            pv_degradation = degradation_rate / 100, # % input
            # Financial parameters
            currency = currency,
            devex = devex,
            capex = capex,
            opex = opex,
            opex_increase = opex_increase / 100, # % input
            loan=loan / 100,
            loan_period=loan_period,
            loan_rate=loan_rate /100, # % input
            # Electricity market parameters
            import_tariff = import_tariff,
            export_tariff = export_tariff,
            import_increase = import_increase / 100, # % input
            export_increase = export_increase / 100, # % input
        )
        if "inputs" not in st.session_state:
            st.session_state['inputs'] = inputs
        else:
            st.session_state.inputs = inputs

        scenario = create_scenario(inputs)

        if "scenario" not in st.session_state:
            st.session_state['scenario'] = scenario
        else:
            st.session_state.scenario = scenario
        
        with display:
            display_scenario(scenario)

@st.cache_resource
def create_scenario(inputs: Inputs = None):

    if not inputs:
        inputs = st.session_state.inputs

    scenario = Scenario(inputs)

    if "scenario" not in st.session_state:
        st.session_state['scenario'] = scenario
    else:
        st.session_state.scenario = scenario
    
    # Create summary spreadsheet for checks
    excel_file_path = create_excel_file(inputs, scenario)

    if "scenario_excel" not in st.session_state:
        st.session_state['scenario_excel'] = excel_file_path
    else:
        st.session_state.scenario_excel = excel_file_path

    return scenario

def create_excel_file(inputs:Inputs, scenario:Scenario):
    
    file_name = 'Scenario.xlsx'
    inputs_for_excel = inputs.to_excel()
    scenario_summary, energy_summary, financial_summary = scenario.format_summary()

    with pd.ExcelWriter(file_name) as writer:
        inputs_for_excel.to_excel(writer, 'Input Summary', header=False)
        scenario_summary.to_excel(writer, sheet_name='Output Summary')  
        scenario.energy_balance_summary.to_excel(writer, sheet_name='Energy Balance')
        scenario.cashflow.to_excel(writer, sheet_name='Cashflow')
        scenario.discounted_cashflow.to_excel(writer, sheet_name='Discounted Cashflow')
    
    return Path.cwd() / file_name

def display_scenario(scenario: Scenario=None):
    if not scenario:
        scenario = st.session_state.scenario    

    with st.container():
        st.write('#### Scenario Summary:')
        display_scenario_summary()
        st.write('#### Scenario Results:')
        display_scenario_results()

        with st.expander('Annual Energy Balance'):
            display_energy_balance()

        with st.expander('Cashflow'):
            display_cashflow()
        
        with st.expander('Discounted Cashflow'):
            display_discounted_cashflow()
        
def display_scenario_summary(scenario: Scenario=None):
    if not scenario:
        scenario = st.session_state.scenario

    summary=pd.DataFrame(
        columns=['Scenario'],
        index=['PV Capacity (kWp)','Reference Specific Yield (kWh/kWp)']
    )
    summary.loc['PV Capacity (kWp)','Scenario'] = scenario.pv_capacity.value
    summary.loc['Reference Specific Yield (kWh/kWp)', 'Scenario'] = scenario.ref_specific_yield.value.sum()
    summary.loc['Annual Load (MWh)', 'Scenario'] = scenario.load.value.sum() / 1000 # MWh
    summary = summary.style.format("{:,.2f}")

    col1, col2, col3, col4 = st.columns((3,1,1,1))
    col1.dataframe(summary, use_container_width=True)

    # Download doc (& generate widget unique key)
    widget_id = (id for id in range(1, 1_000_000))
    with open(st.session_state.scenario_excel, "rb") as f:
        btn = col3.download_button(
            label="Download Scenario",
            data=f,
            file_name=st.session_state.scenario_excel.name,
            key=widget_id
        )

def display_scenario_results(scenario: Scenario=None):
    if not scenario:
        scenario = st.session_state.scenario

    summary, energy_summary, financial_summary = scenario.format_summary()
    energy_summary = energy_summary
    financial_summary = financial_summary

    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(energy_summary, height=280, use_container_width=True)
    with col2:
        st.dataframe(financial_summary, height=280, use_container_width=True)

def display_energy_balance(scenario: Scenario=None):
    if not scenario:
        scenario = st.session_state.scenario

    energy_balance = scenario.energy_balance_summary
    energy_balance.loc[:,['PV self-cons (%)','PV usage (%)']] *= 100
    energy_balance = energy_balance.rename(columns={
        'enLoad':'Load (MWh)',
        'enPV total': 'PV Yield (MWh)',
        'enPV self-cons':'PV Self-consumption (MWh)',
        'enGrid import': 'Grid Imports (MWh)',
        'enGrid export': 'Grid Exports (MWh)',
        'PV self-cons (%)': 'PV Self-consumption(%)',
        'PV usage (%)': 'PV Usage (%)'
    }).style.format("{:,.2f}")
    
    st.dataframe(energy_balance, height=400, use_container_width=True)

def display_cashflow(scenario: Scenario=None):
    if not scenario:
        scenario = st.session_state.scenario

    currency = scenario.currency.value
    cashflow = scenario.cashflow.loc[:,'import costs':]
    cashflow = cashflow.rename(columns={
        'import costs': f'Import costs ({currency})',
        'export sales': f'Export revenues ({currency})',
        'enPV revenues': f'PV savings & revenues ({currency})',
        'opex': f'OpEx ({currency})',
        'loan_payment': f'Loan Payment ({currency})',
        'cashflow': f'Cashflow ({currency})',
        'cash balance': f'Cash balance ({currency})',
    }).style.format("{:,.0f}")
    st.dataframe(cashflow, height=400, use_container_width=True)

def display_discounted_cashflow(scenario: Scenario=None):
    if not scenario:
        scenario = st.session_state.scenario
    currency = scenario.currency.value
    cashflow = scenario.discounted_cashflow.loc[:,'import costs':]
    cashflow = cashflow.rename(columns={
        'import costs': f'Import costs ({currency})',
        'export sales': f'Export revenues ({currency})',
        'enPV revenues': f'PV savings & revenues ({currency})',
        'opex': f'OpEx ({currency})',
        'loan_payment': f'Loan Payment ({currency})',
        'cashflow': f'Cashflow ({currency})',
        'cash balance': f'Cash balance ({currency})',
    }).style.format("{:,.0f}")
    st.dataframe(cashflow, height=400, use_container_width=True)

if __name__ == "__main__":
    scenario_page()
