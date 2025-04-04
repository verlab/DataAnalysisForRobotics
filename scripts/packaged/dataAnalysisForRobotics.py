import os
from bagpy import bagreader
import shutil
import warnings
import yaml
import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import mean_squared_error

def load_config(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config['topics']

def convert_bags_to_csv(bag_folder, num_bags, topics):
    if not isinstance(num_bags, int) or num_bags <= 0:
        raise ValueError(f"{num_bags} is not a valid number. Must be a positive integer")
    
    base_output_folder = os.path.join(bag_folder, "csv_files", "per_run")
    os.makedirs(base_output_folder, exist_ok=True)
    
    # Check if trajectory plan needs cleaning
    plan_topic = topics.get('trajectory_plan')
    clean_plan = plan_topic and plan_topic['type'] == "nav_msgs/Path"
    plan_csv_name = plan_topic['csv_file'] if plan_topic else None

    for i in range(num_bags):
        bag_name = f'run_{i}.bag'
        bag_path = os.path.join(bag_folder, bag_name)

        if not os.path.isfile(bag_path):
            print(f"[WARNING] Bag file not found: {bag_path}")
            continue

        print(f"[INFO] Reading: {bag_path}")
        b = bagreader(bag_path)

        run_folder = os.path.join(base_output_folder, f"run_{i}")
        os.makedirs(run_folder, exist_ok=True)

        for topic in b.topics:
            csv_path = b.message_by_topic(topic)
            print(f"[INFO] Saved CSV in original folder: {csv_path}")

            dest_path = os.path.join(run_folder, os.path.basename(csv_path))
            shutil.move(csv_path, dest_path)
            print(f"[INFO] Moved CSV to: {dest_path}")

            # If it's the trajectory plan and type is nav_msgs/Path clean it
            if clean_plan and os.path.basename(csv_path) == plan_csv_name:
                print(f"[INFO] Cleaning trajectory plan CSV for run_{i}")
                extract_poses_from_csv(dest_path, dest_path)

def parse_pose_block(pose_block):
    pos_match = re.search(r'position:\s*x:\s*([-\d.e]+)\s*y:\s*([-\d.e]+)\s*z:\s*([-\d.e]+)', pose_block)
    ori_match = re.search(r'orientation:\s*x:\s*([-\d.e]+)\s*y:\s*([-\d.e]+)\s*z:\s*([-\d.e]+)\s*w:\s*([-\d.e]+)', pose_block)

    if pos_match and ori_match:
        pos = [float(pos_match.group(i)) for i in range(1, 4)]
        ori = [float(ori_match.group(i)) for i in range(1, 5)]
        return pos + ori
    else:
        return [None] * 7

def extract_poses_from_csv(input_csv, output_csv):
    df = pd.read_csv(input_csv)
    pose_data = []

    for _, row in df.iterrows():
        poses_str = row['poses'].replace('\n', '').replace('  ', '')
        pose_blocks = poses_str.split('header:')[1:] 

        for pose_block in pose_blocks:
            parsed = parse_pose_block(pose_block)
            if parsed[0] is not None:
                pose_data.append({
                    'Time': row['Time'],
                    'header.seq': row['header.seq'],
                    'header.stamp.secs': row['header.stamp.secs'],
                    'header.stamp.nsecs': row['header.stamp.nsecs'],
                    'header.frame_id': row['header.frame_id'],
                    'position.x': parsed[0],
                    'position.y': parsed[1],
                    'position.z': parsed[2],
                    'orientation.x': parsed[3],
                    'orientation.y': parsed[4],
                    'orientation.z': parsed[5],
                    'orientation.w': parsed[6],
                })

    parsed_df = pd.DataFrame(pose_data)
    parsed_df.to_csv(output_csv, index=False)
    print(f"[INFO] Cleaned CSV written to: {output_csv}")

def organize_csv_per_topic(bag_folder, num_bags, topics):
    source_root = os.path.join(bag_folder, "csv_files", "per_run")
    destination_root = os.path.join(bag_folder, "csv_files", "per_topic")
    os.makedirs(destination_root, exist_ok=True)

    # Go through only topics defined in config file
    for key, topic in topics.items():
        topic_csv = topic.get('csv_file')
        if topic_csv is None:
            continue  # skip if csv_file not defined

        topic_folder = os.path.splitext(topic_csv)[0]  # remove .csv
        topic_dest = os.path.join(destination_root, topic_folder)
        os.makedirs(topic_dest, exist_ok=True)

        for i in range(num_bags):
            run_folder = os.path.join(source_root, f"run_{i}")
            src_file = os.path.join(run_folder, topic_csv)
            if os.path.isfile(src_file):
                dest_filename = f"{topic_folder}_run_{i}.csv"
                dest_file = os.path.join(topic_dest, dest_filename)
                shutil.copy2(src_file, dest_file)
                print(f"[INFO] Copied {src_file} → {dest_file}")
            else:
                print(f"[WARNING] File not found for run_{i}: {src_file}")

def plot_linear_velocities(folder_path, file_names, output_file, show_plot=False):
    linear_cols = ['linear.x', 'linear.y', 'linear.z']

    plt.figure(figsize=(12, 6))
    for i, file in enumerate(file_names):
        csv_path = os.path.join(folder_path, file)
        df = pd.read_csv(csv_path)
        for col in linear_cols:
            plt.plot(df[col].values, label=f"{col} run {i}", alpha=0.6)

    plt.title(f"Linear Velocities Across {len(file_names)} Runs")
    plt.xlabel("Time step (index)")
    plt.ylabel("Velocity (m/s)")
    plt.legend(loc="upper right", fontsize="small", ncol=3)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_file)
    print(f"Saved linear velocity plot to {output_file}")
    if show_plot:
        plt.show()
    plt.close()

