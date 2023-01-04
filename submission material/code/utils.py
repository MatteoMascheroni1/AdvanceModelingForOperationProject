import random

def read_line_info(path: str, conversion_factor=60):
    """
    :param path: str path to the file
    :param conversion_factor: adjust measure unit, default is 60 (from minutes to seconds)
    :return: Tuple (x, y, cycle times, UL weights)

    Read file and return lines info.
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


def compute_distance(x1: float, x2: float, y1: float, y2: float, max_x: float = 75):
    """
    :param x1: float, x of first point
    :param x2: float, x of second point
    :param y1: float, y of first point
    :param y2: float, y of second point
    :param max_x: correction factor. Default is 75
    :return: rect distance between two points

    Returns rectilinear distance between two points. The x_max is the correction factor to avoid the miscalculation
    of distance between station 3 e 4.
    """
    if y2 > y1:
        return abs(max_x - x1) + (max_x - x2) + abs(y1 - y2)
    else:
        return abs((max_x - x1) - (max_x - x2)) + abs(y1 - y2)


def compute_speed(weight: float, max_weight: float = 2000):
    """
    :param weight: float, carried weight
    :param max_weight: float, maximum weight. Default is 2000kg
    :return: float speed [m/s]

    Returns the speed [m/s] of a tugger considering the weight it is transporting. Here, we assume that the speed
    decreases linearly with the load. Assume by a rule of thumb that speed_min = 1.2 m/s and speed_max = 1.6 m/s
    """
    speed_min = 1.2
    speed_max = 1.6
    speed = speed_max - weight / max_weight * (speed_max - speed_min)
    return speed


def compute_time(distance: float, speed: float, nextline: int = 0, random_flag: bool=True):
    """
    :param distance: float, distance to be travelled
    :param speed: float, speed of the tuggers
    :param nextline: int, id of next line
    :param random_flag: bool, if set True consider process stochasticity. Default is True
    :return: times [s]

    Returns the cartesians' movements' time  considering distance [m] to be travelled, speed, and the
    plane's area which the tugger moves on. The time is computed adding a random
    delay depending on the final destination and on the distance.
    Furthermore a fixed amount corresponding to acceleration and decelaration has been added.
    The function returns time in seconds.
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


def compute_energy(time: float, consumption: float = 2.6):
    """
    :param time: float, time in seconds
    :param consumption: consumption in [kWh]. Default is 2.6
    :return: Energy Consumed

    Consumption is defined as an average consumption by EN standard.
    """
    energy = consumption / 3600 * time
    return energy


def compute_energy_loading(weight: float, disp: float = 1.2, frict: float = 1.2):
    """
    :param weight: float, UL weight
    :param disp: displacement in meters to compute energy used. Default is 1.2
    :param frict: friction coefficient. Default is 1.2
    :return: energy consumed [kWh]

    Returns energy consumed to load and unload the pallet loads, computed on the displacement moved
    and the weight of the pallet.
    """
    energy = disp * weight * 9.81 / 3600000 * frict
    return energy


def progress(percent=0, width=40):
    """
    :param percent: percentage of completion
    :param width: bar size. Default is 40.
    :return: None
    Print progress bar.
    """
    left = width * percent // 100
    right = width - left
    tags = "=" * left
    spaces = " " * right
    percents = f"{percent:.0f}%"
    print("\r[", tags, spaces, "] ", percents, sep="", end="", flush=True)


def read_charging_phases(path: str):
    """
    :param path: str, path of the csv file
    :return: dict with all the charging data
    Read the file with the charging times
    """
    charge = dict()
    with open(path, "r") as f:
        f.seek(0)
        for line in f.readlines()[1:]:
            a = line.split(',')
            charge[float(a[0])] = int(a[1].replace("\n", ""))*60
    return charge


def compute_charging_time(charge: dict, remaining_energy: float, tot_cap: float):
    """
    :param charge: Dictionary with charging stages
    :param remaining_energy: float, Remaining energy of the tugger
    :param tot_cap: float, Total capacity of the battery
    :return: Time to reach full charge

    Compute time to reach full charge by assuming linear interpolation between different percentage. Under expert advice,
    we used iphone pro charging function phases.
    """
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


def check_behavior(*args):
    """
    :param args: parameters
    :return: True if just one args is True or if all args are False. Otherwise return False

    Check if simulation parameters have been defined properly.
    """
    return sum(args) == 1 or sum(args) == 0


def check_combination(*args):
    """
    :param args: Lists of hyperparameters
    :return: True if the more than one parameter was declared in hyperparameters lists, False otherwise

    Function that return True if the more than one parameter was declared in hyperparameters lists.
    """
    s_ = 0
    for a in args:
        s_ += len(a)
    return s_ > 3


