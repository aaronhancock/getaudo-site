from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUT = ASSETS / "social-ads"

LOGO = ASSETS / "audo-logo-white.png"
PORTRAIT = ASSETS / "founder-field-portrait.webp"
HERO = ASSETS / "consulting-technology-hero.webp"

FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"

INK = "#18221d"
PAPER = "#fbfbf7"
WHITE = "#ffffff"
MUTED = "#d7ded8"
MUTED_DARK = "#5f6b62"
EVERGREEN = "#101815"
GREEN = "#1f4739"
TEAL = "#4d8c83"
BRASS = "#f0c66f"
CREAM = "#f4dca9"
COPPER = "#b56748"

SIZES = {
    "portrait": (1080, 1350),
    "square": (1080, 1080),
    "landscape": (1200, 628),
}


def font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    path = FONT_REGULAR
    if weight == "bold":
        path = FONT_BOLD
    elif weight == "black":
        path = FONT_BLACK
    return ImageFont.truetype(path, size)


def cover_image(path: Path, size: tuple[int, int], anchor: tuple[float, float] = (0.5, 0.5)) -> Image.Image:
    image = Image.open(path).convert("RGB")
    w, h = image.size
    tw, th = size
    scale = max(tw / w, th / h)
    nw, nh = int(w * scale + 0.5), int(h * scale + 0.5)
    image = image.resize((nw, nh), Image.Resampling.LANCZOS)
    max_x = max(0, nw - tw)
    max_y = max(0, nh - th)
    left = int(max_x * anchor[0])
    top = int(max_y * anchor[1])
    return image.crop((left, top, left + tw, top + th))


def color_layer(size: tuple[int, int], start: str, end: str) -> Image.Image:
    w, h = size
    base = Image.new("RGB", size, start)
    overlay = Image.new("RGB", size, end)
    mask = Image.new("L", size)
    draw = ImageDraw.Draw(mask)
    for y in range(h):
        value = int(255 * y / max(1, h - 1))
        draw.line((0, y, w, y), fill=value)
    return Image.composite(overlay, base, mask)


def rounded_rectangle(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill: str, outline: str | None = None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if text_size(draw, trial, fnt)[0] <= width:
            current = trial
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    fnt: ImageFont.FreeTypeFont,
    fill: str,
    width: int,
    line_gap: int,
    max_lines: int | None = None,
) -> int:
    x, y = xy
    lines = wrap_text(draw, text, fnt, width)
    if max_lines:
        lines = lines[:max_lines]
    _, line_h = text_size(draw, "Ag", fnt)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += line_h + line_gap
    return y


def fit_font(draw: ImageDraw.ImageDraw, text: str, width: int, max_size: int, min_size: int, weight: str = "black") -> ImageFont.FreeTypeFont:
    for size in range(max_size, min_size - 1, -2):
        fnt = font(size, weight)
        if all(text_size(draw, line, fnt)[0] <= width for line in wrap_text(draw, text, fnt, width)):
            return fnt
    return font(min_size, weight)


def draw_logo(image: Image.Image, x: int, y: int, width: int) -> None:
    logo = Image.open(LOGO).convert("RGBA")
    ratio = width / logo.width
    logo = logo.resize((width, int(logo.height * ratio)), Image.Resampling.LANCZOS)
    image.alpha_composite(logo, (x, y))


def draw_cta(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, scale: float = 1.0) -> tuple[int, int]:
    fnt = font(round(24 * scale), "bold")
    px = round(28 * scale)
    py = round(17 * scale)
    tw, th = text_size(draw, text, fnt)
    box = (x, y, x + tw + px * 2, y + th + py * 2)
    rounded_rectangle(draw, box, round(10 * scale), BRASS)
    draw.text((x + px, y + py - 1), text, font=fnt, fill=INK)
    return box[2], box[3]


def add_texture(image: Image.Image, opacity: int = 18) -> None:
    w, h = image.size
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    spacing = 18
    for x in range(-h, w, spacing):
      draw.line((x, 0, x + h, h), fill=(255, 255, 255, opacity), width=1)
    image.alpha_composite(overlay)


def add_tint(image: Image.Image, fill: tuple[int, int, int, int]) -> None:
    overlay = Image.new("RGBA", image.size, fill)
    image.alpha_composite(overlay)