def plot_angular_velocities(folder_path, file_names, output_file, show_plot=False):
    angular_cols = ['angular.x', 'angular.y', 'angular.z']

    plt.figure(figsize=(12, 6))
    for i, file in enumerate(file_names):
        csv_path = os.path.join(folder_path, file)
        df = pd.read_csv(csv_path)
        for col in angular_cols:
            plt.plot(df[col].values, label=f"{col} run {i}", alpha=0.6)

    plt.title(f"Angular Velocities Across {len(file_names)} Runs")
    plt.xlabel("Time step (index)")
    plt.ylabel("Angular Velocity (rad/s)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_file)
    print(f"Saved angular velocity plot to {output_file}")
    if show_plot:
        plt.show()
    plt.close()

def plot_velocities_for_all_runs(bag_folder, num_bags, topics):
    # Define the base folder where the CSV files are located
    per_topic_folder = os.path.join(bag_folder, "csv_files", "per_topic")

    # Initialize lists to hold the file paths for real and planned velocities
    real_vel_files_paths = []
    planned_vel_files_paths = []

    # Loop through the topics and find the real and planned velocity topics
    for topic_key, topic in topics.items():
        csv_file = topic.get('csv_file')
        if not csv_file:
            continue  # Skip if no csv_file is defined for the topic
        
        # Find the correct folder for this topic inside per_topic
        topic_folder = topic.get('name')  # The folder is named after the topic's 'name' in config.yaml
        topic_folder_path = os.path.join(per_topic_folder, topic_folder)

        if topic_key == 'real_velocity':  # real_velocity is for the real velocities
            # Add all runs' CSV paths to the list
            for i in range(num_bags):
                run_file_name = f"{csv_file[:-4]}_run_{i}.csv"  # Remove '.csv' and add run index
                run_file_path = os.path.join(topic_folder_path, run_file_name)
                real_vel_files_paths.append(run_file_path)

        elif topic_key == 'controller_velocity':  # controller_velocity is for planned velocities
            # Add all runs' CSV paths to the list
            for i in range(num_bags):
                run_file_name = f"{csv_file[:-4]}_run_{i}.csv"  # Remove '.csv' and add run index
                run_file_path = os.path.join(topic_folder_path, run_file_name)
                planned_vel_files_paths.append(run_file_path)

    if not real_vel_files_paths or not planned_vel_files_paths:
        print("[WARNING] Could not find the velocity topics or CSV files in the per_topic directory.")
        return
    
    # Create a "plots" folder in the same directory as the rosbags
    plots_folder = os.path.join(bag_folder, "plots")
    os.makedirs(plots_folder, exist_ok=True)

    # Set the output file paths for the plots in the "plots" folder
    real_vel_linear_output = os.path.join(plots_folder, "real_vel_linear_all_runs.png")
    real_vel_angular_output = os.path.join(plots_folder, "real_vel_angular_all_runs.png")
    planned_vel_linear_output = os.path.join(plots_folder, "planned_vel_linear_all_runs.png")
    planned_vel_angular_output = os.path.join(plots_folder, "planned_vel_angular_all_runs.png")

    # Plot linear velocities
    plot_linear_velocities(bag_folder, real_vel_files_paths, real_vel_linear_output)
    plot_linear_velocities(bag_folder, planned_vel_files_paths, planned_vel_linear_output)

    # Plot angular velocities
    plot_angular_velocities(bag_folder, real_vel_files_paths, real_vel_angular_output)
    plot_angular_velocities(bag_folder, planned_vel_files_paths, planned_vel_angular_output)

def plot_velocities_for_single_run(bag_folder, run_id, topics):
    # Get the relevant topic names and their corresponding CSV file names from config
    real_vel_topic = topics.get('real_velocity', {}).get('csv_file')
    planned_vel_topic = topics.get('controller_velocity', {}).get('csv_file')

    if not real_vel_topic or not planned_vel_topic:
        print("[WARNING] Could not find required velocity topics in config.")
        return

    # Define the path for the current run (run_id)
    run_folder = os.path.join(bag_folder, "csv_files", "per_run", f"run_{run_id}")

    # Construct the full path for the CSV files
    real_vel_file = os.path.join(run_folder, real_vel_topic)
    planned_vel_file = os.path.join(run_folder, planned_vel_topic)

    # Check if the CSV files exist
    if not os.path.isfile(real_vel_file):
        print(f"[ERROR] {real_vel_file} not found!")
        return

    if not os.path.isfile(planned_vel_file):
        print(f"[ERROR] {planned_vel_file} not found!")
        return

    # Read the CSV files into pandas DataFrames
    real_vel_df = pd.read_csv(real_vel_file)
    planned_vel_df = pd.read_csv(planned_vel_file)

    # Create the "plots" folder inside the same folder as the bags (if it doesn't exist)
    plots_folder = os.path.join(bag_folder, "plots")
    os.makedirs(plots_folder, exist_ok=True)

    # Plot real velocities (6 graphs in 3x2 grid)
    fig, axes = plt.subplots(3, 2, figsize=(14, 10))

    # Plot real linear velocities
    axes[0, 0].plot(real_vel_df['linear.x'], label='linear.x', color='blue')
    axes[0, 0].set_title('Real Velocity - Linear X')
    axes[0, 0].set_xlabel('Time (index)')
    axes[0, 0].set_ylabel('Linear Velocity (m/s)')
    axes[0, 0].grid(True)

    axes[1, 0].plot(real_vel_df['linear.y'], label='linear.y', color='blue')
    axes[1, 0].set_title('Real Velocity - Linear Y')
    axes[1, 0].set_xlabel('Time (index)')
    axes[1, 0].set_ylabel('Linear Velocity (m/s)')
    axes[1, 0].grid(True)

    axes[2, 0].plot(real_vel_df['linear.z'], label='linear.z', color='blue')
    axes[2, 0].set_title('Real Velocity - Linear Z')
    axes[2, 0].set_xlabel('Time (index)')
    axes[2, 0].set_ylabel('Linear Velocity (m/s)')
    axes[2, 0].grid(True)

    # Plot real angular velocities
    axes[0, 1].plot(real_vel_df['angular.x'], label='angular.x', color='blue')
    axes[0, 1].set_title('Real Velocity - Angular X')
    axes[0, 1].set_xlabel('Time (index)')
    axes[0, 1].set_ylabel('Angular Velocity (rad/s)')
    axes[0, 1].grid(True)

    axes[1, 1].plot(real_vel_df['angular.y'], label='angular.y', color='blue')
    axes[1, 1].set_title('Real Velocity - Angular Y')
    axes[1, 1].set_xlabel('Time (index)')
    axes[1, 1].set_ylabel('Angular Velocity (rad/s)')
    axes[1, 1].grid(True)

    axes[2, 1].plot(real_vel_df['angular.z'], label='angular.z', color='blue')
    axes[2, 1].set_title('Real Velocity - Angular Z')
    axes[2, 1].set_xlabel('Time (index)')
    axes[2, 1].set_ylabel('Angular Velocity (rad/s)')
    axes[2, 1].grid(True)

    # Adjust layout and save the real velocity plot to a file in "plots" folder
    plt.tight_layout()
    plt.suptitle(f"Real Velocities for Run {run_id}", fontsize=16)
    plt.subplots_adjust(top=0.93)
    real_vel_output_file = os.path.join(plots_folder, f"real_velocities_run_{run_id}.png")
    plt.savefig(real_vel_output_file)
    print(f"Saved real velocity plot for run {run_id} to {real_vel_output_file}")

    plt.close()

    # Plot planned velocities (6 graphs in 3x2 grid)
    fig, axes = plt.subplots(3, 2, figsize=(14, 10))

    # Plot planned linear velocities
    axes[0, 0].plot(planned_vel_df['linear.x'], label='linear.x', color='red')
    axes[0, 0].set_title('Planned Velocity - Linear X')
    axes[0, 0].set_xlabel('Time (index)')
    axes[0, 0].set_ylabel('Linear Velocity (m/s)')
    axes[0, 0].grid(True)

    axes[1, 0].plot(planned_vel_df['linear.y'], label='linear.y', color='red')
    axes[1, 0].set_title('Planned Velocity - Linear Y')
    axes[1, 0].set_xlabel('Time (index)')
    axes[1, 0].set_ylabel('Linear Velocity (m/s)')
    axes[1, 0].grid(True)

    axes[2, 0].plot(planned_vel_df['linear.z'], label='linear.z', color='red')
    axes[2, 0].set_title('Planned Velocity - Linear Z')
    axes[2, 0].set_xlabel('Time (index)')
    axes[2, 0].set_ylabel('Linear Velocity (m/s)')
    axes[2, 0].grid(True)

    # Plot planned angular velocities
    axes[0, 1].plot(planned_vel_df['angular.x'], label='angular.x', color='red')
    axes[0, 1].set_title('Planned Velocity - Angular X')
    axes[0, 1].set_xlabel('Time (index)')
    axes[0, 1].set_ylabel('Angular Velocity (rad/s)')
    axes[0, 1].grid(True)

    axes[1, 1].plot(planned_vel_df['angular.y'], label='angular.y', color='red')
    axes[1, 1].set_title('Planned Velocity - Angular Y')
    axes[1, 1].set_xlabel('Time (index)')
    axes[1, 1].set_ylabel('Angular Velocity (rad/s)')
    axes[1, 1].grid(True)

    axes[2, 1].plot(planned_vel_df['angular.z'], label='angular.z', color='red')
    axes[2, 1].set_title('Planned Velocity - Angular Z')
    axes[2, 1].set_xlabel('Time (index)')
    axes[2, 1].set_ylabel('Angular Velocity (rad/s)')
    axes[2, 1].grid(True)

    # Adjust layout and save the planned velocity plot to a file in "plots" folder
    plt.tight_layout()
    plt.suptitle(f"Planned Velocities for Run {run_id}", fontsize=16)
    plt.subplots_adjust(top=0.93)
    planned_vel_output_file = os.path.join(plots_folder, f"planned_velocities_run_{run_id}.png")
    plt.savefig(planned_vel_output_file)
    print(f"Saved planned velocity plot for run {run_id} to {planned_vel_output_file}")

    plt.close()

def plot_mean_velocity(bag_folder, run_ids, topic_name, topics):
    # Find the corresponding topic from the config by matching the 'name' field
    topic = None
    for key, value in topics.items():
        if value.get('name') == topic_name:
            topic = value
            break

    if topic:
        topic_type = value.get('type', '').strip()
        # Check if the topic type is not 'geometry_msgs/Twist'
        if topic_type != "geometry_msgs/Twist":
            print(f"[WARNING] The topic '{key}' you passed isn't a 'geometry_msgs/Twist' message (What this function expects). Continue with caution.")


    if not topic:
        print(f"[ERROR] Topic with name '{topic_name}' not found in config file.")
        return

    # Get the CSV file name for the selected topic
    topic_csv_file = topic.get('csv_file')
    
    if not topic_csv_file:
        print(f"[ERROR] Topic '{topic_name}' does not have a 'csv_file' in config.")
        return

    # Define the folder path for the topic inside 'csv_files/per_topic'
    topic_folder = os.path.join(bag_folder, "csv_files", "per_topic", topic_name)

    # List to store DataFrames for each run
    all_runs = []

    # Loop through the selected run_ids and read the corresponding CSV files
    for run_id in run_ids:
        file_name = f"{topic_name}_run_{run_id}.csv"
        file_path = os.path.join(topic_folder, file_name)
        
        if not os.path.isfile(file_path):
            print(f"[ERROR] File {file_path} not found!")
            return
        
        # Read the CSV file into a DataFrame and append to the list
        df = pd.read_csv(file_path)
        all_runs.append(df)

    # Find the minimum length of all the runs to align the data
    min_len = min(len(df) for df in all_runs)
    all_runs_trimmed = [df.iloc[:min_len] for df in all_runs]

    # Stack the data for linear and angular velocities across the runs
    linear_cols = ['linear.x', 'linear.y', 'linear.z']
    angular_cols = ['angular.x', 'angular.y', 'angular.z']

    stacked = np.stack([df[linear_cols + angular_cols].values for df in all_runs_trimmed])

    # Calculate the mean across the selected runs
    mean_over_runs = stacked.mean(axis=0)

    # Create the "plots" folder inside the same folder as the bags (if it doesn't exist)
    plots_folder = os.path.join(bag_folder, "plots")
    os.makedirs(plots_folder, exist_ok=True)

    # Plot mean linear velocities (3 graphs in 1 row)
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    
    for i, col in enumerate(linear_cols):
        axes[i].plot(mean_over_runs[:, i], label=col, color='blue')
        axes[i].set_title(f'Mean {col}')
        axes[i].set_xlabel('Time (index)')
        axes[i].set_ylabel('Velocity (m/s)')
        axes[i].grid(True)
        axes[i].legend()

    # Adjust layout and save the figure for linear velocities
    plt.tight_layout()
    plt.suptitle(f"Mean Linear Velocities for Topic {topic_name}", fontsize=16)
    plt.subplots_adjust(top=0.85)  # Adjust title position
    mean_linear_output_file = os.path.join(plots_folder, f"mean_linear_{topic_name}.png")
    plt.savefig(mean_linear_output_file)
    print(f"Saved mean linear velocity plot to {mean_linear_output_file}")
    plt.close()

    # Plot mean angular velocities (3 graphs in 1 row)
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    
    for i, col in enumerate(angular_cols):
        axes[i].plot(mean_over_runs[:, i + 3], label=col, color='red')
        axes[i].set_title(f'Mean {col}')
        axes[i].set_xlabel('Time (index)')
        axes[i].set_ylabel('Angular Velocity (rad/s)')
        axes[i].grid(True)
        axes[i].legend()

    # Adjust layout and save the figure for angular velocities
    plt.tight_layout()
    plt.suptitle(f"Mean Angular Velocities for Topic {topic_name}", fontsize=16)
    plt.subplots_adjust(top=0.85)  # Adjust title position
    mean_angular_output_file = os.path.join(plots_folder, f"mean_angular_{topic_name}.png")
    plt.savefig(mean_angular_output_file)
    print(f"Saved mean angular velocity plot to {mean_angular_output_file}")
    plt.close()

def plot_trajectory(csv_path, label=None, color=None, offset_to_origin=False):
    """
    Plot the trajectory based on CSV file
    """
    df = pd.read_csv(csv_path)

    # Determine file type (because for some reason, the names sometimes change)
    if 'position.x' in df.columns and 'position.y' in df.columns:
        x_vals = df['position.x']
        y_vals = df['position.y']

        if offset_to_origin:
            # Apply offset to bring initial position to (0,0), if you want your trajectory starting from (0,0)
            x_offset = x_vals.iloc[0]
            y_offset = y_vals.iloc[0]
            x_vals = x_vals - x_offset
            y_vals = y_vals - y_offset
    elif 'pose.position.x' in df.columns and 'pose.position.y' in df.columns:
        x_vals = df['pose.position.x']
        y_vals = df['pose.position.y']

        if offset_to_origin:
            # Apply offset to bring initial position to (0,0), if you want your trajectory starting from (0,0)
            x_offset = x_vals.iloc[0]
            y_offset = y_vals.iloc[0]
            x_vals = x_vals - x_offset
            y_vals = y_vals - y_offset
    else:
        raise ValueError("Unknown CSV structure. Expected 'poses' or 'pose.position.x/y' columns.")

    plt.plot(x_vals, y_vals, marker='o', markersize=3, linewidth=1, label=label, color=color)
    plt.plot(x_vals.iloc[0], y_vals.iloc[0], marker='*', color='red', markersize=12)  # Start point in red

def plot_waypoints(csv_path, color='purple'):
    """
    Plot waypoints based on CSV file
    """
    df = pd.read_csv(csv_path)

    if 'poses' not in df.columns:
        raise ValueError("Waypoint file structure unexpected. 'poses' column missing.")

    # Extract all x, y pairs from the poses string
    poses_text = " ".join(df['poses'].values)
    x_vals = [float(x) for x in re.findall(r'x:\s*([-\d.]+)', poses_text)]
    y_vals = [float(y) for y in re.findall(r'y:\s*([-\d.]+)', poses_text)]

    # Plot waypoints
    plt.scatter(x_vals, y_vals, color=color, marker='x', s=70, label='Waypoints', zorder=4)

def plot_single_trajectory_or_comparison(bag_folder, run_id, topics, plot_real_trajectory=False, plot_planned_trajectory=False, offset_planned=False, offset_real=False):
    # Get the relevant topic names and their corresponding CSV file names from config
    real_pos_topic = topics.get('real_position', {}).get('name')
    planned_trajectory_topic = topics.get('trajectory_plan', {}).get('name')
    waypoints_topic = topics.get('waypoints', {}).get('name')

    # Define the base folder for the selected run
    run_folder = os.path.join(bag_folder, "csv_files", "per_run", f"run_{run_id}")
    
    # Prepare to plot the graph
    plt.figure(figsize=(10, 8))

    # Plot real trajectory if selected
    if plot_real_trajectory and real_pos_topic:
        real_pos_file = os.path.join(bag_folder, "csv_files", "per_run", f"run_{run_id}", f"{real_pos_topic}.csv")
        if os.path.isfile(real_pos_file):
            if offset_real:
                plot_trajectory(real_pos_file, label="Real Trajectory", color="blue", offset_to_origin=True)
            else:
                plot_trajectory(real_pos_file, label="Real Trajectory", color="blue", offset_to_origin=False)

        else:
            print(f"[WARNING] Real trajectory file for run {run_id} not found.")

    # Plot planned trajectory if selected
    if plot_planned_trajectory and planned_trajectory_topic:
        planned_trajectory_file = os.path.join(bag_folder, "csv_files", "per_run", f"run_{run_id}", f"{planned_trajectory_topic}.csv")
        if os.path.isfile(planned_trajectory_file):
            if offset_planned:
                plot_trajectory(planned_trajectory_file, label="Planned Trajectory", color="orange", offset_to_origin=True)
            else:
                plot_trajectory(planned_trajectory_file, label="Planned Trajectory", color="orange", offset_to_origin=False)

        else:
            print(f"[WARNING] Planned trajectory file for run {run_id} not found.")

    # Customize the plot
    # plt.title(f"Trajectory Comparison for Run {run_id}")
    plt.xlabel("X Position")
    plt.ylabel("Y Position")
    plt.grid(True)

    # Save and show the plot

    if plot_real_trajectory==True and plot_planned_trajectory==True:
        plt.tight_layout()
        output_file = os.path.join(bag_folder, "plots", f"trajectory_comparison_run_{run_id}.png")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)  # Make sure the plots directory exists
        plt.savefig(output_file)
        print(f"Saved trajectory comparison plot for run {run_id} to {output_file}")
    elif plot_real_trajectory==True and plot_planned_trajectory==False:
        plt.tight_layout()
        output_file = os.path.join(bag_folder, "plots", f"real_trajectory_run_{run_id}.png")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)  # Make sure the plots directory exists
        plt.savefig(output_file)
        print(f"Saved real trajectory plot for run {run_id} to {output_file}")
    elif plot_real_trajectory==False and plot_planned_trajectory==True:
        plt.tight_layout()
        output_file = os.path.join(bag_folder, "plots", f"planned_trajectory_run_{run_id}.png")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)  # Make sure the plots directory exists
        plt.savefig(output_file)
        print(f"Saved planned plot for run {run_id} to {output_file}")
    else:
        print(f"[ERROR] No trajectory to be plotted?")

