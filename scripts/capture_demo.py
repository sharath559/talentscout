"""Capture real offline CLI output and render an animated terminal transcript with Pillow."""

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from time import monotonic

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def font(size):
    for path in (
        "/System/Library/Fonts/Menlo.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def main():
    command = [sys.executable, "-m", "talentscout.main", "--offline", "--metrics"]
    started = monotonic()
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    events = []
    lines = []
    for line in process.stdout:
        events.append([round(monotonic() - started, 4), "o", line.replace("\n", "\r\n")])
        lines.append(line.rstrip("\n"))
    if process.wait() != 0:
        raise RuntimeError("offline CLI capture failed")
    transcript = "\n".join(lines) + "\n"
    (ROOT / "docs/demo-transcript.txt").write_text(transcript)
    header = {
        "version": 2,
        "width": 118,
        "height": 40,
        "title": "TalentScout offline CLI: recorded output",
        "env": {"TERM": "xterm-256color"},
    }
    (ROOT / "docs/demo.cast").write_text(
        "\n".join(json.dumps(item) for item in [header, *events]) + "\n"
    )
    metrics = json.loads(lines[-1])
    if metrics["api_calls"] != 0:
        raise RuntimeError("demo must use zero API calls")
    # Paging is a presentation of the unedited captured output, not a simulated terminal UI.
    pages = [lines[:15], lines[15:29], lines[29:41], lines[41:53], lines[53:-1]]
    frames = []
    for index, page in enumerate(pages):
        canvas = Image.new("RGB", (1440, 820), "#101916")
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle((28, 26, 1412, 790), radius=18, fill="#17221e", outline="#35473d")
        for x, color in [(58, "#f17d72"), (82, "#e9c46a"), (106, "#8cbf91")]:
            draw.ellipse((x, 48, x + 12, 60), fill=color)
        draw.text((142, 44), "talentscout / recorded CLI output", font=font(19), fill="#9bb2a2")
        draw.text((58, 100), "Evidence before recommendations.", font=font(33), fill="#e4eddf")
        draw.text(
            (58, 157), "$ uv run talent_scout --offline --metrics", font=font(21), fill="#a6d5ac"
        )
        y = 214
        for line in page:
            for wrapped in textwrap.wrap(
                line, width=106, replace_whitespace=False, drop_whitespace=False
            ) or [""]:
                color = (
                    "#a6d5ac" if line.startswith(("1.", "2.", "3.", "4.", "Source")) else "#d1dbce"
                )
                draw.text((58, y), wrapped, font=font(19), fill=color)
                y += 27
        draw.line((58, 730, 1380, 730), fill="#35473d", width=1)
        draw.text(
            (58, 751),
            "OFFLINE  /  4 synthetic candidates  /  0 API calls  /  $0.00",
            font=font(18),
            fill="#9bb2a2",
        )
        draw.text((1250, 751), f"{index + 1} / {len(pages)}", font=font(18), fill="#9bb2a2")
        frames.append(canvas)
    frames[0].save(ROOT / "docs/demo-preview.png")
    frames[0].save(
        ROOT / "docs/demo.gif",
        save_all=True,
        append_images=frames[1:],
        duration=[3000, 2400, 2400, 2400, 4000],
        loop=0,
        optimize=True,
    )
    print("Captured offline CLI: docs/demo.gif, demo.cast, demo-transcript.txt")


if __name__ == "__main__":
    main()
