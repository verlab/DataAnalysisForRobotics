# Data Analysis for Robotics Simulations

This repository contains a set of scripts and utilities to process and analyze ROS bag files. It converts ROS bags into CSV format, organizes data per topic, generates plots for velocities and trajectories, and computes errors for analysis.

<p align="center">
  <img src="./images/mean_linear_real_vel.png" width="200" height="200" alt="Image 1"/>
  <img src="./images/real_velocities_run_0.png" width="200" height="200" alt="Image 2"/>
  <img src="./images/True_vs_Planned_Path_run_10.png" width="200" height="200" alt="Image 3"/>
</p>

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

Install dependencies with:

```
pip install bagpy pandas matplotlib pyyaml numpy scikit-learn glob2
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
    name: "lego_loam-odom"
    type: "geometry_msgs/PoseStamped"
    csv_file: "lego_loam-odom.csv"
  trajectory_plan:
    name: "move_base-DWAPlannerROS-global_plan"
    type: "nav_msgs/Path"
    csv_file: "move_base-DWAPlannerROS-global_plan.csv" # it will be the name of the topic.csv
  gps_plan:
    name: "reach-fix"
    type: "gps/points"
    csv_file: "reach-fix.csv"
  waypoints_coords:
    name: "simulation_demo.yaml"
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
5. missing functions

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
  - 2D trajectory visualization (X vs. Y) of both real and planned paths.
  - Optional offset to origin for alignment and easier visual comparison.

Each plot is saved as a PNG image and named accordingly (e.g., `real_velocities_run_0.png`, `trajectory_comparison_run_1.png`, etc.).

### missing plots of distance x waypoint

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

### missing functions

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

### Error Computation

## Notes and Warnings

- CSV file naming and topic definitions in your configuration file must match exactly, so please do not move or rename any folder or file.
- Some functions issue warnings if expected data or CSV files are missing or incorrectly formatted.

---