def load_and_subsample(estimated_df, ground_truth_df):
    factor = len(estimated_df) // len(ground_truth_df)
    estimated_subsampled = estimated_df.iloc[::max(1, factor)].reset_index(drop=True)

    min_len = min(len(estimated_subsampled), len(ground_truth_df))
    estimated_subsampled = estimated_subsampled.iloc[:min_len]
    ground_truth_df = ground_truth_df.iloc[:min_len]

    return estimated_subsampled, ground_truth_df

def compute_rmse_per_axis(gt_df, est_df):
    return {
        axis: np.sqrt(mean_squared_error(gt_df[axis], est_df[axis]))
        for axis in gt_df.columns
    }

def compute_absolute_errors_per_axis(gt_df, est_df):
    return {
        axis: np.abs(gt_df[axis] - est_df[axis]).values
        for axis in gt_df.columns
    }

def extract_position_columns(df, label):
    candidates = [
        ('pose.position.x', 'pose.position.y', 'pose.position.z'),
        ('pose.pose.position.x', 'pose.pose.position.y', 'pose.pose.position.z'),
        ('position.x', 'position.y', 'position.z'),
        ('x', 'y', 'z'),
    ]
    for cols in candidates:
        if all(col in df.columns for col in cols):
            pos_df = df[list(cols)].copy()
            pos_df.columns = ['pose.position.x', 'pose.position.y', 'pose.position.z']
            return pos_df

    print(f"[ERROR] Could not find position x/y/z columns in {label} file.")
    print(f"Available columns: {list(df.columns)}")
    raise KeyError(f"{label}: missing expected position columns")

