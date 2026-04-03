# -*- coding: utf-8 -*-
"""
TCOmodel
========

This module contains the classes used for modelling the costs of a BEV fleet,
and several functions useful for data processing and visualization.

Main Features
-------------

The main features include:
    Classes for estimating the costs of BEV fleet, charging equipment, 
    digital solutions and mining workforce
    
    Functions for summarizing all cashflows and determining the total cost of 
    ownership of the mining BEV fleet
    
    Functions for visualizing the TCO results

"""

import sys
import pandas as pd
import math
from bisect import bisect_right
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as tkr
try:
    from matplotlib_inline.backend_inline import set_matplotlib_formats
except ImportError:
    def set_matplotlib_formats(*args, **kwargs):
        pass
import numpy as np
import numpy_financial as nf
from collections import defaultdict


class FleetCell():
    """
    Class used to represent a fleet of vehicles.
    
    This class is used to calculate the CAPEX and OPEX of a fleet of vehicles 
    in a mine.
    
    An instance of the class should represent a homogeneous subset of vehicles 
    in the overall mine fleet. If the overall fleet contains several different
    makes or models of vehicles, each group of vehicles should be described by 
    its own FleetCell object.
    
    Attributes
    ----------
    fleet_params : dict
        Dictionary containing the TCO analysis input parameters describing 
        the fleet to be analyzed. The keys are described in Notes below.
    vehicles_params : dict
        Dictionary containing data on the type of vehicle the fleet is 
        made up from. The keys are described in Notes below.
    evse_params : dict
        Dictionary containing data on the type of EV support equipment 
        (charger) used by the fleet. The keys are described in Notes below.
    business_params : dict
        Dictionary containing the TCO analysis input parameters relating to 
        running the business (financial, energy costs, subsidies, labour 
        rates, etc.). The keys are described in Notes below.
    fleet_op_hours : pd.DataFrame or dict
        Pandas DataFrame or dict containing the operating hours per vehicle in the 
        fleet per month. The keys are described in Notes below.
    capex_dates : dict, optional
        Dictionary containing the start and end dates for any CAPEX cost
        DataFrames in the TCO analysis. The keys are 'start date' and 'end date'
        and the corresponding values should be date strings in format YYYY-MM-DD.
        Required to perform the CAPEX analyses.
    opex_dates : dict, optional
        Dictionary containing the start and end dates for any OPEX cost
        DataFrames in the TCO analysis. The keys are 'start date' and 'end date'
        and the corresponding values should be date strings in format YYYY-MM-DD.
        Required to perform the OPEX analyses.
    production_sched : pd.DataFrame or dict, optional
        Pandas DataFrame or dict containing the tonnes of material produced 
        per month. The keys are described in Notes below. The default is None.
    location : str, optional
        Geographic location of the fleet in the mine. The default is None.
    info : str
        Description of the object class.
    vehicles_required : pd.DataFrame or dict
        Pandas DataFrame or dict containing the total number of vehicles required per 
        month to meet the production schedule.
    capex_timeline : pd.DataFrame
        Pandas DataFrame containing the monthly CAPEX analysis results.
    opex_timeline : pd.DataFrame
        Pandas DataFrame containing the monthly OPEX analysis results.
    energy_consumed : pd.DataFrame
        Pandas DataFrame containing the energy consumed by the fleet per month.
    GHG_emissions : pd.DataFrame
        Pandas DataFrame containing the amount of GHG emissions produced by the 
        fleet per month.
    energy_costs : pd.DataFrame
        Pandas DataFrame containing the cost of electricy for the fleet per month.
    baas_costs : pd.DataFrame
        Pandas DataFrame containing the cost of BAAS service contracts for the 
        fleet per month.
    maintenance_costs : pd.DataFrame
        Pandas DataFrame containing the maintenance costs per vehicle in the 
        fleet per month.
    opex_subsidies : pd.DataFrame
        Pandas DataFrame containing the low carbon fuel OPEX subsidy per month.
    fleet_costs : pd.DataFrame
        Pandas DataFrame containing the fleet CAPEX costs per month.
    fleet_subsidies : pd.DataFrame
        Pandas DataFrame containing the CAPEX subsidy per month.
    variables : dict
        Dictionary containing the class instance's variables.
    capex_variables : dict
        Dictionary containing the class instance's CAPEX variables.
    opex_variables : dict
        Dictionary containing the class instance's OPEX variables.
    
    Methods
    -------
    convert_to_df(inp_var)
        Converts a dictionary (inp_var) to a Pandas DataFrame.
    energy_consumption_analysis()
        Calculates the energy consumption of the fleet.
    energy_cost_analysis()
        Calculates the energy usage costs for the fleet.
    peak_power()
        Calculates the peak power draw from a charger.
    power_consumption_analysis()
        Calculates the power consumption of the fleet.
    power_cost_analysis()
        Calculates the power consumption costs for the fleet.
    GHG_emissions_analysis()
        Calculates the GHG emissions produced by the fleet.
    baas_costs_analysis
        Calculates the Battery As A service costs for the fleet.
    maint_interval_costs(cumul_op_hours, op_hours, cost_intervals)
        Calculates the maintenance cost per hour based on the operating hours 
        of the fleet and the maintenance intervals.
    maintenance_costs_analysis()
        Calculates the maintenance costs for each vehicle in the fleet.
    opex_subsidies_analysis()
        Calculates the OPEX subsidies applied to the fleet.
    fleet_purchase_analysis()
        Calculates the fleet purchase costs based on the purchase schedule.
    capex_subsidies_analysis()
        Calculates the CAPEX subsidies applied to the fleet.
    opex_analysis()
        Calculates the total OPEX (operating costs) for the fleet.
    capex_analysis()
        Calculates the total CAPEX (capital costs) for the fleet.
    execute_analysis()
        Executes the steps to analyse the fleet object's costs.
    add_variable(name, value, variables_dict)
        Adds objects to the variables dictionary.
    get_variable(name)
        Returns objects from the variables dictionary by name.
    
    Notes
    -----
    Keys in the input dictionary: **fleet_params**
    
    model : str
        Model name / number for the vehicles.
    vehicles : int
        Number of vehicles in the fleet.
    batteries : int
        Number of batteries in the fleet.
    fleet purchase schedule : list
        A list specifying the dates each fraction of the fleet is purchased.
        E.g. if the payment schedule is 20% on Jan 1st 2022 and the remaining 
        80% a year later, the fleet purchase schedule is entered as the 
        following list:
            [['2022-01-01', 0.20], ['2023-01-01', 0.80]]
    subsidies : list
        A list specifying the dates any subsidies are applied to the fleet 
        CAPEX. Subsidies are entered as a fraction of the total fleet purchase 
        costs. E.g. if a 10% subsidy on the purchase price is applied 6 months 
        after the initial payment, the subsidies are entered as the following 
        list:
            [['2022-06-01', 0.10]]
    
    Keys in the input dictionary: **vehicles_params**
    
    energy consumption : int, float
        Average energy consumption of the BEVs in kW.
    BaaS monthly rate : int, float
        Monthly BaaS fee per vehicle.
    BaaS charger monthly rate : int, float
        Monthly BaaS fee per charger.
    unit price : int, float
        Purchase price of a vehicle.
    maintenance costs : dict
        A dictionary describing the maintenance costs for set intervals of 
        machine operation. The first key is the "Machine Hours" with a 
        corresponding list of the interval hours. The remaining keys allow for
        cost estimates of various components/sub-systems. E.g. if maintenance 
        costs are estimated on a 250hr interval basis, then the resulting 
        dictionary is the following:
        
            {"Machine Hours": [250, 500, 750, 1000],
            "Battery": [1000, 1500, 2500, 2000],
            "Inverter": [100, 1000, 1500, 2000],
            "Tires": [500, 500, 500, 1800]}
    
    Keys in the input dictionary: **evse_params**
    
    model : str
        Model name / number for the chargers.
    cooling cube power : int, float
        Rated power draw for any cooling equipment.
    efficiency : float
        Total energy conversion efficiency for the charger.
    power factor : float
       Power Factor for the charger, indicating power conversion efficiency. 
    
    Keys in the input dictionary: **business_params**
    
    energy costs : dict
        A dictionary of energy cost parameters. Keys include: `cost per kWh`...
        Values are either int or float.
    emissions factors : dict
        A dictionary of GHG calculation parameters. Keys include: 
        `grid CO2e emissions`... Values are either int or float.
    subsidies : dict
        A dictionary of OPEX subsidy parameters. Keys include: `fuel rebate`...
        Values are either int or float.
    
    Keys in the input dictionary: **fleet_op_hours**
    
    date : list
        A list of dates in YYYY-MM-DD format.
    Vehicle_ID : list
        A list of operating hours for each month for the vehicle `Vehicle_ID` as
        either int or float. Each vehicle in the fleet gets its own key and list
        of operating hours. The keys for each vehicle (Vehicle_ID) must be unique.

    Keys in the input dictionary: **production_sched**

    date : list
        A list of dates in YYYY-MM-DD format.
    tonnes/month
        A list of float or int values representing the tonnes of ore moved per 
        month, for a production fleet.
    
    Examples
    --------
    >>> import bevcost.TCOmodel as tco
    >>> capex_dates = {'start date': '2022-01-01', 
    ...                'end date': '2022-02-01'}
    >>> opex_dates = {'start date': '2022-01-01', 
    ...               'end date': '2022-02-01'}
    >>> fleet_op_hours = pd.DataFrame({'date': ['01/01/2022', 
    ...                                         '01/02/2022'],
    ...                                'LHD-1': [100, 
    ...                                          100]})
    >>> production_sched = pd.DataFrame({'date': ['01/01/2022', 
    ...                                           '01/02/2022'],
    ...                                  'tonnes/month': [100, 
    ...                                                   100]})
    >>> business_params = {'energy costs': {'cost per kWh': 0.05},
    ...                    'emissions factors': {'grid CO2e emissions': 10.0},
    ...                    'subsidies': {'fuel rebate': 150}}
    >>> fleet_params = {'vehicles': 1,
    ...                 'fleet purchase schedule': [['2022-01-01', 0.20], 
    ...                                             ['2022-02-01', 0.80]],
    ...                 'subsidies': [['2022-02-01', 0.1]]}
    >>> vehicles_params = {'energy consumption': 50,
    ...                    'BaaS monthly rate': 1000,
    ...                    'BaaS charger monthly rate': 10000,
    ...                    'unit price': 500000,
    ...                    'maintenance costs': {"Machine Hours": [250, 
    ...                                                            500, 
    ...                                                            750, 
    ...                                                            1000],
    ...                                          "Major Components": [10000, 
    ...                                                               20000, 
    ...                                                               25000, 
    ...                                                               30000]}}
    
    >>> fleet_1 = tco.FleetCell(fleet_params, 
    ...                         vehicles_params, 
    ...                         business_params, 
    ...                         fleet_op_hours, 
    ...                         capex_dates=capex_dates,
    ...                         opex_dates=opex_dates,
    ...                         production_sched=production_sched,
    ...                         location=None)
    >>> fleet_1.execute_analysis()
    
    >>> fleet_1.fleet_costs
            date  fleet capex
    0 2022-01-01       100000
    1 2022-02-01       400000
    >>> fleet_1.maintenance_costs
            date  LHD-1  maintenance costs
    0 2022-01-01   4000               4000
    1 2022-02-01   4000               4000
    
    """
    
    def __init__(self, fleet_params, vehicles_params, evse_params, business_params, 
                 fleet_op_hours, capex_dates=None, opex_dates=None, 
                 production_sched=None, location=None):
        """Class used to represent a fleet of vehicles.

        Parameters
        ----------
        fleet_params : dict
            Dictionary containing the TCO analysis input parameters describing 
            the fleet to be analyzed. The keys are described in Notes below.
        vehicles_params : dict
            Dictionary containing data on the type of vehicle the fleet is 
            made up from. The keys are described in Notes below.
        evse_params : dict
            Dictionary containing data on the type of EV support equipment 
            (charger) used by the fleet. The keys are described in Notes below.
        business_params : dict
            Dictionary containing the TCO analysis input parameters relating to 
            running the business (financial, energy costs, subsidies, labour 
            rates, etc.). The keys are described in Notes below.
        fleet_op_hours : pd.DataFrame or dict
            Pandas DataFrame or dict containing the operating hours per vehicle 
            in the fleet per month. The keys are described in Notes below.
        capex_dates : dict, optional
            Dictionary containing the start and end dates for any CAPEX cost
            DataFrames in the TCO analysis. The keys are 'start date' and 'end date'
            and the corresponding values should be date strings in format YYYY-MM-DD.
            Required to perform the CAPEX analyses.
        opex_dates : dict, optional
            Dictionary containing the start and end dates for any OPEX cost
            DataFrames in the TCO analysis. The keys are 'start date' and 'end date'
            and the corresponding values should be date strings in format YYYY-MM-DD.
            Required to perform the OPEX analyses.
        production_sched : pd.DataFrame or dict, optional
            Pandas DataFrame or dict containing the tonnes of material produced 
            per month. The keys are described in Notes below. The default is None.
        location : str, optional
            Geographic location of the fleet in the mine. The default is None.
        """
        self.info = "fleet"
        
        # Parameters describing the fleet
        self.fleet_params = fleet_params 
        
        # Parameters describing the vehicle type making up the fleet
        self.vehicles_params = vehicles_params 
        
        # Parameters describing the type of EV support equipment (chargers) used
        # with the fleet's vehicles
        self.evse_params = evse_params 
        
        # Fleet location designation
        self.location = location 
        
        # Parameters relating to business operations
        self.business_params = business_params 
        
        # Production schedule for the fleet cell
        if(production_sched is not None):
            self.production_sched = self.convert_to_df(production_sched) 
            self.production_sched['date'] = pd.to_datetime(self.production_sched['date'], format='%Y-%m-%d')
        
        # Blank CAPEX and OPEX schedules for the fleet costs
        if(capex_dates):
            self.capex_dates = capex_dates
            start, end = [datetime.strptime(_, "%Y-%m-%d") for _ in list(capex_dates.values())]
            self.capex_timeline = pd.date_range(start, end, freq='MS').to_frame(index=False, name='date')
        
        if(opex_dates):
            start, end = [datetime.strptime(_, "%Y-%m-%d") for _ in list(opex_dates.values())]
            self.opex_dates = opex_dates
            self.opex_timeline = pd.date_range(start, end, freq='MS').to_frame(index=False, name='date')
        
        # DataFrame of the operating hours for the fleet
        self.fleet_op_hours = self.convert_to_df(fleet_op_hours)
        
        # List of the vehicle IDs
        self.vehicle_IDs = self.fleet_op_hours.keys()[1:] 
        
        # DataFrame of the total number of vehicles in the fleet each month
        # based on the fleet operating hours
        fleet_hours = self.fleet_op_hours.iloc[:,1:]
        fleet_hours = fleet_hours.replace(0, np.nan)
        self.vehicles_required = pd.DataFrame(data=fleet_hours.count(axis='columns'), 
                                              columns=["vehicles required"])
        
        # Dictionaries to save the object's attributes or other variables 
        self.variables = {}
        self.capex_variables = {}
        self.opex_variables = {}
        
        self.add_variable("location", self.location, self.variables)
        self.add_variable("operating hours", self.fleet_op_hours, self.variables)
    
    def add_variable(self, name, value, variables_dict):
        """Add variables to the variables dictionary."""
        variables_dict[name] = value
    
    def get_variable(self, name):
        """Return variables in the variables dictionary."""
        return self.variables.get(name)
    
    def convert_to_df(self, inp_var):
        """Convert an input dictionary to a Pandas DataFrame."""
        if(type(inp_var) is dict):
            return pd.DataFrame(inp_var)
        
        elif(type(inp_var) is pd.core.frame.DataFrame): 
            return inp_var
        
        else:
            print(f"TypeError converting FleetCell argument to DataFrame: {inp_var}", file=sys.stderr)
    
    def energy_consumption_analysis(self):
        """Calculate the energy consumption of the fleet."""
        # Energy costs array
        energy_consumed = self.opex_timeline.copy() # Energy costs are incurred based on operations
        energy_consumed["energy consumption"] = 0
        
        # Determine the average energy consumption of the fleet's vehicles
        average_consumption = self.vehicles_params["energy consumption"]
        
        # Determine the monthly energy consumption of the fleet
        for mnth in range(len(energy_consumed)):
            
            # Energy costs (in kWh) are calculated based on the total fleet 
            # operating hours and the average energy consumption of those vehicles
            energy_consumed["energy consumption"].iat[mnth] = self.fleet_op_hours.iloc[mnth][1:].sum() * average_consumption

        return energy_consumed
    
    def energy_cost_analysis(self):
        """Calculate the energy usage costs for the fleet."""
        energy_costs = self.opex_timeline.copy()
        energy_costs["energy costs"] = 0
        energy_costs["energy costs"] = self.energy_consumed["energy consumption"] \
                                       * self.business_params["energy costs"]["cost per kWh"]
        
        return energy_costs
    
    def peak_power(self, evse_name, evse_num):
        """Calculate the peak power draw from a charger."""
        if('double' in evse_name):
            mult_factor = 2
            rounded = math.ceil(evse_num)
        else:
            mult_factor = 1
            rounded = math.ceil(evse_num / 2.0)
        
        charge_power = self.vehicles_params["charging power"]
        cooler_power = self.evse_params["cooling cube power"]
        charger_efficiency = self.evse_params["efficiency"]
        power_factor = self.evse_params["power factor"]
        
        peak = ((mult_factor*evse_num*charge_power / 4.0) + rounded*cooler_power) \
                	/ charger_efficiency / power_factor
        
        return peak
    
    def power_consumption_analysis(self):
        """Calculate the power consumption of the fleet."""
        # Power costs are incurred based on delivery dates of equipment
        power_consumed = self.opex_timeline.copy() 
        power_consumed["power consumption"] = 0
        
        for mth in range(len(power_consumed)):
            evse_name = self.evse_params["model"]
            evse_num = self.vehicles_required["vehicles required"].iat[mth]
            
            power_consumed["power consumption"].iat[mth] = self.peak_power(evse_name, evse_num)
            
        return power_consumed
    
    def power_cost_analysis(self):
        """Calculate the power consumption costs for the fleet."""
        power_costs = self.opex_timeline.copy()
        power_costs["power costs"] = 0
        
        power_costs["power costs"] = self.power_consumed["power consumption"] \
                                     * self.business_params["energy costs"]["cost per kVA"]
        
        return power_costs
        
    def GHG_emissions_analysis(self):
        """Calculate the GHG emissions produced by the fleet."""
        GHG_emissions = self.opex_timeline.copy()
        GHG_emissions["emissions"] = self.energy_consumed["energy consumption"] \
                                     * self.business_params["emissions factors"]["grid CO2e emissions"] / 1000.0
        
        return GHG_emissions
    
    def baas_costs_analysis(self):
        """Calculate the Battery As A service costs for the fleet."""
        # BaaS costs array
        baas_costs = self.opex_timeline.copy() # BaaS costs are incurred based on delivery dates of equipment
        baas_costs["baas costs"] = 0
        
        baas_rate = self.vehicles_params["BaaS monthly rate"]
        charger_baas_rate = self.evse_params["BaaS charger monthly rate"]
        
        for mnth in range(len(baas_costs)):
            # BaaS costs include BaaS for the vehicle and for the associated charger/support equipment
            vehicle_count = self.vehicles_required["vehicles required"].iat[mnth]
            baas_costs["baas costs"].iat[mnth] = vehicle_count * (baas_rate + charger_baas_rate)
        
        return baas_costs
    
    def maint_interval_costs(self, cumul_op_hours, op_hours, cost_intervals):
        """Calculate the maintenance cost per hour from the maintenance intervals."""
        # Find the index for the appropriate maintenance interval
        int_index = bisect_right(cost_intervals['Machine Hours'].values, cumul_op_hours)

        if(int_index >= len(cost_intervals)):
            int_index = len(cost_intervals)-1
        
        # Find the hourly rate of maintenance activities
        if(int_index == 0):
            maint_rate = (cost_intervals.iloc[int_index].sum() - cost_intervals.iloc[int_index]['Machine Hours']) / cost_intervals.iloc[int_index]['Machine Hours']
        else:
            maint_rate = (cost_intervals.iloc[int_index].sum() - cost_intervals.iloc[int_index]['Machine Hours']) / (cost_intervals.iloc[int_index]['Machine Hours'] - cost_intervals.iloc[int_index-1]['Machine Hours'])
        
        return maint_rate*op_hours
    
    def maintenance_costs_analysis(self):
        """Calculate the maintenance costs for each vehicle in the fleet."""        
        # Use the defined maintenance cost intervals
        cost_intervals = pd.DataFrame(self.vehicles_params['maintenance costs'])
        
        bev_maint_costs = self.opex_timeline.copy() # Maintenance costs are incurred during production
        maintenance_costs = self.opex_timeline.copy() # Maintenance costs are incurred during production

        # Add columns for each vehicle
        for vehicle_name in self.vehicle_IDs:
            bev_maint_costs[vehicle_name] = 0
        
        for mnth in range(len(bev_maint_costs)):
            
            for vhc_name in self.vehicle_IDs:
                # Maintenance costs are based on operating hours and cumuluative operating hours for each vehicle
                cumul_op_hours = self.fleet_op_hours[vhc_name].cumsum().iat[mnth]
                op_hours = self.fleet_op_hours[vhc_name].iat[mnth]
                
                bev_maint_costs[vhc_name].iat[mnth] = self.maint_interval_costs(cumul_op_hours, op_hours, cost_intervals)
        
        maintenance_costs["maintenance costs"] = bev_maint_costs[self.vehicle_IDs].sum(axis=1)
        
        return bev_maint_costs, maintenance_costs
    
    def opex_subsidies_analysis(self):
        """Calculate the OPEX subsidies applied to the fleet."""
        opex_subsidies = self.opex_timeline.copy()
        opex_subsidies["opex subsidies"] = -(self.energy_consumed["energy consumption"] \
                                             * self.business_params["subsidies"]["fuel rebate"] / 1000.0)
        
        return opex_subsidies
    
    def fleet_purchase_analysis(self):
        """Calculate the fleet purchase costs based on the purchase schedule."""
        # Determine fleet capex
        fleet_costs = self.capex_timeline.copy() 
        fleet_costs["fleet capex"] = 0
        fleet_costs = fleet_costs.set_index("date")
        
        total_capex = self.fleet_params["vehicles"] * self.vehicles_params["unit price"]
        
        for split in self.fleet_params["fleet purchase schedule"]:
            
            date = datetime.strptime(split[0], "%Y-%m-%d")
            fleet_costs.loc[date] = split[1] * total_capex
        
        fleet_costs = fleet_costs.reset_index()
            
        return fleet_costs
    
    def capex_subsidies_analysis(self):
        """Calculate the CAPEX subsidies applied to the fleet."""
        capex_subsidies = self.capex_timeline.copy()
        capex_subsidies["capex subsidies"] = 0
        capex_subsidies = capex_subsidies.set_index("date")
        
        total_capex = self.fleet_params["vehicles"] * self.vehicles_params["unit price"]
        
        for split in self.fleet_params["subsidies"]:
            
            date = datetime.strptime(split[0], "%Y-%m-%d")
            capex_subsidies.loc[date] =  -(split[1] * total_capex)
        
        capex_subsidies = capex_subsidies.reset_index()
        
        return capex_subsidies
    
    def opex_analysis(self):
        """Calculate the total OPEX (operating costs) for the fleet.
        
        OPEX for the fleet may include energy costs, BaaS service contract
        costs, maintenance costs and subsidies.
        """
        ## Energy & power costs
        if("energy costs" in self.business_params.keys()):
            # Energy usage costs
            if("cost per kWh" in self.business_params["energy costs"].keys()):
                # Energy consumption
                self.energy_consumed = self.energy_consumption_analysis()
                self.add_variable("energy consumption", self.energy_consumed, self.variables)
                
                self.energy_costs = self.energy_cost_analysis()
                self.add_variable("energy costs", self.energy_costs, self.variables)
                self.add_variable("energy costs", self.energy_costs, self.opex_variables)
            
            # Power usage costs
            if("cost per kVA" in self.business_params["energy costs"].keys()):
                # Power consumption
                self.power_consumed = self.power_consumption_analysis()
                self.add_variable("power consumption", self.power_consumed, self.variables)
                
                # Power costs
                self.power_costs = self.power_cost_analysis()
                self.add_variable("power costs", self.power_costs, self.variables)
                self.add_variable("power costs", self.power_costs, self.opex_variables)
        
        ## BaaS costs
        if("BaaS monthly rate" in self.vehicles_params.keys()):
            self.baas_costs = self.baas_costs_analysis()
            self.add_variable("baas costs", self.baas_costs, self.variables)
            self.add_variable("baas costs", self.baas_costs, self.opex_variables)
        
        ## Fleet maintenance costs
        if("maintenance costs" in self.vehicles_params.keys()):
            self.bev_maint_costs, self.maintenance_costs = self.maintenance_costs_analysis()
            self.add_variable("bev maintenance costs", self.bev_maint_costs, self.variables)
            self.add_variable("maintenance costs", self.maintenance_costs, self.variables)
            self.add_variable("maintenance costs", self.maintenance_costs, self.opex_variables)
        
        ## GHG emissions
        if("emissions factors" in self.business_params.keys()):
            if("grid CO2e emissions" in self.business_params["emissions factors"].keys()):
                self.GHG_emissions = self.GHG_emissions_analysis()
                self.add_variable("emissions", self.GHG_emissions, self.variables)
        
        ## OPEX subsidies/savings
        if("subsidies" in self.business_params.keys()):
            if("fuel rebate" in self.business_params["subsidies"].keys()):
                self.opex_subsidies = self.opex_subsidies_analysis()
                self.add_variable("opex subsidies", self.opex_subsidies, self.variables)
                self.add_variable("opex subsidies", self.opex_subsidies, self.opex_variables)

    def capex_analysis(self):
        """Calculate the total CAPEX (capital costs) for the fleet.
        
        CAPEX for the fleet may include vehicle purchase costs and purchase 
        subsidies.
        """
        ## Fleet capital costs
        if("vehicles" in self.fleet_params.keys()):
            self.fleet_costs = self.fleet_purchase_analysis()
            self.add_variable("fleet capex", self.fleet_costs, self.variables)
            self.add_variable("fleet capex", self.fleet_costs, self.capex_variables)
        
        ## CAPEX subsidies/savings
        if("subsidies" in self.fleet_params.keys()):
            self.capex_subsidies = self.capex_subsidies_analysis()
            self.add_variable("capex subsidies", self.capex_subsidies, self.variables)
            self.add_variable("capex subsidies", self.capex_subsidies, self.capex_variables)

    def execute_analysis(self):
        """Execute the steps to analyse the fleet object's costs."""
        if(self.opex_dates):
            self.opex_analysis()
            
        if(self.capex_dates):
            self.capex_analysis()


