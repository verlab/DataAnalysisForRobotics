import os
from bagpy import bagreader
import shutil
import yaml
import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import mean_squared_error
import glob
from geopy.distance import geodesic
import rospkg

def load_config(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config['topics']

def get_sorted_bag_mapping(bag_folder):
    bag_files = glob.glob(os.path.join(bag_folder, "*.bag"))
    if not bag_files:
        raise FileNotFoundError(f"No .bag files found in {bag_folder}")

    # Expected filename pattern
    pattern = re.compile(r"\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}\.bag$")


    valid_bags = []
    for bag in bag_files:
        if pattern.match(os.path.basename(bag)):
            valid_bags.append(bag)
        else:
            print(f"[WARNING] Skipping file with invalid name format: {os.path.basename(bag)}")

    if not valid_bags:
        raise ValueError("No valid bag files found after format filtering.")

    # Sort by file modification time (oldest first)
    sorted_bags = sorted(valid_bags, key=os.path.getmtime)

    # Map run index to bag path
    bag_mapping = {f"run_{i}": path for i, path in enumerate(sorted_bags)}

    # Print the mapping
    print("\n[INFO] Bag Mapping (oldest → newest):")
    for run_id, path in bag_mapping.items():
        print(f"  {run_id} → {os.path.basename(path)}")

    return bag_mapping

def convert_bags_to_csv(bag_folder, bag_mapping, topics):
    base_output_folder = os.path.join(bag_folder, "csv_files", "per_run")
    os.makedirs(base_output_folder, exist_ok=True)

    plan_topic = topics.get('trajectory_plan')
    plan_csv_name = plan_topic['name'].lstrip("/").replace("/", "-")+".csv" if plan_topic else None

    for run_label, bag_path in bag_mapping.items():
        if not os.path.isfile(bag_path):
            print(f"[WARNING] Bag file not found: {bag_path}")
            continue

        print(f"[INFO] Reading: {bag_path}")
        b = bagreader(bag_path)

        run_folder = os.path.join(base_output_folder, run_label)
        os.makedirs(run_folder, exist_ok=True)

        for topic in b.topics:
            if topic not in [t.get('name') for t in topics.values()]:
                continue  # Skip topics not defined in config
            csv_path = b.message_by_topic(topic)
            print(f"[INFO] Saved CSV in original folder: {csv_path}")

            dest_path = os.path.join(run_folder, os.path.basename(csv_path))
            shutil.move(csv_path, dest_path)
            print(f"[INFO] Moved CSV to: {dest_path}")

            if plan_topic and os.path.basename(csv_path) == plan_csv_name:
                print(f"[INFO] Cleaning trajectory plan CSV for {run_label}")
                extract_poses_from_csv(dest_path, dest_path)

        bag_name_without_ext = os.path.splitext(os.path.basename(bag_path))[0]
        bag_output_folder = os.path.join(bag_folder, bag_name_without_ext)
        if os.path.isdir(bag_output_folder) and not os.listdir(bag_output_folder):
            try:
                os.rmdir(bag_output_folder)
                print(f"[INFO] Removed empty bag folder: {bag_output_folder}")
            except Exception as e:
                print(f"[WARNING] Failed to remove folder {bag_output_folder}: {e}")

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
        topic_name = topic.get('name')
        if topic_name is None:
            continue  # skip if csv_file not defined
        
        topic_csv = topic_name.lstrip("/").replace("/", "-")+".csv"
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

def plot_trajectory(csv_path, label=None, color=None, offset_to_origin=False, run_id=0, bag_folder=None):
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
    elif 'x' in df.columns and 'y' in df.columns:
        x_vals = df['x']
        y_vals = df['y']

        if offset_to_origin:
            # Apply offset to bring initial position to (0,0), if you want your trajectory starting from (0,0)
            x_offset = x_vals.iloc[0]
            y_offset = y_vals.iloc[0]
            x_vals = x_vals - x_offset
            y_vals = y_vals - y_offset
    elif 'pose.pose.position.x' in df.columns and 'pose.pose.position.y' in df.columns:
        x_vals = df['pose.pose.position.x']
        y_vals = df['pose.pose.position.y']

        if offset_to_origin:
            # Apply offset to bring initial position to (0,0), if you want your trajectory starting from (0,0)
            x_offset = x_vals.iloc[0]
            y_offset = y_vals.iloc[0]
            x_vals = x_vals - x_offset
            y_vals = y_vals - y_offset
    else:
        raise ValueError("Unknown CSV structure. Expected 'poses' or 'pose.position.x/y' columns.")
    
    x_vals = np.array(x_vals)
    y_vals = np.array(y_vals)

    plt.plot(x_vals, y_vals, marker='o', markersize=3, linewidth=1, label=label, color=color)
    plt.plot(x_vals[0], y_vals[0], marker='*', color='red', markersize=12)  # Start point in red
    plt.axis('equal')
    
def plot_single_trajectory_or_comparison(bag_folder, run_id, topics, plot_estimated_trajectory=False, plot_gps_trajectory=False, offset_est=False, offset_gps=False):
    # Get the relevant topic names and their corresponding CSV file names from config
    est_pos_topic = topics.get('estimated_position', {}).get('name')
    waypoints_gps = load_gps_waypoints(bag_folder, topics)
    if waypoints_gps is not None:
        latitudes = [wp['lat'] for wp in waypoints_gps]
        longitudes = [wp['lon'] for wp in waypoints_gps]
        x_waypoints, y_waypoints = latlon_to_local_xy(latitudes=latitudes, longitudes=longitudes)

    # Define the base folder for the selected run
    run_folder = os.path.join(bag_folder, "csv_files", "per_run", f"run_{run_id}")
    
    # Prepare to plot the graph
    plt.figure(figsize=(10, 8))

    # Plot real trajectory if selected
    if plot_estimated_trajectory and est_pos_topic:
        est_pos_file = est_pos_topic.lstrip("/").replace("/", "-")
        real_pos_file = os.path.join(bag_folder, "csv_files", "per_run", f"run_{run_id}", f"{est_pos_file}.csv")
        if os.path.isfile(real_pos_file):
            if offset_est:
                plot_trajectory(real_pos_file, label="Estimated Trajectory", color="blue", offset_to_origin=True)
            else:
                plot_trajectory(real_pos_file, label="Estimated Trajectory", color="blue", offset_to_origin=False)

        else:
            print(f"[WARNING] Estimated trajectory file for run {run_id} not found.")

    # Plot planned trajectory if selected
    if plot_gps_trajectory:
        planned_trajectory_file = os.path.join(bag_folder, "csv_files", "per_run", f"run_{run_id}", "gps_to_local.csv")
        if os.path.isfile(planned_trajectory_file):
            if offset_gps:
                plot_trajectory(planned_trajectory_file, label="GPS Trajectory", color="orange", offset_to_origin=True)
            else:
                plot_trajectory(planned_trajectory_file, label="GPS Trajectory", color="orange", offset_to_origin=False)

        else:
            print(f"[WARNING] GPS trajectory file for run {run_id} not found.")
    if waypoints_gps is not None:
        plt.plot(x_waypoints, y_waypoints, marker='*', color='gray', markersize=10, label="Waypoints")

    # Customize the plot
    plt.title(f"Trajectory Comparison for Run {run_id}")
    plt.xlabel("X Position")
    plt.ylabel("Y Position")
    plt.grid(True)
    plt.legend()

    # Save and show the plot
    if plot_estimated_trajectory==True and plot_gps_trajectory==True:
        plt.tight_layout()
        output_file = os.path.join(bag_folder, "plots", f"trajectory_comparison_run_{run_id}.png")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)  # Make sure the plots directory exists
        plt.savefig(output_file)
        print(f"Saved trajectory comparison plot for run {run_id} to {output_file}")
    elif plot_estimated_trajectory==True and plot_gps_trajectory==False:
        plt.tight_layout()
        output_file = os.path.join(bag_folder, "plots", f"estimated_trajectory_run_{run_id}.png")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)  # Make sure the plots directory exists
        plt.savefig(output_file)
        print(f"Saved estimated trajectory plot for run {run_id} to {output_file}")
    elif plot_estimated_trajectory==False and plot_gps_trajectory==True:
        plt.tight_layout()
        output_file = os.path.join(bag_folder, "plots", f"gps_trajectory_run_{run_id}.png")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)  # Make sure the plots directory exists
        plt.savefig(output_file)
        print(f"Saved GPS plot for run {run_id} to {output_file}")
    else:
        print(f"[ERROR] No trajectory to be plotted!")

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

