from pathlib import Path
from PIL import Image, ImageDraw

root = Path(r"C:\Users\LHW66\Documents\Codex\2026-09-23\abenzerps-qwen-image-2-1-uncensored\outputs\manga_drawer\roughs")
root.mkdir(parents=True, exist_ok=True)
w = h = 768


def base():
    im = Image.new("RGB", (w, h), (245, 245, 242))
    d = ImageDraw.Draw(im)
    d.rectangle((5, 5, w - 6, h - 6), outline=(20, 20, 20), width=8)
    return im, d


def label(d, text):
    d.text((24, 20), text, fill=(55, 55, 55))


im, d = base(); label(d, "p05")
d.polygon([(0, 0), (260, 0), (360, 260), (360, 768), (0, 768)], fill=(232, 232, 230), outline=(40, 40, 40))
d.rectangle((420, 280, 700, 650), outline=(35, 35, 35), width=6)
d.ellipse((245, 185, 365, 310), fill=(175, 175, 175), outline=(25, 25, 25), width=4)
d.polygon([(240, 305), (375, 305), (420, 700), (190, 700)], fill=(205, 205, 205), outline=(25, 25, 25))
d.line((255, 430, 365, 430), fill=(60, 60, 60), width=8)
im.save(root / "p05.png")

im, d = base(); label(d, "p06")
d.rounded_rectangle((90, 430, 680, 720), radius=70, outline=(30, 30, 30), width=7)
d.ellipse((245, 135, 430, 320), fill=(180, 180, 180), outline=(25, 25, 25), width=5)
d.polygon([(220, 300), (455, 300), (555, 680), (155, 680)], fill=(150, 150, 150), outline=(20, 20, 20))
d.ellipse((470, 155, 630, 315), fill=(120, 120, 120), outline=(25, 25, 25), width=5)
d.polygon([(455, 285), (650, 285), (720, 680), (390, 680)], fill=(100, 100, 100), outline=(20, 20, 20))
im.save(root / "p06.png")

im, d = base(); label(d, "p07")
d.ellipse((125, 70, 640, 720), fill=(205, 205, 205), outline=(25, 25, 25), width=7)
d.arc((210, 250, 330, 390), 10, 170, fill=(20, 20, 20), width=7)
d.arc((435, 250, 555, 390), 10, 170, fill=(20, 20, 20), width=7)
d.ellipse((265, 315, 300, 345), fill=(50, 50, 50))
d.ellipse((470, 315, 505, 345), fill=(50, 50, 50))
d.ellipse((360, 460, 430, 570), fill=(100, 100, 100), outline=(20, 20, 20), width=4)
d.line((230, 180, 385, 255), fill=(30, 30, 30), width=7)
d.line((540, 180, 390, 255), fill=(30, 30, 30), width=7)
im.save(root / "p07.png")

im, d = base(); label(d, "p08")
d.polygon([(90, 690), (680, 690), (600, 410), (170, 410)], fill=(160, 160, 160), outline=(20, 20, 20))
d.ellipse((220, 175, 410, 355), fill=(185, 185, 185), outline=(25, 25, 25), width=5)
d.ellipse((355, 160, 560, 365), fill=(115, 115, 115), outline=(25, 25, 25), width=5)
d.line((150, 420, 620, 420), fill=(30, 30, 30), width=8)
im.save(root / "p08.png")

im, d = base(); label(d, "p09")
d.ellipse((100, 120, 670, 700), fill=(210, 210, 210), outline=(25, 25, 25), width=8)
d.ellipse((355, 300, 420, 430), fill=(45, 45, 45), outline=(15, 15, 15), width=5)
for x in range(160, 620, 55):
    d.arc((x, 140, x + 180, 600), 200, 340, fill=(100, 100, 100), width=4)
im.save(root / "p09.png")

im, d = base(); label(d, "p10")
d.rounded_rectangle((110, 630, 680, 735), radius=40, outline=(30, 30, 30), width=6)
d.ellipse((280, 105, 470, 300), fill=(190, 190, 190), outline=(25, 25, 25), width=5)
d.polygon([(260, 280), (490, 280), (590, 680), (160, 680)], fill=(150, 150, 150), outline=(20, 20, 20))
d.line((155, 390, 620, 390), fill=(40, 40, 40), width=8)
d.line((155, 520, 620, 520), fill=(40, 40, 40), width=6)
im.save(root / "p10.png")

im, d = base(); label(d, "p11")
d.ellipse((95, 55, 680, 755), fill=(205, 205, 205), outline=(25, 25, 25), width=8)
d.arc((210, 260, 330, 400), 10, 170, fill=(20, 20, 20), width=7)
d.arc((440, 260, 560, 400), 10, 170, fill=(20, 20, 20), width=7)
d.ellipse((265, 325, 300, 355), fill=(50, 50, 50))
d.ellipse((475, 325, 510, 355), fill=(50, 50, 50))
d.ellipse((355, 470, 430, 590), fill=(90, 90, 90), outline=(20, 20, 20), width=4)
for x in range(150, 650, 70):
    d.line((x, 120, x - 30, 250), fill=(150, 150, 150), width=3)
im.save(root / "p11.png")

im, d = base(); label(d, "p12")
d.rounded_rectangle((90, 450, 680, 720), radius=70, outline=(30, 30, 30), width=7)
d.ellipse((260, 170, 415, 325), fill=(185, 185, 185), outline=(25, 25, 25), width=5)
d.polygon([(240, 310), (440, 310), (520, 650), (160, 650)], fill=(160, 160, 160), outline=(20, 20, 20))
d.ellipse((430, 230, 600, 400), fill=(115, 115, 115), outline=(25, 25, 25), width=5)
d.line((120, 420, 650, 420), fill=(60, 60, 60), width=6)
im.save(root / "p12.png")

print("created", len(list(root.glob("p*.png"))), "roughs")