class InfraCell():
    """
    A class used to represent BEV-related infrastructure.
    
    This class is used to calculate the CAPEX and OPEX of the BEV infrastructure 
    in a mine. Infrastructure types include charging equipment, electrical 
    equipment, charging stations and maintenance bays.
    
    Attributes
    ----------
    data : dict
        Dictionary containing the input data describing the infrastructure 
        to be analyzed. The keys are described in Notes below.
    facility_params : list
        List of dictionaries containing data on each type of infrastructure.
        The keys are described in Notes below.
    evse_params : list, dict
        List of dictionaries containing data on each type of electrical 
        equipment or a single dictionary if only one equipment type is 
        required in the analysis. The keys are described in Notes below.
    capex_dates : dict, optional
        Dictionary containing the start and end dates for any CAPEX cost
        DataFrames in the TCO analysis. The keys are 'start date' and 'end date'
        and the corresponding values should be date strings in format YYYY-MM-DD.
        Required to perform the CAPEX analyses.
    opex_dates : dict, optional
        Dictionary containing the start and end dates for any OPEX cost
        DataFrames in the TCO analysis. The keys are 'start date' and 'end date'
        and the corresponding values should be date strings in format YYYY-MM-DD.
        Required to perform the OPEX analyses.
    info : str
        Description of the object class.
    evse_dict : dict
        Dictionary of dictionaries containing data on each type of electrical 
        equipment. Each item's key is the EVSE model name.
    evse_stock : dict
        Dictionary containing the number of each type of EVSE (Electric Vehicle
        Support Equipment) model. Keys are model names, values are the number 
        of equipment.
    location : str, optional
        Geographic location of the infrastructure in the mine. The default is None.
    capex_timeline : pd.DataFrame
        Pandas DataFrame containing the months of the CAPEX analysis.
    opex_timeline : pd.DataFrame
        Pandas DataFrame containing the months of the OPEX analysis.
    infra_type : str
        Label for the object's infrastructure type. Options include: 
        "charging station"
    capex_sched : pd.DataFrame
        Pandas DataFrame containing the schedule for incurring CAPEX costs.
    opex_sched : pd.DataFrame
        Pandas DataFrame containing the schedule for incurring OPEX costs.
    const_sched : pd.DataFrame
        Pandas DataFrame containing the schedule for incurring construction costs.
    baas_costs : pd.DataFrame
        Pandas DataFrame containing the BAAS (Battery As A Service) costs per 
        month.
    equipment_costs : pd.DataFrame
        Pandas DataFrame containing the EVSE CAPEX costs per month.
    construction_costs : float
        Pandas DataFrame containing the infrastructure construction costs per 
        month.
    variables : dict
        Dictionary containing the class instance's variables.
    capex_variables : dict
        Dictionary containing the class instance's CAPEX variables.
    opex_variables : dict
        Dictionary containing the class instance's OPEX variables.
    
    Methods
    -------
    charging_station_analysis()
        Calculates the costs for construction of a charging station.
    charging_equipment_analysis()
        Calculates the purchase costs for charging equipment.
    baas_costs_analysis()
        Calculates the Battery As A service (BAAS) costs for the infrastructure.
    capex_analysis()
        Calculates the total CAPEX (capital costs) for the infrastructure.
    opex_analysis()
        Calculates the total OPEX (operating costs) for the infrastructure.    
    execute_analysis()
        Executes the steps to analyse the infrastructure object's costs.
    add_variable(name, value, variables_dict)
        Adds objects to the variables dictionary.
    get_variable(name)
        Returns objects from the variables dictionary by name.
    
    Notes
    -----
    Keys in the input dictionary: **data**
    
    infrastructure type : str
        Type of BEV infrastructure, options include: charging station.
    charger-cooler ratio : int
        Ratio of chargers to cooling equipment.
    cable length : float
        Length of power cable that must be installed in/to the infrastructure.
    batteries : int
        Number of batteries that can be accommodated in a charging station.
    evse : dict
        Dictionary containing the types of EV charging equipment located within
        the infrastructure, keys are the EVSE model name and values are the 
        number of EVSE.
    construction schedule : list
        A list specifying the dates each fraction of the infrastructure 
        construction costs are paid. E.g. if the construction schedule is 20% 
        on Jan 1st 2022 and the remaining 80% a year later, the construction 
        schedule is entered as the following list:
            [['2022-01-01', 0.20], ['2023-01-01', 0.80]]
    capex schedule : list
        A list specifying the dates each fraction of the equipment purchase 
        costs are paid. E.g. if the CAPEX schedule is 80% on Jan 1st 2022 and 
        the remaining 20% is paid three months later, the CAPEX schedule is 
        entered as the following list:
            [['2022-01-01', 0.80], ['2022-04-01', 0.20]]
    BaaS subscription : dict
        A dictionary with two entries, the first is the "frequency" which the 
        subscription is paid (options include: monthly). The second is the 
        "dates" defining the start and end dates for the BAAS subscription.
        This is defined as a dictionary with the keys 'start date' and 'end date'
        and the corresponding values should be date strings in format YYYY-MM-DD.
    
    Keys in the input dictionary: **facility_params**
    
    infrastructure type : str
        Type of BEV infrastructure, options include: charging station.
    development rate ($/m) : float
        The cost per metre for U/G development required to excavate space for 
        the infrastructure.
    development cost : float
        The installation/commissioning costs associated with the infrastructure.
    cable pull ($/m) : float
        The cost per metre to install power cable for the infrastructure.
    
    Keys in the input dictionary: **evse_params**
    
    evse type : str
        The type of EV support equipment, e.g. charger.
    model : str
        The model name for the EVSE.
    charge current : float
        The charging current, for an EV charger.
    cooling cube power : float
        The rated power consumption for EVSE cooling equipment.
    efficiency : float
        The charger efficiency (between 0 and 1).
    power factor : float
        The power factor for a charger.
    current derating : float
        The current derating factor for a charger.
    BaaS charger monthly rate : float
        The monthly BAAS subscription costs for a charger.
    unit price : float
        The purchase price for a charger.
    
    Examples
    --------
    >>> import bevcost.TCOmodel as tco
    >>> capex_dates = {'start date': '2022-01-01', 
    ...                'end date': '2022-02-01'}
    >>> opex_dates = {'start date': '2022-01-01', 
    ...               'end date': '2022-02-01'}
    >>> infra_data = {"infrastructure type": "charging station",
    ...               "charger-cooler ratio": 1,
    ...               "cable length": 100.0,
    ...               "batteries": 2,
    ...               "evse": {"LH411B - single charger": 1},
    ...               "construction schedule": [["2022-02-01", 1.0]],
    ...               "capex schedule": [["2022-02-01", 1.0]],
    ...               "BaaS subscription": {"frequency": "monthly",
    ...                                     "dates": {"start date": "2022-01-01",
    ...                                               "end date": "2022-02-01"}}}
    >>> facility_params = {"infrastructure type": "charging station",
    ...                    "development rate ($/m)": 200.0,
    ...                    "development cost": 100000.0,
    ...                    "cable pull ($/m)": 100.0}
    >>> evse_params = [{"evse type": "charger",
    ...                 "model": "LH411B - single charger",
    ...                 "charge current": 500.0,
    ...                 "cooling cube power": 100.0,
    ...                 "efficiency": 0.9,
    ...                 "power factor": 0.9,
    ...                 "current derating": 0.9,
    ...                 "BaaS charger monthly rate": 10000.0,
    ...                 "unit price": 50000.0}]
    
    >>> infra_1 = tco.InfraCell(infra_data, 
    ...                         facility_params, 
    ...                         evse_params,
    ...                         capex_dates=capex_dates, 
    ...                         opex_dates=opex_dates)
    >>> infra_1.execute_analysis()
    
    >>> infra_1.equipment_costs
                Equipment CAPEX
    date                       
    2022-01-01                0
    2022-02-01            50000
    >>> infra_1.construction_costs
                charging station costs
    date                              
    2022-01-01                       0
    2022-02-01                  110000
    """
    
    def __init__(self, data, facility_params, evse_params,
                 capex_dates=None, opex_dates=None, location=None):
        """Class used to represent BEV-related infrastructure.

        Parameters
        ----------
        data : dict
            Dictionary containing the input data describing the infrastructure 
            to be analyzed. The keys are described in Notes below.
        facility_params : list
            List of dictionaries containing data on each type of infrastructure.
            The keys are described in Notes below.
        evse_params : list, dict
            List of dictionaries containing data on each type of electrical 
            equipment or a single dictionary if only one equipment type is 
            required in the analysis. The keys are described in Notes below.
        capex_dates : dict, optional
            Dictionary containing the start and end dates for any CAPEX cost
            DataFrames in the TCO analysis. The keys are 'start date' and 'end date'
            and the corresponding values should be date strings in format YYYY-MM-DD.
            Required to perform the CAPEX analyses.
        opex_dates : dict, optional
            Dictionary containing the start and end dates for any OPEX cost
            DataFrames in the TCO analysis. The keys are 'start date' and 'end date'
            and the corresponding values should be date strings in format YYYY-MM-DD.
            Required to perform the OPEX analyses.
        location : str, optional
            Geographic location of the infrastructure in the mine. The default is None.
        """
        self.info = "infra"
        
        # Parameters describing the electrical and charging infrastructure
        self.data = data
        
        # Parameters relating to BEV infrastructure / support facilities
        self.facility_params = facility_params
        
        # The location of the infrastructure
        self.location = location
        
        self.evse_dict = {} # Make into a dictionary for easier referencing
        
        if(type(evse_params) is list):
            for evse_model in evse_params:
                self.evse_dict[evse_model["model"]] = evse_model
        elif(type(evse_params) is dict):
            self.evse_dict[evse_params["model"]] = evse_params
        
        if("evse" in self.data.keys()):
            self.evse_stock = self.data["evse"]
            
        self.infra_type = self.data["infrastructure type"]
        
        # Blank CAPEX and OPEX schedules for the fleet costs
        if(capex_dates):
            self.capex_dates = capex_dates
            start, end = [datetime.strptime(_, "%Y-%m-%d") for _ in list(capex_dates.values())]
            self.capex_timeline = pd.date_range(start, end, freq='MS').to_frame(index=False, name='date')
        
        if(opex_dates):
            start, end = [datetime.strptime(_, "%Y-%m-%d") for _ in list(opex_dates.values())]
            self.opex_dates = opex_dates
            self.opex_timeline = pd.date_range(start, end, freq='MS').to_frame(index=False, name='date')
        
        if("capex schedule" in self.data.keys()):
            capex_sched_list = self.data["capex schedule"]
            self.capex_sched = pd.DataFrame(capex_sched_list, columns=["date", "fraction"])
            self.capex_sched['date'] = pd.to_datetime(self.capex_sched['date'], format='%Y-%m-%d')
        
        if("opex schedule" in self.data.keys()):
            opex_sched_list = self.data["opex schedule"]
            self.opex_sched = pd.DataFrame(opex_sched_list, columns=["date", "fraction"])
            self.opex_sched['date'] = pd.to_datetime(self.opex_sched['date'], format='%Y-%m-%d')
        
        if("construction schedule" in self.data.keys()):
            const_sched_list = self.data["construction schedule"]
            self.const_sched = pd.DataFrame(const_sched_list, columns=["date", "fraction"])
            self.const_sched['date'] = pd.to_datetime(self.const_sched['date'], format='%Y-%m-%d')
        
        # Dictionaries to save the object's attributes or other variables 
        self.variables = {}
        self.capex_variables = {}
        self.opex_variables = {}
        
        self.add_variable("location", self.location, self.variables)
        
    def add_variable(self, name, value, variables_dict):
        """Add variables to the variables dictionary."""
        variables_dict[name] = value
    
    def get_variable(self, name):
        """Return variables in the variables dictionary."""
        return self.variables.get(name)
    
    def charging_station_analysis(self):
        """Calculate the costs for construction of a charging station."""
        construction_costs = self.capex_timeline.copy() 
        construction_costs["charging station costs"] = 0
        construction_costs = construction_costs.set_index("date")
        
        # The volume of the charging station is scaled by the number of batteries divided by 2
        dev_cost = self.facility_params["development cost"] * self.data["batteries"] / 2
        
        cable_cost = self.facility_params["cable pull ($/m)"] * self.data["cable length"]

        install_costs = dev_cost + cable_cost
        
        # Assign the construction costs per the construction schedule
        for frac in range(len(self.const_sched)):
            
            construction_costs.loc[self.const_sched.iloc[frac][0]] += self.const_sched.iloc[frac][1] * install_costs
        
        construction_costs = construction_costs.reset_index()
        
        return construction_costs
    
    def charging_equipment_analysis(self):
        """Calculate the purchase costs for charging equipment."""
        equipment_costs = self.capex_timeline.copy()
        equipment_costs["Equipment CAPEX"] = 0
        equipment_costs = equipment_costs.set_index("date")
        
        for equip_key, equip_val in self.evse_stock.items():
            
            evse_cost = self.evse_dict[equip_key]["unit price"] * equip_val

            # Assign the equipment costs per the capex schedule
            for frac in range(len(self.capex_sched)):
                
                mnth = self.capex_sched.iloc[frac][0]
                equipment_costs.loc[mnth] += self.capex_sched.iloc[frac][1] * evse_cost
        
        equipment_costs = equipment_costs.reset_index()
        
        return equipment_costs
    
    def baas_costs_analysis(self):
        """Calculate the Battery As A service (BAAS) costs for the infrastructure."""
        start, end = [datetime.strptime(_, "%Y-%m-%d") for _ in list(self.data["BaaS subscription"]["dates"].values())]
        baas_costs = pd.date_range(start, end, freq='MS').to_frame(index=False, name='date')
        
        # BaaS costs
        baas_costs["baas costs"] = 0
        
        if(self.data["BaaS subscription"]["frequency"] == "monthly"):
            for evse_key, num_evse in self.evse_stock.items():
                baas_rate = self.evse_dict[evse_key]["BaaS charger monthly rate"]
                baas_costs["baas costs"] += num_evse * baas_rate
        
        return baas_costs
    
    def opex_analysis(self):
        """Calculate the total OPEX (operating costs) for the infrastructure.
        
        OPEX costs for infrastructure may include battery as a service (BAAS) 
        costs, power costs and recurring software costs.
        """
        ## BaaS costs
        if("BaaS subscription" in self.data.keys()):
            self.baas_costs = self.baas_costs_analysis()
            self.add_variable("baas costs", self.baas_costs, self.variables)
            self.add_variable("baas costs", self.baas_costs, self.opex_variables)
    
    def capex_analysis(self):
        """Calculate the total CAPEX (capital costs) for the infrastructure.

        CAPEX costs for infrastructure may include charging station development
        and construction costs, EV support equipment (chargers, etc.) costs,
        and upfront software purchase costs.
        """
        ## Charging station CAPEX
        if(self.infra_type == "charging station"):
            
            # Construction costs
            if("construction schedule" in self.data.keys() and
               str(self.data.get("construction costs", "True")).strip().lower() != "false"):
                self.construction_costs = self.charging_station_analysis()
                self.add_variable("charging station costs", self.construction_costs, self.variables)
                self.add_variable("charging station costs", self.construction_costs, self.capex_variables)
            
            # EV support equipment purchase costs
            if(self.evse_stock):
                self.equipment_costs = self.charging_equipment_analysis()
                self.add_variable("Equipment CAPEX", self.equipment_costs, self.variables)
                self.add_variable("Equipment CAPEX", self.equipment_costs, self.capex_variables)
    
    def execute_analysis(self):
        """Execute the steps to analyse the infrastructure object's costs."""
        if(self.opex_dates):
            self.opex_analysis()
            
        if(self.capex_dates):
            self.capex_analysis()