def save_errors_to_csv(errors_dict, bag_folder, run_id, label="position"):
    errors_folder = os.path.join(bag_folder, "errors")
    os.makedirs(errors_folder, exist_ok=True)

    flat_data = {'run': run_id}
    
    # Iterar sobre os erros e salvar valores numéricos diretamente
    for category, subdict in errors_dict.items():
        for error_type, value in subdict.items():
            if isinstance(value, dict):  # Caso seja um dicionário, como no erro de posição
                for axis, val in value.items():
                    key = f"{category}_{error_type}_{axis}"
                    flat_data[key] = val
            else:
                # Caso o valor seja numérico
                key = f"{category}_{error_type}"
                flat_data[key] = value

    df = pd.DataFrame([flat_data])
    out_file = os.path.join(errors_folder, f"errors_{label}_run_{run_id}.csv")
    df.to_csv(out_file, index=False)
    print(f"[INFO] Saved {label} errors to {out_file}")

def calculate_and_save_all_errors(
    bag_folder, run_ids, topics,
    position_error=True, length_drift_error=True
):
    all_position_errors = []
    all_drift_errors = []

    for run_id in run_ids:
        print(f"\n[INFO] Processing run {run_id}...")

        # --- GPS vs Odometry Position Errors ---
        if position_error:
            pos_errors = calculate_position_error_gps_vs_odometry(
                bag_folder, run_id, topics
            )
            if pos_errors:
                flat_pos = {'run': run_id}
                for category, subdict in pos_errors.items():
                    for error_type, val_dict in subdict.items():
                        for axis, value in val_dict.items():
                            key = f"{category}_{error_type}_{axis}"
                            flat_pos[key] = value
                all_position_errors.append(flat_pos)
                save_errors_to_csv(pos_errors, bag_folder, run_id, label="position")

        # --- Length Drift Errors ---
        if length_drift_error:
            drift_errors = calculate_length_drift_error(bag_folder, run_id, topics)
            if drift_errors:
                flat_drift = {'run': run_id}
                for category, subdict in drift_errors.items():
                    for error_type, val_dict in subdict.items():
                        for axis, value in val_dict.items():
                            key = f"{category}_{error_type}_{axis}"
                            flat_drift[key] = value
                all_drift_errors.append(flat_drift)
                save_errors_to_csv(drift_errors, bag_folder, run_id, label="length_drift")

    # --- Save combined CSVs ---
    errors_folder = os.path.join(bag_folder, "errors")
    os.makedirs(errors_folder, exist_ok=True)

    if all_position_errors:
        df_pos = pd.DataFrame(all_position_errors)
        df_pos.to_csv(os.path.join(errors_folder, "all_runs_position_errors.csv"), index=False)
        print("[INFO] Saved position errors for all runs.")

    if all_drift_errors:
        df_drift = pd.DataFrame(all_drift_errors)
        df_drift.to_csv(os.path.join(errors_folder, "all_runs_length_drift_errors.csv"), index=False)
        print("[INFO] Saved length drift errors for all runs.")

