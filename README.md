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