class DigitalSolutionsCell():
    """
    Class used to represent digital solutions (IT/OT products).
    
    This class is used to calculate the CAPEX and OPEX of any digital solutions 
    used with the BEV fleet and/or infrastructure, e.g. an energy management 
    system or vehicle automation solutions.
    
    An instance of the class should represent a homogeneous subset of digital 
    solutions used by the mine. If the mine contains several different types 
    of digital solutions, each should be described by its own 
    DigitalSolutionsCell object.
    
    Attributes
    ----------
    data : dict
        Dictionary containing the TCO analysis input parameters describing 
        the digital solutions to be analyzed. The keys are described in 
        Notes below.
    solutions_params : dict
        Dictionary containing data on the type of digital solution. The 
        keys are described in Notes below.
    capex_dates : dict, optional
        Dictionary containing the start and end dates for any CAPEX cost
        DataFrames in the TCO analysis. The keys are 'start date' and 'end date'
        and the corresponding values should be date strings in format YYYY-MM-DD.
        Required to perform the CAPEX analyses.
    opex_dates : dict, optional
        Dictionary containing the start and end dates for any OPEX cost
        DataFrames in the TCO analysis. The keys are 'start date' and 'end date'
        and the corresponding values should be date strings in format YYYY-MM-DD.
        Required to perform the OPEX analyses.
    location : str, optional
        Geographic location of the fleet in the mine. The default is None.
    info : str
        Description of the object class.
    software_costs : pd.DataFrame
        Pandas DataFrame containing the software CAPEX costs per month.
    software_subs : pd.DataFrame
        Pandas DataFrame containing the software OPEX costs per month.
    capex_timeline : pd.DataFrame
        Pandas DataFrame containing the months of the CAPEX analysis.
    opex_timeline : pd.DataFrame
        Pandas DataFrame containing the months of the OPEX analysis.
    variables : dict
        Dictionary containing the class instance's variables.
    capex_variables : dict
        Dictionary containing the class instance's CAPEX variables.
    opex_variables : dict
        Dictionary containing the class instance's OPEX variables.
        
    Methods
    -------
    commission_analysis()
        Calculates the solution commissioning and installation costs.
    subscription_analysis()
        Calculate the solution subscription costs.
    capex_analysis()
        Calculates the total CAPEX (capital costs) for the infrastructure.
    opex_analysis()
        Calculates the total OPEX (operating costs) for the infrastructure.    
    execute_analysis()
        Executes the steps to analyse the infrastructure object's costs.
    add_variable(name, value, variables_dict)
        Adds objects to the variables dictionary.
    get_variable(name)
        Returns objects from the variables dictionary by name.
    
    Notes
    -----
    Keys in the input dictionary: **data**
    
    location : str
        Geographic location of the infrastructure in the mine. 
    type : str
        Type of digital solution, e.g. software.
    evse : dict
        Dictionary containing the types of EV charging equipment 
        related to the digital solution, keys are the EVSE model 
        name and values are the number of EVSE.
    capex schedule : list
        A list specifying the dates each fraction of the 
        digital solution purchase costs are paid. E.g. if the 
        CAPEX schedule is 80% on Jan 1st 2022 and the remaining 
        20% is paid three months later, the CAPEX schedule is 
        entered as the following list:
            [['2022-01-01', 0.80], ['2022-04-01', 0.20]]
    opex schedule : list
        A list specifying the dates and payment percentages for 
        digital solution subscription costs. E.g. if the 
        OPEX schedule is quarterly, with subscription payments 
        on Jan 1st 2022 and then again three months later, the 
        OPEX schedule is entered as the following list (where
        a value of 1.0 indicates a payment of 100% of the 
        monthly subscription fee):
            [['2022-01-01', 1.0], ['2022-04-01', 1.0]]
    
    Keys in the input dictionary: **solutions_params**
    
    infrastructure type : str
        The type of digital solution, e.g. software.
    solution name : str
        The name of the digital solution.
    unit price : float
        The upfront cost for the digital solution, e.g. for 
        system commissioning. Only required for CAPEX 
        calculations.
    subscription price : float
        The regularly occurring subscription (OPEX) fee for 
        the digital solution. The frequency of payment is defined
        in the 'data' dictionary.
        
    Examples
    --------
    >>> import bevcost.TCOmodel as tco
    >>> capex_dates = {'start date': '2022-01-01', 
    ... 			   'end date': '2022-02-01'}
    >>> opex_dates = {'start date': '2022-01-01', 
    ... 			  'end date': '2022-02-01'}
    >>> data = {"location": "IOC",
    ... 		"type": "software",
    ... 		"evse": {"workshop charger": 1},
    ... 		"capex schedule": [["2022-01-01", 1.0]],
    ... 		"opex schedule": [["2022-01-01", 1.0],
    ... 						  ["2022-02-01", 1.0]]}
    >>> solutions_params = {"infrastructure type": "software",
    ... 					"solution name": "Fleet Management System",
    ... 					"unit price": 200000,
    ... 					"subscription price": 25000}
    
    >>> digital_1 = tco.DigitalSolutionsCell(data,
    ... 									 solutions_params,
    ... 									 capex_dates=capex_dates, 
    ... 									 opex_dates=opex_dates)
    >>> digital_1.execute_analysis()
    
    >>> digital_1.software_costs
            date  Software CAPEX
    0 2022-01-01          200000
    1 2022-02-01               0
    
    """
    def __init__(self, data, solutions_params, capex_dates=None, 
                 opex_dates=None, location=None):
        """
        Class used to represent various digital solutions.
        
        Parameters
        ----------
        data : dict
            Dictionary containing the TCO analysis input parameters describing 
            the digital solutions to be analyzed. The keys are described in 
            Notes below.
        solutions_params : dict
            Dictionary containing data on the type of digital solution. The 
            keys are described in Notes below.
        capex_dates : dict, optional
            Dictionary containing the start and end dates for any CAPEX cost
            DataFrames in the TCO analysis. The keys are 'start date' and 'end date'
            and the corresponding values should be date strings in format YYYY-MM-DD.
            Required to perform the CAPEX analyses.
        opex_dates : dict, optional
            Dictionary containing the start and end dates for any OPEX cost
            DataFrames in the TCO analysis. The keys are 'start date' and 'end date'
            and the corresponding values should be date strings in format YYYY-MM-DD.
            Required to perform the OPEX analyses.
        location : str, optional
            Geographic location of the fleet in the mine. The default is None.
        """
        self.info = "digital"
        
        # Data describing the digital solution to be analysed
        self.data = data
        
        # Parameters relating to BEV infrastructure / support facilities
        self.solutions_params = solutions_params
        
        # The location for the DigitalSolutionsCell object
        self.location = self.data["location"]
        
        # Blank CAPEX and OPEX schedules for the fleet costs
        if(capex_dates):
            self.capex_dates = capex_dates
            start, end = [datetime.strptime(_, "%Y-%m-%d") for _ in list(capex_dates.values())]
            self.capex_timeline = pd.date_range(start, end, freq='MS').to_frame(index=False, name='date')
        
        if(opex_dates):
            start, end = [datetime.strptime(_, "%Y-%m-%d") for _ in list(opex_dates.values())]
            self.opex_dates = opex_dates
            self.opex_timeline = pd.date_range(start, end, freq='MS').to_frame(index=False, name='date')
        
        if("capex schedule" in self.data.keys()):
            capex_sched_list = self.data["capex schedule"]
            self.capex_sched = pd.DataFrame(capex_sched_list, columns=["date", "fraction"])
            self.capex_sched['date'] = pd.to_datetime(self.capex_sched['date'], format='%Y-%m-%d')
        
        if("opex schedule" in self.data.keys()):
            opex_sched_list = self.data["opex schedule"]
            self.opex_sched = pd.DataFrame(opex_sched_list, columns=["date", "fraction"])
            self.opex_sched['date'] = pd.to_datetime(self.opex_sched['date'], format='%Y-%m-%d')
        
        # Dictionaries to save the object's attributes or other variables 
        self.variables = {}
        self.capex_variables = {}
        self.opex_variables = {}
        
        self.add_variable("location", self.location, self.variables)
        
    def add_variable(self, name, value, variables_dict):
        """Add variables to the variables dictionary."""
        variables_dict[name] = value
    
    def get_variable(self, name):
        """Return variables in the variables dictionary."""
        return self.variables.get(name)
    
    def commission_analysis(self):
        """Calculate the solution commissioning and installation costs."""
        software_costs = self.capex_timeline.copy() # BaaS costs are incurred based on delivery dates of equipment
        software_costs["Software CAPEX"] = 0
        software_costs = software_costs.set_index("date")
        
        # Assign the software costs per the software capex schedule
        for frac in range(len(self.capex_sched)):
            
           software_costs.loc[self.capex_sched.iloc[frac][0]] += self.capex_sched.iloc[frac][1] * self.solutions_params["unit price"]
        
        software_costs = software_costs.reset_index()
        
        return software_costs
    
    def subscription_analysis(self):
        """Calculate the solution subscription costs."""
        software_subs = self.opex_timeline.copy() 
        software_subs["Software OPEX"] = 0
        software_subs = software_subs.set_index("date")
        
        # Assign the software costs per the software capex schedule
        for frac in range(len(self.opex_sched)):
            
           software_subs.loc[self.opex_sched.iloc[frac][0]] += self.opex_sched.iloc[frac][1] * self.solutions_params["subscription price"]
      
        software_subs = software_subs.reset_index()
        
        return software_subs
    
    def opex_analysis(self):
        """Calculate the total OPEX (operating costs) for the infrastructure.
        
        OPEX costs for infrastructure may include battery as a service (BAAS) 
        costs, power costs and recurring software costs.
        """
        # Recurring software costs
        self.software_subs = self.subscription_analysis()
        
        self.add_variable("Software OPEX", self.software_subs, self.variables)
        self.add_variable("Software OPEX", self.software_subs, self.opex_variables)
    
    def capex_analysis(self):
        """Calculate the total CAPEX (capital costs) for the infrastructure.

        CAPEX costs for infrastructure may include charging station development
        and construction costs, EV support equipment (chargers, etc.) costs,
        and upfront software purchase costs.
        """
        # Upfront software costs
        self.software_costs = self.commission_analysis()
        self.add_variable("Software CAPEX", self.software_costs, self.variables)
        self.add_variable("Software CAPEX", self.software_costs, self.capex_variables)
    
    def execute_analysis(self):
        """Execute the steps to analyse the infrastructure object's costs."""
        if(self.opex_dates):
            self.opex_analysis()
        
        if(self.capex_dates):
            self.capex_analysis()