def draw_footer(draw: ImageDraw.ImageDraw, w: int, h: int, x: int, y: int, dark: bool = True) -> None:
    color = CREAM if dark else "#755315"
    draw.text((x, y), "getaudo.com", font=font(max(22, int(w * 0.022)), "bold"), fill=color)


def base_dark(size: tuple[int, int]) -> Image.Image:
    image = color_layer(size, "#0c1210", "#1f4739").convert("RGBA")
    add_texture(image, 11)
    return image


def layout_metrics(size: tuple[int, int]) -> dict[str, int | bool | float]:
    w, h = size
    landscape = w > h
    margin = round(w * (0.07 if not landscape else 0.055))
    logo_w = round(w * (0.16 if not landscape else 0.12))
    headline = round(w * (0.072 if not landscape else 0.057))
    sub = round(w * (0.034 if not landscape else 0.026))
    return {
        "w": w,
        "h": h,
        "landscape": landscape,
        "margin": margin,
        "logo_w": logo_w,
        "headline": headline,
        "sub": sub,
    }


def hidden_problem(size: tuple[int, int]) -> Image.Image:
    m = layout_metrics(size)
    w, h = size
    image = base_dark(size)
    draw = ImageDraw.Draw(image)
    margin = int(m["margin"])

    for i, alpha in enumerate((30, 24, 18)):
        cx = w - margin - i * round(w * 0.10)
        cy = round(h * (0.18 + i * 0.24))
        r = round(w * (0.14 - i * 0.022))
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(240, 198, 111, alpha), width=max(2, round(w * 0.004)))
        qf = font(round(w * (0.18 - i * 0.025)), "black")
        qw, qh = text_size(draw, "?", qf)
        draw.text((cx - qw // 2, cy - qh // 2 - round(h * 0.01)), "?", font=qf, fill=(240, 198, 111, alpha + 24))

    draw_logo(image, margin, margin, int(m["logo_w"]))
    tag = font(round(w * 0.024), "bold")
    draw.text((margin, round(h * 0.21)), "FREE DISCOVERY", font=tag, fill=CREAM)

    max_width = round(w * (0.62 if not m["landscape"] else 0.52))
    hf = fit_font(draw, "You may not know the problem yet.", max_width, int(m["headline"]), round(w * 0.043), "black")
    y = round(h * (0.29 if not m["landscape"] else 0.27))
    y = draw_wrapped(draw, "You may not know the problem yet.", (margin, y), hf, WHITE, max_width, round(w * 0.013))
    y += round(h * 0.028)
    y = draw_wrapped(
        draw,
        "Start with what feels slow or unclear. I will help find the next step.",
        (margin, y),
        font(int(m["sub"]), "regular"),
        MUTED,
        max_width,
        round(w * 0.01),
    )
    y += round(h * 0.045)
    draw_cta(draw, margin, y, "Request Free Discovery", 1 if not m["landscape"] else 0.82)
    draw_footer(draw, w, h, margin, h - margin - round(w * 0.03))
    return image


def agency_alternative(size: tuple[int, int]) -> Image.Image:
    m = layout_metrics(size)
    w, h = size
    image = base_dark(size)
    draw = ImageDraw.Draw(image)
    margin = int(m["margin"])
    draw_logo(image, margin, margin, int(m["logo_w"]))

    left_w = round(w * (0.40 if m["landscape"] else 0.82))
    y = round(h * (0.22 if m["landscape"] else 0.18))
    layers = ["Sales call", "Account manager", "Project handoff", "Another meeting", "Maybe the work"]
    card_h = round(h * (0.075 if not m["landscape"] else 0.085))
    for index, layer in enumerate(layers):
        x = margin + index * round(w * 0.012)
        rounded_rectangle(draw, (x, y + index * round(card_h * 0.6), x + left_w, y + index * round(card_h * 0.6) + card_h), 12, "#20332b", "#426355", 2)
        draw.text((x + 22, y + index * round(card_h * 0.6) + round(card_h * 0.26)), layer, font=font(round(w * 0.023), "bold"), fill="#aebbb3")

    text_x = margin if not m["landscape"] else round(w * 0.52)
    text_y = round(h * (0.55 if not m["landscape"] else 0.22))
    text_w = w - text_x - margin
    hf = fit_font(draw, "No agency runaround.", text_w, int(m["headline"]), round(w * 0.045), "black")
    y2 = draw_wrapped(draw, "No agency runaround.", (text_x, text_y), hf, WHITE, text_w, round(w * 0.012))
    y2 += round(h * 0.025)
    y2 = draw_wrapped(draw, "Work directly with Aaron. No account layers. No handoff chain.", (text_x, y2), font(int(m["sub"]), "regular"), MUTED, text_w, round(w * 0.01))
    y2 += round(h * 0.045)
    draw_cta(draw, text_x, y2, "Get a clear next step", 1 if not m["landscape"] else 0.82)
    draw_footer(draw, w, h, text_x, h - margin - round(w * 0.03))
    return image


def put_off_work(size: tuple[int, int]) -> Image.Image:
    m = layout_metrics(size)
    w, h = size
    image = Image.new("RGBA", size, PAPER)
    draw = ImageDraw.Draw(image)
    margin = int(m["margin"])

    for x in range(0, w, 28):
        draw.line((x, 0, x + h, h), fill=(31, 71, 57, 10), width=1)

    dark_panel = (margin, margin, w - margin, round(h * (0.43 if not m["landscape"] else 0.91)))
    if not m["landscape"]:
        rounded_rectangle(draw, dark_panel, 20, EVERGREEN)
        draw_logo(image, margin + 34, margin + 34, int(m["logo_w"]))
        text_x = margin + 34
        text_y = margin + round(h * 0.14)
        text_w = dark_panel[2] - text_x - 34
    else:
        rounded_rectangle(draw, (margin, margin, round(w * 0.49), h - margin), 20, EVERGREEN)
        draw_logo(image, margin + 32, margin + 32, int(m["logo_w"]))
        text_x = margin + 32
        text_y = round(h * 0.24)
        text_w = round(w * 0.37)

    hf = fit_font(draw, "Still on your list?", text_w, int(m["headline"]), round(w * 0.044), "black")
    y = draw_wrapped(draw, "Still on your list?", (text_x, text_y), hf, WHITE, text_w, round(w * 0.012))
    y += round(h * 0.03)
    draw_wrapped(draw, "The task you keep delaying may be easier to handle than you think.", (text_x, y), font(int(m["sub"]), "regular"), MUTED, text_w, round(w * 0.01))

    list_x = margin + 28 if not m["landscape"] else round(w * 0.55)
    list_y = round(h * (0.50 if not m["landscape"] else 0.16))
    list_w = w - list_x - margin
    items = ["Website update", "Broken form", "Manual follow-up", "AI question", "App cleanup"]
    item_h = round(h * (0.075 if not m["landscape"] else 0.105))
    for i, item in enumerate(items):
        y_item = list_y + i * round(item_h * 1.12)
        rounded_rectangle(draw, (list_x, y_item, list_x + list_w, y_item + item_h), 14, WHITE, "#dce2de", 2)
        draw.ellipse((list_x + 22, y_item + item_h // 2 - 9, list_x + 40, y_item + item_h // 2 + 9), fill=BRASS)
        draw.text((list_x + 60, y_item + round(item_h * 0.26)), item, font=font(round(w * 0.030), "bold"), fill=INK)

    cta_y = h - margin - round(h * 0.09)
    draw_cta(draw, list_x, cta_y, "Get it handled", 0.9 if m["landscape"] else 1)
    draw_footer(draw, w, h, list_x + round(w * 0.28), cta_y + round(h * 0.02), dark=False)
    return image


def practical_ai(size: tuple[int, int]) -> Image.Image:
    m = layout_metrics(size)
    w, h = size
    image = base_dark(size)
    draw = ImageDraw.Draw(image)
    margin = int(m["margin"])
    draw_logo(image, margin, margin, int(m["logo_w"]))

    card = (
        margin,
        round(h * (0.18 if not m["landscape"] else 0.20)),
        w - margin,
        round(h * (0.47 if not m["landscape"] else 0.80)),
    )
    if m["landscape"]:
        card = (round(w * 0.56), margin, w - margin, h - margin)
    rounded_rectangle(draw, card, 18, "#f8faf7", "#dfe5e1", 2)
    prompt_f = font(round(w * 0.022), "bold")
    body_f = font(round(w * (0.027 if not m["landscape"] else 0.023)), "regular")
    draw.text((card[0] + 28, card[1] + 28), "AI question", font=prompt_f, fill="#755315")
    draw_wrapped(draw, "Could AI help with this, or am I solving the wrong problem?", (card[0] + 28, card[1] + 72), body_f, INK, card[2] - card[0] - 56, round(w * 0.01))
    rounded_rectangle(draw, (card[0] + 28, card[3] - 82, card[2] - 28, card[3] - 26), 12, "#e8eee9")
    draw.text((card[0] + 48, card[3] - 65), "Start with the business problem.", font=font(round(w * 0.022), "bold"), fill=GREEN)

    text_x = margin
    text_y = round(h * (0.56 if not m["landscape"] else 0.26))
    text_w = w - margin * 2
    if m["landscape"]:
        text_w = round(w * 0.43)
    hf = fit_font(draw, "AI without the hype.", text_w, int(m["headline"]), round(w * 0.044), "black")
    y = draw_wrapped(draw, "AI without the hype.", (text_x, text_y), hf, WHITE, text_w, round(w * 0.012))
    y += round(h * 0.025)
    y = draw_wrapped(draw, "Choose the right use case, workflow, tool, and guardrails.", (text_x, y), font(int(m["sub"]), "regular"), MUTED, text_w, round(w * 0.01))
    y += round(h * 0.045)
    draw_cta(draw, text_x, y, "Use AI with confidence", 1 if not m["landscape"] else 0.82)
    draw_footer(draw, w, h, text_x, h - margin - round(w * 0.03))
    return image


def one_senior_partner(size: tuple[int, int]) -> Image.Image:
    m = layout_metrics(size)
    w, h = size
    photo_anchor = (0.52, 0.54 if not m["landscape"] else 0.46)
    image = cover_image(PORTRAIT, size, photo_anchor).convert("RGBA")
    add_tint(image, (12, 18, 16, 144))
    draw = ImageDraw.Draw(image)
    margin = int(m["margin"])

    if m["landscape"]:
        add_tint(image, (12, 18, 16, 58))
        shade = Image.new("RGBA", size, (0, 0, 0, 0))
        shade_draw = ImageDraw.Draw(shade)
        for x in range(w):
            alpha = int(190 * max(0, 1 - x / (w * 0.76)))
            shade_draw.line((x, 0, x, h), fill=(12, 18, 16, alpha))
        image.alpha_composite(shade)
        text_w = round(w * 0.50)
    else:
        shade = Image.new("RGBA", size, (0, 0, 0, 0))
        shade_draw = ImageDraw.Draw(shade)
        for y_line in range(h):
            alpha = int(214 * max(0, 1 - y_line / (h * 0.76)))
            shade_draw.line((0, y_line, w, y_line), fill=(12, 18, 16, alpha))
        image.alpha_composite(shade)
        text_w = w - margin * 2
    add_texture(image, 10)

    draw_logo(image, margin, margin, int(m["logo_w"]))
    draw.text((margin, round(h * 0.19)), "30 YEARS IN TECHNOLOGY", font=font(round(w * 0.024), "bold"), fill=CREAM)
    hf = fit_font(draw, "One senior tech partner.", text_w, int(m["headline"]), round(w * 0.044), "black")
    y = round(h * (0.27 if not m["landscape"] else 0.30))
    y = draw_wrapped(draw, "One senior tech partner.", (margin, y), hf, WHITE, text_w, round(w * 0.012))
    y += round(h * 0.025)
    y = draw_wrapped(draw, "Direct help from Aaron for websites, apps, automation, AI, and product decisions.", (margin, y), font(int(m["sub"]), "regular"), MUTED, text_w, round(w * 0.01))
    y += round(h * 0.045)
    draw_cta(draw, margin, y, "Work directly with Aaron", 1 if not m["landscape"] else 0.82)
    draw_footer(draw, w, h, margin, h - margin - round(w * 0.03))
    return image


CREATIVES = {
    "hidden-problem": hidden_problem,
    "agency-alternative": agency_alternative,
    "put-off-work": put_off_work,
    "practical-ai": practical_ai,
    "one-senior-partner": one_senior_partner,
}


def export() -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for slug, create in CREATIVES.items():
        for label, size in SIZES.items():
            image = create(size).convert("RGB")
            out = OUT / f"audo-{slug}-{label}.jpg"
            image.save(out, "JPEG", quality=94, optimize=True, progressive=True)
            written.append(out)
    return written


if __name__ == "__main__":
    for path in export():
        print(path.relative_to(ROOT))
