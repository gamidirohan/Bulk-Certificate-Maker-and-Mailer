from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .name_formatter import fit_name


def generate_certificate(background, font_path, output, name, config):
    image = Image.open(background).convert("RGB")
    draw = ImageDraw.Draw(image)
    layers = config.get("texts") or [{**config, "content": "Participant Name", "participantName": True}]
    warnings = []
    for layer in layers:
        text = name if layer.get("participantName") else str(layer.get("content", ""))
        if not text:
            continue
        size = int(layer.get("fontSize", 72))
        max_width = int(layer.get("maxWidth", image.width * 0.7))
        if layer.get("participantName"):
            text, size, warning = fit_name(text, font_path, size, max_width)
            if warning:
                warnings.append(warning)
        font = ImageFont.truetype(str(font_path), size)
        left, _, right, _ = font.getbbox(text)
        width = right - left
        x = int(layer.get("x", (image.width - max_width) // 2))
        y = int(layer.get("y", 0))
        if layer.get("align", "center") == "center":
            x += (max_width - width) // 2
        elif layer.get("align") == "right":
            x += max_width - width
        # Browser and PDF both use the layer's supplied top-left Y coordinate.
        draw.text((x, y), text, font=font, fill=layer.get("color", "#0a1d41"), anchor="lt")
    image.save(output, "PDF", resolution=300.0)
    return "; ".join(warnings) or None
