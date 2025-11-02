# IMU-Based Pose Estimation with Deep Learning

A comprehensive system for human pose estimation using wearable IMU sensors and deep learning techniques. This project combines inertial measurement unit (IMU) data with computer vision-based pose estimation to create a robust, real-time pose tracking system.

**This project is part of a Master's thesis titled "Enhancing IMU Based Posture and Motion Estimation through Multi-Modal Training Using Video Posture Detection Models".**

## �� Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Data Collection](#data-collection)
- [Data Processing Pipeline](#data-processing-pipeline)
- [Model Training](#model-training)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Results](#results)
- [Contributing](#contributing)

## 🎯 Overview

This project implements a novel approach to human pose estimation by combining:

- **Wearable IMU sensors** (Seeed Studio XIAO NRF52840) for real-time motion data
- **Computer vision** (Sports2D) for ground truth pose estimation
- **Deep learning models** (LSTM networks) for sensor fusion and pose prediction

The system can predict joint angles and positions using only IMU data, making it suitable for applications where camera-based tracking is impractical or unavailable.

## ✨ Features

- **Multi-sensor fusion**: 5 IMU sensors positioned on key body segments
- **Real-time processing**: Bluetooth Low Energy (BLE) communication
- **Comprehensive data pipeline**: From raw sensor data to trained models
- **Multiple dataset variations**: Support for different sensor configurations
- **Automated preprocessing**: Complete pipeline from video to training data
- **Detailed logging**: Comprehensive experiment tracking and visualization
- **Modular architecture**: Easy to extend and modify

## 🔧 Prerequisites

### Hardware Requirements

- 5x IMU sensors
- Computer with Bluetooth capability
- Camera for video recording

### Software Requirements

- Python 3.8+
- Arduino IDE
- Sports2D software
- Required Python packages (see installation section)

## 📦 Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd masters
   ```
2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```
3. **Set up Arduino environment**

   - Install Arduino IDE
   - Add Seeed nRF52 board support
   - Install required libraries for IMU sensors
4. **Configure Sports2D**

   - Install Sports2D software
   - Configure camera calibration
   - Set up pose estimation parameters

## 📊 Data Collection

### IMU Sensor Setup

1. **Hardware Assembly**

   - Connect IMU sensors to XIAO NRF52840 boards
   - Position sensors on body segments:
     - Right wrist
     - Left wrist
     - Right ankle
     - Left ankle
     - Sternum
2. **Sensor Programming**

   - Upload appropriate firmware from `sensors_code/` directory
   - Each sensor has a unique identifier and sampling rate
   - Sensors transmit data via BLE
3. **Data Collection Process**

   ```bash
   python scripts/bluetooth_script.py
   ```

   - Script automatically discovers and connects to sensors
   - Creates new trial directory for each session
   - Saves raw IMU data as CSV files

### Video Recording

1. **Setup**

   - Position camera for full body view
   - Ensure good lighting and minimal occlusion
   - Record at 60 FPS for optimal Sports2D processing
2. **Processing**

   ```bash
   python scripts/preprocessing/video_preprocessing.py
   ```

   - Reduces frame rate to match IMU sampling
   - Converts format for Sports2D compatibility

## 🔄 Data Processing Pipeline

The complete data processing pipeline includes several stages:

### 1. Video Processing

- Frame rate reduction and format conversion
- Sports2D pose estimation
- Angle extraction and storage

### 2. IMU Data Processing

- Raw sensor data collection
- Synchronization across sensors
- Data normalization and filtering

### 3. Data Alignment

- Temporal alignment of IMU and video data
- Coordinate system transformation
- Quality control and validation

### 4. Dataset Creation

- Feature extraction from IMU data
- Label preparation from pose estimation
- Train/validation/test splits

### 5. Dataset Variations

Multiple dataset configurations are available:

- **Full dataset**: All sensors active
- **No left arm**: Excludes left arm sensor
- **No left leg**: Excludes left leg sensors
- **No left limbs**: Excludes all left side sensors
- **No sternum**: Excludes sternum sensor

## 🤖 Model Training

### Architecture

- **LSTM-based models** for temporal sequence processing
- **Multi-input networks** for sensor fusion
- **Regression output** for joint angle prediction

### Training Process

1. **Data Preparation**

   ```bash
   python scripts/preprocessing/align_imu_angles.py
   ```
2. **Model Training**

   ```bash
   python lstm.ipynb
   ```
3. **Hyperparameter Optimization**

   - Automated hyperparameter search
   - Cross-validation for model selection
   - Performance metrics tracking

### Evaluation Metrics

- **RMSE**: Root Mean Square Error for joint angles
- **MAE**: Mean Absolute Error
- **Per-joint analysis**: Individual joint performance
- **Visualization**: Training curves and prediction plots

## 🚀 Usage

### Quick Start

1. **Collect new data**

   ```bash
   python scripts/bluetooth_script.py
   ```
2. **Process data**

   ```bash
   bash scripts/run_all_preprocessing.sh
   ```
3. **Train model**

   ```bash
   jupyter notebook lstm.ipynb
   ```

### Advanced Usage

#### Custom Dataset Creation

```bash
python scripts/dataset_reduction/no_left_arm.py
```

#### Data Visualization

```bash
python scripts/visualization/plot_angles.py
python scripts/visualization/plotting_imu.py
```

#### Batch Processing

```bash
python scripts/preprocessing/run_sports2d_batch.py
```

## 📁 Project Structure

```
.
├── Config_Sports2D.toml          # Sports2D configuration
├── Config_TEMP.toml              # Temperature configuration
├── README.md                     # This file
├── dataset/                      # All datasets
│   ├── final_dataset/            # Processed training data
│   │   ├── trial_1/
│   │   │   ├── X.csv            # IMU features
│   │   │   └── Y.csv            # Joint angles
│   │   └── ...
│   └── intermediate_data/        # Processing stages
│       ├── aligned_dataset/      # Synchronized data
│       ├── angles_data/          # Pose estimation results
│       ├── imu_data/             # Raw sensor data
│       ├── sync_imu_data/        # Synchronized IMU data
│       └── wrapped_angles/       # Processed angles
│   └── reduced_dataset/          # Sensor ablation studies
├── logs/                         # Experiment logs
│   ├── run_YYYY-MM-DD_HH-MM-SS/ # Individual runs
│   │   ├── hyperparameters.json
│   │   ├── metrics.csv
│   │   ├── model_weights.pth
│   │   └── visualization plots
│   └── logs_saved.txt
├── lstm.ipynb                    # Main training notebook
├── scripts/                          # Processing scripts
│   ├── dataset_reduction/            # Dataset creation
│   │   ├── no_left_arm.py           # Remove left arm sensor data
│   │   ├── no_left_leg.py           # Remove left leg sensor data
│   │   ├── no_left_leg_arm.py       # Remove left arm and leg data
│   │   └── no_sternum.py            # Remove sternum sensor data
│   ├── preprocessing/                # Data processing
│   │   ├── align_imu_angles.py      # Synchronize IMU and angle data
│   │   ├── collect_dataset_files.py # Gather all dataset files
│   │   ├── collect_mot_files.py     # Collect Sports2D .mot files
│   │   ├── mot_to_csv.py            # Convert .mot files to CSV
│   │   ├── normalize_imu.py         # Normalize IMU sensor data
│   │   ├── run_sports2d_batch.py    # Batch process videos with Sports2D
│   │   ├── synchronize_imu_data.py  # Sync multiple IMU sensors
│   │   ├── video_preprocessing.py   # Process video files (fps, format)
│   │   ├── video_renaming.py        # Rename video files for consistency
│   │   └── wrap_angles.py           # Process and wrap joint angles
│   ├── visualization/                # Plotting tools
│   │   ├── plot_angles.py           # Visualize joint angles
│   │   └── plotting_imu.py          # Plot IMU sensor data
│   └── run_all_preprocessing.sh      # Complete pipeline automation
├── sensors_code/                 # Arduino firmware
│   ├── BT_imu1/                 # Sensor 1 firmware
│   ├── BT_imu2/                 # Sensor 2 firmware
│   └── ...
├── Sports2D_results/             # Pose estimation results
├── Sports2D_screenshots/         # Processing screenshots
└── videos_data/                  # Video recordings
```

## 📈 Results

### Performance Metrics

- **Average RMSE**: 4.88° across all joints
- **Best performing joints**: Pelvis, hip
- **Challenging joints**: Wrist, ankle

### Key Findings

- IMU-only pose estimation achieves competitive accuracy
- Multi-sensor fusion significantly improves performance
- Temporal modeling (LSTM) crucial for smooth predictions
- Sensor placement optimization critical for accuracy

### Visualization

- Training/validation curves
- Per-joint error analysis
- Prediction vs. ground truth plots
- Real-time pose visualization

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Submit a pull request**

## 📄 License

[Add your license information here]

## 🙏 Acknowledgments

- Seeed Studio for XIAO NRF52840 development boards
- Sports2D team for pose estimation software
- Open-source community for various libraries and tools

## 📞 Contact

Please reach out to me at miskmabdalla@gmail.com for any comments!

---

**Note**: This project is actively under development. Please check the issues page for known limitations and planned features.