class WorkforceCell():
    """
    A class used to represent a group of workers.
    
    This class is used to calculate the labour costs and other OPEX related
    to the workforce in a mine. Workers in each instance of the class must be 
    homogeneous, i.e. all have the same role.
    
    Attributes
    ----------
    info : str
        Description of the object class.
    business_params : dict
        Dictionary containing the analysis input parameters relating to 
        running the business (financial, energy costs, subsidies, labour rates, 
        etc.).
    data : dict
        Dictionary containing data on the workers (roles, 
        departments, number of personnel required each year).
    labour_rates : dict
        Dictionary containing the annual employment costs for specific roles.
    role : str
        Role assigned to the workers in the class instanace.
    location : str
        Geographic location of the workers in the mine.
    workforce : pd.DataFrame
        Pandas DataFrame containing the number of peronnel required each year.
    labour : pd.DataFrame
        Pandas DataFrame containing the labour costs per year.
    variables : dict
        Dictionary containing the class instance's attributes.
    
    Methods
    -------
    add_variable(name, value)
        Adds objects to the variables dictionary.
    get_variable(name)
        Returns objects from the variables dictionary by name.
    opex_analysis
        Determines the OPEX (i.e. labour costs) for the workers.
    execute_analysis
        Executes the steps to analyse the workforce object's costs.
        
        
    Notes
    -----
    Keys in the input dictionary: **data**
    
    role : str
        The type of role/vocation of the group of workers represented by the 
        class instance, e.g. underground miner or electrician.
    location : str
        The location in the mine the group of workers are assigned.
    personnel : dict
        A dictionary with two items, the first is a "date" key with 
        corresponding list of years. The second is a "workforce size" key with 
        a list containing the number of workers for each year.
    
    Keys in the input dictionary: **data**
    
    labour rates : dict
        A dictionary with two items, the first key is a role string, with 
        the corresponding value as the labour rate for that role (a float). The
        second key is "frequency" indicating the payment frequency for the
        labour rate, e.g. annual, monthly or hourly.
    
    Examples
    --------
    >>> import bevcost.TCOmodel as tco
    >>> opex_dates = {'start date': '2022-01-01',
    ...               'end date': '2022-02-01'}
    >>> data = {"role": "underground miner",
    ... 		"location": "extraction",
    ... 		"personnel": {"date": [2022],
    ... 					  "workforce size": [10]}}
    >>> business_params = {"labour rates": {"underground miner": 120000.0,
    ... 									"frequency": "annual"}}
    
    >>> workforce_1 = tco.WorkforceCell(data,
    ... 								business_params,
    ... 								opex_dates=opex_dates)
    >>> workforce_1.execute_analysis()
    
    >>> workforce_1.labour_costs
            date    labour
    0 2022-01-01  100000.0
    1 2022-02-01  100000.0
        
    """
    
    def __init__(self, data, business_params, capex_dates=None, 
                 opex_dates=None, location=None):
        """Class used to represent a group of workers.
        
        Parameters
        ----------
        data : dict
            Dictionary containing data on the workers (roles, departments, 
            number of personnel required each year).
        business_params : dict
            Dictionary containing the analysis input parameters relating to 
            running the business (financial, energy costs, subsidies, 
            labour rates, etc.).
        """
        self.info = "workforce"
        
        # Initialize variables
        self.business_params = business_params
        
        self.data = data
        
        self.location = location
        
        if(capex_dates):
            self.capex_dates = capex_dates
            start, end = [datetime.strptime(_, "%Y-%m-%d") for _ in list(capex_dates.values())]
            self.capex_timeline = pd.date_range(start, end, freq='MS').to_frame(index=False, name='date')
        
        if(opex_dates):
            start, end = [datetime.strptime(_, "%Y-%m-%d") for _ in list(opex_dates.values())]
            self.opex_dates = opex_dates
            self.opex_timeline = pd.date_range(start, end, freq='MS').to_frame(index=False, name='date')
        
        # Extract model parameters from input data
        self.role = self.data["role"]
        
        self.workforce_plan = pd.DataFrame(self.data["personnel"])
        self.workforce_plan.date = pd.to_datetime(self.workforce_plan.date, format='%Y')
        
        # Dictionaries to save the object's attributes or other variables 
        self.variables = {}
        self.capex_variables = {}
        self.opex_variables = {}
        
        self.add_variable("workforce", self.workforce_plan, self.variables)
        self.add_variable("location", self.location, self.variables)
        
    def add_variable(self, name, value, variables_dict):
        """Add variables to the variables dictionary."""
        variables_dict[name] = value

    def get_variable(self, name):
        """Return variables in the variables dictionary."""
        return self.variables.get(name)
    
    def labour_costs_analysis(self):
        """Determine the labour costs."""
        
        labour = self.opex_timeline.copy() # Energy costs are incurred based on operations
        labour["labour"] = 0.0
        
        # labour = self.workforce_plan.copy()
        # del labour["workforce size"]
        # labour["labour"] = self.workforce_plan["workforce size"] * monthly_rate
        
        if(self.business_params["labour rates"]["frequency"] == "annual"):
            # If labour rates are provided on an annual basis, find monthly rates
            monthly_rate = self.business_params["labour rates"][self.role] / 12.0
            
            # Use the workforce size each year and the monthly rate to get 
            # monthly workforce labour costs
            for year in self.workforce_plan.date.dt.year:
                annual_wf_size = self.workforce_plan[self.workforce_plan.date.dt.year == year]["workforce size"].iat[0]
                
                labour.loc[labour.date.dt.year == year, 'labour'] = annual_wf_size * monthly_rate
        
        return labour
    
    def opex_analysis(self):
        """Determine the OPEX (operating costs) for the workers.
        
        Worker labour costs are based on number of workers and their cost per 
        hour based on their roles.
        """
        
        self.labour_costs = self.labour_costs_analysis()
        
        self.add_variable("labour", self.labour_costs, self.variables)
        self.add_variable("labour", self.labour_costs, self.opex_variables)
    
    def execute_analysis(self):
        """Execute the steps to analyse the workforce object's costs."""
        self.opex_analysis()


