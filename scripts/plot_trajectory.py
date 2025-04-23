#!/usr/bin/env python3

'''
Trajectory Plot for CARLA experiments
---------------------------------------

This script plots the CARLA's vehicle trajectory and the SLAM odometry trajectory to compare.
Also calculates the endpoint translation error between the trajectories.

Usage:
------

To run this script and plot the trajectory from a bag file, you need to edit the config.yaml modifying the parameters.

Parameters:
    BAG_DIR (string): Path to the bags folders. Must be "BAG_DIR/{algorithm}/{map}/{bag_file}.bag";
    SKIP_RATE (int): Skip rate to plot the trajectory points;
    ODOM_TOPICS (dictionary): If you want to add a new SLAM algorithm, you need to define the algorithm name and the odometry topic;
    
Outputs:
    Image plots with CARLA odometry and SLAM algorithm odometry trajectories (png files);
    Image boxplots from the endpoint translation error (png files);
    Endpoint translation error (terminal).
    Mean and Standard Deviation from endpoint translation error (terminal).

Navigate into the script path and execute:

    'python3 plot_trajectory.py'
'''

import os
import numpy as np
import matplotlib.pyplot as plt
from bagpy import bagreader
import pandas as pd
import yaml
from collections import defaultdict

def load_config(config_path='config.yaml'):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def get_spawn_point(map_name, algorithm):
    map_name = map_name.lower()
    lidar_offset = 4.3 if algorithm != "dlio" else 0.0

    if map_name in ['town03', 'town3']:
        return -149.0, 20.0 - lidar_offset, 0.0, np.radians(-90.0)
    elif map_name in ['town04', 'town4']:
        return -15.7, -75.0 - lidar_offset, 0.0, np.radians(-90.0)
    elif map_name in ['town06', 'town6']:
        return -175.0 - lidar_offset, 15.3, 0.0, np.radians(180.0)
    else:
        raise ValueError(f"Invalid Map: {map_name}")

def transform_carla_point(x, y, T):
    global_point = np.array([[x], [y], [1]])
    local_point = np.linalg.inv(T) @ global_point
    return local_point[0, 0], local_point[1, 0]

def process_bag(bag_path, carla_topic, odom_topic, skip_rate, spawn_point, output_path, algorithm):
    bag = bagreader(bag_path)

    try:
        carla_csv = bag.message_by_topic(carla_topic)
        odom_csv = bag.message_by_topic(odom_topic)
    except ValueError as e:
        print(f"Error reading bag {bag_path}: {e}")
        return None  # <- Avoid NoneType error

    df_carla = pd.read_csv(carla_csv)
    df_odom = pd.read_csv(odom_csv)

    vehicle_x, vehicle_y, vehicle_z, vehicle_yaw = spawn_point
    T = np.array([
        [np.cos(vehicle_yaw), -np.sin(vehicle_yaw), vehicle_x],
        [np.sin(vehicle_yaw), np.cos(vehicle_yaw), vehicle_y],
        [0, 0, 1]
    ])

    x_true, y_true, z_true = [], [], []
    x_odom, y_odom, z_odom = [], [], []

    for i, row in df_carla.iterrows():
        if i % skip_rate == 0:
            x, y = transform_carla_point(row["pose.pose.position.x"], row["pose.pose.position.y"], T)
            x_true.append(x)
            y_true.append(y)
            z_true.append(row["pose.pose.position.z"])

    for i, row in df_odom.iterrows():
        if i % skip_rate == 0:
            x_odom.append(row["pose.pose.position.x"])
            y_odom.append(row["pose.pose.position.y"])
            z_odom.append(row["pose.pose.position.z"])

    if not x_true or not x_odom:
        print(f"Empty data in {bag_path}")
        return None

    translation_error = np.sqrt(
        x_odom[-1] ** 2 + y_odom[-1] ** 2 + z_odom[-1] ** 2
    )
    print(f"{os.path.basename(bag_path)} - Translation Error: {translation_error:.2f} m")
    
    pretty_names = {
        "lego_loam": "LeGO-LOAM",
        "lio_sam": "LIO-SAM",
        "fast_lio": "Fast-LIO2",
        "dlio": "DLIO"
    }

    # Trajectory Plot
    plt.figure(figsize=(8, 6))
    plt.plot(x_true, y_true, marker="o", linestyle="-", markersize=2, label="CARLA perfect odometry")
    plt.plot(x_odom, y_odom, marker="o", linestyle="-", markersize=2, label="Estimated odometry")
    plt.xlabel("X Position (m)")
    plt.ylabel("Y Position (m)")
    plt.title(f"Vehicle Trajectory - {pretty_names.get(algorithm, algorithm)}")
    plt.legend()
    plt.grid(True)

    os.makedirs(output_path, exist_ok=True)
    filename = os.path.splitext(os.path.basename(bag_path))[0]
    plt.savefig(os.path.join(output_path, f"{filename}.png"), dpi=300, bbox_inches='tight')
    plt.close()

    return translation_error