def extract_orientation_x_column(df, label):
    candidates = [
        'pose.orientation.x',
        'pose.pose.orientation.x',
        'orientation.x'
    ]
    for col in candidates:
        if col in df.columns:
            return df[[col]].rename(columns={col: 'pose.orientation.x'})

    print(f"[WARNING] Could not find orientation.x column in {label} file.")
    return None

def calculate_position_errors(bag_folder, run_id, topics, position_error=True, yaw_error=True):
    real_topic_name = topics.get('real_position', {}).get('name')
    est_topic_name = topics.get('estimated_position', {}).get('name')

    if not real_topic_name or not est_topic_name:
        print("[ERROR] Could not find real or estimated position topics in config.")
        return None

    run_folder = os.path.join(bag_folder, "csv_files", "per_run", f"run_{run_id}")
    real_path = os.path.join(run_folder, f"{real_topic_name}.csv")
    est_path = os.path.join(run_folder, f"{est_topic_name}.csv")

    if not os.path.isfile(real_path):
        print(f"[ERROR] Ground truth file not found: {real_path}")
        return None
    if not os.path.isfile(est_path):
        print(f"[ERROR] Estimated position file not found: {est_path}")
        return None

    # Load and clean
    real_df = pd.read_csv(real_path)
    est_df = pd.read_csv(est_path)
    real_df.columns = real_df.columns.str.strip()
    est_df.columns = est_df.columns.str.strip()

    # --- Position Error ---
    if position_error:
        real_pos = extract_position_columns(real_df, label="Ground Truth")
        est_pos = extract_position_columns(est_df, label="Estimated Position")
        est_pos_sub, real_pos_sub = load_and_subsample(est_pos, real_pos)

        rmse_pos = compute_rmse_per_axis(real_pos_sub, est_pos_sub)
        ape_pos = compute_absolute_errors_per_axis(real_pos_sub, est_pos_sub)
        ape_mean_pos = {axis: np.mean(ape_pos[axis]) for axis in ape_pos}
        ape_max_pos = {axis: np.max(ape_pos[axis]) for axis in ape_pos}

    # --- Orientation.x Error ---
    if yaw_error:
        real_ori = extract_orientation_x_column(real_df, label="Ground Truth")
        est_ori = extract_orientation_x_column(est_df, label="Estimated Position")
        orientation_results = {}

        if real_ori is not None and est_ori is not None:
            est_ori_sub, real_ori_sub = load_and_subsample(est_ori, real_ori)

            rmse_ori = compute_rmse_per_axis(real_ori_sub, est_ori_sub)
            ape_ori = compute_absolute_errors_per_axis(real_ori_sub, est_ori_sub)
            ape_mean_ori = {axis: np.mean(ape_ori[axis]) for axis in ape_ori}
            ape_max_ori = {axis: np.max(ape_ori[axis]) for axis in ape_ori}

            # Print and store orientation.x errors
            print(f"[INFO] Orientation.x RMSE (run {run_id}): {rmse_ori}")
            print(f"[INFO] Orientation.x Mean Absolute Error: {ape_mean_ori}")
            print(f"[INFO] Orientation.x Max Absolute Error: {ape_max_ori}")

            orientation_results = {
                'rmse': rmse_ori,
                'mean_absolute_error': ape_mean_ori,
                'max_absolute_error': ape_max_ori
            }
        else:
            print(f"[WARNING] Orientation.x not found in one or both files — skipping orientation error.")

    # --- Print and Return All ---
    if position_error:
        print(f"[INFO] Position RMSE per axis (run {run_id}): {rmse_pos}")
        print(f"[INFO] Mean Absolute Position Error per axis: {ape_mean_pos}")
        print(f"[INFO] Max Absolute Position Error per axis: {ape_max_pos}")

    if position_error and yaw_error:
        return {
            'position': {
                'rmse': rmse_pos,
                'mean_absolute_error': ape_mean_pos,
                'max_absolute_error': ape_max_pos
            },
            'orientation': orientation_results}
    
    elif position_error and not yaw_error:
        return {
            'position': {
                'rmse': rmse_pos,
                'mean_absolute_error': ape_mean_pos,
                'max_absolute_error': ape_max_pos
            }}
    
    elif not position_error and yaw_error:
        return {
            'orientation': orientation_results}
    

