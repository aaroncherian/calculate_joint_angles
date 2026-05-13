"""
Skeleton Data Viewer
====================
A lightweight browser viewer for a skellymodels Human object plus optional
joint-angle and XYZ trajectory plots.

Usage from your script:

    from skeleton_data_viewer import visualize_data

    angles_dataframe = calculate_joint_angles(human, neutral_stance_frames=neutral_stance_frames)

    visualize_data(
        human=human,
        angles_dataframe=angles_dataframe,
        trajectory_markers=["left_hip", "left_knee", "left_ankle", "right_hip", "right_knee", "right_ankle"],
        fps=30,
    )
"""

from __future__ import annotations

import json
import socket
import tempfile
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from skellymodels.managers.human import Human


DEFAULT_TRAJECTORY_MARKERS = [
    "left_hip", "left_knee", "left_ankle", "left_heel", "left_foot_index",
    "right_hip", "right_knee", "right_ankle", "right_heel", "right_foot_index",
]


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _get_human_positions(human: Human) -> np.ndarray:
    """Return skeleton xyz data as frames x landmarks x 3."""
    positions = human.body.xyz.as_array
    positions = np.asarray(positions, dtype=float)
    if positions.ndim != 3 or positions.shape[2] != 3:
        raise ValueError(f"Expected Human body xyz data with shape frames x landmarks x 3, got {positions.shape}")
    return positions


def _get_landmark_names(human: Human) -> list[str]:
    return list(human.body.anatomical_structure.landmark_names)


def _convert_connections(human: Human, landmark_names: list[str]) -> list[list[str]]:
    """Convert skellymodels segment connections to JS-friendly landmark-name pairs."""
    valid = set(landmark_names)
    segment_connections = human.body.anatomical_structure.segment_connections
    connections: list[list[str]] = []

    for seg in segment_connections.values():
        proximal = seg.get("proximal") if isinstance(seg, dict) else getattr(seg, "proximal", None)
        distal = seg.get("distal") if isinstance(seg, dict) else getattr(seg, "distal", None)
        if proximal in valid and distal in valid:
            connections.append([proximal, distal])

    return connections


def _joint_angles_to_payload(angles_dataframe: pd.DataFrame | None) -> dict | None:
    """
    Convert a long-format joint angle dataframe into a JS-friendly payload.

    Expected columns:
        frame, side, joint, component, angle
    """
    if angles_dataframe is None or angles_dataframe.empty:
        return None

    required = {"frame", "side", "joint", "component", "angle"}
    missing = required - set(angles_dataframe.columns)
    if missing:
        raise ValueError(f"angles_dataframe is missing required columns: {sorted(missing)}")

    df = angles_dataframe.copy()
    df["frame"] = df["frame"].astype(int)
    df["side"] = df["side"].astype(str).str.lower()
    df["joint"] = df["joint"].astype(str).str.lower()
    df["component"] = df["component"].astype(str).str.lower()
    df["angle"] = pd.to_numeric(df["angle"], errors="coerce")

    max_frame = int(df["frame"].max())
    data: dict[str, list[float | None]] = {}

    for (side, joint, component), group in df.groupby(["side", "joint", "component"], sort=True):
        key = f"{side}_{joint}_{component}"
        arr: list[float | None] = [None] * (max_frame + 1)
        for row in group.itertuples(index=False):
            val = None if pd.isna(row.angle) else float(row.angle)
            arr[int(row.frame)] = val
        data[key] = arr

    return {
        "joints": sorted(df["joint"].dropna().unique().tolist()),
        "components": sorted(df["component"].dropna().unique().tolist()),
        "sides": sorted(df["side"].dropna().unique().tolist()),
        "data": data,
    }


