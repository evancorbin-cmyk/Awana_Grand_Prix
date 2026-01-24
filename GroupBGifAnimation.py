import pygame
import random
import math
from PIL import Image
import sys
import os

# ---------------- CONFIG ----------------
IMAGE_PATH = "GroupB.png"
OUTPUT_GIF = "group_b_epic_race.gif"

WIDTH, HEIGHT = 960, 540
FPS = 60
DURATION_SECONDS = 4
TOTAL_FRAMES = FPS * DURATION_SECONDS

SHAKE_INTENSITY = 6
SMOKE_PARTICLES = 160
MOTION_BLUR_STRENGTH = 3
# ----------------------------------------

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Load image
base_image = pygame.image.load(IMAGE_PATH).convert_alpha()
base_image = pygame.transform.smoothscale(base_image, (WIDTH, HEIGHT))

# For motion blur
previous_frames = []

frames = []

for frame in range(TOTAL_FRAMES):
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Camera shake
    shake_x = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY)
    shake_y = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY)

    screen.fill((25, 20, 15))

    # Draw main image
    screen.blit(base_image, (shake_x, shake_y))


    # ---- MOTION BLUR ----
    blur_surface = screen.copy()
    previous_frames.append(blur_surface)

    if len(previous_frames) > MOTION_BLUR_STRENGTH:
        previous_frames.pop(0)

    for i, past in enumerate(previous_frames):
        alpha = int(255 * (i / MOTION_BLUR_STRENGTH) * 0.4)
        past.set_alpha(alpha)
        screen.blit(past, (0, 0))

    pygame.display.flip()

    # Convert frame to PIL Image
    raw_str = pygame.image.tostring(screen, "RGB")
    img = Image.frombytes("RGB", (WIDTH, HEIGHT), raw_str)
    frames.append(img)

pygame.quit()

# Export GIF
frames[0].save(
    OUTPUT_GIF,
    save_all=True,
    append_images=frames[1:],
    duration=int(1000 / FPS),
    loop=0,
    optimize=True,
)

print(f"✅ GIF exported as {OUTPUT_GIF}")
