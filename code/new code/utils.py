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
# Dove possiamo mettere la fase di accellerazione e decellerazione, qui oppure in compute time
# meglio in compute time
def compute_speed(weight:float, max_weight:float = 2000):
    '''
    weight:float

    Return the speed [m/s] of a train considering the weight is transporting, it supposes that the velocity
    decrease linearly with the load

    Returns
    -------
    float speed [m/s]
    '''
    speed_min = 1.2
    speed_max = 1.6
    return 1.6 - weight/max_weight * (speed_max - speed_min)


def compute_time(distance:float, speed = 1.4, nextline:int = 0):
    '''
    distance:float, speed:float
    
    Return time to travel considering the distance [m] and the speed. The time is computed adding a random
    delay depending on the final destination. It returns time in seconds [s]. There is a fixed amount of time
    added considering acceleration and deceleration time.
    
    Return
    -------
    float time [s]
    '''

    if nextline == 1 or 2 or 4:
        return distance/speed + random.uniform(1.0, 2.0) * distance + 5
    else:
        return distance/speed + random.uniform(0.0, 1.0) * distance + 5




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