def objects_annual(objects_list, var_name, col_name, div=1.0, agg='sum', verbose=True):
    """Create annual summaries of cost categories.

    Parameters
    ----------
    objects_list : list
        List of class objects (fleet, infrastructure, workforce or digital solutions).
    var_name : str
        DataFrame in object representing a cost category, used to create annual summary.
    col_name : str
        Name of DataFrame column for output.
    div : float, optional
        Factor to divide the summed values by. The default is 1.0.
    agg : str, optional
        Option to aggregate cost categories (from Pandas). The default is 'sum'.
    verbose : bool, option
        Option to turn on/off error print statements. The default is True.

    Returns
    -------
    obj_summary : pd.DataFrame
        A single DataFrame of the original fleet, infrastructure or workforce
        objects concatenated with totals columns.

    """
    obj_list = []
    
    # Get the summaries for the desired DataFrames from each object in the list
    for obj in objects_list:
        
        try:
            obj_name = obj.location
            
            obj_vars = (obj.variables[var_name].reset_index())
            
            obj_vars_annual = obj_vars.groupby(obj_vars["date"].dt.year)[col_name].agg([agg]) / div
            
            obj_vars_annual.columns = [f'{obj_name} {col_name}']
            
            obj_list.append(obj_vars_annual)
            
        except KeyError as e:
            
            if(verbose):
                print(f"Error: {var_name} variable in {obj.info}: {e}", file=sys.stderr)
            
            pass 
    
    # Concatenate the resulting list of DataFrames
    if not obj_list:
        
        if(verbose):
            print(f"No {var_name} variables in object list", file=sys.stderr)
        
    else:
        obj_summary = pd.concat(obj_list, axis=1)
        
        obj_summary[f'{col_name} total'] = obj_summary.sum(axis=1)
        
        return obj_summary


