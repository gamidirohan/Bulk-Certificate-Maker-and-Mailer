from PIL import ImageFont


def fit_name(name, font_path, size, max_width, min_size=28):
    def width(text, font_size):
        left, _, right, _ = ImageFont.truetype(str(font_path), font_size).getbbox(text)
        return right - left

    current = size
    while current > min_size and width(name, current) > max_width:
        current -= 2
    if width(name, current) <= max_width:
        return name, current, None
    parts = name.split()
    short = " ".join(parts[:-1]) + (f" {parts[-1][0]}." if len(parts) > 1 else "")
    while current > min_size and width(short, current) > max_width:
        current -= 2
    warning = "Name reduced to minimum size; verify layout" if width(short, current) > max_width else None
    return short, current, warning
