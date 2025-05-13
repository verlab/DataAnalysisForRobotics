# DataAnalysisForRobotics
Data Analysis for Robotics Projects with ROS

## Data analysis for GNSS systems
Tools to plot and verify the data from a GNSS system, checking RTK status and random walk.

### Stationary test
Check the deviation of a GNSS system.

#### What it does
* It will draw one circle within the specified range, defined by the user as a kind of random walk limit

* It will draw an ellipse containing 95% of the points to check it's distribution while stationary. 

#### How to run it
* Collect a `/fix` rosbag. 
* Rename it to `run_<run_number>.bag` (e.g `run_42.bag`)
* Convert the bag into a csv file with `bag_to_csv.py`
  From the repository folder, run:
  ```bash 
  python scripts/bag_to_csv.py --folder /path/to/bag/folder --num_bags 1
  ```
  Arguments:
  ----------
  --folder   : Path to the folder containing the .bag files.

  --num_bags : Number of bag files to process. Practicaly, it should always be one, as there is no reasson to merge more than one bag, unless it was a interrupted stationary test or something similar

* Run the script to generate the stationary plot, with the csv generated as input
  ```bash
  python <plot_gps_from_csv.py path> --csv <.csv file path> --max-distance <distance_threshold>
  ```
  Arguments:
  ----------
  --csv  Path of the csv file(usually inside the `run_<run_number>` folder)

  --max-distance  Distance of the max distance threshold(Circle)

  e.g.
  ```
  python3 scripts/plot_gps_from_csv.py --csv run_0/ublox-fix.csv --max-distance 0.2
  ```

### Moving (Lap) Test
Segment a trajectory into laps and plot continuous, colored paths for each run.

#### What it does
* Scans every `run_*` folder under a user‑provided root directory.  
* For each `run_X`, reads all `*-fix.csv` files (e.g. `ublox_F9P-fix.csv`, `blabla-fix.csv`).  
* Segments each file’s latitude/longitude data into laps based on:
  - **distance threshold** (meters to close a lap)  
  - **minimum duration** (seconds before considering a lap closed)  
* Generates:
  1. **Per‑sensor plots**: `run_X_<sensor>_continuous_laps.png` (one PNG per sensor per run).  
  2. **Combined plot**: `run_X_combined_continuous_laps.png`, overlaying all sensors’ laps.  

All plots are saved in the `plots/` folder under the specified root.

#### How to run it
From the `GNSS/scripts/` directory:
```bash
python plot_gps_laps_from_csv.py \
  --data_dir /path/to/GNSS \
  [--run_distance_threshold 5.0] \
  [--min_run_duration 30.0]
```

**Arguments**  
- `--data_dir`              : Root folder containing `run_*` subdirectories (required).  
- `--run_distance_threshold`: Meters to close a lap (default: `5.0`).  
- `--min_run_duration`      : Min lap duration in seconds (default: `30.0`).  

**Example**  
```bash
python plot_gps_laps_from_csv.py \
  --data_dir ~/Documents/VAL/GNSS/git/DataAnalysisForRobotics \
  --run_distance_threshold 3.0 \
  --min_run_duration 20.0
```

After running, check the `plots/` folder at the project root for all generated PNGs.