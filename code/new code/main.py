import statistics
from mesa import Agent, Model
from mesa.time import BaseScheduler
import random
import utils as u
import pandas as pd
import scipy.stats
import numpy as np
import matplotlib.pyplot as plt
from time import sleep
import csv

import importlib
importlib.reload(u)


#############################
# Read file for coordinates #
#############################
path = "./lines_info.csv"
lines_output_points_x, lines_output_points_y, lines_cycle_times, output_weight = u.read_line_info(path)

#################################
# Read file for charging phases #
#################################
path = "./charging.csv"
charging_dict = u.read_charging_phases(path)


##############
# Parameters #
##############
# Simulation parameters
n_shift = 2   # Shifts per day
wh = 7.5  # Working Hours per shift
seed = 42

# Model Parameters
warehouse_coord = [0, 80]   # x and y coordinates of the warehouse input point
charging_stations_x = [0, 0]   # x coordinates of the first and second charging station, respectively
charging_stations_y = [10, 20]   # y coordinates of the first and second charging station, respectively
battery_size = 4.8   # kWh

# Debug parameters
verbose = False  # Run a verbose simulation
system_time_on = False   # Print system time
check_model_output = False  # Check if data collection was successful
isSearching = True  # Perform grid search
verboseSearch = False  # Show each combination of hyperparameters


# Parameters to find N
findN = False  # Set to True to find N
N = 5000
alpha = 0.05
precision = 0.0125

# Save output
path = "./output/output_N/"
export_df_to_csv = True  # Export df with collected data to csv
export_df_to_feather = True  # Export df to feather format
# Note that to have system time both verbose and system_time_on must be True
# Note that check_model_output is working properly only when isSearching = True



#########################
# Model hyperparameters #
#########################

# If isSearching = False and more than 1 parameter is specified, just the first element of the list will be used
# Same for findN

hyper_tugger_train_number = [6 for i in range(800)]
hyper_ul_buffer = [[3, 3, 3, 3, 3]]
hyper_tugger_train_capacity = [4]
hyper_n_charging_station = [2, 3, 4, 5, 6]


###################
# Data Collectors #
###################
buffer_cap = []
tuggers_number = []
n_stations = []
average_idle_times = []

##########################################
# List to keep track of system evolution #
##########################################
lines_production = {0: [], 1: [], 2: [], 3: [], 4: []}
lines_buffer = {0: [], 1: [], 2: [], 3: [], 4: []}
lines_idle = {0: [], 1: [], 2: [], 3: [], 4: []}
charging_status = {0: [], 1: []}

param_buff = []
param_capacity = []
param_tuggers = []
param_stations = []
param_saturation = []
time = []

