"""Generate a waving flag effect GIF from a source image.

Usage:
    python Waving_Flag_Generator.py input.png
    python Waving_Flag_Generator.py input.png output.gif --frames 24 --duration 45

How it works:
1. Load the source image with Pillow.
2. Split the image into thin vertical strips.
3. Shift each strip up or down using a sine wave.
4. Repeat that process across a sequence of phases to create animation frames.
5. Save the frames as a looped GIF.

The result is a vertical waving effect that works well for banners, flags, and flat artwork.
"""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
from statistics import mean

try:
    from PIL import Image, ImageStat
except ImportError as exc:  # pragma: no cover - handled at runtime for the user
    raise SystemExit(
        "Pillow is required. Install it with: pip install Pillow"
    ) from exc


def parse_args() -> argparse.Namespace:
    # All animation controls are exposed as command-line flags so the script can be
    # reused for different images without editing the source code.
    parser = argparse.ArgumentParser(
        description="Generate a waving flag effect GIF from a still image."
    )
    parser.add_argument("input_image", help="Path to the source image file.")
    parser.add_argument(
        "output_gif",
        nargs="?",
        help="Output GIF path. Defaults to <input_stem>_waving.gif.",
    )
    parser.add_argument("--frames", type=int, default=24, help="Number of frames to render.")
    parser.add_argument(
        "--duration",
        type=int,
        default=205,
        help="Frame duration in milliseconds.",
    )
    parser.add_argument(
        "--amplitude",
        type=float,
        default=10.0,
        help="Maximum vertical wave offset in pixels.",
    )
    parser.add_argument(
        "--wavelength",
        type=float,
        default=200.0,
        help="Wave length in pixels from crest to crest.",
    )
    parser.add_argument(
        "--band-height",
        type=int,
        default=1,
        help="Width of each vertical strip used to build the wave.",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Optional scale factor applied before animation.",
    )
    return parser.parse_args()


def build_output_path(input_path: Path, output_arg: str | None) -> Path:
    # If the caller supplies an output file, respect it. Otherwise, create a sibling
    # GIF named after the source image so the default behavior is predictable.
    if output_arg:
        return Path(output_arg)
    return input_path.with_name(f"{input_path.stem}_waving.gif")


def average_border_color(image: Image.Image) -> tuple[int, int, int]:
    # We sample the corners and edge midpoints to estimate the background color.
    # That keeps the empty areas around the shifted bands visually consistent.
    rgba = image.convert("RGBA")
    width, height = rgba.size
    border_pixels: list[tuple[int, int, int]] = []

    sample_points = [
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1),
        (width // 2, 0),
        (width // 2, height - 1),
        (0, height // 2),
        (width - 1, height // 2),
    ]

    for x, y in sample_points:
        r, g, b, _ = rgba.getpixel((x, y))
        border_pixels.append((r, g, b))

    if not border_pixels:
        return (255, 255, 255)

    return tuple(int(round(mean(channel[i] for channel in border_pixels))) for i in range(3))


def load_image(path: Path, scale: float) -> Image.Image:
    # Convert the source image to RGBA so the animation can preserve transparency
    # and so every frame uses the same channel layout.
    image = Image.open(path).convert("RGBA")
    if scale != 1.0:
        if scale <= 0:
            raise ValueError("Scale must be greater than zero.")
        # Scaling happens before frame generation so the wave effect runs on the
        # final resolution instead of doing extra work per frame.
        width = max(1, int(round(image.width * scale)))
        height = max(1, int(round(image.height * scale)))
        image = image.resize((width, height), Image.Resampling.LANCZOS)
    return image


def wave_frame(
    source: Image.Image,
    phase: float,
    amplitude: float,
    wavelength: float,
    band_height: int,
    background_color: tuple[int, int, int],
) -> Image.Image:
    width, height = source.size
    # Start with a flat background fill. Any pixels not covered by shifted strips
    # will show this color, which helps hide gaps along the image edges.
    frame = Image.new("RGBA", (width, height), background_color + (255,))

    for left in range(0, width, band_height):
        right = min(width, left + band_height)
        strip_center = (left + right) / 2.0
        horizontal_progress = strip_center / max(1.0, width - 1.0)
        # The sine taper makes the middle of the image move more than the left
        # and right edges. That keeps the effect anchored at the sides.
        taper = max(0.0, math.sin(math.pi * horizontal_progress)) ** 0.85
        # The phase term animates the flag. Advancing phase over time moves the
        # wave smoothly up and down through the image.
        offset = int(
            round(
                amplitude
                * taper
                * math.sin((2.0 * math.pi * strip_center / wavelength) + phase)
            )
        )
        # Slice one thin vertical strip from the source image and paste it into
        # the new frame at its computed vertical offset.
        strip = source.crop((left, 0, right, height))
        frame.paste(strip, (left, offset))

    return frame


def make_frames(
    source: Image.Image,
    frame_count: int,
    amplitude: float,
    wavelength: float,
    band_height: int,
) -> list[Image.Image]:
    # Build a full animation cycle by stepping phase evenly across the requested
    # number of frames.
    background_color = average_border_color(source)
    frames: list[Image.Image] = []

    for index in range(frame_count):
        phase = (2.0 * math.pi * index) / frame_count
        frame = wave_frame(
            source=source,
            phase=phase,
            amplitude=amplitude,
            wavelength=wavelength,
            band_height=max(1, band_height),
            background_color=background_color,
        )
        frames.append(frame)

    return frames


def save_gif(frames: list[Image.Image], output_path: Path, duration: int) -> None:
    if not frames:
        raise ValueError("No frames were generated.")

    # GIFs use a limited palette, so each frame is quantized before saving.
    paletted_frames = [frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=256) for frame in frames]
    first_frame, *rest_frames = paletted_frames
    first_frame.save(
        output_path,
        save_all=True,
        append_images=rest_frames,
        duration=duration,
        loop=0,
        optimize=False,
        disposal=2,
    )


def main() -> None:
    # Parse options, load the source image, generate the frame list, and save the
    # final animated GIF to disk.
    args = parse_args()
    input_path = Path(args.input_image)

    if not input_path.exists():
        raise SystemExit(f"Input image not found: {input_path}")

    output_path = build_output_path(input_path, args.output_gif)
    source = load_image(input_path, args.scale)
    frames = make_frames(
        source=source,
        frame_count=args.frames,
        amplitude=args.amplitude,
        wavelength=args.wavelength,
        band_height=args.band_height,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_gif(frames, output_path, args.duration)
    print(f"Saved waving flag GIF to {output_path}")


if __name__ == "__main__":
    main()