def save_errors_to_csv(errors_dict, bag_folder, run_id):
    # Create output folder
    errors_folder = os.path.join(bag_folder, "errors")
    os.makedirs(errors_folder, exist_ok=True)

    # Flatten the nested dictionary into a single-level dict
    flat_data = {}
    for category, subdict in errors_dict.items():
        for error_type, value_dict in subdict.items():
            for axis, val in value_dict.items():
                key = f"{category}_{error_type}_{axis}"
                flat_data[key] = val

    # Save as single-row CSV
    df = pd.DataFrame([flat_data])
    out_file = os.path.join(errors_folder, f"errors_run_{run_id}.csv")
    df.to_csv(out_file, index=False)
    print(f"[INFO] Saved errors to {out_file}")

def calculate_and_save_all_errors(bag_folder, run_ids, topics, position_error=True, yaw_error=True):
    all_errors = []

    for run_id in run_ids:
        print(f"\n[INFO] Processing run {run_id}...")
        errors = calculate_position_errors(
            bag_folder, run_id, topics,
            position_error=position_error,
            yaw_error=yaw_error
        )

        if errors:
            # Flatten error dict
            flat_data = {'run': run_id}
            for category, subdict in errors.items():
                for error_type, val_dict in subdict.items():
                    for axis, value in val_dict.items():
                        key = f"{category}_{error_type}_{axis}"
                        flat_data[key] = value

            all_errors.append(flat_data)

    if not all_errors:
        print("[WARNING] No error data collected.")
        return

    # Create output folder
    errors_folder = os.path.join(bag_folder, "errors")
    os.makedirs(errors_folder, exist_ok=True)

    # Save everything to a single CSV file
    errors_df = pd.DataFrame(all_errors)
    out_path = os.path.join(errors_folder, "all_runs_errors.csv")
    errors_df.to_csv(out_path, index=False)
    print(f"[INFO] Saved all error metrics to {out_path}")

