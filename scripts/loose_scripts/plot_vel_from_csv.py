import os
import pandas as pd
import matplotlib.pyplot as plt

"""
Velocity Plotting Script
------------------------

This script reads CSV files containing linear and angular velocity data per run 
and generates two plots:
1. Linear Velocities Plot
2. Angular Velocities Plot

The script is parametrized:
- You can specify the folder path where your CSV files are located.
- This script expects a folder with csv files
- You can pass the list of CSV file names you want to include in the plot.
- You can set custom output file names for the generated plots.
- Optionally, you can display the plot interactively in addition to saving.

Expected CSV format:
Each CSV file should contain columns (or something like it, but you will have to modify the code, lines 31 and 53):
    - linear.x, linear.y, linear.z
    - angular.x, angular.y, angular.z
Each file represents a run, typically named like: real_vel_run_0.csv, real_vel_run_1.csv, etc.

"""


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

# usage example, modify as needed
# def main():
#     folder_path = ""   # modify to match where your velocities csv files are
#     file_names = [f"real_vel_run_{i}.csv" for i in range(2)] # modify to match how your files are named (make sure they follow a pattern)

#     plot_linear_velocities(
#         folder_path=folder_path,
#         file_names=file_names,
#         output_file="real_vel_linear.png"
#     )

#     plot_angular_velocities(
#         folder_path=folder_path,
#         file_names=file_names,
#         output_file="real_vel_angular.png"
#     )

# if __name__ == "__main__":
#     main()
