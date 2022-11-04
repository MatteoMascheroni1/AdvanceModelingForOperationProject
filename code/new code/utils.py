import random
# Parameters
max_x = 75 # Extreme right point of tugger train path




def read_line_info(path:str, conversion_factor = 60):
    '''
    path:str path to the file
    conversion_factor: adjust measure unit
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
            cycle_times.append(float(a[3])*conversion_factor)
            weights.append(float(a[4]))
    return (x, y, cycle_times, weights)




def compute_distance(x1:float, x2:float, y1:float, y2:float, max_x = max_x):
    '''
    x1:float, x2:float, y1:float, y2:float
    
    Return rectilinear distance between two points. The if condition is to avoid the miscalculation of distance between station 3 e 4.
    
    Return
    -------
    float distance
    '''

    if y2 > y1:
        return abs(max_x - x1) + (max_x - x2) + abs(y1 - y2)
    else:
        return abs((max_x - x1) - (max_x - x2)) + abs(y1 - y2)
    return abs(x1 - x2) + abs(y1 - y2)



'''
def compute_speed(weight:float):
    speed = funct
    return speed
'''

def compute_time(distance:float, speed = 1.4):
    '''
    distance:float, speed:float
    
    Return time to travel a distance given a certain speed. Random component is distributed as ~unif(0,60) secondi.
    Distance is expressed in [m] and speed in [m/s]
    
    Return
    -------
    float time
    '''
    time = distance/speed + random.uniform(0,60)
    return time #[seconds]




def compute_energy(time:float, consumption = 2.6):
    '''
    time:float
    consumption: [kwh]
    Consumption is defined as average consumption by EN standard.
    
    Return energy consumed.

    -------
    float energy
    '''
    energy = consumption / 60 * time/60
    return energy
