from pathlib import Path 

parent_dir = Path.cwd().parent 
data_dir   = parent_dir / "data" / "processed" / "energy_demand.csv"

storage_capacity                     = 6863.45 # in kWh
maximum_discharge_charge_power_rate  = 0.6 #maximum charging and discharging power 
storage_power                        = maximum_discharge_charge_power_rate * storage_capacity #in kW
initial_SOC                          = 0.0 #initial State of Charge (ratio from capacity)
charging_efficiency                  = 0.94
discharging_efficiency               = 0.94
delta_t                              = 1 #in h
pv_max_power                         = 5417.185 #maximum pv power production in kW
p_supply                             = 0.24 #in €/ kWh
p_fit                                = 0.0778 # in €/kWh
PV_cap                               = 6863.45 #k