def tco_summary(fleet_objects, infra_objects, labour_objects, 
                digital_solution_objects, capex_contingency=None, 
                opex_contingency=None, verbose=True):
    """Summarize the annual totals of production, consumption, cost and waste variables.

    Parameters
    ----------
    fleet_objects : list
        List of fleet class objects.
    infra_objects : list
        List of infrastructure class objects.
    labour_objects : list
        List of workforce class objects.
    digital_solution_objects : list
        List of ...
    verbose : bool, option
        Option to turn on/off error print statements. The default is True.

    Returns
    -------
    production : pd.DataFrame
        Production variables (tonnes mined, operating hours, personnel) summed 
        per year.
    consumption : pd.DataFrame
        Consumption variables (energy, power) summed per year.
    capex : pd.DataFrame
        CAPEX variables (asset purchase costs, software costs, contingency, subsidies)
        summed per year.
    opex : pd.DataFrame
        OPEX variables (energy costs, software costs, maintenance costs, labour costs,
        subsidies) summed per year.
    waste : pd.DataFrame
        Waste variables (emissions) summed per year.

    """
    ## Production Variables
    # Operating hours
    fleet_hours = objects_annual(fleet_objects, "operating hours", "hours", div=1.0, verbose=verbose)
    
    # Workforce
    workforce = objects_annual(labour_objects, "workforce", "workforce size", div=1.0, verbose=verbose)
    
    # Production summary
    production = pd.concat([fleet_hours, workforce], axis=1)
    
    
    ## Consumption Variables
    # Energy consumption
    energy_consumed = objects_annual(fleet_objects, "energy consumption", "energy consumption", div=1000.0, verbose=verbose)
    
    # Power consumption
    # power_consumed = objects_annual(infra_objects, "power consumption", "power (sum)", div=1.0, verbose=verbose)
    # max_power = objects_annual(infra_objects, "power consumption", "power (max)", div=1.0, agg="max", verbose=verbose)
    power_consumed = objects_annual(fleet_objects, "power consumption", "power consumption", div=1.0, verbose=verbose)
    # max_power = objects_annual(fleet_objects, "power consumption", "power (max)", div=1.0, agg="max", verbose=verbose)
    
    # Consumption summary
    # consumption = pd.concat([energy_consumed, max_power, power_consumed], axis=1)
    consumption = pd.concat([energy_consumed, power_consumed], axis=1)
    
    
    ## CAPEX Variables
    # Fleet CAPEX
    fleet_capex = objects_annual(fleet_objects, "fleet capex", "fleet", div=1000000.0, verbose=verbose)
    
    # Infrastructure CAPEX
    infra_capex = objects_annual(infra_objects, "charging station costs", "infra", div=1000000.0, verbose=verbose)
    equipment_capex = objects_annual(infra_objects, "Equipment CAPEX", "EVSE", div=1000000.0, verbose=verbose)
    
    # Software CAPEX
    # software_capex = objects_annual(infra_objects, "Software CAPEX", "software", div=1000000.0, verbose=verbose)
    software_capex = objects_annual(digital_solution_objects, "Software CAPEX", "Software CAPEX", div=1000000.0, verbose=verbose)

    # Contingency
    if(capex_contingency):
        contingency = list(capex_contingency * (fleet_capex['fleet total'] + infra_capex['infra total'] + equipment_capex['EVSE total'] + software_capex['software total']))
        capex_contingency = pd.DataFrame(data=contingency, index=software_capex.index.values, columns=["contingency total"])
    else:
        capex_contingency = pd.DataFrame(data=0, index=software_capex.index.values, columns=["contingency total"])
    
    # Subsidies
    capex_subsidies = objects_annual(fleet_objects, "capex subsidies", "capex subsidies", div=1000000.0, verbose=verbose)
    
    # Total CAPEX
    capex = pd.concat([fleet_capex, infra_capex, equipment_capex, software_capex, capex_contingency, capex_subsidies], axis=1)
    capex['capex total'] = capex['fleet total'] + capex['infra total'] + capex['EVSE total'] + capex['software total'] + capex['contingency total']
    
    # Total CAPEX after Subsidies
    capex['capex total (less sub)'] = capex['capex total'] + capex_subsidies["capex subsidies total"]
    
    
    ## OPEX Variables
    # Energy OPEX
    energy_costs = objects_annual(fleet_objects, "energy costs", "energy", div=1000000.0, verbose=verbose)
    # power_costs = objects_annual(infra_objects, "power costs", "power", div=1000000.0, verbose=verbose)
    power_costs = objects_annual(fleet_objects, "power costs", "power", div=1000000.0, verbose=verbose)

    # BaaS OPEX
    baas_fleet_costs = objects_annual(fleet_objects, "baas costs", "baas fleet", div=1000000.0, verbose=verbose)
    baas_infra_costs = objects_annual(infra_objects, "baas costs", "baas infra", div=1000000.0, verbose=verbose)
    
    # Maintenance OPEX
    maintenance_costs = objects_annual(fleet_objects, "maintenance costs", "maintenance", div=1000000.0, verbose=verbose)
    
    # Software OPEX
    # software_costs = objects_annual(infra_objects, "Software OPEX", "software", div=1000000.0, verbose=verbose)
    software_costs = objects_annual(digital_solution_objects, "Software OPEX", "software", div=1000000.0, verbose=verbose)

    # Labour OPEX
    labour_costs = objects_annual(labour_objects, "labour", "labour", div=1000000.0, verbose=verbose)
    
    # Subsidies
    opex_subsidies = objects_annual(fleet_objects, "opex subsidies", "opex subsidies", div=1000000.0, verbose=verbose)
    
    # Total OPEX
    opex = pd.concat([energy_costs, power_costs, baas_fleet_costs, baas_infra_costs, software_costs, maintenance_costs, labour_costs, opex_subsidies], axis=1)
    opex['baas total'] = opex['baas fleet total'] + opex['baas infra total']
    opex['opex total'] = opex['energy total'] + opex['baas total'] + opex['power total'] + opex['software total'] + opex['maintenance total'] + opex['labour total']
    
    # Total OPEX after Subsidies
    opex['opex total (less sub)'] = opex['opex total'] + opex_subsidies["opex subsidies total"]
    

    ## Waste Variables
    GHG_emissions = objects_annual(fleet_objects, "emissions", "emissions", div=1000.0, verbose=verbose)
    
    waste = GHG_emissions
    
    return capex, opex, production, consumption, waste


