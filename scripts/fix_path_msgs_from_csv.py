import pandas as pd
import re
import os
"""
CSV Pose Data Cleaner for nav_msgs/Path
---------------------------------------

This script fixes and restructures pose data extracted from ROS bag files 
containing `nav_msgs/Path` messages. The `bagpy` library's default CSV export 
does not correctly format `poses` field data, resulting in an unreadable, 
multi-line string that is difficult to process.

What this script does:
----------------------
- Parses the messy `poses` string field from the CSV exported by `bagpy`.
- Extracts numeric position and orientation values from each pose in the path.
- Creates a clean, flat CSV file with one row per pose, containing:
    - Timestamp and header information.
    - Position (x, y, z).
    - Orientation (x, y, z, w).

Usage:
------
Update the `input_base` and `output_base` variables to match the input and output folders.

This example processes 50 CSV files:
    move_base-DWAPlannerROS-global_plan_run_0.csv
    move_base-DWAPlannerROS-global_plan_run_1.csv
    ...
    move_base-DWAPlannerROS-global_plan_run_49.csv

For each file:
- Reads the original CSV file.
- Extracts and flattens the pose information.
- Writes a cleaned CSV file named: global_plan_run_X.csv

"""

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
    print(f"Cleaned CSV written to: {output_csv}")

# Example usage:
# Adjust the folder path and file name pattern according to your CSV files' location and naming convention.

# input_base = ''
# output_base = ''

# # Loop through files 0 to 50
# for i in range(50):
#     input_file = os.path.join(input_base, f'path_run_{i}.csv')
#     output_file = os.path.join(output_base, f'global_plan_run_{i}.csv')
#     extract_poses_from_csv(input_file, output_file)