def interpolate_to_match(reference_df, target_df, columns):
    """
    Interpolate columns of `target_df` to match `reference_df`'s timestamps.
    """
    interpolated = {}
    for col in columns:
        interpolated[col] = np.interp(
            reference_df['Time'].astype(float),
            target_df['Time'].astype(float),
            target_df[col].astype(float)
        )
    return pd.DataFrame(interpolated)

def calculate_gps_path_length(bag_folder, run_id, topics):
    gps_topic = topics.get('gps_plan', {})
    gps_topic_name = gps_topic.get('name')

    if not gps_topic_name:
        print("[ERROR] 'gps_plan' topic missing or does not specify a 'csv_file' in config.yaml.")
        return None

    gps_csv_file = gps_topic_name.lstrip("/").replace("/", "-")+".csv"
    gps_csv_path = os.path.join(bag_folder, "csv_files", "per_run", f"run_{run_id}", gps_csv_file)

    if not os.path.isfile(gps_csv_path):
        print(f"[ERROR] GPS CSV file not found at path: {gps_csv_path}")
        return None

    # Load the GPS data
    df = pd.read_csv(gps_csv_path)
    df.columns = df.columns.str.strip()  # Clean column names

    # Determine column names
    lat_col = None
    lon_col = None
    alt_col = None

    for lat_cand in ['latitude', 'lat']:
        if lat_cand in df.columns:
            lat_col = lat_cand
            break
    for lon_cand in ['longitude', 'lon']:
        if lon_cand in df.columns:
            lon_col = lon_cand
            break
    for alt_cand in ['altitude', 'alt']:
        if alt_cand in df.columns:
            alt_col = alt_cand
            break

    if not lat_col or not lon_col:
        print(f"[ERROR] Could not find latitude/longitude columns in {gps_csv_path}. Found columns: {list(df.columns)}")
        return None

    # Compute total distance using geodesic distances between consecutive points
    coords = list(zip(df[lat_col], df[lon_col]))
    total_distance = 0.0

    for i in range(1, len(coords)):
        total_distance += geodesic(coords[i - 1], coords[i]).meters

    print(f"[INFO] Total GPS path length for run_{run_id}: {total_distance:.2f} meters")
    return total_distance

