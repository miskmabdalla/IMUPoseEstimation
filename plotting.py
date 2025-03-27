import os
import matplotlib.pyplot as plt
import pandas as pd

# Directory where IMU CSV files are stored
DATA_DIR = "imu_data"

def plot_imu_data(file_path):
    """
    Reads IMU data from a CSV file and plots acceleration & gyroscope values over time.
    """
    try:
        df = pd.read_csv(file_path)

        # Ensure correct column names
        if df.shape[1] != 7:
            print(f"Invalid CSV format: {file_path}")
            return

        df.columns = ["Timestamp", "AccelX", "AccelY", "AccelZ", "GyroX", "GyroY", "GyroZ"]
        df["Timestamp"] -= df["Timestamp"].iloc[0]  # Convert timestamp to relative time

        # Create a new figure for each file
        plt.figure(figsize=(12, 5))

        # Plot acceleration data
        plt.subplot(2, 1, 1)
        plt.plot(df["Timestamp"], df["AccelX"], label="Accel X", color="r")
        plt.plot(df["Timestamp"], df["AccelY"], label="Accel Y", color="g")
        plt.plot(df["Timestamp"], df["AccelZ"], label="Accel Z", color="b")
        plt.ylabel("Acceleration (m/s²)")
        plt.legend()
        plt.title(f"Accelerometer Data - {os.path.basename(file_path)}")

        # Plot gyroscope data
        plt.subplot(2, 1, 2)
        plt.plot(df["Timestamp"], df["GyroX"], label="Gyro X", color="r")
        plt.plot(df["Timestamp"], df["GyroY"], label="Gyro Y", color="g")
        plt.plot(df["Timestamp"], df["GyroZ"], label="Gyro Z", color="b")
        plt.ylabel("Gyroscope (°/s)")
        plt.xlabel("Time (s)")
        plt.legend()
        plt.title(f"Gyroscope Data - {os.path.basename(file_path)}")

        plt.tight_layout()

    except Exception as e:
        print(f"Error reading file {file_path}: {e}")

def plot_all_imu_data():
    """
    Loops over all CSV files in the imu_data folder and plots them.
    """
    if not os.path.exists(DATA_DIR):
        print(f"Error: Data directory '{DATA_DIR}' does not exist.")
        return

    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]

    if not files:
        print("No CSV files found in the imu_data folder.")
        return

    for file in files:
        file_path = os.path.join(DATA_DIR, file)
        print(f"Plotting data from {file_path}...")
        plot_imu_data(file_path)

    # Show all figures at once (Navigation arrows will appear)
    plt.show()

# Run the function to plot all IMU data
plot_all_imu_data()
