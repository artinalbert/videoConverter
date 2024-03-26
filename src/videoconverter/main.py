from pathlib import Path
import subprocess
from tqdm import tqdm
from Foundation import NSFileManager, NSURL


file_manager = NSFileManager.defaultManager()

def delete_file(file: Path):
    file_url = NSURL.fileURLWithPath_(str(file.resolve()))
    result = file_manager.trashItemAtURL_resultingItemURL_error_(file_url, None, None)
    if not result[0]:
        raise OSError(result[2].localizedFailureReason())


def get_video_files(dir: Path):
    video_files = [f for f in tqdm(dir.iterdir(), desc="Collecting Files") if f.suffix == ".mov"]
    video_files.sort()
    return video_files

def convert_video(input_file: Path, output_video_path: Path):
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
        text=True
    )
    while ffmpeg.poll() is not None or ffmpeg:
        tqdm.write(ffmpeg.stdout.readline())

    # ffmpeg = subprocess.run(
    #     [
    #         "ffmpeg",
    #         f"-i",
    #         f"{input_file}",
    #         "-c:v",
    #         "libx265",
    #         "-preset",
    #         "veryfast",
    #         "-tag:v",
    #         "hvc1",
    #         f"{Path(output_video_path,file_name)}",
    #     ],
    #     check=False,
    #     capture_output=True,
    # )
    # tqdm.write(ffmpeg.stdout.decode())
    # tqdm.write(ffmpeg.stderr.decode())
    # if ffmpeg.returncode != 0:
    #     raise Exception("Process failed")
    # delete_file(input_file)

def main():
    src_video_path = Path("/Users/artin/Desktop")
    output_video_path = Path("/Users/artin/Desktop/videoOutput")

    if src_video_path.exists():
        if not output_video_path.exists():
            output_video_path.mkdir()
        video_files = get_video_files(src_video_path)
        for input_file in tqdm(video_files, desc="Converting Files"):
            convert_video(input_file, output_video_path)


if __name__ == "__main__":
    main()
