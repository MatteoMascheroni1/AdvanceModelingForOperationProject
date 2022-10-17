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
            cycle_times.append(float(a[3]))
            weights.append(float(a[4]))
    return(x, y, cycle_times, weights)




def compute_distance(x1:float, x2:float, y1:float, y2:float):
    '''
    x1:int, x2:int, y1:int, y2:int
    
    Return rectilinear distance between two points.
    
    Return
    -------
    float distance
    '''
    return abs(x1 - x2) + abs(y1 - y2)