def generate_boxplots(errors):
    os.makedirs("plots/boxplots", exist_ok=True)

    # Boxplot by algorithm
    algo_data = defaultdict(list)
    for (algo, _map), errs in errors.items():
        algo_data[algo].extend(errs)

    plt.figure(figsize=(10, 6))
    plt.boxplot([algo_data[a] for a in algo_data], labels=algo_data.keys())
    plt.title("Translation Error by Algorithm")
    plt.ylabel("Final Point Error (m)")
    plt.grid(True)
    plt.savefig("plots/boxplots/boxplot_algorithms.png", dpi=300, bbox_inches="tight")
    plt.close()

    # Boxplot by (algorithm, map)
    plt.figure(figsize=(12, 6))
    keys = list(errors.keys())
    labels = [f"{a}\n{m}" for (a, m) in keys]
    data = [errors[k] for k in keys]
    plt.boxplot(data, labels=labels)
    plt.title("Final Point Error by Algorithm and Map")
    plt.ylabel("Final Point Error (m)")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("plots/boxplots/boxplot_maps.png", dpi=300, bbox_inches="tight")
    plt.close()
    
    # Remove lego_loam
    filtered_errors = {
        (algo, _map): errs
        for (algo, _map), errs in errors.items()
        if algo != "lego_loam"
    }

    algo_data = defaultdict(list)
    for (algo, _map), errs in filtered_errors.items():
        algo_data[algo].extend(errs)

    plt.figure(figsize=(10, 6))
    plt.boxplot([algo_data[a] for a in algo_data], labels=algo_data.keys())
    plt.title("Final Point Error by Algorithm")
    plt.ylabel("Final Point Error (m)")
    plt.grid(True)
    plt.savefig("plots/boxplots/boxplot_algorithms_no_lego_loam.png", dpi=300, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(12, 6))
    keys = list(filtered_errors.keys())
    labels = [f"{a}\n{m}" for (a, m) in keys]
    data = [filtered_errors[k] for k in keys]
    plt.boxplot(data, labels=labels)
    plt.title("Final Point Error by Algorithm and Map")
    plt.ylabel("Final Point Error (m)")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("plots/boxplots/boxplot_maps_no_lego_loam.png", dpi=300, bbox_inches="tight")
    plt.close()

def compute_algorithm_statistics(errors):
    algo_errors = defaultdict(list)
    
    for (algo, _map), err_list in errors.items():
        algo_errors[algo].extend(err_list)
    
    stats = {}
    for algo, errs in algo_errors.items():
        if errs:
            stats[algo] = {
                "mean": np.mean(errs),
                "std": np.std(errs)
            }
        else:
            stats[algo] = {
                "mean": None,
                "std": None
            }
    return stats

def main():
    config = load_config()

    input_dir = config["BAG_DIR"]
    carla_topic = config["CARLA_TOPIC"]
    skip_rate = config["SKIP_RATE"]
    odom_topics = config["ODOM_TOPICS"]

    errors = defaultdict(list)

    for algorithm, odom_topic in odom_topics.items():
        algorithm_path = os.path.join(input_dir, algorithm)
        if not os.path.isdir(algorithm_path):
            continue

        for map_name in os.listdir(algorithm_path):
            map_path = os.path.join(algorithm_path, map_name)
            if not os.path.isdir(map_path):
                continue

            try:
                spawn_point = get_spawn_point(map_name, algorithm)
            except ValueError:
                print(f"Ignoring {map_name} (not recognized map)")
                continue

            for file in os.listdir(map_path):
                if file.endswith(".bag"):
                    bag_path = os.path.join(map_path, file)
                    output_path = os.path.join("plots", algorithm, map_name)
                    error = process_bag(bag_path, carla_topic, odom_topic, skip_rate, spawn_point, output_path, algorithm)
                    if error is not None:
                        errors[(algorithm, map_name)].append(error)

    generate_boxplots(errors)
    
    stats = compute_algorithm_statistics(errors)
    for algo, stat in stats.items():
        print(f"{algo}: Mean = {stat['mean']:.3f} m, Standard Deviation = {stat['std']:.3f} m")

if __name__ == "__main__":
    main()
