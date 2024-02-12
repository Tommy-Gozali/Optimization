from pyomo.opt import SolverFactory
import pyomo.environ as pyo
import numpy  as np
import pandas as pd 
import matplotlib.pyplot as plt

from project.config import *
from project.utils  import *

data = pd.read_csv(data_dir)
hour_in_year = [*range(len(data))]

''' FIRST OBJECTIVE FUNCTION '''
#LP model is implemented here
def mincost(data):
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

    def objective_rule(model):
        return pyo.summation(model.objective1)    # first obj function

    model.obj = pyo.Objective(rule = objective_rule, sense=pyo.minimize)

    opt = SolverFactory("glpk")

    opt.solve(model)
    return model

model_result = mincost(data)

df_result = get_results_as_df(model_result, hour_in_year, data)

SCR, SSR  = get_SCR_SSR(df = df_result, charge_efficiency= charging_efficiency, discharge_efficiency=discharging_efficiency)