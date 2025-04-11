import os
import argparse
from dataAnalysisForRobotics import (
    load_config,
    get_sorted_bag_mapping,
    convert_bags_to_csv,
    organize_csv_per_topic,
    plot_velocities_for_all_runs,
    plot_velocities_for_single_run,
    plot_mean_velocity,
    plot_single_trajectory_or_comparison,
    calculate_position_errors,
    calculate_velocity_errors,
    save_errors_to_csv,
    calculate_and_save_all_errors
)

def analyze_data(bag_folder, config_path):
    topics = load_config(config_path)

    # Get bag file mapping sorted by time
    bag_mapping = get_sorted_bag_mapping(bag_folder)
    run_ids = list(range(len(bag_mapping)))
    num_bags = len(run_ids)

    convert_bags_to_csv(bag_folder, bag_mapping, topics)
    organize_csv_per_topic(bag_folder, num_bags, topics)
    plot_velocities_for_all_runs(bag_folder, num_bags, topics)

    for run_id in run_ids:
        plot_velocities_for_single_run(bag_folder, run_id=run_id, topics=topics)
        plot_mean_velocity(bag_folder, run_ids=[run_id], topic_name="real_vel", topics=topics)
        plot_single_trajectory_or_comparison(
            bag_folder,
            run_id=run_id,
            topics=topics,
            plot_real_trajectory=True,
            plot_planned_trajectory=True,
            offset_real=True
        )

        pos_errors = calculate_position_errors(bag_folder, run_id, topics)
        save_errors_to_csv(pos_errors, bag_folder, run_id=run_id)

        vel_errors = calculate_velocity_errors(bag_folder, run_id, topics)
        save_errors_to_csv(vel_errors, bag_folder, run_id, label="velocity")

    calculate_and_save_all_errors(
        bag_folder=bag_folder,
        run_ids=run_ids,
        topics=topics,
        position_error=True,
        yaw_error=True,
        velocity_error=True
    )

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
