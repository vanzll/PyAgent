from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
VIDEO_DIR = ROOT / "video"
ASSET_DIR = VIDEO_DIR / "generated"
SCENE_DIR = ASSET_DIR / "scenes"
OUTPUT_VIDEO = VIDEO_DIR / "financial_agent_demo_90s.mp4"
HOME_SCREENSHOT = ASSET_DIR / "homepage.png"

WIDTH = 1280
HEIGHT = 720

BG = (10, 18, 33)
BG_SOFT = (21, 36, 60)
CREAM = (247, 244, 237)
INK = (22, 32, 51)
INK_SOFT = (96, 108, 126)
GOLD = (210, 164, 92)
GOLD_SOFT = (240, 207, 147)
BLUE = (78, 125, 209)
GREEN = (43, 140, 116)
WHITE = (255, 255, 255)
PANEL = (19, 39, 64)


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


SERIF_BOLD = font("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 28)
SERIF_TITLE = font("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 48)
SANS = font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
SANS_SMALL = font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
SANS_TINY = font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
SANS_BOLD = font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
SANS_BOLD_SMALL = font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, text=True, **kwargs)


def wait_for_server(base_url: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    with httpx.Client(timeout=10) as client:
        while time.time() < deadline:
            try:
                response = client.get(base_url)
                if response.status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(0.4)
    raise RuntimeError("Web app did not start in time")


def is_server_running(base_url: str) -> bool:
    try:
        response = httpx.get(base_url, timeout=5)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


def request_run(client: httpx.Client, base_url: str, tickers: str, prompt: str) -> dict:
    response = client.post(f"{base_url}/api/runs", data={"tickers": tickers, "prompt": prompt})
    response.raise_for_status()
    run_id = response.json()["run_id"]
    for _ in range(120):
        payload = client.get(f"{base_url}/api/runs/{run_id}").json()
        if payload["status"] in {"completed", "failed"}:
            if payload["status"] != "completed":
                raise RuntimeError(f"Run failed for {tickers}: {payload['error_message']}")
            payload["run_id"] = run_id
            return payload
        time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for run {run_id}")


def download_artifact(client: httpx.Client, base_url: str, run_id: str, name: str, target: Path) -> None:
    response = client.get(f"{base_url}/api/runs/{run_id}/artifacts/{name}")
    response.raise_for_status()
    target.write_bytes(response.content)


def wrap(draw: ImageDraw.ImageDraw, text: str, text_font: ImageFont.FreeTypeFont, max_width: int) -> str:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        width = draw.textbbox((0, 0), candidate, font=text_font)[2]
        if width <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return "\n".join(lines)


def draw_pill(draw: ImageDraw.ImageDraw, xy, text: str, fill, text_color, text_font=SANS_BOLD_SMALL) -> None:
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=18, fill=fill)
    bbox = draw.textbbox((0, 0), text, font=text_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x0 + (x1 - x0 - tw) / 2, y0 + (y1 - y0 - th) / 2 - 1), text, fill=text_color, font=text_font)


def make_canvas(background=CREAM) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), background)
    return image, ImageDraw.Draw(image)


def add_footer(draw: ImageDraw.ImageDraw, text: str) -> None:
    draw.text((52, 678), text, fill=(122, 135, 151), font=SANS_TINY)


