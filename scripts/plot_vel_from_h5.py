import h5py
import numpy as np
import matplotlib.pyplot as plt

"""
Velocity Plotter from HDF5 File
-------------------------------

This script reads linear and angular velocity data stored in an HDF5 (.h5) file 
and generates time series plots for each velocity component (X, Y, Z) across 
multiple experimental runs.

What the script does:
---------------------
- Reads datasets stored in the path: `per_topic/real_vel/run_X` for X in range(num_runs).
- Extracts time, linear velocities (x, y, z), and angular velocities (x, y, z) from the data.
- Generates and saves six separate plots:
    1. Linear Velocity X across all runs
    2. Linear Velocity Y across all runs
    3. Linear Velocity Z across all runs
    4. Angular Velocity X across all runs
    5. Angular Velocity Y across all runs
    6. Angular Velocity Z across all runs
- Saves each plot as a PNG image.

Usage:
------
Modify the example usage at the bottom of the script with the correct path to your `.h5` file:

Parameters:
-----------
- file_path (str) : Path to the HDF5 file containing velocity data.
- num_runs (int)  : Number of experimental runs to process (default: 50).

Notes:
------
- The dataset path inside the HDF5 file is currently hardcoded as: `per_topic/real_vel/run_X`.
  Adjust the `run_path` variable in the function if your folder structure or naming is different.
- The function assumes that the velocity data is stored in the first seven columns:
    [time, linear.x, linear.y, linear.z, angular.x, angular.y, angular.z].
- Missing runs will be skipped, and a warning will be printed.

"""


def plot_velocities_from_h5(file_path, num_runs=50):

    # Create lists to store each run's data
    times = []
    linear_xs = []
    linear_ys = []
    linear_zs = []
    angular_xs = []
    angular_ys = []
    angular_zs = []

    with h5py.File(file_path, 'r') as f:
        for i in range(num_runs):
            run_path = f"per_topic/real_vel/run_{i}" # modify this line to your folder structure, where your velocities are stored and how they are  named
            if run_path not in f:
                print(f"Warning: {run_path} not found in the file.")
                continue
            
            data = f[run_path][:]
            # Extract columns (adjust to match your file’s columns)
            t = data[:, 0]
            v_x = data[:, 1]
            v_y = data[:, 2]
            v_z = data[:, 3]
            w_x = data[:, 4]
            w_y = data[:, 5]
            w_z = data[:, 6]

            times.append(t)
            linear_xs.append(v_x)
            linear_ys.append(v_y)
            linear_zs.append(v_z)
            angular_xs.append(w_x)
            angular_ys.append(w_y)
            angular_zs.append(w_z)

    # --- Plot linear.x (all runs in one figure) ---
    plt.figure()
    for i in range(len(times)):
        plt.plot(times[i], linear_xs[i], label=f"run_{i}")
    plt.xlabel("Time")
    plt.ylabel("Linear Velocity X")
    plt.title("Linear Velocity X (All Runs)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("linear_x_all_runs.png")

    # --- Plot linear.y (all runs) ---
    plt.figure()
    for i in range(len(times)):
        plt.plot(times[i], linear_ys[i], label=f"run_{i}")
    plt.xlabel("Time")
    plt.ylabel("Linear Velocity Y")
    plt.title("Linear Velocity Y (All Runs)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("linear_y_all_runs.png")

    # --- Plot linear.z (all runs) ---
    plt.figure()
    for i in range(len(times)):
        plt.plot(times[i], linear_zs[i], label=f"run_{i}")
    plt.xlabel("Time")
    plt.ylabel("Linear Velocity Z")
    plt.title("Linear Velocity Z (All Runs)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("linear_z_all_runs.png")

    # --- Plot angular.x (all runs) ---
    plt.figure()
    for i in range(len(times)):
        plt.plot(times[i], angular_xs[i], label=f"run_{i}")
    plt.xlabel("Time")
    plt.ylabel("Angular Velocity X")
    plt.title("Angular Velocity X (All Runs)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("angular_x_all_runs.png")

    # --- Plot angular.y (all runs) ---
    plt.figure()
    for i in range(len(times)):
        plt.plot(times[i], angular_ys[i], label=f"run_{i}")
    plt.xlabel("Time")
    plt.ylabel("Angular Velocity Y")
    plt.title("Angular Velocity Y (All Runs)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("angular_y_all_runs.png")

    # --- Plot angular.z (all runs) ---
    plt.figure()
    for i in range(len(times)):
        plt.plot(times[i], angular_zs[i], label=f"run_{i}")
    plt.xlabel("Time")
    plt.ylabel("Angular Velocity Z")
    plt.title("Angular Velocity Z (All Runs)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("angular_z_all_runs.png")

# example usage
# if __name__ == "__main__":
#    plot_velocities_from_h5("/experiments.h5")
