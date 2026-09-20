# -*- coding: utf-8 -*-
"""生成应用图标 app.ico

风格：深色扁平一致——圆角主色渐变底 + 白色粗体 “Aa”。
先以 1024 超采样绘制再缩到 256 作为主图，导出 16~256 全尺寸 ICO。
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "app.ico")

R = 1024                      # 超采样渲染尺寸
RADIUS = int(R * 0.22)        # 圆角半径
FONT_PATH = r"C:\Windows\Fonts\msyhbd.ttc"   # 微软雅黑 Bold

TOP = (108, 155, 255)         # 主色渐变的浅端（对应 #6C9BFF）
BOT = (61, 107, 255)          # 主色渐变的深端（对应 #3D6BFF）
SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def render_base():
    """圆角 + 垂直渐变的底板。"""
    img = Image.new("RGBA", (R, R), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(R):
        t = y / (R - 1)
        c = (int(TOP[0] + (BOT[0] - TOP[0]) * t),
             int(TOP[1] + (BOT[1] - TOP[1]) * t),
             int(TOP[2] + (BOT[2] - TOP[2]) * t), 255)
        d.line([(0, y), (R, y)], fill=c)

    mask = Image.new("L", (R, R), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, R - 1, R - 1],
                                           radius=RADIUS, fill=255)
    out = Image.new("RGBA", (R, R), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def draw_glyph(img):
    """居中绘制白色粗体 “Aa”。"""
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, int(R * 0.46))
    text = "Aa"
    bbox = d.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((R - w) / 2 - bbox[0], (R - h) / 2 - bbox[1]), text,
           font=font, fill=(255, 255, 255, 255))
    return img


def main():
    img = draw_glyph(render_base())
    master = img.resize((256, 256), Image.LANCZOS)
    master.save(OUT, format="ICO", sizes=SIZES)
    with Image.open(OUT) as chk:
        got = sorted(chk.info.get("sizes", []))
    print(f"saved {OUT} ({os.path.getsize(OUT)} bytes); sizes={got}")


if __name__ == "__main__":
    main()
