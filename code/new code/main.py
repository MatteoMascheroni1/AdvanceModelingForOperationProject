from mesa import Agent, Model
from mesa.time import BaseScheduler #BaseScheduler activates all the agents at each step, one agent at a time, in the order they were added to the scheduler
import random
import utils as u

#################################
### Read file for coordinates ###
#################################

path = "./lines_info.csv"
lines_output_points_x, lines_output_points_y, lines_cycle_times, output_weight = u.read_line_info(path)

##################
### Parameters ###
##################

n_shift = 2 # Shifts per day
wh = 8 # Working Hours per shift
warehouse_coord = [0,80] #x and y coordinates of the warehouse input point
charging_stations_x = [0,0] #x coordinates of the first and second charging station, respectively
charging_stations_y = [10,20] #y coordinates of the first and second charging station, respectively
speed = 1.4 #[m/s] - Average speed meant to account for high-speed travel, low-speed turns, and acceleration/deceleration times
battery_size = 4.8 #kWh




class Train(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.battery_size = battery_size # [kWh] 
        self.remaining_energy = battery_size * random.uniform(0.6,1) #[kWh] - At the beginning of the simulation, the battery charge level of each vehicle is between 60% and 100% of the maximum
        self.capacity = 4 #Maximum number of unit loads which can be loaded on a tugger train
        self.load = 0 #Current load of the tugger train
        self.pos_x = warehouse_coord[0] #Current position of the tugger train. The starting position is the warehouse input/output point
        self.pos_y = warehouse_coord[1]
        self.next_stop_x = lines_output_points_x[0] #This attribute will be updated with the x coordinate of the next line/charging station/warehouse to be visited
        self.next_stop_y = lines_output_points_y[0] #This attribute will be updated with the y coordinate of the next line/charging station/warehouse to be visited
        self.task_endtime = 0 #Every time the tugger train completes a task, this variable will be increased by a value equal to the task duration
        self.next_line = 0 #Id of the next line output point to be visited
        self.need_to_charge = False #This attribute will be True if the vehicle needs to charge
        self.selected_charging_station = None #This attribute will be updated with the ID of the charging station where the vehicle is going to charge
        self.weight_capacity = 2000
        self.weight = 0
                       
    def check_charge(self): #Function that checks if the vehicle battery level is enough to perform the following pick-up tour
        if self.remaining_energy < 0.4*self.battery_size:
            self.selected_charging_station = random.choice(range(len(charging_stations_x))) #One of the charging stations is randomly selected
            self.next_stop_x = charging_stations_x[self.selected_charging_station]
            self.next_stop_y = charging_stations_y[self.selected_charging_station]
            self.need_to_charge = True
        else: 
            self.next_line = 0
            self.next_stop_x = lines_output_points_x[self.next_line]
            self.next_stop_y = lines_output_points_y[self.next_line]
            
    def move(self): #Function that simulates the travel of the tugger train to the next stop and the loading/unloading of unit loads:
        distance_next_stop = u.compute_distance(self.pos_x, self.next_stop_x, self.pos_y, self.next_stop_y)
        self.task_endtime += u.compute_time(distance_next_stop, speed = u.compute_speed(self.weight), nextline = self.next_line) #Travel time
        self.remaining_energy -= u.compute_energy(u.compute_time(distance_next_stop,speed = u.compute_speed(self.weight), nextline = self.next_line,))
        
        self.pos_x = self.next_stop_x
        self.pos_y = self.next_stop_y
        
        if self.need_to_charge == False: #If the next stop is not a charging station
            if (self.pos_x,self.pos_y) != (warehouse_coord[0],warehouse_coord[1]): #If the reached position is a line output point (and not the warehouse)
                if self.model.schedule_lines.agents[self.next_line].UL_in_buffer >= 1: #If there is at least one unit load at the line output point
                    if self.load < self.capacity:
                        if (self.weight + output_weight[self.next_line]) <= self.weight_capacity:# If the train is not full, it loads one unit load
                            print("\n"+self.unique_id,"going to line",self.next_line,"and picking up a unit load")
                            loading_time = random.uniform(30, 60) #Loading time (between 30 seconds and 1 minute)
                            self.task_endtime += loading_time
                            self.remaining_energy -= u.compute_energy_loading(output_weight[self.next_line])
                            self.model.schedule_lines.agents[self.next_line].UL_in_buffer -= 1
                            self.load += 1
                            self.weight += output_weight[self.next_line]
                        else:
                            print("\n" + self.unique_id, "- Not enough weight capacity left.")

                    else:
                        print("\n"+self.unique_id,"going to line",self.next_line,"- Not enough loading capacity left") 
                else:
                   print("\n"+self.unique_id,"going to line",self.next_line,"- No unit loads to be picked up")
                #self.next_line += 1
            else:
                print("\n"+self.unique_id,"going back to the warehouse and unloading",self.load,"unit loads")
                unloading_time = 30 + random.uniform(30, 60)*self.load #Fixed time to stop the vehicle in the right position (30 seconds) + unloading time for each unit load (between 30 seconds and 1 minute)
                self.task_endtime += unloading_time
                self.remaining_energy -= u.compute_energy_loading(self.weight)
                self.load = 0
                self.weight=0
        
            if self.next_line >= 4:
                self.next_stop_x = warehouse_coord[0]
                self.next_stop_y = warehouse_coord[1]

            else: # Added
                self.next_line += 1
                self.next_stop_x = lines_output_points_x[self.next_line]
                self.next_stop_y = lines_output_points_y[self.next_line]
        print("Travelled distance:",distance_next_stop,"m","- Task endtime (hours):",round(self.task_endtime/3600,2),"- Remaining energy:",round(self.remaining_energy,2),"kWh", " - Carried weight: ", self.weight)
        
    def charging(self): #Function that simulates the (possible) queuing at the charging station and the battery charging:
        print("\n"+self.unique_id,'charging at charging station',self.selected_charging_station)
        
        #Queuing time (waiting for the charging station to be available):
        self.task_endtime += self.model.schedule_stations.agents[self.selected_charging_station].waiting_time #schedule_stations.agents contains the list of all ChargingStation agents
        
        charging_size = self.battery_size - self.remaining_energy #It is assumed to restore the maximum battery level
        power = 4.9 #[kW] - Power of the charging station
        charging_time = (charging_size/power)*3600  # seconds
        self.remaining_energy += charging_size
        self.model.schedule_stations.agents[self.selected_charging_station].waiting_time += charging_time
        self.task_endtime += charging_time
        print("Task endtime (hours):",round(self.task_endtime/3600,2),"- Remaining energy:",self.remaining_energy, "kWh")
        self.next_line = 0
        self.need_to_charge = False
        
    def step(self):
        if self.task_endtime <= self.model.system_time:
            if (self.pos_x,self.pos_y) == (warehouse_coord[0],warehouse_coord[1]):
                self.check_charge()
            if self.need_to_charge == True:
                self.charging()
            else:
                self.move()


class ChargingStation(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.waiting_time = 0 #Time that a tugger train must wait before beginning its charging process at this station

    def step(self):
        if self.waiting_time >= 1: #1 is the step duration
            self.waiting_time -= 1 #1 is the step duration
        else:
            self.waiting_time = 0 # Potrebbe essere inutile?

class Line(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.line_index = int(self.unique_id[-1]) #The last character in the unique_id is the number indicating the line (see FactoryModel)
        self.cycle_time = lines_cycle_times[self.line_index] #Production time of one unit load (minutes)
        self.buffer_size = 3 #Maximum number of unit Loads in the buffer at the line output point
        self.UL_in_buffer = 0 #Actual number of unit loads in the buffer at the line output point. The buffer is empty at the beginning of the simulation 
        self.total_production = 0 #Overall number of unit loads produced by the line
        self.idle_time = 0 #Time (minutes) during which the station is not producing since the buffer is full
        self.count_time = 0 #Attribute needed to simulate the production of one unit load "every cycle time" (see the step function)

    def step(self):
        if self.UL_in_buffer < self.buffer_size: #If the buffer at the output point is not full
            self.count_time += 1
            if self.count_time == self.cycle_time:    
                self.total_production += 1
                self.UL_in_buffer += 1
                self.count_time = 0
        else:
            self.idle_time += 1
        
class FactoryModel(Model):
    def __init__(self): 
        super().__init__()
        self.schedule_trains = BaseScheduler(self)
        self.schedule_stations = BaseScheduler(self)
        self.schedule_lines = BaseScheduler(self)
        self.system_time = 0 #This attribute will keep track of the system time, advancing by 1 minute at each step
        
        #Creating tugger trains, charging stations and lines:
        self.schedule_trains.add(Train("Tugger train_1", self))

        for i in range(len(charging_stations_x)):
            a = ChargingStation("Charging station_"+str(i), self)
            self.schedule_stations.add(a)

        for i in range(5): #5 is the number of lines in the factory
            a = Line("Line_"+str(i), self)
            self.schedule_lines.add(a)
            
    def step(self):
        self.system_time += 1
        #print("System time: " + str(self.system_time))
        self.schedule_lines.step()
        self.schedule_trains.step()
        self.schedule_stations.step()

#Running the simulation:    
model = FactoryModel()
for i in range(n_shift*wh*3600):  # Seconds
    model.step()

print("\n","\n","SYSTEM PERFORMANCE:")
for i in range(5): #5 is the number of lines in the factory
    print(" Line",i,"\n","Actual production [UL]:",model.schedule_lines.agents[i].total_production," -  Maximum production [UL]:",int(model.system_time/lines_cycle_times[i]),"\n","Total idle time [sec]:",model.schedule_lines.agents[i].idle_time,"\n")
