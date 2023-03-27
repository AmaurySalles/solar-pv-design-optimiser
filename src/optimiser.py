import pandas as pd
import plotly.express as px
from platypus import NSGAII, Problem, Real, nondominated



from src.pv_sizing import Scenario, Variable

class PlatypusOptimiser:

    def __init__(self, scenario:Scenario):
        self.scenario = scenario

        self.optimisation_problem()
        self.run_optimiser()

    def problem_function(self, x):
        self.scenario.update_variable(Variable['PV Capacity (kWp)'], x[0])

               # Objective                        # Constraints
        return self.scenario.summary.pv_capacity,[self.scenario.summary.npv, self.scenario.summary.blcoe]

    def optimisation_problem(self):

        self.problem = Problem(1,2)
        self.problem.types[:] = Real(0,5_000)
        self.problem.function = self.problem_function
        self.problem.constraints[:] = "<0"
        self.problem.directions[0] = Problem.MAXIMIZE
        self.problem.directions[1] = Problem.MINIMIZE
    
    def run_optimiser(self):
        self.algorithm = NSGAII(self.problem)
        self.algorithm.run(100)

        # self.solutions = []
        # for solution in algorithm.result:
        #     self.solution = solution
        #     print(solution.objectives)
        #     print(solution.variables)
        self.solutions = [s for s in self.algorithm.result if s.feasible]

    def graph_solution(self):
        
        graph_data = pd.DataFrame()
        graph_data.index = [s.variables[0] for s in self.solutions]
        graph_data['NPV'] = [s.objectives[1][0] for s in self.solutions]
        graph_data['BLCOE'] = [s.objectives[1][1] for s in self.solutions]
        # graph_data[1] = [s.objectives[1] for s in self.solutions]

        graph_data = graph_data[graph_data['NPV'] > 0].sort_index()
        print(graph_data)

        fig = px.scatter(graph_data['NPV'])

        return fig


class ScipyOptimiser:

    def __init__(self,
                scenario: Scenario,
                objective:str,
                optimisation:str,
                variable:str,
                init_value:float,
                to_value:float=0):

        self.scenario = scenario
        self.objective = objective
        self.optimisation = optimisation
        self.variable = variable
        self.init_value = init_value
        self.to_value = to_value

        self.run_optimiser()

    def optimising_function_wrapper(self, x):
        """
        This function allows the optimiser to be customisable in terms of variable 
        and optimisation strategy (min, max, goal-seek).

        Args:
            x (list[int]): the value of the variable which is iterated by the optimiser

        Returns:
            float: Scenario objective value (according to optimisation strategy)
       
        """
        print(x)

        # Updating the scenario variable will trigger a scenario update
        match self.variable:
            case "Study Period":
                self.scenario.study_period = x[0]
            case "Discount Rate":
                self.scenario.discount_rate = x[0]
            case "PV Capacity":
                self.scenario.pv_capacity = x[0]
            case "Module Degradation":
                self.scenario.pv_degradation = x[0]
            case "CAPEX":
                self.scenario.capex = x[0]
            case "OPEX":
                self.scenario.opex = x[0]
            case "Import Tariff":
                self.scenario.import_tariff = x[0]
            case "Export Tariff":
                self.scenario.export_tariff = x[0]
            case _:
                raise ValueError('Variable name not recognised.')
        
        # Run scenario calculations
        self.scenario.update_scenario()

        # After which, we can alter the results, depending on the optimisation strategy
        match self.optimisation:
            case 'Min':
                return self.scenario.summary[self.objective]
            case 'Max':
                # Inversing the output from the function will maximise the function output
                return self.scenario.summary[self.objective] * -1
            case 'Goal-Seek':
                # Subtracting the goal from the function output will goal-seek by minimising the difference down to zero.
                return self.scenario.summary[self.objective] - self.to_value
            case _:
                raise ValueError("Optimisation strategy possible values: 'Min', 'Max', 'Goal-seek'.")

    def run_optimiser(self):
               
        # Contraint: objective cannot be lower than 0
        constraints = ({"type":"ineq",
                        "fun": lambda x: x - 0},
                        {"type":"ineq",
                        "fun": lambda x: x - 1_000_000})
        
        Bounds(0,None)
        
        # Optimisation function from scipy.optimise.minimize
        results = minimize(fun = self.optimising_function_wrapper,
                           x0 = self.init_value,
                           constraints = constraints,
                        #    bounds=bounds,
                           options={"disp":True, "maxiter":20})
        

        return self.scenario

