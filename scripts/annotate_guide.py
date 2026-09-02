# -*- coding: utf-8 -*-
"""在教程截图上绘制少量说明，输出到 guide/annotated/。"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "guide" / "annotated"

FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\simhei.ttf"),
    Path("/System/Library/Fonts/PingFang.ttc"),
]

# x,y 为相对位置；w,h 为相对圈选框宽高（可选）
ANNOTATIONS: dict[str, list[dict]] = {
    "IMG_0482.jpeg": [
        {
            "box": (0.11, 0.374, 0.15, 0.013),
            "text": "可以直接写 [图1]，或在下方图片点「插入正文」",
            "note_y": 0.403,
        },
        {
            "box": (0.06, 0.398, 0.88, 0.135),
            "text": "十种默认配色，也可以自定义颜色",
        },
    ],
    "IMG_0483.png": [
        {
            "box": (0.62, 0.59, 0.32, 0.05),
            "text": "可分享至朋友圈、小红书、抖音等",
        },
    ],
    "IMG_0484.png": [
        {
            "box": (0.08, 0.18, 0.84, 0.22),
            "text": "好友会直接收到带标题、正文和图片的链接",
        },
    ],
}


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for ch in text:
        trial = current + ch
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines or [text]


def annotate_image(src: Path, items: list[dict], dest: Path) -> None:
    base = Image.open(src).convert("RGBA")
    w, h = base.size
    pad = max(20, w // 32)
    font = load_font(max(17, w // 36))
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for item in items:
        bx, by, bw, bh = item["box"]
        left = int(bx * w)
        top = int(by * h)
        right = int((bx + bw) * w)
        bottom = int((by + bh) * h)

        draw.rounded_rectangle(
            (left, top, right, bottom),
            radius=12,
            outline=(156, 47, 42, 255),
            width=max(3, w // 200),
        )

        text = item["text"]
        max_text_w = int(w * 0.88)
        lines = wrap_text(draw, text, font, max_text_w)
        line_h = int(font.size * 1.3)
        box_h = line_h * len(lines) + pad
        box_w = min(max_text_w + pad, w - pad * 2)
        note_left = (w - box_w) // 2
        if item.get("note_y") is not None:
            note_top = int(item["note_y"] * h)
        else:
            note_top = min(bottom + 10, h - box_h - pad)
            if note_top < bottom + 6:
                note_top = max(pad, top - box_h - 10)
            # 避免说明压住下一个标注框
            if item.get("note_max_y"):
                note_top = min(note_top, int(item["note_max_y"] * h) - box_h)

        draw.rounded_rectangle(
            (note_left, note_top, note_left + box_w, note_top + box_h),
            radius=10,
            fill=(16, 14, 12, 225),
            outline=(239, 230, 214, 140),
            width=1,
        )
        ty = note_top + pad // 2
        for line in lines:
            draw.text((note_left + pad // 2, ty), line, fill=(239, 230, 214, 255), font=font)
            ty += line_h

    out = Image.alpha_composite(base, overlay).convert("RGB")
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.save(dest, quality=92, optimize=True)
    print(f"Wrote {dest.relative_to(ROOT)}")


def main() -> None:
    for name, items in ANNOTATIONS.items():
        src = ROOT / name
        if not src.exists():
            raise FileNotFoundError(src)
        ext = src.suffix.lower()
        annotate_image(src, items, OUT / f"{src.stem}{ext}")


if __name__ == "__main__":
    main()
