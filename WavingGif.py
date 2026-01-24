from PIL import Image
import numpy as np
import imageio

# Load image
img = Image.open("Journey.png").convert("RGBA")
w, h = img.size

frames = []
num_frames = 24        # animation smoothness
amplitude = 6         # wave height (vertical displacement)
wavelength = 120       # wave length
duration = 0.16        # seconds per frame
loop = -1              # infinite loop

pixels = np.array(img)

for i in range(num_frames):
    phase = 2 * np.pi * i / num_frames
    new_pixels = np.zeros_like(pixels)

    for x in range(w):
        offset = int(amplitude * np.sin(2 * np.pi * x / wavelength + phase))
        if offset > 0:
            new_pixels[offset:, x] = pixels[:-offset, x]
        elif offset < 0:
            new_pixels[:offset, x] = pixels[-offset:, x]
        else:
            new_pixels[:, x] = pixels[:, x]

    frames.append(new_pixels)

# Save GIF
imageio.mimsave("Journey_horizontal_waving.gif", frames, duration=duration, loop=loop)

print("GIF created: TT_horizontal_waving.gif")
