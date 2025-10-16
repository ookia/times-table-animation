import glob
from pathlib import Path
import subprocess

FRAMES_DIR = Path(__file__).parent / 'frames'
OUTPUT_PATH = Path(__file__).parent / 'video.mov'
FPS = 60

# Set `FFMPEG_PATH` to the local path of your installation of ffmpeg.
# I use the Homebrew version: https://formulae.brew.sh/formula/ffmpeg
FFMPEG_PATH = glob.glob(r"C:\Users\osoki\University of Michigan Dropbox\Oluka Okia\Oluka Okia files\Home\non-school\Audio Visualization\ffmpeg\bin\ffmpeg.exe")[-1]


def main():
    frames_pattern = FRAMES_DIR / 'frame_%d.png'
    args = [
        FFMPEG_PATH,
        '-y',
        '-f',
        'image2',
        '-framerate',
        str(FPS),
        '-i',
        frames_pattern,
        '-c:v', 'libx264',
        '-crf', '18',
        '-pix_fmt', 'yuv420p',
        OUTPUT_PATH,
    ]

    print(f'Writing video...')
    subprocess.run(args)


if __name__ == '__main__':
    main()
