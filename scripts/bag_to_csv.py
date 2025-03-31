import os
import argparse
from bagpy import bagreader

"""
ROS Bag to CSV Converter
------------------------

This script reads a sequence of ROS bag files and converts the messages of each topic 
into individual CSV files using the `bagpy` library.

Functionality:
--------------
- Reads bag files named in the pattern: run_0.bag, run_1.bag, ..., run_N.bag. (But you can modify line 38 if your bags follow a different name structure)
- For each bag file, extracts all topics and saves the message data to separate CSV files.
- Skips bag files that are missing and logs a warning.

Usage:
------
Run the script from the terminal:

python bag_to_csv.py --folder /path/to/bag/folder --num_bags 50

Arguments:
----------
--folder   : Path to the folder containing the .bag files
--num_bags : Number of bag files to process (starting from run_0.bag)

Example:
--------
If your bag folder is `/home/user/bags` and you have 10 bag files (run_0.bag to run_9.bag), run:

python bag_to_csv.py --folder /home/user/bags --num_bags 10
"""

def convert_bags_to_csv(bag_folder, num_bags):
    for i in range(num_bags):
        bag_name = f'run_{i}.bag'
        bag_path = os.path.join(bag_folder, bag_name)

        if not os.path.isfile(bag_path):
            print(f"[WARNING] Bag file not found: {bag_path}")
            continue

        print(f"[INFO] Reading: {bag_path}")
        b = bagreader(bag_path)

        for topic in b.topics:
            csv_path = b.message_by_topic(topic)
            print(f"[INFO] Saved CSV: {csv_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert ROS bag files to CSV format.")
    parser.add_argument("--folder", type=str, required=True, help="Path to the folder containing bag files")
    parser.add_argument("--num_bags", type=int, required=True, help="Number of bag files to process")

    args = parser.parse_args()

    convert_bags_to_csv(args.folder, args.num_bags)