class Train(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.battery_size = battery_size   # [kWh]

        # initial battery charge is 60% and 100% of the maximum
        self.remaining_energy = battery_size * random.uniform(0.05, 0.98)   # [kWh]
        self.capacity = tugger_train_capacity   # Maximum number of unit loads which can be loaded on a tugger train
        self.load = 0   # Current load of the tugger train

        # Current position of the tugger train. The starting position is the warehouse input/output point
        self.pos_x = warehouse_coord[0]
        self.pos_y = warehouse_coord[1]

        # This attribute will be updated with the x coordinate of the next line/charging station/warehouse to be visited
        self.next_stop_x = lines_output_points_x[0]

        # This attribute will be updated with the y coordinate of the next line/charging station/warehouse to be visited
        self.next_stop_y = lines_output_points_y[0]

        # Increased by a value equal to the task duration every time the tugger train completes a task
        self.task_endtime = 0

        # Id of the next line output point to be visited
        self.next_line = 0

        # This attribute will be True if the vehicle needs to charge
        self.need_to_charge = False

        # This attribute will be updated with the ID of the charging station where the vehicle is going to charge
        self.selected_charging_station = None
        self.weight_capacity = 2000
        self.weight = 0

        # Attribute to correct the functioning of the loading
        self.flag_load = False

    def check_charge(self):
        # Function that checks if the vehicle battery level is enough to perform the following pick-up tour
        if self.remaining_energy < self.charge_threshold():
            # One of the charging stations is randomly selected
            # self.selected_charging_station = random.choice(range(len(charging_stations_x)))
            self.selected_charging_station = self.model.schedule_stations.agents.index(min(self.model.schedule_stations.agents, 
                                                                                           key=lambda x:x.waiting_time))
            self.next_stop_x = charging_stations_x[self.selected_charging_station]
            self.next_stop_y = charging_stations_y[self.selected_charging_station]
            self.need_to_charge = True
            if verbose:
                print("\n\n", self.unique_id, "in need of charging\n- Remaining charge:", round(self.remaining_energy, 4), "KWh\n- Going to recharge at station", self.selected_charging_station, "\n   - Travelled distance:", u.compute_distance(self.pos_x, self.next_stop_x, self.pos_y, self.next_stop_y), "m")
            
        else: 
            self.next_line = 0
            self.next_stop_x = lines_output_points_x[self.next_line]
            self.next_stop_y = lines_output_points_y[self.next_line]
            
    def move(self):
        if (not self.flag_load) or (self.next_stop_x == warehouse_coord[0] and self.next_stop_y == warehouse_coord[1] and self.pos_x== 20.0 and self.pos_y == 80.0) :
            distance_next_stop = u.compute_distance(self.pos_x, self.next_stop_x, self.pos_y, self.next_stop_y)
            if self.flag_load: 
                if verbose:
                    print("\n\n" + self.unique_id, "going to the warehouse", "\n- Travelled distance:",
                          distance_next_stop, "m")

            else:
                if verbose:
                    print("\n\n", self.unique_id + " going to line", self.next_line,
                          "\n- Travelled distance:", distance_next_stop, "m", "\n- Carried weight: ", self.weight, "kg",
                          "\n- Task endtime:", round(self.task_endtime / 3600, 2), "h", "\n\n" + self.unique_id,
                          "at line", self.next_line)
            self.task_endtime += u.compute_time(distance_next_stop,
                                                speed=u.compute_speed(self.weight),
                                                nextline=self.next_line)
            self.remaining_energy -= u.compute_energy(
                u.compute_time(distance_next_stop, speed=u.compute_speed(self.weight), nextline=self.next_line))
            self.pos_x = self.next_stop_x
            self.pos_y = self.next_stop_y
            self.flag_load = True

        else:
            # If the next stop is not a charging station
            if not self.need_to_charge:
                # If the reached position is a line output point (and not the warehouse)
                if (self.pos_x, self.pos_y) != (warehouse_coord[0], warehouse_coord[1]):
                    # If there is at least one unit load at the line output point
                    while self.model.schedule_lines.agents[self.next_line].UL_in_buffer >= 1:
                        if self.load < self.capacity:
                            if (self.weight + output_weight[self.next_line]) <= self.weight_capacity:
                                if verbose:
                                    print("- Picking up a unit load", "\n   - Task endtime:",
                                          round(self.task_endtime/3600, 2), "h")
                                    
                                # Loading time (between 30 seconds and 60 seconds)
                                loading_time = random.uniform(30, 60)
                                self.task_endtime += loading_time
                                self.remaining_energy -= u.compute_energy_loading(output_weight[self.next_line])
                                self.model.schedule_lines.agents[self.next_line].UL_in_buffer -= 1
                                self.load += 1
                                self.weight += output_weight[self.next_line]
                            else:
                                if verbose:
                                    print("- Not enough weight capacity left")
                                break
                        else:
                            if verbose:
                                print("- Not enough loading capacity left")
                            break
                    else:
                        if verbose:
                            print("- No (more) unit loads to be picked up")
                else:
                    if verbose:
                        print("- Unloading", self.load, "unit loads")
                    unloading_time = 30 + random.uniform(30, 60)*self.load
                    self.task_endtime += unloading_time
                    self.remaining_energy -= u.compute_energy_loading(self.weight)
                    self.load = 0
                    self.weight = 0
                    self.next_line = 0
                    self.flag_load = False

                if self.next_line >= 4:
                    self.next_stop_x = warehouse_coord[0]
                    self.next_stop_y = warehouse_coord[1]
                    # if verbose:
                    #    print("- Going back to the warehouse")

                else:
                    self.next_line += 1
                    self.next_stop_x = lines_output_points_x[self.next_line]
                    self.next_stop_y = lines_output_points_y[self.next_line]
                    self.flag_load = False
                    
            if verbose:
                print("   - Task endtime:", round(self.task_endtime/3600, 2), "h", "\n   - Carried weight: ",
                      self.weight, "kg")
        
    def charging(self):
        # Function that simulates the (possible) queuing at the charging station and the battery charging:
        # Queuing time (waiting for the charging station to be available):
        # schedule_stations.agents contains the list of all ChargingStation agents
        self.task_endtime += self.model.schedule_stations.agents[self.selected_charging_station].waiting_time

        # The battery is fully charged
        charging_size = self.battery_size - self.remaining_energy
        charging_time = u.compute_charging_time(charging_dict, self.remaining_energy, self.battery_size)  # seconds
        self.remaining_energy += charging_size
        self.model.schedule_stations.agents[self.selected_charging_station].waiting_time += charging_time
        self.model.schedule_stations.agents[self.selected_charging_station].task_endtime = self.model.schedule_stations.agents[self.selected_charging_station].waiting_time+self.model.system_time
        self.task_endtime += charging_time
        if verbose:
            print("   - Task endtime:", round(self.task_endtime/3600, 2), "h", "\n   - Remaining charge:",
                  self.remaining_energy, "KWh")

        self.next_line = 0
        self.need_to_charge = False
        self.pos_x = charging_stations_x[self.selected_charging_station]
        self.pos_y = charging_stations_y[self.selected_charging_station]
        self.next_stop_x = lines_output_points_x[self.next_line]
        self.next_stop_y = lines_output_points_y[self.next_line]

    def charge_threshold(self):
        # consumo per viaggare carico al massimo, consume per caricare e scaricare tutti i pallet,
        time = 0
        line_output_for_charging_x = [0]+lines_output_points_x+[0]
        line_output_for_charging_y = [80]+lines_output_points_y+[80]
        for i in range(5):
            time += u.compute_time(u.compute_distance(x1=line_output_for_charging_x[i],
                                                      x2=line_output_for_charging_x[i+1],
                                                      y1=line_output_for_charging_y[i],
                                                      y2=line_output_for_charging_y[i+1]),
                                   speed=u.compute_speed(weight=self.weight_capacity),
                                   random_flag=False)
        time += 190+u.compute_time(u.compute_distance(x1=0, x2=0, y1=80, y2=10),
                                   speed=u.compute_speed(weight=0),
                                   random_flag=False)
        est_consumption = u.compute_energy(time=time)+u.compute_energy_loading(weight=self.weight_capacity)*2
        return est_consumption
    
    def step(self):
        if self.task_endtime <= self.model.system_time:
            if (self.pos_x, self.pos_y) == (warehouse_coord[0], warehouse_coord[1]) and self.flag_load == False:
                self.check_charge()
            if self.need_to_charge:
                self.charging()
                self.move()
            else:
                self.move()


class ChargingStation(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        # Time that a tugger train must wait before beginning its charging process at this station
        self.waiting_time = 0
        self.task_endtime = 0
        self.is_charging = False

    def step(self):
        # Step duration: 1 second
        if self.task_endtime > self.model.system_time:
            self.is_charging = True
        else:
            self.is_charging = False
        if self.waiting_time >= 1:
            self.waiting_time -= 1
        else:
            self.waiting_time = 0   # Potrebbe essere inutile?


class Line(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

        # The last character in the unique_id is the number indicating the line (see FactoryModel)
        self.line_index = int(self.unique_id[-1])

        # Production time of one unit load (minutes)
        self.cycle_time = lines_cycle_times[self.line_index]

        # Maximum number of unit Loads in the buffer at the line output point
        self.buffer_size = ul_buffer[self.line_index]

        # Actual number of unit loads in the buffer at the line output point.
        # The buffer is empty at the beginning of the simulation
        self.UL_in_buffer = 0

        # Overall number of unit loads produced by the line
        self.total_production = 0

        # Time (minutes) during which the station is not producing since the buffer is full
        self.idle_time = 0

        # Attribute needed to simulate the production of one unit load "every cycle time" (see the step function)
        self.count_time = 0

    def step(self):
        # If the buffer is not full
        if self.UL_in_buffer < self.buffer_size:
            self.count_time += 1
            if self.count_time == self.cycle_time:    
                self.total_production += 1
                self.UL_in_buffer += 1
                self.count_time = 0
        else:
            self.idle_time += 1


class FactoryModel(Model):
    def __init__(self, seed=None):
        super().__init__()
        self.schedule_trains = BaseScheduler(self)
        self.schedule_stations = BaseScheduler(self)
        self.schedule_lines = BaseScheduler(self)
        # This attribute will keep track of the system time, advancing by 1 second at each step
        self.system_time = 0

        # Creating tugger trains, charging stations and lines:
        for tug in range(tugger_train_number):
            a = Train("Tugger train_" + str(tug+1), self)
            self.schedule_trains.add(a)
            
        for stat in range(len(charging_stations_x)):
            a = ChargingStation("Charging station_"+str(stat), self)
            self.schedule_stations.add(a)

        for line in range(5):   # Lines in the factory
            a = Line("Line_"+str(line), self)
            self.schedule_lines.add(a)
            
    def step(self):
        self.system_time += 1
        if verbose and system_time_on:
            print("System time: " + str(self.system_time))
        self.schedule_lines.step()
        self.schedule_trains.step()
        self.schedule_stations.step()


##########################
# Running the simulation #
##########################

if isSearching:
    counting = 0
    combination = len(hyper_tugger_train_capacity)*len(hyper_ul_buffer)*len(hyper_tugger_train_number)*len(hyper_n_charging_station)
    total = int(combination*n_shift*wh*3600)
    print("Starting...")
    for k in hyper_ul_buffer:
        for j in hyper_tugger_train_number:
            for h in hyper_tugger_train_capacity:
                for s in hyper_n_charging_station:
                    charging_stations_x = [i*0 for i in range(s)]
                    charging_stations_y = [(i+1)*10 for i in range(s)]
                    tugger_train_capacity = h
                    tugger_train_number = j
                    ul_buffer = k
                    if verboseSearch:
                        print("Started with (buffer, tugger N, tugger capacity, number of stations):",
                              k, "-", j, "-", h, "-", s)
                    model = FactoryModel(seed=seed)
                    for i in range(int(n_shift*wh*3600)):
                        model.step()
                        time.append(i)
                        param_buff.append(k)
                        param_capacity.append(h)
                        param_tuggers.append(j)
                        param_stations.append(s)
                        saturation = 0
                        for z in range(5):
                            lines_production[z].append(model.schedule_lines.agents[z].total_production)
                            lines_buffer[z].append(model.schedule_lines.agents[z].UL_in_buffer)
                            lines_idle[z].append(model.schedule_lines.agents[z].idle_time)
                        for station in range(s):
                            saturation += model.schedule_stations.agents[station].is_charging
                        param_saturation.append(saturation /s)
                        u.progress(int(round(counting/total*100, 0)))
                        counting += 1
                    buffer_cap.append(k)
                    tuggers_number.append(j)
                    n_stations.append(s)
                    avg_idle_time = 0
                    avg_time_per_line = []
                    for key,value in lines_idle.items():
                        avg_time_per_line.append(value[-1])
                    avg_idle_time = sum(avg_time_per_line)/(5*60)
                    average_idle_times.append(avg_idle_time)
    print("\nHyperparameter search simulation completed.\n")
    print(combination, "Number of hyperparameters combinations have been performed.")
    print(f"Total iterations: {total:,}")


    dataframe = pd.DataFrame(zip(tuggers_number, n_stations, buffer_cap, average_idle_times),
                             columns=["Number of tuggers", "Number of stations", "Buffer Size", "Average Idle Times[min]"])
    if export_df_to_csv:
        print("Saving dataframe to csv.")
        dataframe.to_csv(path + "dataframe_4.csv", index=False)

    if export_df_to_feather:
        print("Saving dataframe to feather.")
        dataframe.to_feather(path + "dataframe_4.feather")
                
elif findN: #This allows to understand which is the correct number of N to reach a reasonable half-width
    while True: 
        mean_idle_times = [] # List of means
        # Parameters' setup: This should be coherent with what tried in the isSearch result
        tugger_train_number = hyper_tugger_train_number[0]
        tugger_train_capacity = hyper_tugger_train_capacity[0]
        charging_stations_x = [i * 0 for i in range(hyper_n_charging_station[0])]  # x coordinates of the first and second charging station, respectively
        charging_stations_y = [(i + 1) * 10 for i in range(hyper_n_charging_station[0])]  # y coordinates of the first and second charging station, respectively
        ul_buffer = hyper_ul_buffer[0]
        print("Starting the procedure to find N...")
        print("Testing N:", N)
        for q in range(N):
            # print('Simulation run', q)
            model = FactoryModel(seed=seed)
            idle_times = [] # Creating a list of idle_times for each run
            for i in range(int(n_shift*wh*3600)):
                model.step()  
                for w in range(5):
                    idle_times.append(model.schedule_lines.agents[w].idle_time)
            mean_idle_times.append(statistics.mean(idle_times))
        s = statistics.variance(mean_idle_times)
        quantile = scipy.stats.t.ppf(1 - alpha / 2, N - 1)
        c = quantile * (s / N) ** 0.5
        if c <= precision*statistics.mean(mean_idle_times):
            with open("./mean.csv", "w") as f:
                writer = csv.writer(f)
                writer.writerow(mean_idle_times) 
            break
        else:
            N = N + 500
            
    print("N is " + str(N))

    if (len(hyper_tugger_train_number) + len(hyper_ul_buffer) + len(hyper_tugger_train_capacity)) > 3:
       print("*****\nWarning: you decided to run the model just for one configuration but you provided more than one "
               "combination of a parameters. The first combination of parameters was used.\n*****")


else:
    tugger_train_number = hyper_tugger_train_number[0]
    tugger_train_capacity = hyper_tugger_train_capacity[0]
    ul_buffer = hyper_ul_buffer[0]
    charging_stations_x = [i * 0 for i in range(hyper_n_charging_station[0])]
    charging_stations_y = [(i + 1) * 10 for i in range(hyper_n_charging_station[0])]
    model = FactoryModel(seed=seed)

    for i in range(int(n_shift*wh*3600)):  # Seconds
        model.step()

    print("\nSYSTEM PERFORMANCES:")
    print("with",
          "\nTugger train number:", tugger_train_number,
          "\nTugger train capacity:", tugger_train_capacity,
          "\nUL buffer line(in order):", ul_buffer, end="\n\n")

    for i in range(5):
        print("************\nLINE", i, "\nActual production [UL]:",
              model.schedule_lines.agents[i].total_production,
              "\nMaximum production [UL]: ", int(model.system_time/lines_cycle_times[i]),
              "\nTotal idle time [min]: ", round(model.schedule_lines.agents[i].idle_time/60, 2))
        if check_model_output:
            print("\nCheck idle:", round(lines_idle[i][-1]/60, 2))
            print("Check actual prod:", round(lines_production[i][-1]))
            print("Total time - Len of prod - Len of prod:", n_shift*wh*3600, len(lines_production[i]), len(lines_idle[i]))
        print("************\n")
    if (len(hyper_tugger_train_number) + len(hyper_ul_buffer) + len(hyper_tugger_train_capacity)) > 3:
        print("*****\nWarning: you decided to run the model just for one configuration but you provided more than one "
              "combination of a parameters. The first combination of parameters was used.\n*****")

