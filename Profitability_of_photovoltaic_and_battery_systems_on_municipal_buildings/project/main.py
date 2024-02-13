from pyomo.opt import SolverFactory
import pyomo.environ as pyo
import numpy  as np
import pandas as pd 
import matplotlib.pyplot as plt

from project.config import *
from project.utils  import *

data = pd.read_csv(data_dir)
hour_in_year = [*range(len(data))]

z1 = "min electricity procurement cost"
z2 = "min electricity procurement cost and peak power feed-in"

objectives = [z1, z2]

''' FIRST OBJECTIVE FUNCTION '''
#LP model is implemented here
def mincost(data, objective: str):
    model = pyo.ConcreteModel()

    model.i = pyo.RangeSet(0, len(data)-1)
        
    model.E_supply         = pyo.Var(model.i, domain=pyo.NonNegativeReals) #Energy supplied from the grid (kWh)
    model.E_feedin         = pyo.Var(model.i, domain=pyo.NonNegativeReals) #Energy fed to the grid (kWh)

    model.battery_capacity = pyo.Var(domain=pyo.NonNegativeReals)
    model.SOC              = pyo.Var(model.i, domain=pyo.NonNegativeReals, bounds = (0.0, storage_capacity))
    model.charge           = pyo.Var(model.i, domain=pyo.NonNegativeReals)
    model.discharge        = pyo.Var(model.i, domain=pyo.NonNegativeReals)
    model.pv_feedin_max    = pyo.Var(model.i, domain=pyo.NonNegativeReals, bounds = (0.0, pv_max_power))

    model.objective1       = pyo.Var(model.i,domain=pyo.NonNegativeReals)
    model.objective2       = pyo.Var(model.i,domain=pyo.NonNegativeReals)

    def SOC_rule(model, i): #SOC constraints
        if i == 0:
            return model.SOC[i] == initial_SOC * (storage_capacity)+ model.charge[i] * charging_efficiency - model.discharge[i] / discharging_efficiency
        else:
            return model.SOC[i] == model.SOC[i-1] + model.charge[i] * charging_efficiency - model.discharge[i] / discharging_efficiency
                    
    def battery_capacity_rule(model, i):
        return model.SOC[i] <= storage_capacity

    def charge_rule(model,i):
        return model.charge[i]/delta_t <= storage_power

    def discharge_rule(model,i):
        return model.discharge[i]/delta_t <= storage_power

    def feedin_rule(model,i):
        return model.E_feedin[i]/delta_t <= model.pv_feedin_max[i]

    def energy_balance_rule(model, i): #Energy balance constraint
        return model.E_supply[i] - model.E_feedin[i] == data['Energy Demand (kWh)'].iloc[i] - data['Energy PV (kWh)'].iloc[i] + model.charge[i] - model.discharge[i]

    def objective1_rule(model,i):
        return model.objective1[i] == model.E_supply[i]*p_supply - model.E_feedin[i]*p_fit
        
    def objective2_rule(model, i):
        return model.objective2[i] == Lambda * ((model.E_supply[i]*p_supply - model.E_feedin[i]*p_fit)/ohm) + (1-Lambda) * (pv_max_power/PV_cap)
                          
    def only_charge_surplus_rule(model, i):
        return model.charge[i] * (data["Energy Demand (kWh)"].iloc[i] - data['Energy PV (kWh)'].iloc[i]) <= 0
    
    def only_discharge_demand_rule(model, i):
        return model.discharge[i] * (data['Energy PV (kWh)'].iloc[i] - data["Energy Demand (kWh)"].iloc[i]) <= 0
                
    model.energy_balance_rule        = pyo.Constraint(model.i, rule = energy_balance_rule)
    model.SOC_rule                   = pyo.Constraint(model.i, rule = SOC_rule)
    model.battery_capacity_rule      = pyo.Constraint(model.i, rule = battery_capacity_rule)
    model.charge_rule                = pyo.Constraint(model.i, rule = charge_rule)
    model.discharge_rule             = pyo.Constraint(model.i, rule = discharge_rule)
    model.feedin_rule                = pyo.Constraint(model.i, rule = feedin_rule)
    model.only_charge_surplus_rule   = pyo.Constraint(model.i, rule = only_charge_surplus_rule)
    model.only_discharge_demand_rule = pyo.Constraint(model.i, rule = only_discharge_demand_rule)
    model.objective1_rule            = pyo.Constraint(model.i, rule = objective1_rule)
    model.objective2_rule            = pyo.Constraint(model.i, rule = objective2_rule)

    def objective_rule_one(model):
        return pyo.summation(model.objective1)    # first obj function
    
    def objective_rule_two(model):
        return pyo.summation(model.objective2)    # second obj function
    
    if objective == "min electricity procurement cost":
        model.obj = pyo.Objective(rule = objective_rule_one, sense=pyo.minimize)

    elif objective == "min electricity procurement cost and peak power feed-in": 
        model.obj = pyo.Objective(rule = objective_rule_two, sense=pyo.minimize)
        
    opt = SolverFactory("glpk")
    opt.solve(model)
    
    return model

model_result_objective_one, model_result_objective_two = mincost(data, objective=z1), mincost(data, objective=z2)

model_results = [model_result_objective_one, model_result_objective_two]

df_results    = [get_results_as_df(result, hour_in_year, data) for result in model_results]

SSR_SCR = []
for n in range(len(objectives)):
    SSR_SCR.append(get_SCR_SSR(df = df_results[n], 
                               charge_efficiency = charging_efficiency, discharge_efficiency = discharging_efficiency, 
                               objective = objectives[n]))
    