def calculate_odometry_path_length(bag_folder, run_id, topics):
    est_topic = topics.get('estimated_position', {})
    est_topic_name = est_topic.get('name')

    if not est_topic_name:
        print("[ERROR] 'estimated_position' topic missing or does not specify a 'csv_file' in config.yaml.")
        return None

    est_csv_file = est_topic_name.lstrip("/").replace("/", "-")+".csv"
    est_csv_path = os.path.join(bag_folder, "csv_files", "per_run", f"run_{run_id}", est_csv_file)

    if not os.path.isfile(est_csv_path):
        print(f"[ERROR] Estimated position CSV file not found at path: {est_csv_path}")
        return None

    # Load the CSV
    df = pd.read_csv(est_csv_path)
    df.columns = df.columns.str.strip()  # Clean column names

    # Detect position columns
    candidates = [
        ('pose.position.x', 'pose.position.y', 'pose.position.z'),
        ('pose.pose.position.x', 'pose.pose.position.y', 'pose.pose.position.z'),
        ('position.x', 'position.y', 'position.z'),
        ('x', 'y', 'z'),
    ]

    pos_cols = None
    for cols in candidates:
        if all(col in df.columns for col in cols):
            pos_cols = cols
            break

    if not pos_cols:
        print(f"[ERROR] Could not find position x/y/z columns in {est_csv_file}. Found columns: {list(df.columns)}")
        return None

    x, y, z = df[pos_cols[0]], df[pos_cols[1]], df[pos_cols[2]]
    positions = np.stack([x, y, z], axis=1)

    # Compute total Euclidean distance
    diffs = np.diff(positions, axis=0)
    segment_lengths = np.linalg.norm(diffs, axis=1)
    total_length = np.sum(segment_lengths)

    print(f"[INFO] Total odometry path length for run_{run_id}: {total_length:.2f} meters")
    return total_length

