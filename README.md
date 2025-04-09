# Data Analysis for Robotics Simulations

This repository contains a set of scripts and utilities to process and analyze ROS bag files. It converts ROS bags into CSV format, organizes data per topic, generates plots for velocities and trajectories, and computes errors for analysis.

## Dependencies

- `bagpy`
- `pandas`
- `matplotlib`
- `pyyaml`
- `numpy`
- `scikit-learn`

Install dependencies with:

```
pip install bagpy pandas matplotlib pyyaml numpy scikit-learn
```


## Folder Structure Created by Script

Upon running the script, the following structure is created within your specified `bag_folder`:

- **csv_files/**
  - **per_run/**
    - **run_0/** (individual run CSV files)
    - **run_1/**
    - ... and so on.
  - **per_topic/**
    - **topic_name_1/**
    - **topic_name_2/**
    - ... and so on.

- **plots/**
  - Velocity and trajectory plots generated from CSV files.

- **errors/**
  - CSV files containing computed position and velocity errors for each run.

## User Manual

### Setup

1.  Place your ROS bag files (`run_X.bag`) inside a folder (`bag_folder`).
2. Prepare your configuration file (`config.yaml`) according to your ROS topics.

Example `config.yaml` structure:

```
topics:
  real_velocity:
    name: "/real_vel"
    csv_file: "real_vel.csv"
    type: "geometry_msgs/Twist"
  controller_velocity:
    name: "/planned_vel"
    csv_file: "planned_vel.csv"
    type: "geometry_msgs/Twist"
  trajectory_plan:
    name: "/trajectory_plan"
    csv_file: "trajectory_plan.csv"
    type: "nav_msgs/Path"
```

### Execution Flow
The script must be executed in the following order in `main()`:

1. **load_config**
2. **convert_bags_to_csv**
3. **organize_csv_per_topic**
4. **plot_velocities_for_all_runs** *(optional plotting)*
5. **plot_velocities_for_single_run** *(optional plotting)*
6. **plot_mean_velocity** *(optional plotting)*
7. **plot_single_trajectory_or_comparison** *(optional plotting)*
8. **calculate_and_save_all_errors**


## functions

### load_config(config_path)
Obligatory to load the names and types of your topics.
- **Parameters:**
  - `config_path` *(str)*: Path to the YAML configuration file.
- **Usage:**
```
topics = load_config("path/to/config.yaml")
```

### convert_bags_to_csv(bag_folder, num_bags, topics)
Obligatory to convert ROS bags into csv files

- Converts `.bag` files into CSV format.
- **Parameters:**
  - `bag_folder` *(str)*: Directory containing `.bag` files.
  - `num_bags` *(int)*: Number of `.bag` files to process.
  - `topics` *(dict)*: Topic definitions from `config.yaml`.
- **Usage:**
```
convert_bags_to_csv("path/to/bag_folder", 2, topics)
```

### organize_csv_per_topic(bag_folder, num_bags, topics)
Obligatory to organize the files into a structure the library works with.

- Organizes CSV files into separate directories per topic.
- **Parameters:**
  - Same as above.
- **Usage:**
```
organize_csv_per_topic("path/to/bag_folder", 2, topics)
```

### plot_velocities_for_all_runs(bag_folder, num_bags, topics)

- Generates velocity plots across all runs.
- **Usage:**
```
plot_velocities_for_all_runs("path/to/bag_folder", 2, topics)
```

### plot_velocities_for_single_run(bag_folder, run_id, topics)

- Generates velocity plots for a single run.
- **Usage:**
```
plot_velocities_for_single_run("path/to/bag_folder", 0, topics)
```

### plot_mean_velocity(bag_folder, run_ids, topic_name, topics)

- Generates plots of mean velocity across multiple runs.
- **Usage:**
```
plot_mean_velocity("path/to/bag_folder", [0, 1], "real_vel", topics)
```

### plot_single_trajectory_or_comparison(bag_folder, run_id, topics, plot_real_trajectory, plot_planned_trajectory, offset_planned, offset_real)

- Plots real and/or planned trajectories, optionally offsetting to origin.
- **Usage:**
```
plot_single_trajectory_or_comparison("path/to/bag_folder", 0, topics, True, True, True, True)
```

### calculate_and_save_all_errors(bag_folder, run_ids, topics, position_error, yaw_error, velocity_error)

- Calculates and saves position, yaw, and velocity errors.
- **Usage:**
```
calculate_and_save_all_errors("path/to/bag_folder", [0, 1], topics, True, True, True)
```


## Errors and Plots

- Errors are computed as RMSE, mean absolute, and max absolute errors per axis (X, Y, Z).
- Plots generated are saved as PNG images in the `plots` folder.


## Notes and Warnings

- CSV file naming and topic definitions in your configuration file must match exactly.
- Some functions issue warnings if expected data or CSV files are missing or incorrectly formatted.

---