def annual_object_summary(cost_variables_dict):
    
    # Make list of cost variables for concatenation
    cost_variables_list = list(cost_variables_dict.values())
    combined_cost_variables = pd.concat([_.set_index("date") for _ in cost_variables_list], axis=1)
    
    # Group cost variables by year
    combined_cost_variables = combined_cost_variables.reset_index()
    annual_cost_variables = combined_cost_variables.groupby(pd.Grouper(key='date', freq='YE')).sum()
    
    return annual_cost_variables
    

def annual_cashflow_summary(fleet_objects=None, infra_objects=None, 
                            labour_objects=None, digital_solution_objects=None):
    """Summarize the annual totals of production, consumption, cost and waste variables.

    Parameters
    ----------
    business_params : dict
        Dictionary containing the analysis input parameters relating to running 
        the business (financial, energy costs, subsidies, labour rates, etc.).
    fleet_objects : list
        List of fleet class objects.
    infra_objects : list
        List of infrastructure class objects.
    labour_objects : list
        List of workforce class objects.
    digital_solution_objects : list
        List of ...
    verbose : bool, option
        Option to turn on/off error print statements. The default is True.

    Returns
    -------
    capex : pd.DataFrame
        CAPEX variables (asset purchase costs, software costs, contingency, subsidies)
        summed per year.
    opex : pd.DataFrame
        OPEX variables (energy costs, software costs, maintenance costs, labour costs,
        subsidies) summed per year.

    """
    
    opex_objects = {}
    opex_vars = {}
    
    capex_objects = {}
    capex_vars = {}
    
    # Summary of fleet costs
    if(fleet_objects):
        # Summary of costs for each fleet object
        for fleet in fleet_objects:
            if(bool(fleet.opex_variables) is True):
                annual_opex = annual_object_summary(fleet.opex_variables)
                opex_objects[f"{fleet.info} {fleet.location}"] = annual_opex
            
            if(bool(fleet.capex_variables) is True):
                annual_capex = annual_object_summary(fleet.capex_variables)
                capex_objects[f"{fleet.info} {fleet.location}"] = annual_capex
        
        # Summary of costs for each fleet cost variable
        fleet_opex_vars = fleet_objects[0].opex_variables.keys()
        
        fleet_label = "fleet"
        for var in fleet_opex_vars:
            opex_vars[f"{fleet_label} {var}"] = objects_annual(fleet_objects,
                                                              var,
                                                              var,
                                                              div=1.0,
                                                              verbose=True)

        fleet_capex_vars = fleet_objects[0].capex_variables.keys()

        for var in fleet_capex_vars:
            capex_vars[f"{fleet_label} {var}"] = objects_annual(fleet_objects,
                                                               var,
                                                               var,
                                                               div=1.0,
                                                               verbose=True)
    
    # Summary of infrastructure costs
    if(infra_objects):
        # Summary of costs for each infrastructure object
        for infra in infra_objects:
            if(bool(infra.opex_variables) is True):
                annual_opex = annual_object_summary(infra.opex_variables)
                opex_objects[f"{infra.info} {infra.location}"] = annual_opex
                
            if(bool(infra.capex_variables) is True):
                annual_capex = annual_object_summary(infra.capex_variables)
                capex_objects[f"{infra.info} {infra.location}"] = annual_capex
        
        # Summary of costs for each fleet cost variable
        infra_opex_vars = infra_objects[0].opex_variables.keys()
        
        for var in infra_opex_vars:
            opex_vars[f"{infra.info} {var}"] = objects_annual(infra_objects, 
                                                              var, 
                                                              var, 
                                                              div=1.0, 
                                                              verbose=True)
        
        infra_capex_vars = infra_objects[0].capex_variables.keys()
        
        for var in infra_capex_vars:
            capex_vars[f"{infra.info} {var}"] = objects_annual(infra_objects, 
                                                               var, 
                                                               var, 
                                                               div=1.0, 
                                                               verbose=True)
    
    # Summary of digital solutions costs
    if(digital_solution_objects):
        # Summary of costs for each digital solutions object
        for digital in digital_solution_objects:
            if(bool(digital.opex_variables) is True):
                annual_opex = annual_object_summary(digital.opex_variables)
                opex_objects[f"{digital.info} {digital.location}"] = annual_opex
                
            if(bool(digital.capex_variables) is True):
                annual_capex = annual_object_summary(digital.capex_variables)
                capex_objects[f"{digital.info} {digital.location}"] = annual_capex
        
    
    # Summary of workforce costs
    if(labour_objects):
        # Summary of costs for each labour object
        for workforce in labour_objects:
            if(bool(workforce.opex_variables) is True):
                annual_opex = annual_object_summary(workforce.opex_variables)
                opex_objects[f"{workforce.info} {workforce.location}"] = annual_opex
                
            if(bool(workforce.capex_variables) is True):
                annual_capex = annual_object_summary(workforce.capex_variables)
                capex_objects[f"{workforce.info} {workforce.location}"] = annual_capex
    
    return opex_objects, opex_vars, capex_objects, capex_vars


