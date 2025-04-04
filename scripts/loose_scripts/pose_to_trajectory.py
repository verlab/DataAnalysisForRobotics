import pandas as pd
import matplotlib.pyplot as plt
import re

"""
Trajectory and Waypoint Plotting Utility
----------------------------------------

This script gets a robots position over time to visualizes it's trajectories and planned waypoints from CSV files.
It supports CSVs with different formats for position data and plots both actual
and planned paths for comparison.

You can plot 1 or N trajectories with or without waypoints (if you don't have them)

Usage:
------
Adjust the file paths in the example below to point to your specific CSV files.
The example shows how to plot:
- The planned trajectory (`global_plan`)
- The ground truth trajectory
- The list of goal waypoints

Notes:
------
- You may uncomment and modify the offset logic in `plot_trajectory()` if you want all trajectories
  to start from the origin (0, 0) for better visual alignment.
- This script assumes each input CSV has a consistent format across rows.
"""

def plot_trajectory(csv_path, label=None, color=None):
    df = pd.read_csv(csv_path)

    # Determine file type (because for some reason, the names sometimes change)
    # if you pose.csv file has columns with diferent names, modify here
    if 'position.x' in df.columns and 'position.y' in df.columns:
        x_vals = df['position.x']
        y_vals = df['position.y']

    elif 'pose.position.x' in df.columns and 'pose.position.y' in df.columns:
        x_vals = df['pose.position.x']
        y_vals = df['pose.position.y']

        # Apply offset to bring initial position to (0,0), if you want your trajectory starting from (0,0)
        # x_offset = x_vals.iloc[0]
        # y_offset = y_vals.iloc[0]
        # x_vals = x_vals - x_offset
        # y_vals = y_vals - y_offset

    else:
        raise ValueError("Unknown CSV structure. Expected 'poses' or 'pose.position.x/y' columns.")

    plt.plot(x_vals, y_vals, marker='o', markersize=3, linewidth=1, label=label, color=color)
    plt.plot(x_vals.iloc[0], y_vals.iloc[0], marker='*', color='red', markersize=12)

    plt.xlabel('X Position')
    plt.ylabel('Y Position')
    plt.grid(True)
    plt.axis('equal')

def plot_waypoints(csv_path, color='purple'):
    df = pd.read_csv(csv_path)

    if 'poses' not in df.columns:
        raise ValueError("Waypoint file structure unexpected. 'poses' column missing.")

    # Extract all x, y pairs from the poses string
    poses_text = " ".join(df['poses'].values)
    x_vals = [float(x) for x in re.findall(r'x:\s*([-\d.]+)', poses_text)]
    y_vals = [float(y) for y in re.findall(r'y:\s*([-\d.]+)', poses_text)]

    # Plot waypoints
    plt.scatter(x_vals, y_vals, color=color, marker='x', s=70, label='Waypoints', zorder=4)

# Example usage:
# Modify the path to your files

# plt.figure(figsize=(10, 8))
# plot_trajectory("/planned_trajectory.csv", label="Planned Trajectory", color="orange")
# plot_trajectory("performed_trajectory.csv", label="Ground Truth Trajectory", color="blue")
# plot_waypoints("/waypoints.csv")

# plt.title("Trajectory Comparison")
# plt.legend()
# plt.savefig('True_vs_Planned_Path.png')
