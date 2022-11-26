from mesa import Agent, Model
from mesa.time import BaseScheduler
import random
import utils as u
import pandas as pd
import matplotlib.pyplot as plt

# Problema a linea 225

#################################
### Read file for coordinates ###
#################################

path = "./lines_info.csv"
lines_output_points_x, lines_output_points_y, lines_cycle_times, output_weight = u.read_line_info(path)

##################
### Parameters ###
##################

# Simulation parameters
n_shift = 2   # Shifts per day
wh = 8   # Working Hours per shift
seed = 42

# Model Parameters
warehouse_coord = [0, 80]   # x and y coordinates of the warehouse input point
charging_stations_x = [0, 0]   # x coordinates of the first and second charging station, respectively
charging_stations_y = [10, 20]   # y coordinates of the first and second charging station, respectively
battery_size = 4.8   # kWh

# Debug parameters
verbose = False   # Run a verbose simulation
system_time_on = False   # Print system time
check_model_output = False  # Check if data collection was successful
export_df_to_csv = True   # Export df with collected data to csv
# Note that to have system time both verbose and system_time_on must be True
# Note that check_model_output is working properly only when isSearching = True



#############################
### Model hyperparameters ###
#############################
isSearching = True   # Perform grid search
verboseSearch = False  # Show each combination of hyperparameters
hyper_tugger_train_number = [1]
hyper_ul_buffer = [[3, 3, 3, 3, 3]]
hyper_tugger_train_capacity = [4]


##############################################
### List to keep track of system evolution ###
##############################################
lines_production = {0: [], 1: [], 2: [], 3: [], 4: []}
lines_buffer = {0: [], 1: [], 2: [], 3: [], 4: []}
lines_idle = {0: [], 1: [], 2: [], 3: [], 4: []}
charging_status = {0: [], 1: []}

param_buff = []
param_capacity = []
param_tuggers = []
time = []

