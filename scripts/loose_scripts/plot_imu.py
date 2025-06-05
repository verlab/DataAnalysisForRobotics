
import matplotlib.pyplot as plt
from bagpy import bagreader
import pandas as pd
import numpy as np
import sys
import os
from tf.transformations import euler_from_quaternion
import gmplot
import rospkg 



#apikey = rospy.get_param('api_key','')


 
imu_topic ='/imu/data_raw'
#mag_topic = '/imu/mag'
odom_topic ='/lego_loam/odom'
#gps_topic = 'gps_topic','/reach/fix'


# Lists to store extracted data
time_imu_vals = []
mag_time_vals = []
orientation_yaw = []
position_x = []
position_y = []
coordinates = []
magnetic_field_module = []


def extract_imu(bagfile,file_name):
    
    # Read IMU data
    imu_csv_path = bagfile.message_by_topic(imu_topic)
    imu_data = pd.read_csv(imu_csv_path)

    # Extract quaternion components
    qx_list = imu_data['orientation.x'].values
    qy_list = imu_data['orientation.y'].values
    qz_list = imu_data['orientation.z'].values
    qw_list = imu_data['orientation.w'].values
    time_list = imu_data['Time'].values  # Extract time

    yaw_list = []
    for i in range(len(qx_list)):
        # Convert quaternion to Euler angles
        roll, pitch, yaw = euler_from_quaternion([qx_list[i], qy_list[i], qz_list[i], qw_list[i]])

        yaw_list.append((np.degrees(yaw)+360)%360)  # Convert yaw to degrees
    
    time_imu_vals.append((file_name,time_list[::10]))
    orientation_yaw.append((file_name,yaw_list[::10]))


def extract_odom(bagfile,file_name):
    
    # Read odometry data
    odom_csv_path = bagfile.message_by_topic(odom_topic)
    odom_data = pd.read_csv(odom_csv_path)

    global position_x, position_y
    position_x.append((file_name,odom_data['pose.pose.position.x'].values))
    position_y.append((file_name,odom_data['pose.pose.position.y'].values))

# def extract_magnetic_field(bagfile,file_name):
    
    
#     magnetic_csv_path = bagfile.message_by_topic(mag_topic)
#     magnetic_data = pd.read_csv(magnetic_csv_path)
    
#     x_list = magnetic_data['magnetic_field.x'].values
#     y_list = magnetic_data['magnetic_field.y'].values
#     z_list = magnetic_data['magnetic_field.z'].values
#     time_list = magnetic_data['Time'].values

#     global magnetic_field_module,mag_time_vals
    
#     magnetic_field_module_list = []
    
#     for i in range(len(x_list)):
#         magnetic_field_module_list.append(np.sqrt((x_list[i]*1e6)**2 + (y_list[i]*1e6)**2 + (z_list[i]*1e6)**2))
    
#     magnetic_field_module.append((file_name,magnetic_field_module_list[::10]))
#     mag_time_vals.append((file_name,time_list[::10]))
    
     
# def extract_gps (bagfile,file_name):
    
    
#     gps_csv_path = bagfile.message_by_topic(gps_topic)
#     gps_data = pd.read_csv(gps_csv_path)
    
#     gps_coordinates = []
    
#     for i in range(len(gps_data['latitude'].values)):
#         gps = (gps_data['latitude'].values[i],gps_data['longitude'].values[i])
#         gps_coordinates.append(gps)
        
#     coordinates.append((file_name,gps_coordinates))
    
    
        
    
# def plot_map():
#     global coordinates,apikey
   
#     gmap = gmplot.GoogleMapPlotter(coordinates[0][0], coordinates[0][1], 14, apikey=apikey)    
#     trajectory = zip(*coordinates)
#     gmap.polygon(*trajectory, color='cornflowerblue', edge_width=10)
#     gmap.draw(f"{PACKAGE_DIR}/graphs/map.html")
    
def plot():
    fig, axes = plt.subplots(2, 2, figsize=(8, 6))  # 2 rows, 1 column
    
    # Plot 1 - IMU Yaw
    contador_um = 0
    for orientation in orientation_yaw:

        axes[0][0].plot(time_imu_vals[contador_um][1], orientation[1])
        contador_um += 1
    axes[0][0].set_xlabel("Time (s)")
    axes[0][0].set_ylabel("Yaw (degrees)")
    axes[0][0].set_title("IMU Orientation - Yaw")
    axes[0][0].legend()
    axes[0][0].grid()

    # Plot 2 - Odometry
    contador_dois = 0
    for position in position_x:
        axes[0][1].plot(position[1], position_y[contador_dois][1])
        contador_dois+=1
    axes[0][1].set_xlabel("x (m)")
    axes[0][1].set_ylabel("y (m)")
    axes[0][1].set_title("Position - Odometry")
    axes[0][1].legend()
    axes[0][1].grid()
    
    # Plot 3 - Magnetic Field
    # contador_tres = 0
    # for magnetic in magnetic_field_module:
    #     axes[1][0].plot(mag_time_vals[contador_tres][1], magnetic[1])
    #     contador_tres += 1
    # axes[1][0].set_xlabel("Time (s)")
    # axes[1][0].set_ylabel("Magnetic Field Module (uT)")
    # axes[1][0].set_title("Magnetic Field Module")
    # axes[1][0].legend()
    # axes[1][0].grid()

    # Adjust layout
    plt.tight_layout()
    # Save the figure
    
    
    plt.savefig(f"{PACKAGE_DIR}/graphs/plot_imu_data.png")
    
    #plot_map()

    
    # Show the figure (optional)
    plt.show()


if __name__ == "__main__":
    # get params
    global imu_topic,mag_topic,odom_topic
    argv = sys.argv
    if len(argv) < 5:
        print("Usage: python plot_imu.py <bag_directory> <imu_topic> <mag_topic> <odom_topic>")
        sys.exit(1)
    
    imu_topic = argv[2]
    #mag_topic = argv[3]
    odom_topic = argv[4]

    # Construct the full path to the .bag file
    BAG_DIR = argv[1] + "/"
    bag_files = [f for f in os.listdir(BAG_DIR) if f.endswith('.bag')]

    for bagfile in bag_files:
        
        bagfile_dir = BAG_DIR + bagfile
        bag = bagreader(bagfile_dir)
        extract_imu(bag,bagfile)
        extract_odom(bag,bagfile)
        #extract_gps(bag,bagfile)
        extract_magnetic_field(bag,bagfile)
        # Read the bag file
    

    # Extract and plot data
    plot()

