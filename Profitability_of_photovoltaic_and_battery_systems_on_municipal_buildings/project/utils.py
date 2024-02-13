import pandas as pd

def get_results_as_df(model_result, 
                      period: int,
                      data_input: pd.DataFrame) -> pd.DataFrame:
    "get values from pyomo model as pandas dataframe"
    E_supply_   = []
    E_feedin_   = []
    cost_       = []
    charge_     = []
    discharge_  = []
    SOC_        = []
    for t in period:
        E_supply_.append(model_result.E_supply[t].value)
        E_feedin_.append(model_result.E_feedin[t].value)
        cost_.append(model_result.objective1[t].value)
        charge_.append(model_result.charge[t].value)
        discharge_.append(model_result.discharge[t].value)
        SOC_.append(model_result.SOC[t].value)
        
    df_result = pd.DataFrame( 
                                { 
                                    "E_supply": E_supply_,
                                    "E_feedin": E_feedin_,
                                    "cost" : cost_,
                                    "E_charge": charge_,
                                    "E_discharge": discharge_,
                                    "SOC": SOC_,
                                    "E_PV": data_input['Energy PV (kWh)'],
                                    "E_demand": data_input['Energy Demand (kWh)']
                                }
                            )
    
    return df_result

def get_SCR_SSR(df: pd.DataFrame, 
                charge_efficiency: int, 
                discharge_efficiency: int,
                objective: str
               ) -> list[int]:
    """Function to calculate Self Consumption Rate (SCR) and Self Suffiency Rate"""
    df['SCR'] = df['E_PV'] - df['E_feedin'] - (1-charge_efficiency) * df['E_charge'] - (1-(1/discharge_efficiency)) * df['E_discharge']

    SCR = (df['SCR'].sum()/df['E_PV'].sum())*100
    SSR = (df['SCR'].sum()/df['E_demand'].sum())*100

    print(f'SCR with obj.function: {objective} = {SCR}%')
    print(f'SSR with obj.function: {objective} = {SSR}%')
    
    return SCR, SSR