def scene_hero(homepage: Path, target: Path) -> None:
    base = Image.open(homepage).convert("RGB")
    scale = max(WIDTH / base.width, HEIGHT / base.height)
    resized = base.resize((int(base.width * scale), int(base.height * scale)))
    left = max(0, (resized.width - WIDTH) // 2)
    top = 0
    cropped = resized.crop((left, top, left + WIDTH, top + HEIGHT)).filter(ImageFilter.GaussianBlur(radius=4))
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (8, 14, 28, 210))
    scene = Image.alpha_composite(cropped.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(scene)
    draw_pill(draw, (56, 48, 320, 92), "NUS CS5260 FINAL PROJECT", GOLD, INK)
    draw.text((58, 146), "PyCallingAgent Research Desk", fill=WHITE, font=SERIF_TITLE)
    draw.text((60, 214), "A public financial research agent for U.S. stocks and ETFs", fill=(221, 228, 239), font=SANS)
    body = "Ask a ticker, fetch public market data, and return charts, tables, and a concise research brief."
    draw.rounded_rectangle((48, 294, 710, 478), radius=28, fill=(11, 20, 35, 180), outline=(35, 48, 72, 180), width=2)
    draw.multiline_text((68, 326), wrap(draw, body, SANS, 590), fill=CREAM, font=SANS, spacing=10)
    for idx, stat in enumerate([("3", "public data sources"), ("SSE", "live or poll"), ("0 SGD", "demo-mode cost")]):
        x = 780 + idx * 152
        draw.rounded_rectangle((x, 150, x + 132, 258), radius=24, fill=BG_SOFT)
        draw.text((x + 20, 176), stat[0], fill=GOLD_SOFT, font=SERIF_BOLD)
        draw.multiline_text((x + 20, 218), stat[1], fill=(214, 223, 237), font=SANS_TINY, spacing=4)
    add_footer(draw, "Public-facing homepage with course statement, source stack, and stable demo mode.")
    scene.convert("RGB").save(target)


def scene_single_stock(result: dict, target: Path) -> None:
    image, draw = make_canvas()
    add_card = lambda xy, fill=WHITE: draw.rounded_rectangle(xy, radius=26, fill=fill, outline=(222, 226, 234), width=2)
    draw_pill(draw, (56, 42, 190, 84), "RUN 01", (234, 240, 249), BLUE)
    draw.text((56, 120), "Single-stock brief", fill=INK, font=SERIF_TITLE)
    prompt = "Prompt: Summarize AAPL and show the recent price trend."
    draw.text((58, 194), prompt, fill=INK_SOFT, font=SANS)
    card = result["snapshot_cards"][0]
    add_card((56, 248, 454, 614))
    draw.text((84, 278), card["ticker"], fill=INK, font=SERIF_BOLD)
    draw.text((84, 326), card["name"], fill=INK_SOFT, font=SANS_SMALL)
    metrics = [
        ("Last price", f"${card['latest_close']:.1f}"),
        ("P/E", f"{card['pe_ratio']:.1f}"),
        ("Market cap", f"${card['market_cap']/1_000_000_000:.1f}B"),
        ("Revenue", f"${card['latest_revenue']/1_000_000_000:.1f}B"),
    ]
    y = 382
    for label, value in metrics:
        draw.text((84, y), label, fill=INK_SOFT, font=SANS_TINY)
        draw.text((234, y - 4), value, fill=INK, font=SANS_BOLD)
        y += 54
    add_card((494, 248, 1224, 614), fill=(248, 250, 252))
    draw_pill(draw, (524, 280, 666, 320), "RESEARCH BRIEF", (251, 243, 229), GOLD)
    summary = result["summary_text"].split("For research use only.")[0].strip()
    draw.multiline_text((524, 346), wrap(draw, summary, SANS, 650), fill=INK, font=SANS, spacing=10)
    add_footer(draw, "The agent returns a snapshot card and a filing-aware summary for a single ticker.")
    image.save(target)


def scene_comparison(result: dict, chart_path: Path, target: Path) -> None:
    image, draw = make_canvas()
    draw_pill(draw, (56, 42, 190, 84), "RUN 02", (251, 243, 229), GOLD)
    draw.text((56, 120), "Peer comparison", fill=INK, font=SERIF_TITLE)
    draw.text((58, 194), "Prompt: Compare AMD and NVDA on valuation, growth, and recent performance.", fill=INK_SOFT, font=SANS)

    cards = result["snapshot_cards"][:2]
    positions = [(56, 258, 318, 446), (342, 258, 604, 446)]
    for card, pos in zip(cards, positions):
        draw.rounded_rectangle(pos, radius=24, fill=WHITE, outline=(222, 226, 234), width=2)
        x0, y0, x1, _ = pos
        draw.text((x0 + 26, y0 + 24), card["ticker"], fill=INK, font=SERIF_BOLD)
        draw.text((x0 + 26, y0 + 66), card["name"], fill=INK_SOFT, font=SANS_TINY)
        metrics = [
            ("Last", f"${card['latest_close']:.1f}"),
            ("P/E", f"{card['pe_ratio']:.1f}"),
            ("Revenue", f"${card['latest_revenue']/1_000_000_000:.1f}B"),
        ]
        my = y0 + 110
        for label, value in metrics:
            draw.text((x0 + 26, my), label, fill=INK_SOFT, font=SANS_TINY)
            draw.text((x0 + 130, my - 2), value, fill=INK, font=SANS_BOLD_SMALL)
            my += 34

    chart = Image.open(chart_path).convert("RGBA")
    chart.thumbnail((560, 360))
    panel = Image.new("RGBA", (594, 388), (248, 250, 252, 255))
    image.paste(panel.convert("RGB"), (630, 246))
    cx = 630 + (594 - chart.width) // 2
    cy = 246 + (388 - chart.height) // 2
    image.paste(chart, (cx, cy), chart)
    draw.rounded_rectangle((630, 246, 1224, 634), radius=24, outline=(222, 226, 234), width=2)
    draw.text((654, 214), "Relative returns chart", fill=INK, font=SANS_BOLD)
    add_footer(draw, "Two snapshot cards plus a chart artifact make the product look like a real research desk.")
    image.save(target)


def scene_etf(result: dict, target: Path) -> None:
    image, draw = make_canvas(background=BG)
    draw_pill(draw, (58, 48, 192, 90), "RUN 03", (36, 58, 96), GOLD_SOFT)
    draw.text((58, 126), "ETF snapshot", fill=WHITE, font=SERIF_TITLE)
    draw.text((60, 196), "Prompt: Give me a market snapshot for SPY and highlight the main risks.", fill=(210, 221, 237), font=SANS)

    draw.rounded_rectangle((58, 256, 420, 610), radius=28, fill=(18, 35, 58))
    card = result["snapshot_cards"][0]
    draw.text((88, 290), card["ticker"], fill=WHITE, font=SERIF_BOLD)
    draw.text((88, 338), card["name"], fill=(208, 219, 233), font=SANS_SMALL)
    draw.text((88, 398), "Latest close", fill=GOLD_SOFT, font=SANS_TINY)
    draw.text((88, 426), f"${card['latest_close']:.1f}", fill=WHITE, font=SANS_BOLD)
    draw.text((88, 476), "Recent filing", fill=GOLD_SOFT, font=SANS_TINY)
    draw.text((88, 504), card["recent_filing_form"] or "n/a", fill=WHITE, font=SANS_BOLD_SMALL)

    draw.rounded_rectangle((456, 256, 1222, 610), radius=28, fill=WHITE)
    draw_pill(draw, (486, 286, 616, 326), "RISK BRIEF", (234, 240, 249), BLUE)
    summary = result["summary_text"].split("For research use only.")[0].strip()
    draw.multiline_text((488, 352), wrap(draw, summary, SANS, 680), fill=INK, font=SANS, spacing=10)
    add_footer(draw, "The same interface also handles ETFs and macro-aware framing, not only single-company equity research.")
    image.save(target)


def scene_grounding(target: Path) -> None:
    image, draw = make_canvas()
    draw_pill(draw, (56, 46, 236, 88), "GROUNDING + DELIVERY", (251, 243, 229), GOLD)
    draw.text((56, 124), "Why this is strong enough to submit", fill=INK, font=SERIF_TITLE)
    subtitles = [
        ("Public source stack", "Alpha Vantage, SEC EDGAR, and FRED are explicit in the product."),
        ("Agent behavior", "The same UI returns different artifacts depending on the question."),
        ("Stable classroom demo", "Demo mode removes API rate-limit and model-latency risk."),
        ("Clear scope", "Every output is labeled research-only, not investment advice."),
    ]
    y = 238
    for title, desc in subtitles:
        draw.rounded_rectangle((58, y, 1220, y + 82), radius=22, fill=WHITE, outline=(225, 229, 236), width=2)
        draw.text((88, y + 18), title, fill=INK, font=SANS_BOLD)
        draw.text((372, y + 18), desc, fill=INK_SOFT, font=SANS_SMALL)
        y += 102
    add_footer(draw, "This product is entirely derived from work conducted as part of the NUS CS5260 course.")
    image.save(target)


def scene_closing(target: Path) -> None:
    image, draw = make_canvas(background=BG)
    draw_pill(draw, (58, 56, 282, 98), "90-SECOND DEMO WRAP-UP", GOLD, INK)
    draw.text((58, 152), "Ready for the final presentation", fill=WHITE, font=SERIF_TITLE)
    bullets = [
        "Public financial research agent with a real web interface",
        "Deterministic demo path for live classroom reliability",
        "Slides, speaker notes, and demo video already prepared",
        "Next hard requirement: move from a temporary tunnel to a persistent public host",
    ]
    draw.rounded_rectangle((58, 246, 760, 590), radius=30, fill=PANEL)
    draw.multiline_text((92, 286), "\n\n".join(f"• {item}" for item in bullets), fill=WHITE, font=SANS, spacing=12)
    draw.rounded_rectangle((806, 246, 1220, 590), radius=30, fill=(18, 35, 58))
    draw.text((838, 284), "Deliverables", fill=GOLD_SOFT, font=SANS_BOLD)
    deliverables = "1. Public URL\n2. 5-minute slides\n3. Demo video\n4. Product homepage statement"
    draw.multiline_text((838, 330), deliverables, fill=WHITE, font=SANS_SMALL, spacing=12)
    add_footer(draw, "Public URL should be moved to a persistent host before final submission.")
    image.save(target)


def make_concat_file(scene_files: list[Path], durations: list[int], concat_path: Path) -> None:
    lines: list[str] = []
    for scene_file, duration in zip(scene_files, durations):
        lines.append(f"file '{scene_file.as_posix()}'")
        lines.append(f"duration {duration}")
    lines.append(f"file '{scene_files[-1].as_posix()}'")
    concat_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    VIDEO_DIR.mkdir(exist_ok=True)
    ASSET_DIR.mkdir(exist_ok=True)
    SCENE_DIR.mkdir(exist_ok=True)

    env = os.environ.copy()
    env["WEBAPP_DEMO_MODE"] = "1"
    env["PYTHONPATH"] = "src"
    env.pop("ALPHAVANTAGE_API_KEY", None)
    env.pop("ALPHA_VANTAGE_API_KEY", None)
    env.pop("FRED_API_KEY", None)
    env.pop("LLM_MODEL_ID", None)
    env.pop("LLM_API_KEY", None)
    env.pop("LLM_BASE_URL", None)

    server = None
    try:
        if not is_server_running("http://127.0.0.1:8000/"):
            server = subprocess.Popen(
                [sys.executable, "-m", "pycallingagent.webapp"],
                cwd=ROOT,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        wait_for_server("http://127.0.0.1:8000/")
        run(
            [
                "firefox",
                "--headless",
                "--window-size",
                "1440,1800",
                "--screenshot",
                str(HOME_SCREENSHOT),
                "http://127.0.0.1:8000/",
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        with httpx.Client(timeout=30) as client:
            aapl = request_run(client, "http://127.0.0.1:8000", "AAPL", "Summarize AAPL and show the recent price trend.")
            comparison = request_run(
                client,
                "http://127.0.0.1:8000",
                "AMD, NVDA",
                "Compare AMD and NVDA on valuation, growth, and recent performance.",
            )
            spy = request_run(
                client,
                "http://127.0.0.1:8000",
                "SPY",
                "Give me a market snapshot for SPY and highlight the main risks.",
            )

            chart_name = comparison["preview_charts"][0]["name"]
            chart_path = ASSET_DIR / chart_name
            download_artifact(client, "http://127.0.0.1:8000", comparison["run_id"], chart_name, chart_path)

        scene_files = [
            SCENE_DIR / "scene-01.png",
            SCENE_DIR / "scene-02.png",
            SCENE_DIR / "scene-03.png",
            SCENE_DIR / "scene-04.png",
            SCENE_DIR / "scene-05.png",
            SCENE_DIR / "scene-06.png",
        ]
        scene_hero(HOME_SCREENSHOT, scene_files[0])
        scene_single_stock(aapl, scene_files[1])
        scene_comparison(comparison, chart_path, scene_files[2])
        scene_etf(spy, scene_files[3])
        scene_grounding(scene_files[4])
        scene_closing(scene_files[5])

        concat_path = ASSET_DIR / "concat.txt"
        durations = [15, 15, 18, 15, 14, 13]
        make_concat_file(scene_files, durations, concat_path)

        run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_path),
                "-vsync",
                "vfr",
                "-pix_fmt",
                "yuv420p",
                str(OUTPUT_VIDEO),
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        metadata = {
            "homepage": str(HOME_SCREENSHOT),
            "scenes": [str(path) for path in scene_files],
            "video": str(OUTPUT_VIDEO),
            "durations_seconds": durations,
        }
        (ASSET_DIR / "video_manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(f"Wrote {OUTPUT_VIDEO}")
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()


if __name__ == "__main__":
    main()
