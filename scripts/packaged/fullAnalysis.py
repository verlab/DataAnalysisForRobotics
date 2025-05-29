import os
import argparse
from dataAnalysisForRobotics import (
    load_config,
    get_sorted_bag_mapping,
    convert_bags_to_csv,
    organize_csv_per_topic,
    save_errors_to_csv,
    calculate_length_drift_error,
    calculate_position_error_gps_vs_odometry,
    plot_distance_to_waypoints,
    calculate_and_save_path_lengths,
    plot_trajectory,
    calculate_trajectory_efficiency_error
)

def analyze_data(bag_folder, config_path):
    topics = load_config(config_path)

    # Create necessary folders for storing results
    os.makedirs(os.path.join(bag_folder, "plots"), exist_ok=True)
    os.makedirs(os.path.join(bag_folder, "errors"), exist_ok=True)

    # Get bag file mapping sorted by time
    bag_mapping = get_sorted_bag_mapping(bag_folder)
    run_ids = list(range(len(bag_mapping)))
    num_bags = len(run_ids)

    # Convert bags to CSV
    convert_bags_to_csv(bag_folder, bag_mapping, topics)
    
    # Organize CSV per topic
    organize_csv_per_topic(bag_folder, num_bags, topics)
    
    # Calculate and save errors for each run
    for run_id in run_ids:
        pos_errors = calculate_position_error_gps_vs_odometry(bag_folder, run_id, topics)
        save_errors_to_csv(pos_errors, bag_folder, run_id)
        
        drift_errors = calculate_length_drift_error(bag_folder, run_id, topics)
        save_errors_to_csv(drift_errors, bag_folder, run_id, label="length_drift")
        
        calculate_and_save_path_lengths(bag_folder, run_id, topics)
        
        calculate_trajectory_efficiency_error(bag_folder, run_id, topics)
        
        # Plot distance to waypoints
        plot_distance_to_waypoints(bag_folder, run_id, topics, waypoint_indices=[0, 1, 2, 3])

        # Plot trajectory for odometry and GPS
        plot_trajectory(os.path.join(bag_folder, "csv_files", "per_run", f"run_{run_id}", "lego_loam-odom.csv"), label="Odometry", run_id=run_id, bag_folder=bag_folder)
        plot_trajectory(os.path.join(bag_folder, "csv_files", "per_run", f"run_{run_id}", "gps_to_local.csv"), label="GPS", run_id=run_id, bag_folder=bag_folder)


def main():
    parser = argparse.ArgumentParser(description="Run full data analysis pipeline.")
    parser.add_argument('--bag_folder', type=str, required=True, help='Path to bag folder')
    parser.add_argument('--config_path', type=str, default="config.yaml", help='Path to config.yaml')

    args = parser.parse_args()

    analyze_data(
        bag_folder=args.bag_folder,
        config_path=args.config_path
    )

if __name__ == "__main__":
    main()
