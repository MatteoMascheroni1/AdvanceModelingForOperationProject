import csv
import scipy as sc
path = "./charging.csv"

#remaining_energy:float, tot_cap:float
def computeChargingTime(percentage:float):
    charge = dict()
    with open(path, "r") as f:
        f.seek(0)
        for line in f.readlines()[1:]:
            a = line.split(',') # The elements of the list a are strings, corresponding to the comma-separated values in the line
            charge[float(a[0])] = int(a[1].replace("\n", ""))*60
    for i in charge.keys():
        if percentage<=i:
            max_index = i
            break
        if percentage>=i:
            min_index = i

    upper_time = charge[max_index]
    lower_time = charge[min_index]

    interpolated_time = lower_time*(max_index - percentage) + upper_time*(percentage - min_index)
    interpolated_time = interpolated_time/(max_index - min_index)
    time = charge[1] - upper_time
    time += interpolated_time
    return time


print(computeChargingTime(0.19))