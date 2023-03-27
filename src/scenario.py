import pandas as pd
import numpy as np
import numpy_financial as npf
from scipy.stats import linregress
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple, Any, Union
from enum import Enum

Currencies = Enum('Currencies', ['USD', 'EUR', 'GBP'])

@dataclass
class UnitVar():
    name: str
    unit: str
    value: Any

    def __post_init__(self):
        self.title = f'{self.name} ({self.unit})'


def empty_hourly_profiles() -> pd.DataFrame:
    index = pd.date_range('01-01-1990 00:00:00', '31-12-1990 23:00:00', freq='1H')
    values = np.zeros(8760)
    return pd.DataFrame(index=index, data=values, columns=['E_Grid'])

@dataclass
class Inputs():
    """Converts inputs into unit variables for display purposes."""
    # TODO: Add area / ground coverage ratio constraint
    load: Union[pd.DataFrame, UnitVar, None] = empty_hourly_profiles()
    ref_yield: Union[pd.DataFrame, UnitVar, None] = empty_hourly_profiles()
    ref_capacity: Union[int, UnitVar] = 10000
    postproc_losses: Union[float, UnitVar] = 0.03
    ref_specific_yield: Union[pd.DataFrame, UnitVar, None] = None
    study_period: Union[int, UnitVar] = 25
    discount_rate: Union[float, UnitVar] = 0.04  
    pv_capacity: Union[int, UnitVar] = 1000
    pv_degradation: Union[float, UnitVar] = 0.005
    currency: Union[Currencies, UnitVar] = Currencies.USD.name
    devex: Union[int, UnitVar] = 0
    capex: Union[int, UnitVar] = 700
    opex: Union[int, UnitVar] = 15
    opex_increase: Union[float, UnitVar] = 0.0
    loan: Union[float, UnitVar] = 0.0
    loan_period: Union[int, UnitVar] = 0
    loan_rate: Union[float, UnitVar] = 0.0
    import_tariff: Union[float, UnitVar] = 0.1
    export_tariff: Union[float, UnitVar] = 0.05
    import_increase: Union[float, UnitVar] = 0.0
    export_increase: Union[float, UnitVar] = 0.0

    def __post_init__(self):
        if self.ref_specific_yield is None:
            self._format_file_inputs()
        self._convert_to_unit_variables()
    
    def _convert_to_unit_variables(self):
        self.load = UnitVar('Load', 'kWh', self.load)
        self.ref_yield = UnitVar('Reference yield', 'kWh', self.ref_yield)
        self.ref_capacity = UnitVar('Reference capacity', 'kWp',self.ref_capacity)
        self.postproc_losses = UnitVar('Post-processing losses', '%', self.postproc_losses)
        self.ref_specific_yield = UnitVar('Reference specific yield','kWh/kWp', self.ref_specific_yield)
        self.study_period = UnitVar('Study period', 'yrs', self.study_period)
        self.discount_rate = UnitVar('Discount rate', '%', self.discount_rate)
        self.pv_capacity = UnitVar('PV capacity', 'kWp', self.pv_capacity)
        self.pv_degradation = UnitVar('PV degradation', '%', self.pv_degradation)
        self.currency = UnitVar('Currency', 'NA', self.currency)
        self.devex = UnitVar('DevEx', f'{self.currency.value}/kWp', self.devex)
        self.capex = UnitVar('CapEx', f'{self.currency.value}/kWp', self.capex)
        self.opex = UnitVar('OpEx', f'{self.currency.value}/kWp', self.opex)
        self.opex_increase = UnitVar('OpEx increase', '%', self.opex_increase)
        self.loan = UnitVar('Loan', '%', self.loan)
        self.loan_period = UnitVar('Loan Period', 'yrs', self.loan_period)
        self.loan_rate = UnitVar('Loan Interest Rate', '%', self.loan_rate)
        self.import_tariff = UnitVar('Import tariff', f'{self.currency.value}/kWh', self.import_tariff)
        self.export_tariff = UnitVar('Export tariff', f'{self.currency.value}/kWh', self.export_tariff)
        self.import_increase = UnitVar('Import increase', '%', self.import_increase)
        self.export_increase = UnitVar('Export increase', '%', self.export_increase)
        return self

    def _format_file_inputs(self):
        """
        Given a reference yield and reference capacity and post-processing losses, 
        calculate the system's specific yield.
        ----------
        Returns: pd.Series containing system's specific yield (kWh/kWp)
        """
        # Align indices between two datasets
        # TODO: update indices alignment - currently only work with both files starting 01/01/YYYY
        self.ref_yield.index = self.load.index

        # Format loads dataset
        self.load = pd.Series(index=self.load.index, 
                              data=self.load.iloc[:,0].astype(float), 
                              name='enLoad')

        # Calculate specific yield of reference yield #
        # Clean up E_Grid by removing negative values
        self.ref_yield.loc[self.ref_yield['E_Grid'] < 0, 'E_Grid'] = 0

        # Calculate final yield (including PVsyst post-processing losses)
        self.ref_yield['enPV ref'] = self.ref_yield['E_Grid'] * (1-self.postproc_losses)
        
        # Calculate specific yield as new column
        self.ref_yield['SY'] = self.ref_yield['enPV ref'] / self.ref_capacity # resulting unit: kWh/kWp

        self.ref_specific_yield = self.ref_yield['SY']
        return self

    def to_excel(self):
        return pd.DataFrame(pd.Series({
            self.study_period.title : self.study_period.value,
            self.discount_rate.title : self.discount_rate.value * 100,
            self.pv_capacity.title : self.pv_capacity.value,
            self.pv_degradation.title : self.pv_degradation.value * 100,
            self.currency.name : self.currency.value,
            self.devex.title : self.devex.value,
            self.capex.title : self.capex.value,
            self.opex.title : self.opex.value,
            self.opex_increase.title : self.opex_increase.value * 100,
            self.loan.title : self.loan.value * 100,
            self.loan_period.title : self.loan_period.value,
            self.loan_rate.title : self.loan_rate.value * 100,
            self.import_tariff.title : self.import_tariff.value,
            self.export_tariff.title : self.export_tariff.value,
            self.import_increase.title : self.import_increase.value * 100,
            self.export_increase.title : self.export_increase.value * 100
        })).style.format("{:,.2f}")


