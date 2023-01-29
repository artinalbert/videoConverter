from pathlib import Path
import subprocess


def main():
    src_video_path = Path("/Users/artin/Downloads")
    if src_video_path.exists():
        for i in src_video_path.iterdir():
            if i.suffix == ".mov":
                output = Path("/Users/artin/Downloads/videoOutput")
                file_name = i.name
                if not output.exists():
                    output.mkdir()
                ffmpeg = subprocess.run(
                    [
                        "ffmpeg",
                        f"-i",
                        f"{i}",
                        "-c:v",
                        "libx265",
                        "-preset",
                        "veryfast",
                        "-tag:v",
                        "hvc1",
                        f"{Path(output,file_name)}",
                    ],
                    check=False,
                    capture_output=True,
                )
                print(ffmpeg.stdout)
                print(ffmpeg.stderr)
                # exit()


if __name__ == "__main__":
    main()
