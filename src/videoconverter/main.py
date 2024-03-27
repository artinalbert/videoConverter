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
        f for f in tqdm(dir.iterdir(), desc="Collecting Files") if f.suffix == ".mov"
    ]
    video_files.sort()
    return video_files


def convert_video(input_file: Path, output_video_path: Path):
    with tqdm(total=None, unit="frames", unit_scale=True) as pbar:
        file_name = input_file.name
        tqdm.write(f"Converting {file_name}")
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
                pattern = r"(\w+)=\s*([0-9]+(?:\.[0-9]*)?|[0-9]*\.[0-9]+)([a-zA-Z%]*)"
                matches = re.findall(pattern, line)
                line_info = {
                    key: float(value) if value.isdigit() or "." in value else value
                    for key, value, unit in matches
                }
                pbar.n = line_info["frame"]
                pbar.update()
            else:
                tqdm.write(line)

        returncode = ffmpeg.wait()
        if returncode != 0:
            raise subprocess.CalledProcessError(returncode, ffmpeg.args)


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
        for input_file in tqdm(video_files, desc="Converting Files"):
            convert_video(input_file, output_video_path)


if __name__ == "__main__":
    main()