def calculate_length_drift_error(bag_folder, run_id, topics):
    """
    Calculate the path length drift error between GPS and odometry.
    """
    gps_len = calculate_gps_path_length(bag_folder, run_id, topics)
    odom_len = calculate_odometry_path_length(bag_folder, run_id, topics)

    if gps_len is None or odom_len is None:
        return None

    # Cálculo dos erros
    error = abs(gps_len - odom_len)
    pct_error = (error / gps_len) * 100 if gps_len > 0 else None  # Erro percentual

    print(f"[INFO] Length Drift Error (run {run_id}): MAE={error:.2f}m, Percent Error={pct_error:.2f}%")

    # Criar o dicionário de erros para salvar
    length_drift_error = {
        'run': run_id,
        'odom_length': odom_len,
        'gps_length': gps_len,
        'absolute_error_m': error,
        'percent_error': pct_error
    }

    # Criar a pasta de saída para salvar o arquivo CSV
    errors_folder = os.path.join(bag_folder, "errors")
    os.makedirs(errors_folder, exist_ok=True)

    # Salvar os dados em um arquivo CSV
    out_file = os.path.join(errors_folder, f"length_drift_error_run_{run_id}.csv")
    df = pd.DataFrame([length_drift_error])
    df.to_csv(out_file, index=False)

    print(f"[INFO] Saved length drift error for run_{run_id} to {out_file}")

    return {
        'length_drift': {
            'odom_length': odom_len,
            'gps_length': gps_len,
            'absolute_error_m': error,
            'percent_error': pct_error
        }
    }

def load_gps_waypoints(bag_folder, topics):
    # --- Load waypoints YAML ---
    waypoint_yaml_file = topics.get('waypoints_coords', {}).get('name')
    if not waypoint_yaml_file:
        print("[ERROR] 'waypoints_coords' name missing or 'name' key not set.")
        return None
    
    try:
        pkg_path = rospkg.RosPack().get_path('global_route_system')
        waypoint_path = os.path.join(pkg_path, "config", waypoint_yaml_file)
        if not os.path.isfile(waypoint_path):
            print(f"[ERROR] Waypoint YAML not found: {waypoint_path}")
            return None
    except:
        waypoint_path = os.path.join(bag_folder, waypoint_yaml_file)
        if not os.path.isfile(waypoint_path):
            print(f"[ERROR] Waypoint YAML not found: {waypoint_path}")
            return None

    with open(waypoint_path, 'r') as f:
        waypoint_data = yaml.safe_load(f)

    all_waypoints = waypoint_data.get('global_route', [])
    if not all_waypoints:
        print("[ERROR] 'global_route' not found or empty in YAML.")
        return None
    
    return all_waypoints

# Find the minimal distance between waypoints
def minimal_path_length(bag_folder, run_id, topics):
    """
    Calculate total geodesic distance through a sequence of lat/lon waypoints from a YAML file.
    This is treated as the minimal path because waypoints are assumed ordered.
    """
    route = load_gps_waypoints(bag_folder, topics)
    if route is None: 
        return
    if len(route) < 2:
        print("[ERROR] Need at least two waypoints to compute a path.")
        return None

    # Extract (lat, lon) tuples
    coords = [(wp['lat'], wp['lon']) for wp in route]

    # Compute total geodesic distance
    total_distance = 0.0
    for i in range(1, len(coords)):
        total_distance += geodesic(coords[i - 1], coords[i]).meters

    print(f"[INFO] Minimal path length from waypoints YAML for run_{run_id}: {total_distance:.2f} meters")
    return total_distance

def calculate_trajectory_efficiency_error(bag_folder, run_id, topics):
    """
    Calcula o erro de eficiência de trajetória como a diferença entre:
    - Caminho mínimo (a partir do arquivo de waypoints)
    - Caminho percorrido (a partir dos dados GPS)
    """
    min_len = minimal_path_length(bag_folder, run_id, topics)
    gps_len = calculate_gps_path_length(bag_folder, run_id, topics)

    if min_len is None or gps_len is None:
        return None

    abs_error = gps_len - min_len
    pct_error = (abs_error / min_len) * 100 if min_len > 0 else None

    print(f"[INFO] Trajectory Efficiency Error (run {run_id}):")
    print(f"       Minimal path = {min_len:.2f} m, GPS path = {gps_len:.2f} m")
    print(f"       Absolute error = {abs_error:.2f} m")
    if pct_error is not None:
        print(f"       Percent error = {pct_error:.2f}%")

    efficiency_error = {
        'run': run_id,
        'minimal_length': min_len,
        'gps_length': gps_len,
        'absolute_error_m': abs_error,
        'percent_error': pct_error
    }


    # Criar a pasta de saída para salvar o arquivo CSV
    errors_folder = os.path.join(bag_folder, "errors")
    os.makedirs(errors_folder, exist_ok=True)

    # Salvar os dados em um arquivo CSV
    out_file = os.path.join(errors_folder, f"trajectory_efficiency_error_run_{run_id}.csv")
    df = pd.DataFrame([efficiency_error])
    df.to_csv(out_file, index=False)

    print(f"[INFO] Saved trajectory efficiency error for run_{run_id} to {out_file}")

    return {
        'trajectory_efficiency': {
            'minimal_length': min_len,
            'gps_length': gps_len,
            'absolute_error_m': abs_error,
            'percent_error': pct_error
        }
    }