def npv_calc(start_year, npv_df, discount):
    """Determine the Net Present Value (NPV) of a DataFrame of annual cashflows.

    Parameters
    ----------
    start_year : int
        Starting year for NPV calculations.
    npv_df : pd.Series
        One-dimensional array of cashflows, indexed by year.
    discount : float
        Discount rate for NPV calculations.

    Returns
    -------
    npv : float
        Net Present Value of the series of cashflows.
        
    
    Example
    -------
    
    opex = tco.extend_timeline(2022, opex)
    tco.npv_calc(2022, capex["capex total (less sub)"] + opex["opex total (less sub)"], 0.05)

    """
    # Determine NPV if the start year matches the first year in the cashflow series
    if(npv_df.index[0] == start_year):
        
        inital_val = npv_df.values[0]
        
        vals_list = list(npv_df.values)
        
        vals_list[0] = 0.0
        
        npv = inital_val + nf.npv(discount, vals_list)
    
    # If the first year for NPV calculations is earlier than the first year in the series
    # prepend extra zero-cashflow years to the series
    else:
        
        inital_val = 0.0
        
        vals_list = list(npv_df.values)
        
        extra_yrs = npv_df.index[0] - start_year
        
        for yr in range(extra_yrs):
            
            vals_list.insert(0, inital_val)
        
        npv = inital_val + nf.npv(discount, vals_list)
    
    return npv


def extend_timeline(start_year, orig_costs_df):
    """Preprend rows to an annual cashflows DataFrame.

    Parameters
    ----------
    start_year : int
        New starting year for the data series.
    orig_costs_df : pd.DataFrame
        Pandas DataFrame containing cashflows.

    Returns
    -------
    extended_costs_df : pd.DataFrame
        Original Pandas DataFrame preprended with rows of zeros.

    """
    extended_costs_df = orig_costs_df

    if(orig_costs_df.index[0] > start_year):

        orig_start = orig_costs_df.index[0]
        extra_yrs = orig_start - start_year

        for yr in range(extra_yrs):
            # Append the new rows, so count backwards from the current year in the DataFrame
            new_year = orig_start - (yr + 1)

            new_df = pd.DataFrame(index=[new_year], columns=list(orig_costs_df.columns), data=0)

            extended_costs_df = pd.concat([new_df, extended_costs_df])

    elif(orig_costs_df.index[0] < start_year):

        print("Error: start year is later than data available", file=sys.stderr)

    return extended_costs_df


def financial_analysis(start_year, costs_list, business_params, costs_dict):
    """Determine the Net Present Values (NPVs) for various cost categories.

    Parameters
    ----------
    start_year : int
        New starting year for the data series.
    costs_list : list
        List of Pandas DataFrames containing costs.
    business_params : dict
        Dictionary containing the analysis input parameters relating to running 
        the business (financial, energy costs, subsidies, labour rates, etc.).
    costs_dict : dict
        Dictionary containing cost categories for NPV caluclations. Optionally 
        NPVs can be caluclated based on a single type of cost or a summation of
        several cost types.

    Returns
    -------
    npv_dict : dict
        Dictionary containing the resulting NPVs.

    """
    new_costs_list = []
    
    # Check each cost DataFrame starts at correct year
    for cost_list in costs_list:
        
        # Prepend rows of zeros if not
        if(cost_list.index[0] > start_year):
            
            cost_list = extend_timeline(start_year, cost_list)
        
        new_costs_list.append(cost_list)
    
    total_costs = pd.concat(new_costs_list, axis=1)
    
    discount_rate = business_params["financial"]["discount rate"]
    
    npv_dict = {}
    
    # Loop through the dictionary defining the costs for NPV analysis
    for key, values in costs_dict.items():
        
        # Calculate the NPVs for all costs in the single cost input list
        if(key == "single"):
            
            # Calculate NPVs for individual cost types
            for costs in values:
                
                npv_dict[costs] = np.round(npv_calc(
                                                    start_year, 
                                                    total_costs[costs], 
                                                    discount_rate
                                                    ), 
                                           3)
        
        # Calculate NPVs for several cost types together
        elif(key == "addition"):
            
            for add_key, add_vals in values.items():
                
                npv_dict[add_key] = np.round(npv_calc(start_year, 
                                                      total_costs[add_vals].sum(axis=1), 
                                                      discount_rate), 
                                             3)
    
    return npv_dict


def spaghetti_line_plots(axes, title, df, palette):
    """Spaghetti chart combined with multiple small charts for TCO cost categories.
    
    Parameters
    ----------
    axes : ndarray
        An array of matplotlib.axes.Axes objects.
    title : str
        Title for the plot.
    df : pd.DataFrame
        Pandas DataFrame containing annual cashflows for cost categories.
    palette : matplotlib.colors.ListedColormap
        Matplotlib colormap object.
    """
    axes = axes.flatten()
    
    # Create subplots
    for num, column in enumerate(df.drop('x', axis=1), start=1):
        
        ax = axes[num-1]
        
        # Plot every line gray and transparent
        for v in df.drop('x', axis=1):
            
            ax.plot(df['x'], 
                    df[v], 
                    marker='', 
                    color='grey', 
                    linewidth=0.6, 
                    alpha=0.3)
        
        # Plot the subplot's main line bold
        ax.plot(df['x'], 
                df[column], 
                marker='', 
                color=palette(num), 
                linewidth=2.4, 
                alpha=1.0, 
                label=column)
        
        ax.tick_params(labelleft=True)
        
        ax.set_title(column, 
                     loc='left', 
                     fontsize=14, 
                     fontweight=10, 
                     weight="bold", 
                     color=palette(num))
    
    return axes


def stacked_bar_chart(ax, data, x_label=None, 
                      label_formats={'x': '${x:,.2f}', 'y': None}, 
                      out_format='svg'):
    """
    Generate stacked bar chart figures.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        A matplotlib Axes object containing all the elements of an individual
        (sub-)plot in a matplotlib figure.
    data : dict
        Either a dictionary with three entries. The first key 'x' contains a list
        of x-axis objects, such as years or categories to compare. 
        
        The second key 'cost labels' contains a list of cost components 
        (the segments in each bar of the bar chart) or if the data entry 
        contains a list of Pandas Series objects this option can be None.
        
        The third key 'data' contains a list of lists of cost values. Each list 
        contains the cost values for one cost component. Alternatively a list 
        of pandas Series each representing a cost component can be provided. 
        Each series must have a name (the cost component) 
        (e.g. pd.Series(data=[5000, 5000, 3000], name="Energy Consumption")).
    x_label : str
        The label for the x-axis. The default is None.
    label_formats : dict
        A dictionary to define the format of the x and y labels. The default value
        for the 'x' key is '${x:,.2f}' (e.g. $1.20), and the default value for 
        the 'y' key is None.
    out_format : str
        The type of image file matplotlib will generate. The default is 'svg'.

    Returns
    -------
    ax : matplotlib.axes.Axes
        A matplotlib Axes object containing all the elements of an individual
        (sub-)plot in a matplotlib figure.

    """
    ## Extract the plotting information from the dictionary
    # Extract data from a list of lists
    if(type(data['data']) is list and type(data['data'][0]) is list):
        x_series = data['x']
        y_series = data['data']
        labels = data['cost labels']
    
    # Extract data from a list of pd.Series objects
    elif(type(data['data']) is list and type(data['data'][0]) is pd.core.series.Series):
        # Confirm the index of each Series matches
        test = []
        
        for ix in range(len(data['data'])-1):
            test.append( data['data'][ix].index.equals(data['data'][ix+1].index) )
            
        if(False in test):
            print("Error: indices for all time series do not match", file=sys.stderr)
            return
        
        x_series = data['x']
        y_series = [_.values for _ in data['data']]
        labels = [_.name for _ in data['data']]
    
    ## Create stacked bar chart
    bottom = np.zeros(len(x_series))
    width = 0.5
    
    # Set the colourmap to use for each cost component
    bar_color = plt.get_cmap('Set1')

    for cost, segment_heights in enumerate(y_series):
        # Add each layer of cost components
        p = ax.bar(x_series, 
                   segment_heights, 
                   width, 
                   label=labels[cost], 
                   bottom=bottom,
                   color=bar_color(cost))
        
        bottom += np.array(segment_heights)
    
    ## Format chart
    # Automatically display legend
    ax.legend(loc="best")
    
    # Format the x-axis
    ax.set_xlabel(x_label, fontweight="bold")
    ax.set_xticks(x_series)
    ax.set_xticklabels(x_series)
    
    # Turn off the top/right axis spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Set the format for x-axis and y-axis values
    if(type(label_formats['x']) is str):
        ax.yaxis.set_major_formatter(tkr.StrMethodFormatter(label_formats['x']))
    
    # if(type(label_formats['y']) is mdates.DateFormatter):
    #     ax.xaxis.set_major_formatter(label_formats['y'])
    #     ax.xaxis.set_major_locator(mdates.YearLocator(interval=12))
    
    # Remove axis ticks
    ax.tick_params(which="major", bottom=False, left=False)
   
    # Make the horizontal grid visible and display behind the bars
    ax.yaxis.grid(True, color="grey", linestyle='-', linewidth=0.75, alpha=0.5)
    ax.set_axisbelow(True)
    
    # Set output file format
    set_matplotlib_formats(out_format)
    
    return ax


def waterfall_chart():
    """Waterfall chart data visualization.

    Returns
    -------
    None.

    """
    plt.show()


def list_to_dict(input_list, key_name):
    """
    

    Parameters
    ----------
    input_list : list
        A list of dictionaries
    key_name : str
        Key in the input dictionaries whose value will be used as the keys in 
        the new dictionary

    Returns
    -------
    new_dict : dict
        DESCRIPTION.

    """
    new_dict = defaultdict(list)
    
    for d in input_list:
        new_dict[d[key_name]] = d
        
    return new_dict
