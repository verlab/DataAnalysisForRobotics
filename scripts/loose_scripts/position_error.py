import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error

def load_and_subsample(odom_file, ground_truth_file):
    # Load CSVs
    odom = pd.read_csv(odom_file)
    gt = pd.read_csv(ground_truth_file)
    
    # Subsample odometry to match ground truth length
    factor = len(odom) // len(gt)
    odom_subsampled = odom.iloc[::factor].reset_index(drop=True)
    
    # In case the last samples mismatch by one
    min_len = min(len(odom_subsampled), len(gt))
    odom_subsampled = odom_subsampled.iloc[:min_len]
    gt = gt.iloc[:min_len]

    return odom_subsampled, gt

def compute_rmse(gt, odom):
    rmse = np.sqrt(mean_squared_error(gt, odom))
    return rmse

def compute_absolute_position_error(gt, odom):
    # Euclidean distance error
    errors = np.linalg.norm(gt.values - odom.values, axis=1)
    return errors

def main():
    odom_file = '/home/manuela/Documents/VerLab/data_analysis/csv_files/per_run/run_0/lego_loam-odom.csv'
    ground_truth_file = '/home/manuela/Documents/VerLab/data_analysis/csv_files/per_run/run_0/ground_truth_pose.csv'
    # output_subsampled_file = 'odom_subsampled.csv'

    odom_sub, gt = load_and_subsample(odom_file, ground_truth_file)

    # odom_sub.to_csv(output_subsampled_file, index=False)
    # print(f"Subsampled odometry saved to: {output_subsampled_file}")

    # Assume columns: x, y (extend to z if you want)
    odom_positions = odom_sub[['pose.pose.position.x', 'pose.pose.position.y', 'pose.pose.position.z']]
    gt_positions = gt[['pose.position.x', 'pose.position.y', 'pose.position.z']]

    rmse = compute_rmse(gt_positions, odom_positions)
    ape = compute_absolute_position_error(gt_positions, odom_positions)

    print(f"RMSE: {rmse}")
    print(f"Mean Absolute Position Error: {np.mean(ape)}")
    print(f"Max Absolute Position Error: {np.max(ape)}")

if __name__ == "__main__":
    main()
