from pathlib import Path
import re
import subprocess
from types import FrameType
from tqdm import tqdm
from Foundation import NSFileManager, NSURL
from argparse import ArgumentParser, Namespace
import signal


file_manager = NSFileManager.defaultManager()
subprocesses: list[subprocess.Popen] = []


def delete_file(file: Path):
    file_url = NSURL.fileURLWithPath_(str(file.resolve()))
    result = file_manager.trashItemAtURL_resultingItemURL_error_(file_url, None, None)
    if not result[0]:
        raise OSError(result[2].localizedFailureReason())


def get_video_files(dir: Path):
    video_files = [
        f
        for f in tqdm(dir.iterdir(), unit="files", desc="Collecting Files")
        if f.suffix == ".mov"
    ]
    video_files.sort()
    return video_files


def get_video_duration(file: Path):
    ffprobe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file,
        ],
        capture_output=True,
        text=True,
    )
    return float(ffprobe.stdout)


def parse_duration(duration: str):
    parts = duration.split(":")
    d = float(parts[0]) * 60 * 60
    d += float(parts[1]) * 60
    d += float(parts[2])
    return d


def convert_video(input_file: Path, output_video_path: Path):
    file_name = input_file.name
    additional_output = ""
    with tqdm(
        total=get_video_duration(input_file),
        unit="seconds",
        unit_scale=True,
        desc=file_name,
    ) as pbar:
        ffmpeg = subprocess.Popen(
            [
                "ffmpeg",
                f"-i",
                f"{input_file}",
                "-c:v",
                "libx265",
                "-preset",
                "veryfast",
                "-tag:v",
                "hvc1",
                f"{Path(output_video_path,file_name)}",
            ],
            bufsize=1,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        subprocesses.append(ffmpeg)
        while ffmpeg.poll() is None:
            line = ffmpeg.stderr.readline().replace("\n", "")
            if line.startswith("frame"):
                pattern = r"(\w+)=\s*(\d+:\d+:\d+\.\d+|\d+\.\d+|\d+)"
                matches = re.findall(pattern, line)
                line_info = {
                    key: value if value.isdigit() or "." in value else value
                    for key, value in matches
                }
                pbar.n = parse_duration(line_info["time"])
                pbar.refresh()
            else:
                additional_output += line + "\n"

        returncode = ffmpeg.wait()
        if returncode != 0:
            tqdm.write(additional_output)
            raise subprocess.CalledProcessError(returncode, ffmpeg.args)
        else:
            delete_file(input_file)


def parse_arguments() -> Namespace:
    # Create the parser
    parser = ArgumentParser(description="Reencode videos to a more efficient format")

    # Add the '-i' argument
    parser.add_argument("-i", type=Path, help="input folder location")

    # Parse the arguments
    args = parser.parse_args()
    return args


def stop_subprocesses(sig: int, frame: FrameType | None):
    for process in subprocesses:
        tqdm.write("Terminating process")
        process.terminate()
        process.wait()
    raise KeyboardInterrupt()


def main():
    args = parse_arguments()
    src_video_path: Path = args.i
    output_video_path = Path(src_video_path, "videoOutput")

    signal.signal(signal.SIGINT, stop_subprocesses)

    if src_video_path.exists():
        if not output_video_path.exists():
            output_video_path.mkdir()
        video_files = get_video_files(src_video_path)
        for input_file in tqdm(video_files, unit="files", desc="Converting Files"):
            convert_video(input_file, output_video_path)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        for process in subprocesses:
            process.terminate()
        raise e