def main():
    bag_folder = "/home/manuela/Documents/VerLab/library_test"

    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "config.yaml")

    num_bags = 20

    topics = load_config(config_path)

    # convert_bags_to_csv(bag_folder, num_bags, topics)

    # organize_csv_per_topic(bag_folder, num_bags, topics)

    # plot_velocities_for_all_runs(bag_folder, num_bags, topics)

    # plot_velocities_for_single_run(bag_folder, run_id=0, topics=topics)

    # plot_velocities_for_single_run(bag_folder, 0, topics)

    # plot_mean_velocity(bag_folder, run_ids=[0, 1], topic_name="real_vel", topics=topics)

    # plot_single_trajectory_or_comparison(
    #  bag_folder, 
    # run_id=0, 
    # topics=topics, 
    # plot_real_trajectory=False, 
    # plot_planned_trajectory=False, 
    # offset_real=True)
    errors = calculate_position_errors(bag_folder, 0, topics)
    save_errors_to_csv(errors, bag_folder, run_id=0)

    calculate_and_save_all_errors(bag_folder, run_ids=list(range(num_bags)), topics=topics)

if __name__ == "__main__":
    main()

# PLOTTING ISSUES
# plot velocities from all the runs together -> OK
# plot vels from one run ! name them based on the run id -> OK
# plot mean velocities between runs -> OK

# plot one trajectory alone -> OK

# plot real trajectory -> OK
# plot planned trajectory -> OK
# plot real x planned trajectory -OK
# obs: make an argument if waypoints is true to plot them as well - NO bc no one will have them but later

# calculating issues
# position error (absolute and rmse)
# orientation error (absolute and rmse)
# velocity error (absolute and rmse)
# trajectory error (absolute and rmse)

