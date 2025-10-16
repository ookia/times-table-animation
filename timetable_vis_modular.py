import cairo
import numpy as np
import subprocess


def generate_times_table_video(
    output_path="output.mp4",
    width=3840,
    height=2160,
    fps=60,
    duration=5,
    num_starting_points=512,
    line_width=2.5,
    base_multiplier=1.0,
    radius_ratio=1/3,
    starting_angle=np.pi * 2 / 8,
    blend_mode="screen",
    color_mode="spectrum",
    line_opacity=1.0,
    controllers=None,  # 👈 new: dict of functions or time-dependent parameter arrays
):
    """
    Modular, audio-reactive-ready times-table generator.
    """

    FFMPEG_PATH = (
        r"C:\Users\osoki\University of Michigan Dropbox\Oluka Okia\Oluka Okia files\Home\non-school\Audio Visualization\ffmpeg\bin\ffmpeg.exe"
    )

    TAU = np.pi * 2
    CENTER = np.array([width / 2, height / 2])
    RADIUS = height * radius_ratio
    LINE_EXTENSION_LENGTH = width * 3 / 4
    MIN_ANGLE_DELTA = np.finfo(np.float64).eps * 1e6
    num_frames = int(fps * duration)

    start_angles = np.arange(num_starting_points) / num_starting_points * TAU
    start_angles -= starting_angle

    # Base color wheel
    base_colors = np.clip(
        np.stack(
            [
                (-np.abs((-start_angles + TAU / 2) % TAU - TAU / 2) + TAU / 3)
                * 6 / TAU,
                (-np.abs((-start_angles - TAU / 6) % TAU - TAU / 2) + TAU / 3)
                * 6 / TAU,
                (-np.abs((-start_angles + TAU / 6) % TAU - TAU / 2) + TAU / 3)
                * 6 / TAU,
            ],
            axis=1,
        ),
        0, 1,
    )

    # ---------------- PARAMETER CONTROLLERS ----------------
    # Each parameter can be static, a callable, or an array of values per frame
    def get_param(name, frame, default):
        if controllers and name in controllers:
            val = controllers[name]
            if callable(val):
                return val(frame / fps)
            elif isinstance(val, (list, np.ndarray)):
                idx = min(frame, len(val) - 1)
                return val[idx]
            else:
                return val
        return default

    # ---------------- FFMPEG PIPE ----------------
    ffmpeg_cmd = [
        FFMPEG_PATH,
        "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgba",
        "-s", f"{width}x{height}",
        "-r", str(fps),
        "-i", "-",  # stdin
        "-c:v", "libx264",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        output_path,
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    # ---------------- FRAME LOOP ----------------
    for frame in range(num_frames):
        t = frame / fps

        # These will be reactive later
        multiplier = get_param("multiplier", frame, base_multiplier + 0.5 * np.sin(t))
        radius_scale = get_param("radius_ratio", frame, radius_ratio)
        color_shift = get_param("color_shift", frame, 0)
        opacity = get_param("line_opacity", frame, line_opacity)
        lw = get_param("line_width", frame, line_width)

        R = height * radius_scale

        delta_angles = (multiplier * start_angles - start_angles) % TAU
        delta_angles = np.clip(delta_angles, MIN_ANGLE_DELTA, TAU - MIN_ANGLE_DELTA)
        end_angles = start_angles + delta_angles

        start_points = CENTER + R * np.stack([np.cos(start_angles), np.sin(start_angles)], axis=1)
        end_points = CENTER + R * np.stack([np.cos(end_angles), np.sin(end_angles)], axis=1)

        diffs = end_points - start_points
        unit_diffs = diffs / np.linalg.norm(diffs, axis=1, keepdims=True)
        start_points -= unit_diffs * LINE_EXTENSION_LENGTH
        end_points += unit_diffs * LINE_EXTENSION_LENGTH

        # Cairo surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context(surface)
        cr.set_source_rgb(0, 0, 0)
        cr.paint()

        if blend_mode == "screen":
            cr.set_operator(cairo.Operator.SCREEN)

        cr.set_line_width(lw)

        # Color adjustment
        colors = np.roll(base_colors, int(color_shift), axis=0)
        for i in range(num_starting_points):
            cr.set_source_rgba(*colors[i], opacity)
            cr.move_to(*start_points[i])
            cr.line_to(*end_points[i])
            cr.stroke()

        proc.stdin.write(surface.get_data())

    proc.stdin.close()
    proc.wait()
    print(f"✅ Saved {output_path}")


if __name__ == "__main__":
    # Test version — will look smooth but is audio-ready.
    generate_times_table_video(
        duration=4,
        controllers={
            "multiplier": lambda t: 2 + np.sin(2 * np.pi * t * 0.3),
            "color_shift": lambda t: int(80 * np.sin(2 * np.pi * t * 0.1)),
            "radius_ratio": lambda t: 1/3 + 0.05 * np.sin(2 * np.pi * t * 0.5),
        },
    )
