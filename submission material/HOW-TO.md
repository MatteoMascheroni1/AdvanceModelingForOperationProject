# How to use the script

We decided to divide the script into two main parts:

* `main.py` is the model of the factory and contains all data structures needed to collect data from the simulation
* `utils.py` in this file there are all the functions related to the model like compute charging time, compute energy consumption, and so on and so forth

## Parameters of the simulation

Henceforth we will refer to each possible way to execute the script as "simulation type".

###### Simulation type: "Run just once"

`isSearching=False`

`runWithSelectedN=False`

`findN=False`

This simulation type runs the model once and print system performances. The output won't be saved. If more than one combination of parameters is provided, the script will consider just the first element of each list.



###### Simulation type: "Find Runs Number"

`isSearching=False`

`runWithSelectedN=False`

`findN=True`

*Note: at maximum one parameter at a time can be set to True*

This simulation type runs the model with an increasing number of N to find the N that meets precision and alpha constraints. The final N will be printed at the end of the simulation and the output won't be saved. 



###### Simulation type: "Check multiple parameters"

`isSearching=True`

`runWithSelectedN=False`

`findN=False`

*Note: at maximum one parameter at a time can be set to True*

This simulation type runs the model just once with all possible combinations of parameters given. In the end, if `export_df_to_csv=True` the dataframe will be exported as csv file, otherwise if  `export_df_to_feather=True` the dataframe will be exported as a feather file. The path can be defined at the beginning of the script. In the table below there are all the attributes of the dataframe.

| Name            | Type | Description                                                  |
| --------------- | ---- | ------------------------------------------------------------ |
| Time            | Int  | Relative time of the combination of parameters               |
| Tugger N        | Int  | Number of tuggers                                            |
| Buffer          | List | List of buffer sizes line by line (ordered)                  |
| Tugger Capacity | Int  | Capacity of tuggers                                          |
| N Stations      | Int  | Number of charging stations                                  |
| Charging Status | List | List with charging status station by station (ordered). `False` if at Time the charging station is free, `True` otherwise. |
| Prod_*          | Int  | Total production until Time                                  |
| UL_in_buffer_*  | Int  | Units in buffer at Time                                      |
| Idle_time_*     | Int  | Total idle time untill Time                                  |

Replace the `*` with a number from 1 to 5 



###### Simulation type: "Runs the model N times with different configurations"

`isSearching=False`

`runWithSelectedN=True`

`findN=False`

*Note: at maximum one parameter at a time can be set to True*

This simulation type runs the model N times with a fixed parameter while varying others. For example, let's assume as in our case, that we want to run the simulation 801 times with 6 tuggers, a combination of buffer sizes of [3, 3, 3, 3, 3] and [4, 4, 4, 4, 4] and with 2 or 3 charging stations.

```{python3}
runWithSelectedN = True
hyper_tugger_train_number = [6 for i in range(801)]
hyper_ul_buffer = [[3, 3, 3, 3, 3], [4, 4, 4, 4, 4]]
hyper_n_charging_station = [2, 3]
```

By doing so, the model will be run in 4 different combinations of parameters 801 times each. We will need to group the dataframe obtained to make some further analysis. The dataframe will be composed of each combination of parameters and the average idle time in minutes. In the end, if `export_df_to_csv=True` the dataframe will be exported as csv file, otherwise if  `export_df_to_feather=True` the dataframe will be exported as a feather file. The path can be defined at the beginning of the script.
