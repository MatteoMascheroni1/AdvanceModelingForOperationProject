import random

def read_line_info(path:str): 
    '''
    path:str path to the file
    Read a file and returns line coordinates, cycle times[min] and weights for each line.
    
    Return
    -------
    Tuple (x, y, cycle times, UL weights)
    '''
    x = []
    y = []
    cycle_times = []
    weights = []
    
    with open(path, "r") as f:
        f.seek(0)
        for line in f.readlines()[1:]:
            a = line.split(',') #The elements of the list a are strings, corresponding to the comma-separated values in the line
            x.append(float(a[1]))
            y.append(float(a[2]))
            cycle_times.append(float(a[3])*60)
            weights.append(float(a[4]))
    return (x, y, cycle_times, weights)




def compute_distance(x1:float, x2:float, y1:float, y2:float):
    '''
    x1:float, x2:float, y1:float, y2:float
    
    Return rectilinear distance between two points.
    
    Return
    -------
    float distance
    '''
    return abs(x1 - x2) + abs(y1 - y2)




def compute_time(distance:float, speed:float):
    '''
    distance:float, speed:float
    
    Return time to travel a distance given a certain speed. Random component is distributed as ~unif(0,60) secondi.
    Distance is expressed in [m] and speed in [m/s]
    
    Return
    -------
    float time
    '''
    time = distance/speed/60 + random.uniform(0,60)
    return  time #[seconds]




def compute_energy(time:float, consumption:float):
    '''
    time:float
    consumption:float [kw/h]
    
    Return energy consumed 
    
    Return
    -------
    float energy
    '''
    energy = 2.6 / 60 * time  # HP: average energy consumption = 2,6 kWh every 60 minutes (both when the tugger train is travelling and when it is loading/unloading unit loads)
    return energy