def _trajectories_to_payload(
    positions: np.ndarray,
    landmark_names: list[str],
    trajectory_markers: Iterable[str] | None,
) -> dict | None:
    if trajectory_markers is None:
        trajectory_markers = DEFAULT_TRAJECTORY_MARKERS

    name_to_idx = {name: i for i, name in enumerate(landmark_names)}
    requested = [name for name in trajectory_markers if name in name_to_idx]
    if not requested:
        return None

    frames = positions.shape[0]
    x = list(range(frames))
    data: dict[str, dict[str, list[float | None]]] = {}

    for marker in requested:
        marker_xyz = positions[:, name_to_idx[marker], :]
        data[marker] = {
            "x": [None if np.isnan(v) else float(v) for v in marker_xyz[:, 0]],
            "y": [None if np.isnan(v) else float(v) for v in marker_xyz[:, 1]],
            "z": [None if np.isnan(v) else float(v) for v in marker_xyz[:, 2]],
        }

    return {"markers": requested, "frames": x, "data": data}


def _build_payload(
    human: Human,
    angles_dataframe: pd.DataFrame | None,
    trajectory_markers: Iterable[str] | None,
    fps: int | float,
) -> dict:
    positions = _get_human_positions(human)
    landmark_names = _get_landmark_names(human)
    connections = _convert_connections(human, landmark_names)

    joint_angles = _joint_angles_to_payload(angles_dataframe)
    trajectories = _trajectories_to_payload(positions, landmark_names, trajectory_markers)

    return {
        "viewer_name": "Skeleton Data Viewer",
        "tracker": getattr(human, "name", None) or getattr(human, "tracker", None) or "skeleton",
        "fps": fps,
        "positions": positions.tolist(),
        "landmarks": landmark_names,
        "connections": connections,
        "joint_angles": joint_angles,
        "trajectories": trajectories,
    }


def visualize_data(
    human: Human,
    angles_dataframe: pd.DataFrame | None = None,
    *,
    trajectory_markers: Iterable[str] | None = None,
    fps: int | float = 30,
    host: str = "127.0.0.1",
    port: int | None = None,
    open_browser: bool = True,
):
    """
    Open a browser-based viewer for a Human skeleton plus optional plot rows.

    Parameters
    ----------
    human:
        A skellymodels Human object.
    angles_dataframe:
        Long-format dataframe from calculate_joint_angles(). Expected columns:
        frame, side, joint, component, angle.
    trajectory_markers:
        Landmark names to show in XYZ trajectory plots. If omitted, tries a useful
        lower-body default list. Missing names are ignored.
    fps:
        Playback framerate.
    open_browser:
        Whether to open the viewer URL automatically.

    Notes
    -----
    This call blocks while the local server is running. Press Ctrl+C in the
    terminal to stop it.
    """
    payload = _build_payload(
        human=human,
        angles_dataframe=angles_dataframe,
        trajectory_markers=trajectory_markers,
        fps=fps,
    )
    payload_bytes = json.dumps(payload, allow_nan=False).encode("utf-8")

    viewer_html = Path(__file__).with_name("skeleton_data_viewer.html")
    if not viewer_html.exists():
        raise FileNotFoundError(f"Could not find viewer HTML next to this file: {viewer_html}")

    tmpdir = Path(tempfile.mkdtemp(prefix="skeleton_data_viewer_"))
    tmp_html = tmpdir / "skeleton_data_viewer.html"
    tmp_html.write_text(viewer_html.read_text(encoding="utf-8"), encoding="utf-8")

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(tmpdir), **kwargs)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/data.json":
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(payload_bytes)))
                self.end_headers()
                self.wfile.write(payload_bytes)
                return
            return super().do_GET()

        def log_message(self, format, *args):
            # Keep console mostly quiet.
            if "data.json" in str(args):
                return
            super().log_message(format, *args)

    port = port or _pick_free_port()
    url = f"http://{host}:{port}/skeleton_data_viewer.html"

    print("\n" + "═" * 60)
    print("  Skeleton Data Viewer")
    print(f"  Frames:  {len(payload['positions'])} @ {fps} Hz")
    print(f"  Points:  {len(payload['landmarks'])}")
    print(f"  Angles:  {'yes' if payload['joint_angles'] else 'no'}")
    print(f"  XYZ:     {'yes' if payload['trajectories'] else 'no'}")
    print(f"  Viewer:  {url}")
    print("═" * 60 + "\n")

    server = ThreadingHTTPServer((host, port), Handler)
    if open_browser:
        threading.Timer(0.3, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping viewer...")
    finally:
        server.server_close()
