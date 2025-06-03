#!/usr/bin/env python3
"""
plot_gps_laps_from_csv.py

Scans all `run_*` folders in a specified root directory, reads `*-fix.csv` files in each,
segments GPS fixes into laps, and generates:
  - One PNG per sensor per run (named `run_X_sensor_continuous_laps.png`).
  - One combined PNG per run (named `run_X_combined_continuous_laps.png`).

All outputs go into a `plots/` folder inside the specified root (created if missing).

Usage:
    cd GNSS/scripts
    python plot_gps_laps_from_csv.py \
        --data_dir /path/to/GNSS \
        [--run_distance_threshold 5.0] [--min_run_duration 30.0]
"""
import os
import glob
import argparse
from math import sqrt

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def segment_runs(times: np.ndarray,
                 lat: np.ndarray,
                 lon: np.ndarray,
                 run_distance_threshold: float,
                 min_run_duration: float):
    segments = []
    if len(times) == 0:
        return segments

    current = [0]
    ref_lat, ref_lon = lat[0], lon[0]
    start_time = times[0]

    for i in range(1, len(times)):
        dx = (lon[i] - ref_lon) * 111320.0
        dy = (lat[i] - ref_lat) * 110540.0
        dist = sqrt(dx*dx + dy*dy)
        current.append(i)
        elapsed = times[i] - start_time
        if dist < run_distance_threshold and elapsed > min_run_duration:
            segments.append(current.copy())
            current = [i]
            start_time = times[i]
            ref_lat, ref_lon = lat[i], lon[i]

    if current:
        segments.append(current)
    return segments


def plot_runs(sensor_id: str, df: pd.DataFrame, segments: list, plots_dir: str, run_name: str):
    lat0, lon0 = df['latitude'].iloc[0], df['longitude'].iloc[0]
    xs = (df['longitude'].to_numpy() - lon0) * 111320.0
    ys = (df['latitude'].to_numpy()  - lat0) * 110540.0

    plt.figure(figsize=(10, 8))
    cmap = plt.get_cmap('tab10')
    for idx, seg in enumerate(segments):
        seg_x = xs[seg]
        seg_y = ys[seg]
        color = cmap(idx % 10)
        plt.plot(seg_x, seg_y, marker='o', linestyle='-', label=f'Lap {idx+1}', color=color)
        plt.plot(seg_x[0], seg_y[0], marker='s', markersize=8, markeredgecolor='k', color=color)

    plt.xlabel('Relative X (m)')
    plt.ylabel('Relative Y (m)')
    plt.title(f'{run_name} - {sensor_id}')
    plt.legend()
    plt.grid(True)
    plt.gca().set_aspect('equal', adjustable='datalim')

    out = os.path.join(plots_dir, f'{run_name}_{sensor_id}_continuous_laps.png')
    plt.savefig(out)
    plt.close()
    print(f'Saved: {out}')


def plot_combined(run_name: str, sensor_data: dict, plots_dir: str):
    plt.figure(figsize=(12, 10))
    cmap = plt.get_cmap('tab10')
    markers = ['o','s','^','x','D','v','*','p','H','+']

    for s_idx, (sensor_id, (df, segments)) in enumerate(sensor_data.items()):
        lat0, lon0 = df['latitude'].iloc[0], df['longitude'].iloc[0]
        xs = (df['longitude'].to_numpy() - lon0) * 111320.0
        ys = (df['latitude'].to_numpy()  - lat0) * 110540.0
        base_color = cmap(s_idx % 10)
        for l_idx, seg in enumerate(segments):
            seg_x = xs[seg]
            seg_y = ys[seg]
            marker = markers[l_idx % len(markers)]
            plt.plot(seg_x, seg_y, marker=marker, linestyle='-', label=f'{sensor_id} Lap {l_idx+1}', color=base_color)

    plt.xlabel('Relative X (m)')
    plt.ylabel('Relative Y (m)')
    plt.title(f'{run_name} - Combined')
    plt.legend(fontsize='small', loc='best', ncol=2)
    plt.grid(True)
    plt.gca().set_aspect('equal', adjustable='datalim')

    out = os.path.join(plots_dir, f'{run_name}_combined_continuous_laps.png')
    plt.savefig(out)
    plt.close()
    print(f'Saved: {out}')


def main():
    parser = argparse.ArgumentParser(
        description='Analyze GPS fix CSV runs and plot laps.')
    parser.add_argument(
        '--data_dir', type=str, required=True,
        help='Root folder containing run_* subdirectories.')
    parser.add_argument(
        '--run_distance_threshold', type=float, default=5.0,
        help='Meters to close a lap (default: 5.0)')
    parser.add_argument(
        '--min_run_duration', type=float, default=30.0,
        help='Min lap duration in seconds (default: 30.0)')
    args = parser.parse_args()

    data_root = os.path.abspath(args.data_dir)
    plots_dir = os.path.join(data_root, 'plots')
    os.makedirs(plots_dir, exist_ok=True)

    run_dirs = sorted(glob.glob(os.path.join(data_root, 'run_*')))
    if not run_dirs:
        print(f'No run_* folders under {data_root}.')
        return

    for run_path in run_dirs:
        run_name = os.path.basename(run_path)
        print(f'=== Processing {run_name} ===')
        fix_files = glob.glob(os.path.join(run_path, '*-fix.csv'))
        if not fix_files:
            print(f'  No fix CSVs in {run_name}, skipping.')
            continue

        sensor_data = {}
        for fp in sorted(fix_files):
            sensor_id = os.path.basename(fp).split('-fix.csv')[0]
            print(f'  Sensor: {sensor_id}')
            df = pd.read_csv(fp)
            if not {'Time','latitude','longitude'}.issubset(df.columns):
                print(f'    Missing cols, skipping.')
                continue
            times = df['Time'].to_numpy()
            lat   = df['latitude'].to_numpy()
            lon   = df['longitude'].to_numpy()

            segments = segment_runs(
                times, lat, lon,
                args.run_distance_threshold,
                args.min_run_duration)
            print(f'    Detected {len(segments)} lap(s)')
            plot_runs(sensor_id, df, segments, plots_dir, run_name)
            sensor_data[sensor_id] = (df, segments)

        if sensor_data:
            plot_combined(run_name, sensor_data, plots_dir)

if __name__ == '__main__':
    main()
