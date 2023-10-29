#!/usr/bin/env python3
"""
A script to automatically copy and compress videos in mounted volumes
"""
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta


def _is_video(file_dir: Path, extensions: list[str] = [".mp4", ".mov"]) -> bool:
    """
    Check if the given directory is a video file
    """
    assert file_dir.is_file()
    return file_dir.suffix in extensions


def _is_recent(file_dir: Path, days: int = 1) -> bool:
    """
    Check if the given directory is recently created
    """
    assert days >= 1  # cannot be negative or zero (since we are comparing timestmaps)
    created_timestamp = datetime.fromtimestamp(file_dir.stat().st_ctime)
    return created_timestamp + timedelta(days=days) >= datetime.today()


def get_new_dir(origin_dir: Path, extension: str = ".mp4") -> Path:
    """
    Create a new file directory with the today's date
    """
    assert origin_dir.exists()
    new_name = datetime.today().strftime("%Y%m%d") + extension
    return origin_dir.parent / new_name


def get_mounted_volumes() -> list[Path]:
    """
    Get a list of mounted volumes, for macOS only
    """
    assert sys.platform == "darwin", "this operation is only supported on macOS"
    result = []
    for sub_dir in Path("/Volumes").iterdir():
        if sub_dir.name != "Macintosh HD" and not sub_dir.name.startswith("."):
            result.append(sub_dir)
    return result


def get_recent_videos(base_dir: Path, n_days: int = 1) -> list[Path]:
    """
    Get a list of recently created videos in a directory
    """
    assert base_dir.is_dir()
    result = []
    for sub_dir in base_dir.iterdir():
        if sub_dir.name.startswith("."):
            continue
        if sub_dir.is_dir():
            result.extend(get_recent_videos(sub_dir, n_days=n_days))
        elif _is_video(sub_dir) and _is_recent(sub_dir, days=n_days):
            result.append(sub_dir)
    return result


def copy_to_dir(source_dir: Path, target_dir: Path = Path.home() / "Movies") -> bool:
    """
    Copy the source file into another directory
    """
    assert target_dir.is_dir()
    command = ["cp", str(source_dir), str(target_dir)]
    process = subprocess.Popen(command)
    process.wait()
    return process.stderr is None


def run_handbrake(source_dir: Path, preset: str = "Fast 1080p30") -> bool:
    """
    Use the command line to run handbrake on the source
    """
    assert _is_video(source_dir)
    new_dir = get_new_dir(source_dir)
    command = ["HandBrakeCLI", "-Z", preset, "-i", str(source_dir), "-o", str(new_dir)]
    process = subprocess.Popen(command)
    process.wait()
    return process.stderr is None


def unmount_volumes(volumes_dir: list[Path]) -> None:
    """
    Use the command line to unmount attached volumes
    """
    for volume in volumes_dir:
        assert volume.is_dir()
        command = ["diskutil", "unmount", str(volume)]
        result = subprocess.Popen(command)
        assert result.stderr is None


if __name__ == "__main__":
    volumes = get_mounted_volumes()
    videos = [video for volume in volumes for video in get_recent_videos(volume)]
    copied = [video for video in videos if copy_to_dir(video)]
    compressed = [video for video in videos if run_handbrake(video)]
    unmount_volumes(volumes)
