# Work in Progress

Pose estimation using IMUs and deep learning





## Prerecs


## How to run


## How it works

Using Seeed studio XIAO NRF52840 IMU sensors, 

Sensors are connected using BLE using the code in sensors/bluetooth_imu/, where the script in scripts/bluetooth_script.py looks through the bluetooth devices and connects to the sensors. It writes the IMU data in a csv respective to the sensor it is recieving the data from. Each time the script runs it creates a new trial_X directory, where all the IMU data from that session is stored.

Videos are recorded then transferred to my laptop, where I run scripts/preprocessing/video_preprocessing.py where I reduce the frame rate to match the sampling rate from the IMUs, and change the extension from .mov to .mp4. The videos are then ran through Sports2D to estimate the pose. I store the angles in .mot files in dataset/angles_data/mot_files/. I then run the script scripts/preprocessing/mot_to_csv.py that loops over the .mot files in the mot_files directory and saves them as .csv in dataset/angles_data/csv_files/ to make it easier to load as input for the model.



## Directory tree WIP


``` bash
.
├── Config_demo.toml
├── README.md
├── __pycache__
│   └── IMU_sensor.cpython-39.pyc
├── dataset
│   ├── angles_data
│   │   ├── csv_files
│   │       ├── trial_1.csv
│   │       ├── trial_2.csv
│   │       ├── trial_3.csv
│   │       └── ...
│   │   └── mot_files
│   │       ├── trial_1.mot
│   │       ├── trial_2.mot
│   │       ├── trial_3.mot
│   │       └── ...
│   └── imu_data
│       ├── trial_1
│       │   ├── 1B46F1B4-A2D2-6E21-BF55-2981B4B35216.csv
│       │   └── C22972B9-EA89-C4CD-E9F5-6369FB2653E6.csv
│       │   └── ...
│       ├── trial_2
│       │   ├── 1B46F1B4-A2D2-6E21-BF55-2981B4B35216.csv
│       │   └── C22972B9-EA89-C4CD-E9F5-6369FB2653E6.csv
│       │   └── ...
│       ├── trial_3
│       │   ├── 1B46F1B4-A2D2-6E21-BF55-2981B4B35216.csv
│       │   └── C22972B9-EA89-C4CD-E9F5-6369FB2653E6.csv
│       │   └── ...
│       └── ...
├── lstm.ipynb
├── scripts
│   ├── bluetooth_script.py
│   ├── preprocessing
│   │   ├── mot_to_csv.py
│   │   └── video_preprocessing.py
│   └── visualization
│       └── plotting_imu.py
├── sensors
│   ├── HighLevelExample
│   │   └── HighLevelExample.ino
│   ├── IMU_Capture
│   │   └── IMU_Capture.ino
│   ├── bluetooth
│   │   └── bluetooth.ino
│   └── bluetooth IMU
│       ├── BT_imu1
│       │   └── BT_imu1.ino
│       └── BT_imu2
│           └── BT_imu2.ino
│       └── ...
└── videos_data
    ├── 50_fps
    │   ├── trial_1.mp4
    │   ├── trial_2.mp4
    │   ├── trial_3.mp4
    │   └── ...
    └── 60_fps
        ├── trial_1.mp4
        ├── trial_2.mp4
        ├── trial_3.mp4
        └── ...
```
