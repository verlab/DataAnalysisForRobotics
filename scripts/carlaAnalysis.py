import os
import argparse
from dataAnalysisForRobotics import (
    load_config,
    get_sorted_bag_mapping,
    convert_bags_to_csv,
    organize_csv_per_topic,
    calculate_position_errors,
    save_errors_to_csv,
    calculate_and_save_all_errors
)
from scipy.spatial.transform import Rotation as R
import pandas as pd
import numpy as np

def apply_inverse_transform_to_position(x, y, z, T_inv):
    p_h = np.array([x, y, z, 1])
    p_transformed = T_inv @ p_h
    return p_transformed[:3]

def apply_inverse_transform_to_orientation(qx, qy, qz, qw, T_inv):
    quat = R.from_quat([qx, qy, qz, qw])
    inv_rot = R.from_matrix(T_inv[:3, :3])
    new_quat = inv_rot * quat
    return new_quat.as_quat()

def apply_odometry_transform(csv_path, rotation_deg, translation_vec):
    df = pd.read_csv(csv_path)

    rot = R.from_euler('z', rotation_deg, degrees=True).as_matrix()
    T = np.eye(4)
    T[:3, :3] = rot
    T[:3, 3] = translation_vec

    T_inv = np.linalg.inv(T)

    df[['pose.pose.position.x', 'pose.pose.position.y', 'pose.pose.position.z']] = df.apply(
        lambda row: apply_inverse_transform_to_position(
            row['pose.pose.position.x'],
            row['pose.pose.position.y'],
            row['pose.pose.position.z'],
            T_inv
        ), axis=1, result_type='expand'
    )

    df[['pose.pose.orientation.x', 'pose.pose.orientation.y', 'pose.pose.orientation.z', 'pose.pose.orientation.w']] = df.apply(
        lambda row: apply_inverse_transform_to_orientation(
            row['pose.pose.orientation.x'],
            row['pose.pose.orientation.y'],
            row['pose.pose.orientation.z'],
            row['pose.pose.orientation.w'],
            T_inv
        ), axis=1, result_type='expand'
    )

    df.to_csv(csv_path, index=False)

def summarize_errors_by_algorithm(base_folder, algorithms):
    all_data = []

    for algorithm in algorithms:
        algorithm_path = os.path.join(base_folder, algorithm)
        if not os.path.isdir(algorithm_path):
            continue

        for map_name in ['Town03', 'Town04', 'Town06']:
            errors_path = os.path.join(algorithm_path, map_name, "errors", "all_runs_position_errors.csv")
            if not os.path.exists(errors_path):
                continue

            df = pd.read_csv(errors_path)

            # RMSE total
            df["position_rmse_total"] = np.sqrt(
                df["position_rmse_pose.position.x"]**2 +
                df["position_rmse_pose.position.y"]**2 +
                df["position_rmse_pose.position.z"]**2
            )

            # MAE total
            df["position_mae_total"] = np.sqrt(
                df["position_mean_absolute_error_pose.position.x"]**2 +
                df["position_mean_absolute_error_pose.position.y"]**2 +
                df["position_mean_absolute_error_pose.position.z"]**2
            )

            # Orientation total
            df["orientation_rmse_total"] = np.abs(df["orientation_rmse_pose.orientation.x"])
            df["orientation_mae_total"] = np.abs(df["orientation_mean_absolute_error_pose.orientation.x"])

            df["algorithm"] = algorithm
            df["map"] = map_name

            all_data.append(df)

    if not all_data:
        print("[W] 'all_runs_position_errors.csv' not found.")
        return

    full_df = pd.concat(all_data, ignore_index=True)

    summary = full_df.groupby("algorithm")[
        ["position_rmse_total", "position_mae_total", "orientation_rmse_total", "orientation_mae_total"]
    ].mean().reset_index()

    output_path = os.path.join(base_folder, "errors_by_algorithm.csv")
    summary.to_csv(output_path, index=False)

def analyze_data(base_folder, config_path):
    topics = load_config(config_path)
    algorithms = topics["estimated_position"].keys()
    for algorithm in algorithms:
        if algorithm not in os.listdir(base_folder):
            continue
        
        topics = load_config(config_path)
        topics["estimated_position"] = topics["estimated_position"][algorithm]

        for map in ['Town03', 'Town04', 'Town06']:
            # Get bag file mapping sorted by time
            bag_folder = base_folder+'/'+algorithm+'/'+map
            
            if map not in os.listdir(base_folder+'/'+algorithm):
                continue
            if 'errors' in os.listdir(bag_folder):
                continue
            
            bag_mapping = get_sorted_bag_mapping(bag_folder)
            run_ids = list(range(len(bag_mapping)))
            num_bags = len(run_ids)

            convert_bags_to_csv(bag_folder, bag_mapping, topics)
            organize_csv_per_topic(bag_folder, num_bags, topics)

            for run_id in run_ids:
                csv_path = bag_folder+'/csv_files/per_run/run_'+str(run_id)+'/carla-ego_vehicle-odometry.csv'
                lidar_offset = 4.3 if algorithm != "dlio" else 0.0
                if map == 'Town03':
                    apply_odometry_transform(csv_path=csv_path, rotation_deg=-90, translation_vec=[-149.0, 20.0 - lidar_offset, 0.0])
                elif map == 'Town04':
                    apply_odometry_transform(csv_path=csv_path, rotation_deg=-90, translation_vec=[-15.7, -75.0 - lidar_offset, 0.0])
                elif map == 'Town06':
                    apply_odometry_transform(csv_path=csv_path, rotation_deg=180, translation_vec=[-175.0 - lidar_offset, 15.3, 0.0])
                else:
                    raise ValueError(f"Invalid Map")
                pos_errors = calculate_position_errors(bag_folder, run_id, topics)
                save_errors_to_csv(pos_errors, bag_folder, run_id=run_id)

            calculate_and_save_all_errors(
                bag_folder=bag_folder,
                run_ids=run_ids,
                topics=topics,
                position_error=True,
                yaw_error=True,
                velocity_error=False,
                trajectory_error=True
            )
            
    summarize_errors_by_algorithm(base_folder, algorithms)

def main():
    parser = argparse.ArgumentParser(description="Run full data analysis pipeline.")
    parser.add_argument('--base_folder', type=str, required=True, help='Path to bags folder')
    parser.add_argument('--config_path', type=str, default="carla_config.yaml", help='Path to config.yaml')

    args = parser.parse_args()

    analyze_data(
        base_folder=args.base_folder,
        config_path=args.config_path
    )

if __name__ == "__main__":
    main()
