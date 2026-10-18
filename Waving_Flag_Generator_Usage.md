# Waving Flag Generator Usage

This script turns a still image into a looped GIF with a vertical waving flag effect.

## File

- Script: `Waving_Flag_Generator.py`
- Output: a GIF file, usually saved next to the source image

## Requirements

- Python 3.11+
- Pillow

If Pillow is not installed yet, install the project requirements or install Pillow directly:

```bash
pip install Pillow
```

## Basic Example

Generate a GIF using the default output name:

```bash
python Waving_Flag_Generator.py images/awana_bg.png
```

This creates:

```text
images/awana_bg_waving.gif
```

## Custom Output Example

You can choose the output file name yourself:

```bash
python Waving_Flag_Generator.py images/awana_bg.png images/custom_flag.gif
```

## Useful Options

- `--frames`: Number of animation frames in the GIF. More frames usually means smoother motion.
- `--duration`: Time in milliseconds for each frame.
- `--amplitude`: How far the image strips shift up and down.
- `--wavelength`: How wide each wave cycle is across the image.
- `--band-height`: Width of each vertical slice used to build the effect.
- `--scale`: Resize the image before generating the GIF.

## Recommended Starting Command

For a good balance of smoothness and file size:

```bash
python Waving_Flag_Generator.py images/awana_bg.png images/awana_bg_waving.gif --frames 24 --duration 145 --amplitude 10 --wavelength 100 --band-height 3
```

## Notes

- The image should look good when shifted in vertical slices. Logos, banners, and flat artwork usually work best.
- Transparent images are supported.
- The script uses the outer edge colors of the image as the background fill for the shifted areas.
- The GIF loops forever.

## What To Expect

The effect works by bending the image into a repeating wave pattern rather than animating individual objects. That makes it useful for flag-style banners and simple graphic animations.