def plot_distance_to_waypoints(bag_folder, run_id, topics, waypoint_indices=None):
    """
    Plots the robot's distance to selected GPS waypoints over time.
    Marks when the robot arrives near each waypoint (including waypoint 0).
    """

    # --- Load robot GPS positions ---
    gps_topic = topics.get('gps_plan', {})
    gps_topic_name = gps_topic.get('name')
    if not gps_topic_name:
        print("[ERROR] 'gps_plan' topic missing or no 'csv_file' in config.yaml.")
        return

    gps_csv_file = gps_topic_name.lstrip("/").replace("/", "-")+".csv"
    gps_csv_path = os.path.join(bag_folder, "csv_files", "per_run", f"run_{run_id}", gps_csv_file)
    if not os.path.isfile(gps_csv_path):
        print(f"[ERROR] GPS CSV file not found: {gps_csv_path}")
        return

    gps_df = pd.read_csv(gps_csv_path)
    gps_df.columns = gps_df.columns.str.strip()
    lat_col = next((c for c in ['latitude', 'lat'] if c in gps_df.columns), None)
    lon_col = next((c for c in ['longitude', 'lon'] if c in gps_df.columns), None)
    if not lat_col or not lon_col:
        print(f"[ERROR] Latitude/Longitude columns not found in {gps_csv_path}.")
        return

    robot_positions = list(zip(gps_df[lat_col], gps_df[lon_col]))

    all_waypoints = load_gps_waypoints(bag_folder, topics)
    if all_waypoints is None: 
        return

    if waypoint_indices is None:
        waypoint_indices = list(range(len(all_waypoints)))

    waypoint_coords = [(all_waypoints[i]['lat'], all_waypoints[i]['lon']) for i in waypoint_indices]

    # --- Compute distances and arrivals ---
    arrival_threshold = 1.0  # meters
    distance_series = {}
    arrival_markers = {}

    for wp_idx, coord in zip(waypoint_indices, waypoint_coords):
        distances = [geodesic(coord, pos).meters for pos in robot_positions]
        distance_series[wp_idx] = distances

        for i, d in enumerate(distances):
            if d <= arrival_threshold:
                arrival_markers[wp_idx] = (i, d)
                break  # Only mark first arrival

    # --- Plot ---
    plt.figure(figsize=(14, 6))
    for wp_idx, distances in distance_series.items():
        plt.plot(distances, label=f"Waypoint {wp_idx}")

        if wp_idx in arrival_markers:
            i, d = arrival_markers[wp_idx]
            plt.scatter(i, d, color='red', zorder=5)
            plt.text(i, d + 0.5, f"Reached WP{wp_idx}", fontsize=9, color='red', ha='center')

    plt.title(f"Distance to Waypoints (run_{run_id})")
    plt.xlabel("Time (index)")
    plt.ylabel("Distance (m)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    # --- Save plot ---
    plot_folder = os.path.join(bag_folder, "plots")
    os.makedirs(plot_folder, exist_ok=True)
    plot_file = os.path.join(plot_folder, f"distance_to_waypoints_run_{run_id}.png")
    plt.savefig(plot_file)
    print(f"[INFO] Saved distance plot to {plot_file}")
    plt.close()

def latlon_to_local_xy(latitudes, longitudes, ref_lat=None, ref_lon=None, rotation_deg=0.0):
    if ref_lat is None or ref_lon is None:
        ref_lat = latitudes[0]
        ref_lon = longitudes[0]

    x = []
    y = []

    for lat, lon in zip(latitudes, longitudes):
        d_y = geodesic((ref_lat, ref_lon), (lat, ref_lon)).meters
        d_x = geodesic((ref_lat, ref_lon), (ref_lat, lon)).meters

        if lon < ref_lon:
            d_x = -d_x
        if lat < ref_lat:
            d_y = -d_y

        x.append(d_x)
        y.append(d_y)
        
    x = np.array(x)
    y = np.array(y)
    
    if rotation_deg != 0.0:
        angle_rad = np.deg2rad(rotation_deg)
        x_rot = np.cos(angle_rad) * x - np.sin(angle_rad) * y
        y_rot = np.sin(angle_rad) * x + np.cos(angle_rad) * y
        return x_rot, y_rot

    return x, y

def synchronize_data(est_df, gps_df):
    est_df = est_df.sort_values('Time').reset_index(drop=True)
    gps_df = gps_df.sort_values('Time').reset_index(drop=True)

    columns = ['x', 'y']

    gps_interp = {}
    for col in columns:
        gps_interp[col] = np.interp(est_df['Time'], gps_df['Time'], gps_df[col])

    gps_sync = pd.DataFrame(gps_interp)
    gps_sync['Time'] = est_df['Time'].values

    est_sync = est_df.reset_index(drop=True)

    return est_sync, gps_sync

def calculate_position_error_gps_vs_odometry(bag_folder, run_id, topics):
    gps_topic = topics.get('gps_plan', {})
    est_topic = topics.get('estimated_position', {})

    gps_topic_name = gps_topic.get('name')
    est_topic_name = est_topic.get('name')

    if not gps_topic_name or not est_topic_name:
        print("[ERROR] Missing gps_plan or estimated_position csv_file in config.")
        return None

    gps_csv_file = gps_topic_name.lstrip("/").replace("/", "-")+".csv"
    est_csv_file = est_topic_name.lstrip("/").replace("/", "-")+".csv"
    
    run_folder = os.path.join(bag_folder, "csv_files", "per_run", f"run_{run_id}")
    gps_path = os.path.join(run_folder, gps_csv_file)
    est_path = os.path.join(run_folder, est_csv_file)

    if not os.path.isfile(gps_path) or not os.path.isfile(est_path):
        print(f"[ERROR] GPS or odometry CSV not found for run {run_id}.")
        return None

    gps_df = pd.read_csv(gps_path)
    est_df = pd.read_csv(est_path)

    gps_df.columns = gps_df.columns.str.strip()
    est_df.columns = est_df.columns.str.strip()

    lat_col = None
    lon_col = None
    for col_candidate in ['latitude', 'lat']:
        if col_candidate in gps_df.columns:
            lat_col = col_candidate
            break
    for col_candidate in ['longitude', 'lon']:
        if col_candidate in gps_df.columns:
            lon_col = col_candidate
            break
    if lat_col is None or lon_col is None:
        print("[ERROR] Latitude or longitude columns not found in GPS CSV.")
        return None

    possible_pos_cols = [
        ('pose.position.x', 'pose.position.y', 'pose.position.z'),
        ('pose.pose.position.x', 'pose.pose.position.y', 'pose.pose.position.z'),
        ('position.x', 'position.y', 'position.z'),
        ('x', 'y', 'z'),
    ]

    est_pos_cols = None
    for cols in possible_pos_cols:
        if all(c in est_df.columns for c in cols):
            est_pos_cols = cols
            break

    if est_pos_cols is None:
        print("[ERROR] Position columns not found in odometry CSV.")
        return None

    est_local = est_df[list(est_pos_cols)].copy()
    est_local.columns = ['x', 'y', 'z']

    if 'Time' in est_df.columns:
        est_local['Time'] = est_df['Time'].values
    else:
        est_local['Time'] = np.arange(len(est_local))

    gps_x, gps_y = latlon_to_local_xy(gps_df[lat_col].values, gps_df[lon_col].values)

    if 'Time' in gps_df.columns:
        gps_local = pd.DataFrame({'Time': gps_df['Time'].values, 'x': gps_x, 'y': gps_y})
    else:
        gps_local = pd.DataFrame({'Time': np.arange(len(gps_df)), 'x': gps_x, 'y': gps_y})

    # Salvar as posições locais do GPS em csv_files/per_run/run_{run_id}/gps_to_local.csv
    gps_local_csv_path = os.path.join(run_folder, "gps_to_local.csv")
    gps_local.to_csv(gps_local_csv_path, index=False)
    print(f"[INFO] Saved GPS local positions to {gps_local_csv_path}")

    est_sync, gps_sync = synchronize_data(est_local[['Time', 'x', 'y']], gps_local)

    diffs = est_sync[['x', 'y']].values - gps_sync[['x', 'y']].values

    rmse = np.sqrt(np.mean(diffs**2, axis=0))
    mae = np.mean(np.abs(diffs), axis=0)

    result = {
        'rmse': {'x': rmse[0], 'y': rmse[1]},
        'mae': {'x': mae[0], 'y': mae[1]}
    }

    print(f"[INFO] Position Errors between Odometry and GPS for run_{run_id}:")
    print(f"       RMSE: x={rmse[0]:.3f} m, y={rmse[1]:.3f} m")
    print(f"       MAE : x={mae[0]:.3f} m, y={mae[1]:.3f} m")

    save_errors_to_csv(result, bag_folder, run_id, label="position")

    return result

def save_path_lengths_to_csv(path_lengths, bag_folder, run_id):
    """
    Salva o comprimento do caminho (odometria vs GPS) para um único run em um CSV.
    """
    # Pasta para salvar os erros
    errors_folder = os.path.join(bag_folder, "errors")
    os.makedirs(errors_folder, exist_ok=True)

    # Salva os comprimentos para o run específico
    df = pd.DataFrame(path_lengths)
    run_file = os.path.join(errors_folder, f"path_lengths_run_{run_id}.csv")
    df.to_csv(run_file, index=False)
    print(f"[INFO] Saved path lengths for run_{run_id} to {run_file}")

def calculate_and_save_path_lengths(bag_folder, run_id, topics):
    # Calcular o comprimento do caminho pela odometria
    odometry_path_length = calculate_odometry_path_length(bag_folder, run_id, topics)
    # Calcular o comprimento do caminho pelo GPS
    gps_path_length = calculate_gps_path_length(bag_folder, run_id, topics)
    # Calcular o comprimento do caminho mínimo (a partir dos waypoints)
    minimal_path_length_value = minimal_path_length(bag_folder, run_id, topics)

    if odometry_path_length is None or gps_path_length is None or minimal_path_length_value is None:
        print(f"[ERROR] Não foi possível calcular os comprimentos dos caminhos para run_{run_id}.")
        return

    # Criar o dicionário de dados a serem salvos
    path_lengths = {
        'run': run_id,
        'odometry_path_length': odometry_path_length,
        'gps_path_length': gps_path_length,
        'minimal_path_length': minimal_path_length_value
    }

    # Criar a pasta de saída para salvar o arquivo CSV
    path_lengths_folder = os.path.join(bag_folder, "path_lengths")
    os.makedirs(path_lengths_folder, exist_ok=True)

    # Salvar os dados em um arquivo CSV
    out_file = os.path.join(path_lengths_folder, f"path_lengths_run_{run_id}.csv")
    df = pd.DataFrame([path_lengths])
    df.to_csv(out_file, index=False)

    print(f"[INFO] Saved path lengths for run_{run_id} to {out_file}")


def main():
    bag_folder = "/home/manuela/Documents/VerLab/dataAnalysisForRobotics/lib_tests/lib_script_test"

    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "config.yaml")

    topics = load_config(config_path)

    # Get sorted bag mapping
    bag_mapping = get_sorted_bag_mapping(bag_folder)

    # Convert bags to CSV using mapping
    convert_bags_to_csv(bag_folder, bag_mapping, topics)

    # Use number of runs from mapping
    num_bags = len(bag_mapping)

    calculate_length_drift_error(bag_folder, 0, topics=topics)

    calculate_trajectory_efficiency_error(bag_folder, run_id=0, topics=topics)

if __name__ == "__main__":
    main()
