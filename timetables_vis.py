import cairo
import numpy as np
import subprocess

def generate_times_table_video(
    output_path="output.mp4",
    width=3840,
    height=2160,
    fps=60,
    duration=1, #sec
    num_starting_points=512,
    line_width=3,
    multiples_per_point=30,
    starting_angle=np.pi*2/8
):
    """
    Generate a times-table style video using Cairo and stream directly to ffmpeg.

    Parameters:
        output_path (str): File path to save video.
        width (int): Frame width in pixels.
        height (int): Frame height in pixels.
        fps (int): Frames per second.
        duration (float): Video duration in seconds.
        num_starting_points (int): Number of points around the circle.
        line_width (float): Width of lines.
        multiples_per_point (float): Granularity of multiples per starting point.
        starting_angle (float): Initial rotation of circle (radians).
    """
    FFMPEG_PATH = r"C:\Users\osoki\University of Michigan Dropbox\Oluka Okia\Oluka Okia files\Home\non-school\Audio Visualization\ffmpeg\bin\ffmpeg.exe"
    # ---------------- CALCULATED ----------------
    TAU = np.pi * 2
    CENTER = np.array([width / 2, height / 2])
    RADIUS = height / 3
    MIN_ANGLE_DELTA = np.finfo(np.float64).eps * 1e6
    LINE_EXTENSION_LENGTH = width * 3 / 4
    num_frames = int(fps * duration)

    # Starting angles and colors
    start_angles = np.arange(num_starting_points) / num_starting_points * TAU
    colors = np.clip(
        np.stack([
            (-np.abs((-start_angles + TAU / 2) % TAU - TAU / 2) + TAU / 3) * 6 / TAU,
            (-np.abs((-start_angles - TAU / 6) % TAU - TAU / 2) + TAU / 3) * 6 / TAU,
            (-np.abs((-start_angles + TAU / 6) % TAU - TAU / 2) + TAU / 3) * 6 / TAU,
        ], axis=1),
        0, 1
    )
    start_angles -= starting_angle

    multiples = np.linspace(1, num_starting_points + 1, num_frames)

    # ---------------- FFMPEG PIPE ----------------
    ffmpeg_cmd = [
        FFMPEG_PATH,
        "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgba",
        "-s", f"{width}x{height}",
        "-r", str(fps),
        "-i", "-",  # read from stdin
        "-c:v", "libx264",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        output_path
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    # ---------------- FRAME LOOP ----------------
    for frame_num, m in enumerate(multiples):
        delta_angles = (m * start_angles - start_angles) % TAU
        delta_angles = np.clip(delta_angles, MIN_ANGLE_DELTA, TAU - MIN_ANGLE_DELTA)
        end_angles = start_angles + delta_angles

        start_points = CENTER + RADIUS * np.stack([np.cos(start_angles), np.sin(start_angles)], axis=1)
        end_points = CENTER + RADIUS * np.stack([np.cos(end_angles), np.sin(end_angles)], axis=1)

        diffs = end_points - start_points
        unit_diffs = diffs / np.linalg.norm(diffs, axis=1, keepdims=True)
        start_points = start_points - unit_diffs * LINE_EXTENSION_LENGTH
        end_points = end_points + unit_diffs * LINE_EXTENSION_LENGTH

        # Cairo surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context(surface)

        cr.set_source_rgb(0, 0, 0)
        cr.paint()

        cr.set_operator(cairo.Operator.SCREEN)
        cr.set_line_width(line_width)

        for i in range(num_starting_points):
            cr.set_source_rgb(*colors[i])
            cr.move_to(*start_points[i])
            cr.line_to(*end_points[i])
            cr.stroke()

        proc.stdin.write(surface.get_data())

    proc.stdin.close()
    proc.wait()
    print(f"✅ Video saved as {output_path}")


if __name__ == "__main__":
    generate_times_table_video(duration=0.5)  # 60 frames at 60 fps