class Train(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.battery_size = battery_size   # [kWh]

        # initial battery charge is 60% and 100% of the maximum
        self.remaining_energy = battery_size * random.uniform(0.6, 1)   # [kWh]
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
                       
    def check_charge(self):
        # Checks if battery level is enough to complete the tour
        if self.remaining_energy < 0.4*self.battery_size:
            # One of the charging stations is randomly selected
            self.selected_charging_station = random.choice(range(len(charging_stations_x)))
            self.next_stop_x = charging_stations_x[self.selected_charging_station]
            self.next_stop_y = charging_stations_y[self.selected_charging_station]
            self.need_to_charge = True
        else: 
            self.next_line = 0
            self.next_stop_x = lines_output_points_x[self.next_line]
            self.next_stop_y = lines_output_points_y[self.next_line]
            
    def move(self):
        # Travel of the tugger train to the next stop and the loading/unloading of unit loads:
        distance_next_stop = u.compute_distance(self.pos_x, self.next_stop_x, self.pos_y, self.next_stop_y)
        # Travel time
        self.task_endtime += u.compute_time(distance_next_stop,
                                            speed=u.compute_speed(self.weight),
                                            nextline=self.next_line)

        self.remaining_energy -= u.compute_energy(u.compute_time(distance_next_stop,
                                                                 speed=u.compute_speed(self.weight),
                                                                 nextline=self.next_line))
        
        self.pos_x = self.next_stop_x
        self.pos_y = self.next_stop_y

        # If the next stop is not a charging station
        if not self.need_to_charge:
            # If the reached position is a line output point (and not the warehouse)
            if (self.pos_x, self.pos_y) != (warehouse_coord[0], warehouse_coord[1]):
                # If there is at least one unit load at the line output point
                if self.model.schedule_lines.agents[self.next_line].UL_in_buffer >= 1:
                    if self.load < self.capacity:
                        # If the train is not full, it loads one unit load
                        if (self.weight + output_weight[self.next_line]) <= self.weight_capacity:
                            if verbose:
                                print("\n"+self.unique_id, "going to line",
                                      self.next_line, "and picking up a unit load")

                            # Loading time (between 30 seconds and 60 seconds)
                            loading_time = random.uniform(30, 60)
                            self.task_endtime += loading_time
                            self.remaining_energy -= u.compute_energy_loading(output_weight[self.next_line])
                            self.model.schedule_lines.agents[self.next_line].UL_in_buffer -= 1
                            self.load += 1
                            self.weight += output_weight[self.next_line]
                        else:
                            if verbose:
                                print("\n" + self.unique_id, "- Not enough weight capacity left.")

                    else:
                        if verbose:
                            print("\n"+self.unique_id, "going to line", self.next_line, "- Not enough loading capacity")
                else:
                    if verbose:
                        print("\n"+self.unique_id, "going to line", self.next_line, "- No unit loads to be picked up")
                # self.next_line += 1
            else:
                if verbose:
                    print("\n"+self.unique_id, "going back to the warehouse and unloading", self.load, "unit loads")

                # Time to stop the vehicle in the right position (30 seconds)
                # + unloading time for each unit load (between 30 seconds and 1 minute)
                unloading_time = 30 + random.uniform(30, 60)*self.load
                self.task_endtime += unloading_time
                self.remaining_energy -= u.compute_energy_loading(self.weight)
                self.load = 0
                self.weight = 0
        
            if self.next_line >= 4:
                self.next_stop_x = warehouse_coord[0]
                self.next_stop_y = warehouse_coord[1]

            else:
                # Added
                self.next_line += 1
                self.next_stop_x = lines_output_points_x[self.next_line]
                self.next_stop_y = lines_output_points_y[self.next_line]
        if verbose:
            print("Travelled distance:", distance_next_stop, "m", "- Task endtime (hours):",
                  round(self.task_endtime/3600, 2), "- Remaining energy:", round(self.remaining_energy, 2),
                  "kWh", " - Carried weight: ", self.weight)
        
    def charging(self):
        # Function that simulates the (possible) queuing at the charging station and the battery charging:
        if verbose:
            print("\n"+self.unique_id, 'charging at charging station', self.selected_charging_station)
        
        # Queuing time (waiting for the charging station to be available):
        self.task_endtime += self.model.schedule_stations.agents[self.selected_charging_station].waiting_time #schedule_stations.agents contains the list of all ChargingStation agents

        # The battery is fully charged
        charging_size = self.battery_size - self.remaining_energy
        power = 4.9   # [kW] - Power of the charging station
        charging_time = (charging_size/power)*3600  # seconds
        self.remaining_energy += charging_size
        self.model.schedule_stations.agents[self.selected_charging_station].waiting_time += charging_time
        self.model.schedule_stations.agents[self.selected_charging_station].task_endtime = self.model.schedule_stations.agents[self.selected_charging_station].waiting_time+self.model.system_time
        self.task_endtime += charging_time
        if verbose:
            print("Task endtime (hours):", round(self.task_endtime/3600, 2), "- Remaining energy:", self.remaining_energy, "kWh")
        self.next_line = 0
        self.need_to_charge = False
        self.next_stop_x = lines_output_points_x[self.next_line]
        self.next_stop_y = lines_output_points_y[self.next_line]
        
    def step(self):
        if self.task_endtime <= self.model.system_time:
            if (self.pos_x, self.pos_y) == (warehouse_coord[0], warehouse_coord[1]):
                self.check_charge()
            if self.need_to_charge:
                self.move()
                self.charging()
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
    def __init__(self,seed=None):
        super().__init__()
        self.schedule_trains = BaseScheduler(self)
        self.schedule_stations = BaseScheduler(self)
        self.schedule_lines = BaseScheduler(self)
        # This attribute will keep track of the system time, advancing by 1 second at each step
        self.system_time = 0
        
        # Creating tugger trains, charging stations and lines:
        for j in range(tugger_train_number):
            a = Train("Tugger train_" + str(j+1), self)
            self.schedule_trains.add(a)
            
        for h in range(len(charging_stations_x)):
            a = ChargingStation("Charging station_"+str(h), self)
            self.schedule_stations.add(a)

        for k in range(5):   # Lines in the factory
            a = Line("Line_"+str(k), self)
            self.schedule_lines.add(a)
            
    def step(self):
        self.system_time += 1
        if verbose and system_time_on:
            print("System time: " + str(self.system_time))
        self.schedule_lines.step()
        self.schedule_trains.step()
        self.schedule_stations.step()


##############################
### Running the simulation ###
##############################

if isSearching:
    counting = 0
    combination = len(hyper_tugger_train_capacity)*len(hyper_ul_buffer)*len(hyper_tugger_train_number)
    total = combination*n_shift*wh*3600
    print("Starting...")
    for k in hyper_ul_buffer:
        for j in hyper_tugger_train_number:
            for h in hyper_tugger_train_capacity:
                tugger_train_capacity = h
                tugger_train_number = j
                ul_buffer = k
                if verboseSearch:
                    print("Started with (buffer, tugger N, tugger capacity):",
                          k, "-", j, "-", h)
                model = FactoryModel(seed=seed)
                for i in range(n_shift*wh*3600):
                    model.step()
                    time.append(i)
                    param_buff.append(k)
                    param_capacity.append(h)
                    param_tuggers.append(j)
                    for z in range(5):
                        lines_production[z].append(model.schedule_lines.agents[z].total_production)
                        lines_buffer[z].append(model.schedule_lines.agents[z].UL_in_buffer)
                        lines_idle[z].append(model.schedule_lines.agents[z].idle_time)
                    for station in range(2):
                        charging_status[station].append(model.schedule_stations.agents[station].is_charging)
                    n = int(round(counting/total*20, 0))
                    progress = '='*n
                    if round(counting/total*100, 0) % 5 == 0:
                        print(f"{progress:20}", str(round(counting/total*100, 2))+"%")
                    counting += 1

    print("Simulation ended.")
    print("Model performed", combination, "hyperparameters combinations.")
    print("Total iterations:", total)

    dataframe = pd.DataFrame(zip(time, param_buff, param_tuggers, param_capacity),
                             columns=["Time", "Buffer", "Tugger N", "Tugger Capacity"])

    for j in range(5):
        dataframe["Prod_"+str(j+1)] = lines_production[j]
        dataframe["UL_in_buffer_"+str(j+1)] = lines_buffer[j]
        dataframe["Idle_time_"+str(j+1)] = lines_idle[z]
    for station in range(2):
        dataframe["Saturation_"+str(station+1)] = charging_status[station]
    if export_df_to_csv:
        print("Saving dataframe to csv.")
        dataframe.to_csv("./output/dataframe.csv")

else:
    tugger_train_number = hyper_tugger_train_number[0]
    tugger_train_capacity = hyper_tugger_train_capacity[0]
    ul_buffer = hyper_ul_buffer[0]
    model = FactoryModel(seed=seed)

    for i in range(n_shift*wh*3600):  # Seconds
        model.step()
        for j in range(5):
            lines_production[j].append(model.schedule_lines.agents[j].total_production)
            lines_buffer[j].append(model.schedule_lines.agents[j].UL_in_buffer)
            lines_idle[j].append(model.schedule_lines.agents[j].idle_time)

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

plt.plot(dataframe.Time,dataframe.Saturation_1,label="Stazione 1")
plt.plot(dataframe.Time,dataframe.Saturation_2,label="Stazione 2")
plt.legend()
plt.show()