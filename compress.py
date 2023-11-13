#!/usr/bin/env python3
"""
A script to automatically copy and compress videos in mounted volumes
"""
import sys
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta


logging.basicConfig(
    filename="message.log",
    format="%(asctime)s: %(levelname)s: %(message)s",
    level=logging.INFO,
)


def _is_video(file_dir: Path, extensions: list[str] = [".mp4", ".mov"]) -> bool:
    """
    Check if the given directory is a video file
    """
    assert file_dir.is_file(), f"{str(file_dir)} is not a file"
    return file_dir.suffix in extensions


def _is_recent(file_dir: Path, days: int = 1) -> bool:
    """
    Check if the given directory is recently created
    """
    assert days >= 1, "days must be at least one (for comparing timestamps"
    created_timestamp = datetime.fromtimestamp(file_dir.stat().st_ctime)
    return created_timestamp + timedelta(days=days) >= datetime.today()


def get_new_dir(origin_dir: Path, extension: str = ".mp4") -> Path:
    """
    Create a new file directory with the today's date
    """
    assert origin_dir.exists(), f"{str(origin_dir)} does not exist"
    new_name = datetime.today().isoformat() + extension
    return origin_dir.parent / new_name


def get_mounted_volumes() -> list[Path]:
    """
    Get a list of mounted volumes, for macOS only
    """
    assert sys.platform == "darwin", "this operation is only supported on macOS"
    logging.info("Searching for mounted volumes...")
    result = []
    for sub_dir in Path("/Volumes").iterdir():
        if sub_dir.name != "Macintosh HD" and not sub_dir.name.startswith("."):
            result.append(sub_dir)
    return result


def get_recent_videos(base_dir: Path, n_days: int = 1) -> list[Path]:
    """
    Get a list of recently created videos in a directory
    """
    assert base_dir.is_dir(), f"{str(base_dir)} is not a directory"
    logging.info("Searching for recently added videos...")
    result = []
    for sub_dir in base_dir.iterdir():
        if sub_dir.name.startswith("."):
            continue
        if sub_dir.is_dir():
            result.extend(get_recent_videos(sub_dir, n_days=n_days))
        elif _is_video(sub_dir) and _is_recent(sub_dir, days=n_days):
            result.append(sub_dir)
    return result


def copy_to_dir(source_dir: Path, target_dir: Path = Path.home() / "Movies") -> Path:
    """
    Copy the source file into another directory
    """
    assert target_dir.is_dir(), f"{str(source_dir)} is not a directory"
    logging.info(f"Copying {source_dir.name} to {str(target_dir)}...")
    command = ["rsync", "--progress", str(source_dir), str(target_dir)]
    process = subprocess.Popen(command)
    process.wait()
    return target_dir / source_dir.name


def run_handbrake(source_dir: Path, preset: str = "Fast 1080p30") -> Path:
    """
    Use the command line to run handbrake on the source
    """
    assert _is_video(source_dir), f"{str(source_dir)} is not a video"
    logging.info(f"Running HandBrake on {source_dir.name}...")
    new_dir = get_new_dir(source_dir)
    command = ["HandBrakeCLI", "-Z", preset, "-i", str(source_dir), "-o", str(new_dir)]
    process = subprocess.Popen(command)
    process.wait()
    return new_dir


def unmount_volumes(volumes_dir: list[Path]) -> list[Path]:
    """
    Use the command line to unmount attached volumes
    """
    done = []
    for volume in volumes_dir:
        logging.info(f"Unmounting {str(volume)}...")
        assert volume.is_dir(), f"{str(volume)} is not a directory"
        command = ["diskutil", "unmount", str(volume)]
        process = subprocess.Popen(command)
        process.wait()
        done.append(volume)
    return done


if __name__ == "__main__":
    volumes = get_mounted_volumes()
    videos = [video for volume in volumes for video in get_recent_videos(volume)]
    copied = [copy_to_dir(video) for video in videos]
    unmounted = unmount_volumes(volumes)
    assert len(volumes) == len(unmounted), "some volumes were not unmounted"
    compressed = [run_handbrake(video) for video in copied]
    assert len(videos) == len(compressed), "some videos were not compressed"
