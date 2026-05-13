# calculate_joint_angles

# Calculate Joint Angles

This repository provides a simple workflow for calculating joint angles from FreeMoCap-style 3D skeleton data.

The main script:

1. Loads a FreeMoCap recording
2. Builds a `Human` skeleton object using `skellymodels`
3. Calculates joint angles
4. Opens an interactive visualization of the skeleton, XYZ trajectories, and joint angles
5. Saves the calculated joint-angle data as a `.csv` file

---

## Installation

This project is designed to work with Python 3.11 or later.

### Recommended: install with `uv`

If you are using [`uv`](https://docs.astral.sh/uv/), you can set up the project with:

```bash
uv sync
```

Personally, highly recommend trying out uv. It's much quicker than pip.

This will create a local virtual environment and install the dependencies listed in `pyproject.toml`.

To run the script through `uv`, use:

```bash
uv run python main.py
```

If you want to manually activate the environment first:

On Windows PowerShell:

```bash
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Then run:

```bash
python main.py
```

---

### Alternative: install with `pip`

Because this project has a `pyproject.toml`, you can also install it with `pip`.

First create and activate a virtual environment with your method of choice (e.g. `venv`, `conda`, etc). Use Python 3.11 or 3.12.

Then install the project:

```bash
pip install -e .
```

If `skellymodels` does not install correctly through `pip`, install it directly from GitHub:

```bash
pip install git+https://github.com/aaroncherian/skellymodels
```

Then run:

```bash
python main.py
```

---

## Basic usage

The main script is designed to be edited directly for each recording.

At the bottom of `main.py`, update these two values:

```python
if __name__ == "__main__":
    path_to_recording = r"D:\validation\data\2025-11-04_ATC\2025-11-04_15-33-01_GMT-5_atc_treadmill_1"
    neutral_stance_frames = range(0, 100)

    main(path_to_recording, neutral_stance_frames)
```

---

## Parameters to adjust

### `path_to_recording`

This should be the path to the FreeMoCap recording folder you want to analyze.

For example:

```python
path_to_recording = r"D:\validation\data\2025-11-04_ATC\2025-11-04_15-33-01_GMT-5_atc_treadmill_1"
```

The script expects the 3D skeleton data to be located at:

```text
<recording_folder>/output_data/mediapipe_body_3d_xyz.npy
```

So if your recording folder is:

```text
D:\my_recordings\example_recording
```

then the script will look for:

```text
D:\my_recordings\example_recording\output_data\mediapipe_body_3d_xyz.npy
```

---

### `neutral_stance_frames`

This tells the joint-angle calculator which frames should be treated as the participant’s neutral standing posture.

For example:

```python
neutral_stance_frames = range(0, 100)
```

means that frames 0 through 99 will be used as the neutral reference posture.

This is useful because raw joint angles depend on how the skeleton coordinate systems are oriented. By providing a neutral stance, the script can subtract out the baseline posture and report joint angles relative to that starting pose.

Use this when the participant is standing still at the beginning of the recording.

If you do not want to normalize to a neutral stance, set:

```python
neutral_stance_frames = None
```

In that case, the joint angles will be calculated without subtracting a neutral-pose offset. 

---

## Visualization

The script opens an interactive browser-based visualization using:

```python
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
```

The visualizer includes:

1. A 3D skeleton view
2. XYZ trajectory plots
3. Joint-angle plots

---

### 3D skeleton viewer

The top section shows the reconstructed skeleton moving through time.

Use the playback controls at the bottom of the page to:

- Play/pause the animation
- Reset to the beginning
- Change playback speed
- Scrub through the recording frame by frame

---

### Turning data views on and off

The visualization includes buttons for different data views:

```text
XYZ trajectories
Joint angles
```

Click these buttons to show or hide each section.

This lets you look at only the skeleton, only the trajectories, only the angles, or both trajectories and angles together.

---

### XYZ trajectories

The XYZ trajectory section shows the position of a selected tracked point over time.

Use the marker dropdown to choose which point to inspect.

For example:

```text
left_knee
right_ankle
left_heel
```

The visualizer shows separate plots for:

```text
X
Y
Z
```

These correspond to the 3D coordinates of the selected point across the recording.

The vertical cursor line shows the current animation frame.

---

### Joint angles

The joint-angle section shows calculated joint angles over time.

Use the dropdowns to choose:

```text
Joint
Side
```

For example:

```text
Joint: Knee
Side: Both
```

The visualizer can show angle components such as:

```text
flex_ext
abd_add
int_ext
```

These correspond to flexion/extension, abduction/adduction, and internal/external rotation components when available.

The vertical cursor line shows the current animation frame.

---

## Choosing trajectory markers

The markers shown in the XYZ trajectory dropdown are controlled by this part of the script:

```python
trajectory_markers=[
    "left_hip", "left_knee", "left_ankle",
    "right_hip", "right_knee", "right_ankle",
    "left_heel", "right_heel",
]
```

You can add or remove markers from this list.

For example, to only show the knees and ankles:

```python
trajectory_markers=[
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
]
```

The marker names need to match the tracked point names in the skeleton model.

---

## Saving output data

After calculating the joint angles, the script saves the results with:

```python
save_data(angles_dataframe, path_to_recording, tracker="mediapipe")
```

The output is saved inside the recording folder at:

```text
<recording_folder>/output_data/data_analysis/joint_angles/mediapipe_joint_angles.csv
```

For example, if your recording is located at:

```text
D:\validation\data\example_recording
```

then the joint angles will be saved to:

```text
D:\validation\data\example_recording\output_data\data_analysis\joint_angles\mediapipe_joint_angles.csv
```

The folder will be created automatically if it does not already exist.

---

## Output CSV format

The saved joint-angle file is a long-format `.csv` file.

Each row contains one angle value for one frame, one side, one joint, and one angle component.

The columns are:

| Column | Description |
|---|---|
| `frame` | Frame number in the recording |
| `side` | Body side, usually `left` or `right` |
| `joint` | Joint name, such as `knee`, `hip`, or `ankle` |
| `angle` | Calculated joint angle value |
| `component` | Angle component, such as `flex_ext`, `abd_add`, or `int_ext` |

Example:

```csv
frame,side,joint,angle,component
0,right,knee,1.608961,flex_ext
0,right,knee,-0.681807,abd_add
0,right,knee,0.035615,int_ext
1,right,knee,0.825295,flex_ext
1,right,knee,-0.448415,abd_add
```

This format is useful because it works well with `pandas`, plotting libraries, and downstream analysis workflows.

For example, to load the saved data:

```python
import pandas as pd

angles = pd.read_csv(
    r"path\to\recording\output_data\data_analysis\joint_angles\mediapipe_joint_angles.csv"
)
```

To get only right knee flexion/extension:

```python
right_knee_flex_ext = angles[
    (angles["side"] == "right")
    & (angles["joint"] == "knee")
    & (angles["component"] == "flex_ext")
]
```

---

## Full workflow

A typical workflow is:

1. Update `path_to_recording`
2. Set `neutral_stance_frames`
3. Run the script
4. Inspect the skeleton, trajectories, and joint angles in the visualizer
5. Find the saved joint-angle `.csv` in:

```text
output_data/data_analysis/joint_angles/
```

## Notes
Because of the nature of joint angles with markerless data, I recommend some caution with intepreting inversion/eversion and abduction/adduction angles. These are often noisier than flexion/extension angles because we don't have as many reference points to correctly calculate all our necessary axes from, and may not be as reliable for downstream analysis.