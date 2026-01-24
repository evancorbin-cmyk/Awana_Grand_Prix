from PIL import Image, ImageSequence

src = "group_b_epic_race.gif"
dst = "group_b_epic_race.gif"

gif = Image.open(src)

frames = []
durations = []

for frame in ImageSequence.Iterator(gif):
    durations.append(frame.info.get("duration", 100))

    # Convert to palette mode (Qt likes this)
    f = frame.convert("P", palette=Image.ADAPTIVE)
    frames.append(f)

frames[0].save(
    dst,
    save_all=True,
    append_images=frames[1:],
    loop=0,          # infinite loop
    disposal=1,      # do not restore background
    optimize=True,
    duration=durations
)

print("Saved:", dst)