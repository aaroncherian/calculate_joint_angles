from pathlib import Path
import numpy as np
import pandas as pd

from skellymodels.managers.human import Human
from skellymodels.models.tracking_model_info import ModelInfo

from calculations.calculate_joint_angles import calculate_joint_angles
from visualize_data.skeleton_data_viewer import visualize_data


def load_data(path_to_recording:str|Path, tracker = "mediapipe") -> Human:
    path_to_recording = Path(path_to_recording)

    path_to_3d_data = path_to_recording/"output_data"/"mediapipe_body_3d_xyz.npy"

    data = np.load(path_to_3d_data)

    path_to_model_folder = Path(__file__).parent/'model_info'
    model_info = ModelInfo.from_config_path(path_to_model_folder/"mediapipe_model_info.yaml")

    return Human.from_tracked_points_numpy_array(
        name = f"{tracker}",
        model_info=model_info,
        tracked_points_numpy_array=data
    ) 


def save_data(
        angles_dataframe: pd.DataFrame,
        path_to_recording: str|Path,
        tracker = "mediapipe"
):
    path_to_recording = Path(path_to_recording)

    path_to_analysis_folder = path_to_recording/"output_data"/"data_analysis"
    path_to_analysis_folder.mkdir(parents=True, exist_ok=True)

    path_to_joint_angles_data = path_to_analysis_folder/"joint_angles"
    path_to_joint_angles_data.mkdir(parents=True, exist_ok=True)
    angles_dataframe.to_csv(path_to_joint_angles_data/f"{tracker}_joint_angles.csv", index=False)

path_to_recording = r"D:\validation\data\2025-11-04_ATC\2025-11-04_15-33-01_GMT-5_atc_treadmill_1"
neutral_stance_frames = range(0,100) #set to some range where the person is standing still to normalize joint angles OR use neutral_stance_frames = None

human:Human = load_data(path_to_recording=path_to_recording)

angles_dataframe = calculate_joint_angles(human, 
                                          neutral_stance_frames=neutral_stance_frames)

visualize_data(
    human=human,
    angles_dataframe=angles_dataframe,
    trajectory_markers=[
        "left_hip", "left_knee", "left_ankle",
        "right_hip", "right_knee", "right_ankle",
        "left_heel", "right_heel",
    ],
    fps=30,
)


save_data(angles_dataframe, path_to_recording, tracker="mediapipe")




f= 2




