import os
import h5py
import pandas as pd

"""
CSV to HDF5 Converter for ROS Data
-----------------------------------

This script reads CSV files containing ROS message data and stores the numeric content 
into a structured HDF5 (.h5) file. The structure is organized in two ways:
1. Per Run: Groups CSV data by run folders.
2. Per Topic: Groups CSV data by topic folders.

The script performs the following:
----------------------------------
- Reads numeric data from CSV files.
- Organizes and stores the data hierarchically in an HDF5 file:
    - /per_run/run_X/ (per run data)
    - /per_topic/topic_Y/ (per topic data)
- Cleans dataset names by removing CSV extensions.
- Uses gzip compression to reduce file size.
- Automatically skips CSV files without numeric data and logs a warning.

Notes:
------
- Only numeric columns (int, float, etc.) are stored in the HDF5 datasets.
- Columns name are passed as atributes of the .h5 file
- Existing datasets will be overwritten if they already exist in the file.
"""

COMPRESSION = "gzip"

def clean_name(name):
    """Make sure names are valid HDF5 keys (remove extensions, etc)."""
    return os.path.splitext(name)[0]

def write_per_run_data(h5file, csv_per_run_dir):
    for run_folder in sorted(os.listdir(csv_per_run_dir)):
        run_path = os.path.join(csv_per_run_dir, run_folder)
        if not os.path.isdir(run_path):
            continue
        print(f"Processing {run_folder}...")
        run_group = h5file.require_group(f"per_run/{run_folder}")

        for csv_file in os.listdir(run_path):
            topic_name = clean_name(csv_file)
            csv_path = os.path.join(run_path, csv_file)
            df = pd.read_csv(csv_path)

            numeric_df = df.select_dtypes(include=["number"])
            if numeric_df.empty:
                print(f"Warning: No numeric data in {csv_path}, skipping.")
                continue

            data = numeric_df.to_numpy()
            dataset_path = f"{topic_name}"

            if dataset_path in run_group:
                del run_group[dataset_path]
            dset = run_group.create_dataset(dataset_path, data=data, compression=COMPRESSION)
            dset.attrs["columns"] = list(numeric_df.columns)

def write_per_topic_data(h5file, csv_per_topic_dir):
    for topic_folder in sorted(os.listdir(csv_per_topic_dir)):
        topic_path = os.path.join(csv_per_topic_dir, topic_folder)
        if not os.path.isdir(topic_path):
            continue
        print(f"Processing topic: {topic_folder}")
        topic_group = h5file.require_group(f"per_topic/{topic_folder}")

        for csv_file in os.listdir(topic_path):
            csv_path = os.path.join(topic_path, csv_file)
            try:
                df = pd.read_csv(csv_path)
            except Exception as e:
                print(f"Failed to read {csv_path}: {e}")
                continue

            base_name = clean_name(csv_file)
            if "_run_" in base_name:
                run_id = base_name.split("_run_")[-1]
                dataset_path = f"run_{run_id}"
            else:
                print(f"Unexpected file name format: {csv_file}")
                continue

            numeric_df = df.select_dtypes(include=["number"])
            if numeric_df.empty:
                print(f"Warning: No numeric data in {csv_path}, skipping.")
                continue

            data = numeric_df.to_numpy()

            if dataset_path in topic_group:
                del topic_group[dataset_path]
            dset = topic_group.create_dataset(dataset_path, data=data, compression=COMPRESSION)
            dset.attrs["columns"] = list(numeric_df.columns)

# usage example below, modify the paths as you need
# def main():
#     csv_per_run_dir = "/csv_files/per_run"
#     csv_per_topic_dir = "/csv_files/per_topic"
#     hdf5_output_file = "gazebo_experiments.h5"

#     with h5py.File(hdf5_output_file, "a") as h5file:
#         print("Writing per-run data...")
#         write_per_run_data(h5file, csv_per_run_dir)
#         print("Writing per-topic data...")
#         write_per_topic_data(h5file, csv_per_topic_dir)
#     print("Done. HDF5 file created at:", hdf5_output_file)

# if __name__ == "__main__":
#     main()
