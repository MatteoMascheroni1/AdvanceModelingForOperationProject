import random
import pandas as pd

# Parameters
max_x = 75  # Extreme right point of tugger train path


def read_line_info(path: str, conversion_factor=60):
    """
    path:str path to the file
    conversion_factor: adjust measure unit
    Read a file and returns line coordinates, cycle times[min] and weights for each line.

    Return
    -------
    Tuple (x, y, cycle times, UL weights)
    """
    x = []
    y = []
    cycle_times = []
    weights = []

    with open(path, "r") as f:
        f.seek(0)
        for line in f.readlines()[1:]:
            a = line.split(
                ',')  # The elements of the list a are strings, corresponding to the comma-separated values in the line
            x.append(float(a[1]))
            y.append(float(a[2]))
            cycle_times.append(float(a[3]) * conversion_factor)
            weights.append(float(a[4]))
    return x, y, cycle_times, weights


def compute_distance(x1: float, x2: float, y1: float, y2: float, max_x = max_x):
    """
    x1:float, x2:float, y1:float, y2:float, max_x

    Returns rectilinear distance between two points. The x_max is the correction factor to avoid the miscalculation of distance between station 3 e 4.

    Return
    -------
    float distance
    """

    if y2 > y1:
        return abs(max_x - x1) + (max_x - x2) + abs(y1 - y2)
    else:
        return abs((max_x - x1) - (max_x - x2)) + abs(y1 - y2)


def compute_speed(weight: float, max_weight: float = 2000):
    """
    weight:float

    Returns the speed [m/s] of a tugger considering the weight it is transporting. Here, we assume that the speed
    decreases linearly with the load. Assume by a rule of thumb that speed_min = 1.2 m/s and speed_max = 1.6 m/s

    Returns
    -------
    float speed [m/s]
    """
    speed_min = 1.2
    speed_max = 1.6
    speed = speed_max - weight / max_weight * (speed_max - speed_min)
    return speed


def compute_time(distance: float, speed: float, nextline: int = 0, random_flag=True):
    """
    distance:float, speed:float

    Returns the cartesians' movements' time  considering distance [m] to be travelled, speed, and the
    plane's area which the tugger moves on. The time is computed adding a random
    delay depending on the final destination and on the distance.
    Furthermore a fixed amount corresponding to acceleration and decelaration has been added.
    The function returns time in seconds.

    Return
    -------
    float time [s]
    """
    # fixed amount for accelerating is taken from LTX_20_T04_50_iGo_EN_TD.pdf page 2, acceleration time for the
    # truck with the same towing capacity

    if random_flag:
        if nextline in (1, 2, 4):
            return distance / speed + random.uniform(0.0, 1.0) * distance + 8
        else:
            return distance / speed + random.uniform(0.0, 0.5) * distance + 8
    else:
        if nextline in (1, 2, 4):
            return distance / speed + 8
        else:
            return distance / speed + 8


def compute_energy(time: float, consumption=2.6):
    """
    time:float
    consumption: [kwh]
    Consumption is defined as an average consumption by EN standard.

    Return energy consumed.

    -------
    float energy
    """
    energy = consumption / 3600 * time
    return energy


def compute_energy_loading(weight: float):
    """
    Parameters
    weight:float

    Returns energy consumed to load and unload the pallet loads, computed on the distance moved
    and the weight of the pallet

    Returns
    float: energy consumed [kWh]

    """
    energy = 1.2 * weight * 9.81 / 3600000 * 1.2
    return energy


def progress(percent=0, width=40):
    left = width * percent // 100
    right = width - left
    tags = "=" * left
    spaces = " " * right
    percents = f"{percent:.0f}%"
    print("\r[", tags, spaces, " ]   ", percents, sep="", end="", flush=True)


def read_charging_phases(path: str):
    """
    :param path: path of the csv file
    :return: dict with all the charging data
    """
    charge = dict()
    with open(path, "r") as f:
        f.seek(0)
        for line in f.readlines()[1:]:
            a = line.split(',')
            charge[float(a[0])] = int(a[1].replace("\n", ""))*60
    return charge


def compute_charging_time(charge: dict, remaining_energy: float, tot_cap: float):
    percentage = remaining_energy/tot_cap
    for i in charge.keys():
        if percentage <= i:
            max_index = i
            break
        if percentage >= i:
            min_index = i

    upper_time = charge[max_index]
    lower_time = charge[min_index]

    interpolated_time = lower_time*(max_index - percentage) + upper_time*(percentage - min_index)
    interpolated_time = interpolated_time/(max_index - min_index)
    time = charge[1] - upper_time
    time += interpolated_time
    return time