class Scenario(Inputs):
    
    def __init__(self, inputs):
        super().__init__(
            load=inputs.load.value,
            ref_yield=inputs.ref_yield.value,
            ref_capacity=inputs.ref_capacity.value,
            postproc_losses=inputs.postproc_losses.value,
            ref_specific_yield=inputs.ref_specific_yield.value,
            study_period=inputs.study_period.value,
            discount_rate=inputs.discount_rate.value,
            pv_capacity=inputs.pv_capacity.value,
            pv_degradation=inputs.pv_degradation.value,
            currency=inputs.currency.value,
            devex=inputs.devex.value,
            capex=inputs.capex.value,
            opex=inputs.opex.value,
            opex_increase=inputs.opex_increase.value,
            loan=inputs.loan.value,
            loan_period=inputs.loan_period.value,
            loan_rate=inputs.loan_rate.value,
            import_tariff=inputs.import_tariff.value,
            export_tariff=inputs.export_tariff.value,
            import_increase=inputs.import_increase.value,
            export_increase=inputs.export_increase.value,
        )

        self.energy_balance = self._calc_annual_energy_balance()
        self.energy_balance_summary = self._calc_energy_balance_summary()
        self.cashflow = self._calc_cashflow()
        self.discounted_cashflow = self._calc_discounted_cashflow()
        self.data = self._calc_summary()
    
    def _calc_annual_energy_balance(self) -> Dict[int,pd.DataFrame]:
        """
        Given a reference dataset (pv and load yields) and scenario parameters, 
        calculate the annual energy balance of the system.
        ---------------
        Returns: Dictionary, with keys representing years, 
                and values containing pd.DataFrames with following columns:
                - 'enLoad': Energy from the load
                - 'enPV total': Energy generated by PV system
                - 'enPV self-cons': Energy from PV that is used for self-consumption
                - 'enGrid import': Shortfall load energy to be imported from grid
                - 'enGrid export': Surplus PV energy to be exported to the grid
                - 'PV self-cons (%)': Percentage of load offset by PV system
                - 'PV usage (%)': Percentage of PV system energy going to load
        """
        
        self.energy_balance = {}
        
        for year in range(1, self.study_period.value + 1):
            
            data = pd.DataFrame(self.load.value)

            # Calculate degraded capacity (averaged linear degradation ~ 6 month in)
            capacity_dc_degr = self.pv_capacity.value * (1 - (self.pv_degradation.value * (year - 0.5)))

            # Calculate annual energy balance
            data['enPV total'] = self.ref_specific_yield.value * capacity_dc_degr

            # Grid import req?
            energy_shortfall = data['enPV total'] < data['enLoad']

            # When there is a shortfall, system consums all of PV system energy output
            data.loc[energy_shortfall, 'enPV self-cons'] = data.loc[energy_shortfall, 'enPV total']

            # When there is a surplus, PV system energy output can supply entire load
            data.loc[~energy_shortfall, 'enPV self-cons'] = data.loc[~energy_shortfall,'enLoad']

            # When there is a shortfall, calculate shortfall amount (to import from grid)
            data.loc[energy_shortfall, 'enGrid import'] = data.loc[energy_shortfall, 'enLoad'] - data.loc[energy_shortfall, 'enPV total']
            data.loc[~energy_shortfall, 'enGrid import'] = 0 # ELse importing 0 from grid

            # When there is a surplus, calculate surplus amount (to export to grid)
            data.loc[~energy_shortfall, 'enGrid export'] = data.loc[~energy_shortfall, 'enPV total'] - data.loc[~energy_shortfall, 'enLoad']
            data.loc[energy_shortfall, 'enGrid export'] = 0 # Else exporting 0 to grid
            
            self.energy_balance[year] = data
        
        return self.energy_balance

    def _calc_energy_balance_summary(self) -> pd.DataFrame:
        
        df = pd.DataFrame()

        for year, data in self.energy_balance.items():      

            # Create annual summary
            df.loc[year,'enLoad']           = data['enLoad'].sum() / 1_000         # MWh
            df.loc[year,'enPV total']       = data['enPV total'].sum() / 1_000     # MWh
            df.loc[year,'enPV self-cons']   = data['enPV self-cons'].sum() / 1_000 # MWh
            df.loc[year,'enGrid import']    = data['enGrid import'].sum() / 1_000  # MWh
            df.loc[year,'enGrid export']    = data['enGrid export'].sum() / 1_000  # MWh
            df.loc[year,'PV self-cons (%)'] = df.loc[year,'enPV self-cons'] / df.loc[year,'enLoad']
            df.loc[year,'PV usage (%)']     = df.loc[year,'enPV self-cons'] / df.loc[year,'enPV total']

            self.energy_balance_summary = df
        return self.energy_balance_summary

    def _calc_cashflow(self) -> pd.DataFrame:
                
        ebs_df = self.energy_balance_summary.copy()
        data = ebs_df[['enLoad', 'enPV total','enPV self-cons','enGrid import', 'enGrid export']].copy()

        total_investment = (self.capex.value + self.devex.value)* self.pv_capacity.value

        for year in data.index:

            # Calculate electricity tariff
            data.loc[year, 'import tariff'] = self.import_tariff.value * ((1 + self.import_increase.value) ** year)
            data.loc[year, 'export tariff'] = self.export_tariff.value * ((1 + self.export_increase.value) ** year)
            data.loc[year, 'combined tariff'] = (ebs_df.loc[year,'PV usage (%)'] * data.loc[year, 'import tariff'])\
                                                + ((1-ebs_df.loc[year,'PV usage (%)']) * data.loc[year, 'export tariff'])
            # Calculate electricity sales
            data.loc[year, 'import costs'] = data.loc[year, 'import tariff'] * (data.loc[year, 'enGrid import'] * 1_000)
            data.loc[year, 'export sales'] = data.loc[year, 'export tariff'] * (data.loc[year, 'enGrid export'] * 1_000)
            data.loc[year, 'enPV revenues'] = data.loc[year, 'combined tariff'] * (data.loc[year, 'enPV total'] * 1_000)
            
            # Calculate annual discounted OPEX (with annual increase)
            opex_increase = (1 + self.opex_increase.value) ** year
            data.loc[year, 'opex'] = (self.opex.value * opex_increase * self.pv_capacity.value)

            # Calculate loan repayment
            data.loc[year,"loan_payment"] = 0
            if year <= self.loan_period.value:
                loan_payment = npf.pmt(self.loan_rate.value, self.loan_period.value, (self.loan.value * total_investment))
                data.loc[year,"loan_payment"] = -round(loan_payment,2)

            # Calculate cashflow
            data.loc[year, 'cashflow'] = - data.loc[year,'opex'] + data.loc[year, 'enPV revenues'] - data.loc[year,"loan_payment"]
        

        # Instantiate cashflow at year 0
        data.loc[0, 'cashflow'] = -total_investment * (1-self.loan.value)
        data = data.sort_index()

        # Calculate cash balance
        for year in data.index:
            if year ==0:
                data.loc[year, 'cash balance'] = data.loc[year, 'cashflow']
            else:
                data.loc[year,'cash balance'] = data.loc[year-1, 'cash balance'] + data.loc[year, 'cashflow']
            

        return data.sort_index()

    def _calc_discounted_cashflow(self) -> pd.DataFrame:
                
        data = self.cashflow.copy()

        total_investment = (self.capex.value + self.devex.value)* self.pv_capacity.value

        for year in data.index:
            if year > 0:
                # Calculate discount rate
                discount_rate = (1+ self.discount_rate.value) ** year

                # Calculate discounted energy values
                data.loc[year, 'enLoad'] = data.loc[year, 'enLoad'] / discount_rate
                data.loc[year, 'enPV total'] = data.loc[year, 'enPV total'] / discount_rate
                data.loc[year, 'enPV self-cons'] = data.loc[year, 'enPV self-cons'] / discount_rate
                data.loc[year, 'enGrid import'] = data.loc[year, 'enGrid import'] / discount_rate
                data.loc[year, 'enGrid export'] = data.loc[year, 'enGrid export'] / discount_rate
                data.loc[year, 'import costs'] = data.loc[year, 'import costs'] / discount_rate
                data.loc[year, 'export sales'] = data.loc[year, 'export sales'] / discount_rate
                # TODO: Discuss this methodology with Oscar - shouldn't it simply be an addition of the above two?
                data.loc[year, 'enPV revenues'] = (data.loc[year, 'combined tariff'] * (data.loc[year, 'enPV total'] * 1_000))
                data.loc[year, 'opex'] = data.loc[year, 'opex'] / discount_rate

                # Calculate loan repayment
                data.loc[year,"loan_payment"] = 0
                if year <= self.loan_period.value:
                    loan_payment = npf.pmt(self.loan_rate.value, self.loan_period.value, (self.loan.value * total_investment))
                    data.loc[year,"loan_payment"] = -round(loan_payment / discount_rate,2)

                # Calculate cashflow & cash balance
                data.loc[year, 'cashflow'] = -data.loc[year,'opex'] + data.loc[year, 'enPV revenues'] - data.loc[year,"loan_payment"]
                data.loc[year,'cash balance'] = data.loc[year-1, 'cash balance'] + data.loc[year, 'cashflow']

        return data.sort_index()
    
    def _calc_LCOE(self) -> Tuple[float]:
        
        # Calculate totals over study period (all discounted)
        investment = (self.capex.value + self.devex.value)* self.pv_capacity.value
        equity =  investment * (1-self.loan.value)
        loan_plus_interest = self.discounted_cashflow["loan_payment"].sum()
        opex  = self.discounted_cashflow['opex'].sum()
        grid_import = self.discounted_cashflow['import costs'].sum()
        grid_export = self.discounted_cashflow['export sales'].sum()
        energy = self.discounted_cashflow['enPV self-cons'].sum() * 1_000    # in kWh
        load   = self.discounted_cashflow['enLoad'].sum() * 1_000            # in kWh

        LCOE = (equity + loan_plus_interest + opex - grid_export) / energy
        BLCOE = (equity + loan_plus_interest + opex - grid_export + grid_import) / load
        
        return LCOE * 1000, BLCOE * 1000

    def _calc_summary(self) -> pd.DataFrame:

        # Save output
        result=pd.DataFrame(index=[self.pv_capacity.value])
        result['load'] = self.cashflow['enLoad'].sum()
        result['energy_pv_total'] = self.cashflow['enPV total'].sum()
        result['energy_pv_self_cons'] = self.cashflow['enPV self-cons'].sum()
        result['energy_grid_import'] = self.cashflow['enGrid import'].sum()
        result['energy_grid_export'] = self.cashflow['enGrid export'].sum()
        result['pv_self_cons'] = (self.cashflow['enPV self-cons'].sum()\
                                        / self.cashflow['enLoad'].sum()) * 100
        result['pv_utilisation'] = (self.cashflow['enPV self-cons'].sum()\
                                        / self.cashflow['enPV total'].sum())* 100
        result['capex'] = self.capex.value * self.pv_capacity.value
        result['opex'] = self.cashflow['opex'].mean()
        result['lcoe'], result['blcoe'] = self._calc_LCOE()
        result['npv'] = self.discounted_cashflow['cashflow'].sum()
        result['irr'] = npf.irr(self.cashflow['cashflow']) * 100
        
        # Calculate point at which cash balance ~ 0 by interpolating values
        # Note, scipy.stat.linregress or np.polyfit do regression by taking both ends of the index.
        # When loans are used, the intercept is incorrect as it is no longer a 1st order equation.
        new_ys = np.round(np.linspace(start=1, 
                                      stop=self.study_period.value, 
                                      num=self.study_period.value*100),2)
        regression = self.cashflow['cash balance'].reindex(new_ys).interpolate()
        result['pay_back_period'] = abs(regression).idxmin()

        return result

    def format_summary(self):
        df = pd.DataFrame(self.data.loc[self.pv_capacity.value].copy())
        df.rename(index={'load':'Total Load (MWh)',
                        'energy_pv_total': 'Total PV Yield (MWh)',
                        'energy_pv_self_cons': 'Total PV Self-consumption (MWh)',
                        'energy_grid_import': 'Toal Energy Grid Import (MWh)',
                        'energy_grid_export': 'Total Energy Grid Export (MWh)',
                        'pv_self_cons': 'Overall PV Self-consumption (%)',
                        'pv_utilisation': 'Overall PV Utilisation (%)',
                        'capex':f'Total CapEx ({self.currency.value})',
                        'opex': f'Average Annual OpEx ({self.currency.value} p.a.)',
                        'lcoe': f'Levelised Cost of Electricity ({self.currency.value}/MWh)',
                        'blcoe': f'Blended Levelised Cost of Electricity ({self.currency.value}/MWh)',
                        'npv': f'Net Present Value (NPV) ({self.currency.value})',
                        'irr': 'Internal Rate of Return (IRR) (%)',
                        'pay_back_period': 'Pay-Back Period (yrs)'},
                    columns={self.pv_capacity.value: 'Output Summary'},
                    inplace=True
        )
        summary = df.copy()
        energy_summary = df[:'Overall PV Utilisation (%)']
        financial_summary = df[f'Total CapEx ({self.currency.value})':]

        return summary, energy_summary, financial_summary