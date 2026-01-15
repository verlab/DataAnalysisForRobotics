# Data Analysis for Robotics Simulations

This repository contains a set of scripts and utilities to process and analyze ROS bag files. It converts ROS bags into CSV format, organizes data per topic, generates plots for velocities and trajectories, and computes errors for analysis.

## Table of Contents

- [Overview](#data-analysis-for-robotics-simulations)
- [Dependencies](#dependencies)
- [Folder Structure Created by Script](#folder-structure-created-by-script)
- [User Manual](#user-manual)
  - [Setup](#setup)
  - [Execution Flow](#execution-flow)
- [Errors and Plots](#errors-and-plots)
- [Bag File Naming Warning](#bag-file-naming-warning)
- [Execution Flow Example](#execution-flow-example)
- [Available Functions](#available-functions)
  - [Setup & Data Preparation](#setup--data-preparation)
  - [Plotting](#plotting)
  - [Error Computation](#error-computation)
- [Notes and Warnings](#notes-and-warnings)

## Dependencies

- `bagpy`
- `pandas`
- `matplotlib`
- `pyyaml`
- `numpy`
- `scikit-learn`
- `re`
- `glob`
- `geopy`

Install dependencies with:

```
pip install bagpy pandas matplotlib pyyaml numpy scikit-learn glob2 geopy
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

1.  Place your ROS bag files inside a folder (`bag_folder`).
2. Prepare your configuration file (`config.yaml`) according to your ROS topics.
3. Include in the same folder as your ROS bags, the .yaml containing the GNSS waypoints of the experiment.

Example `config.yaml` structure:

```
topics:
  estimated_position:
    name: "/odometry/global"
  trajectory_plan:
    name: "/move_base/TEBPlannerROS/global_plan"
  gps_plan:
    name: "/gnss_left/fix"
  waypoints_coords:
    name: "demo_baylands.yaml"
```

### Command Line Usage
You can use this repository either as a Python library, calling individual functions within your own code, or run it as a standalone script that automatically processes the bag files—handling conversion, plotting, and error calculations in one go.

 From the root of the repository, run:

```python
cd scripts/packaged/
```
Then run the code:
```python
python fullAnalysis.py --bag_folder <path-to-ros-bags> --config_path config.yaml
```

### Execution Flow
To use it as a library, there are some obligatory commands, the script must be executed in the following order in `main()`:

1. **load_config**
2. **get_sorted_bag_mapping**
3. **convert_bags_to_csv**
4. **organize_csv_per_topic**
5. **calculate errors**
6. **plot functions**

## Errors and Plots

This library generates visualizations and numerical evaluations of your robot's performance by comparing ground-truth data with planned or estimated trajectories and velocities.

### Error Metrics

Errors are calculated along three axes — X, Y, and Z — using the following metrics:

- **RMSE (Root Mean Square Error)**  
  Measures the standard deviation of the differences between predicted and actual values. A lower RMSE indicates better performance.

- **Mean Absolute Error (MAE)**  
  The average magnitude of errors in each axis, giving a direct sense of how far off the values are on average.

- **Max Absolute Error**  
  The single largest deviation observed for each axis, useful for identifying worst-case behavior.

The following types of errors are computed:

- **Position Error:**  
  Compares estimated robot positions against ground-truth (e.g., from localization vs. odometry).

- **Yaw Error (Orientation):**  
  Specifically compares the X component of quaternion orientation to assess heading error.

All errors are saved as CSV files in the `errors/` directory and aggregated for all specified runs.

### Bag File Naming Warning

> **ROS Bag File Format Requirement**
>
> This tool requires your ROS bag files to follow the **default ROS naming convention**, which looks like this:
>
> ```` 
> YYYY-MM-DD-HH-MM-SS.bag
> ````
>
> Example:
>
> ```` 
> 2025-04-11-13-55-04.bag
> ````
>
> Files that do not match this exact format will be **ignored** during processing.  
> This naming convention is used to determine the temporal order of the bags (oldest to newest) before assigning them internally as `run_0`, `run_1`, etc.
>
> Valid: `2024-12-01-08-00-00.bag`  
> Invalid: `test_run1.bag`, `04112025_13_55_04.bag`, `run0.bag`

### Execution Flow Example

### Plot Outputs

Plots are automatically generated from CSV data and saved in the `plots/` folder. These help visually assess the system's behavior and compare it to expectations.

- **Trajectory Plots:**
  - 2D trajectory comparision (Ground Truth GPS vs. estimated odometry) of executed paths.
  - Optional offset to origin for alignment and easier visual comparison.

- **Distance to waypoints:**
  - Distance (in meters) until reach each of the fisrt three waypoints.

Each plot is saved as a PNG image and named accordingly (e.g., `distance_to_waypoints_run_0.png`, `trajectory_comparison_run_1.png`, etc.).

## Execution Flow Example

The following steps illustrate a typical usage of the library by walking through the `main()` function. Each function call processes ROS bag data and generates structured outputs, plots, and evaluation metrics.


### 1.) Load Topic Configuration

Load your topic definitions (names, types, and CSV output filenames) from a YAML config file.

```python
topics = load_config("config.yaml")
```

*Loads topic metadata required for all downstream steps.*

### 2.) Sort ROS Bags

Sort your bag files in chronological order.

```python
get_sorted_bag_mapping(bag_folder)
```

### 3.) Convert ROS Bags to CSV

Convert `.bag` files into individual CSV files, one folder per run.

```python
convert_bags_to_csv(bag_folder, num_bags, topics)
```

*Creates `csv_files/per_run/run_X/` folders, each with CSVs for all topics.*


### 4.) Organize CSVs by Topic

Reorganize per-run CSVs into per-topic folders.

```python
organize_csv_per_topic(bag_folder, num_bags, topics)
```

*Creates `csv_files/per_topic/topic_name/` folders for analysis.*

### 5.) Calculate and Save Errors

Iterate through each run to calculate position errors (GPS vs. Odometry) and length drift, saving the results to CSV files within the errors directory.

```python
for run_id in run_ids:
  # Position Errors
  pos_errors = calculate_position_error_gps_vs_odometry(bag_folder, run_id, topics)
  save_errors_to_csv(pos_errors, bag_folder, run_id)
  
  # Drift Errors
  drift_errors = calculate_length_drift_error(bag_folder, run_id, topics)
  save_errors_to_csv(drift_errors, bag_folder, run_id, label="length_drift")
```

*Generates error reports in `errors/run_X_...csv` for quantitative analysis.*

### 6.) Compute Path Metrics

Calculate total path lengths and trajectory efficiency to evaluate the robot's performance consistency.

```python
calculate_and_save_path_lengths(bag_folder, run_id, topics)
calculate_trajectory_efficiency_error(bag_folder, run_id, topics)
```

*Computes and saves metrics regarding the distance traveled and path efficiency.*

### 7.) Generate Plots

Create visualizations for distance to specific waypoints and compare the estimated odometry trajectory against the GPS ground truth.

```python
# Plot distance to waypoints
plot_distance_to_waypoints(bag_folder, run_id, topics, waypoint_indices=[0, 1, 2, 3])

# Plot trajectory comparison
plot_single_trajectory_or_comparison(
    bag_folder, run_id, topics, 
    plot_estimated_trajectory=True, 
    plot_gps_trajectory=True, 
    offset_est=False, 
    offset_gps=False
)
```

*Saves visual plots in the `plots/` directory to facilitate manual inspection of the robot's behavior.*

## Available Functions

Below is a summary of the core functions provided by this library. These functions are designed to streamline the process of working with ROS bag files, organizing data, plotting results, and evaluating performance metrics.

---

### Setup & Data Preparation

- **`load_config(config_path)`**  
  Loads the YAML configuration file with topic names and types.  
  **Usage:**  
  ```python
  topics = load_config("path/to/config.yaml")
  ```

- **`get_sorted_bag_mapping(bag_folder`**  
Scans for `.bag` files in the folder and returns a dictionary mapping `run_X` file path, sorted by modification time.

  **Usage:**  
  ```python
  python bag_mapping = get_sorted_bag_mapping("path/to/bag_folder")
  ```

- **`convert_bags_to_csv(bag_folder, num_bags, topics)`**  
  Converts `.bag` files into CSV format. Creates `csv_files/per_run` with separated CSVs per run.  
  **Usage:**  
  ```python
  convert_bags_to_csv("path/to/bag_folder", 2, topics)
  ```

- **`organize_csv_per_topic(bag_folder, num_bags, topics)`**  
  Organizes CSVs into folders per topic for downstream processing.  
  **Usage:**  
  ```python
  organize_csv_per_topic("path/to/bag_folder", 2, topics)
  ```

- **`extract_poses_from_csv(input_csv, output_csv)`**  
  Parses pose data from complex CSVs (e.g., trajectory plans) and rewrites them into structured format.  

- **`parse_pose_block(pose_block)`**  
  Helper to extract position and orientation from raw YAML-style blocks.


### Plotting

- **`plot_single_trajectory_or_comparison(bag_folder, run_id, topics, ...)`** Generates a 2D plot comparing the Estimated Trajectory (Odometry) against the GPS Trajectory (Ground Truth). It can also plot the waypoints. It supports offsetting trajectories to the origin (0,0) for easier visual comparison of shapes.  
  **Usage:** 
  ```python
  plot_single_trajectory_or_comparison(
      bag_folder, 
      run_id=0, 
      topics=topics, 
      plot_estimated_trajectory=True, 
      plot_gps_trajectory=True,
      offset_est=False,
      offset_gps=False
  )
  ```

- **`plot_distance_to_waypoints(bag_folder, run_id, topics, waypoint_indices)`** Plots the Euclidean distance from the robot to specific waypoints over time. It visually marks the exact timestamp when the robot arrived (distance < threshold) at a specific waypoint.  
  **Usage:** 
  ```python
  # Plot distance to the first 4 waypoints
  plot_distance_to_waypoints(bag_folder, 0, topics, waypoint_indices=[0, 1, 2, 3])
  ```

### Error Computation

- **`calculate_position_error_gps_vs_odometry(bag_folder, run_id, topics)`** Computes the Root Mean Square Error (RMSE) and Mean Absolute Error (MAE) between the Estimated Odometry and the GPS Ground Truth.  
  *Note: This function automatically synchronizes the two time-series (via interpolation) and converts GPS Lat/Lon to local X/Y coordinates before comparison.* **Usage:** 
  ```python
  errors = calculate_position_error_gps_vs_odometry(bag_folder, 0, topics)
  # Returns: {'rmse': {'x': ..., 'y': ...}, 'mae': {...}}
  # Saves to: errors/errors_position_run_0.csv
  ```

- **`calculate_length_drift_error(bag_folder, run_id, topics)`** Calculates the difference in **total path length** measured by Odometry versus GPS. This is useful for identifying odometry scaling issues (e.g., wheel radius calibration).  
  **Usage:** 
  ```python
  calculate_length_drift_error(bag_folder, 0, topics)
  # Saves to: errors/length_drift_error_run_0.csv
  ```

- **`calculate_trajectory_efficiency_error(bag_folder, run_id, topics)`** Evaluates how efficient the robot's path was by comparing the **GPS path length** (actual distance traveled) against the **Minimal Waypoint path length** (ideal straight lines between waypoints).  
  **Usage:** 
  ```python
  calculate_trajectory_efficiency_error(bag_folder, 0, topics)
  # Saves to: errors/trajectory_efficiency_error_run_0.csv
  ```

- **`calculate_and_save_path_lengths(bag_folder, run_id, topics)`** A helper function that computes Odometry length, GPS length, and Minimal length simultaneously and saves them to a consolidated CSV for general comparison.  
  **Usage:** 
  ```python
  calculate_and_save_path_lengths(bag_folder, 0, topics)
  # Saves to: path_lengths/path_lengths_run_0.csv
  ```

## Notes and Warnings

- CSV file naming and topic definitions in your configuration file must match exactly, so please do not move or rename any folder or file.
- Some functions issue warnings if expected data or CSV files are missing or incorrectly formatted.

---
