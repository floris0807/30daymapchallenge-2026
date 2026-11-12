#!/usr/bin/env python3
"""日本近海の「今の」風と波を Open-Meteo から取って data.json に保存する。

標準ライブラリだけで動く。使い方: python3 fetch.py
格子: 北緯 24〜46、東経 122〜150、1度刻み（23 x 29 = 667 点）。
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

LATS = range(24, 47)
LONS = range(122, 151)
# 1リクエストの地点数。URL は 100 点で約 1.5KB に収まる
CHUNK = 100
# 無料枠は分あたり 600 コール（複数地点は地点数ぶん数える）。100 点 x 5 回/分 = 500 に抑える
SLEEP_BETWEEN = 12
RETRIES = 4

MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
WIND_URL = "https://api.open-meteo.com/v1/forecast"
MARINE_VARS = [
    "wave_height", "wave_direction", "wave_period",
    "wind_wave_height", "wind_wave_direction", "wind_wave_period",
    "swell_wave_height", "swell_wave_direction", "swell_wave_period",
]
WIND_VARS = ["wind_speed_10m", "wind_direction_10m"]
JST = timezone(timedelta(hours=9))
OUT = Path(__file__).resolve().parent / "data.json"


def get_json(base, params):
    url = base + "?" + urllib.parse.urlencode(params, safe=",")
    req = urllib.request.Request(url, headers={"User-Agent": "30daymapchallenge-day13/1.0"})
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError) as e:
            code = getattr(e, "code", None)
            # 4xx（429 以外）は引数の誤り。リトライしても直らない
            if code and 400 <= code < 500 and code != 429:
                raise
            if attempt == RETRIES:
                raise
            wait = 30 * attempt if code == 429 else 5 * attempt
            print(f"  retry {attempt}/{RETRIES - 1} after {wait}s: {e}")
            time.sleep(wait)


def fetch_all(base, variables, points, extra):
    results = []
    chunks = [points[i:i + CHUNK] for i in range(0, len(points), CHUNK)]
    for n, chunk in enumerate(chunks, 1):
        if n > 1:
            time.sleep(SLEEP_BETWEEN)
        params = {
            "latitude": ",".join(str(p[0]) for p in chunk),
            "longitude": ",".join(str(p[1]) for p in chunk),
            "current": ",".join(variables),
            "timezone": "Asia/Tokyo",
            **extra,
        }
        data = get_json(base, params)
        if isinstance(data, dict):  # 1 点だけのときは配列でなく単体で返る
            data = [data]
        if len(data) != len(chunk):
            raise RuntimeError(f"{base}: {len(chunk)} 点要求して {len(data)} 点返った")
        results.extend(data)
        print(f"  {base.split('/')[2]} {n}/{len(chunks)} ok")
    return results


def r(v, nd=2):
    return None if v is None else round(v, nd)


def main():
    points = [(lat, lon) for lat in LATS for lon in LONS]
    fetched_at = datetime.now(JST).isoformat(timespec="seconds")
    print(f"{len(points)} points")
    marine = fetch_all(MARINE_URL, MARINE_VARS, points, {})
    time.sleep(SLEEP_BETWEEN)
    wind = fetch_all(WIND_URL, WIND_VARS, points, {"wind_speed_unit": "kn"})

    out_points = []
    for (lat, lon), m, w in zip(points, marine, wind):
        mc, wc = m["current"], w["current"]
        out_points.append({
            "grid": [lat, lon],
            "wave_at": [r(m["latitude"], 4), r(m["longitude"], 4)],
            "wind_at": [r(w["latitude"], 4), r(w["longitude"], 4)],
            **{k: mc.get(k) for k in MARINE_VARS},
            "wind_speed_kn": wc.get("wind_speed_10m"),
            "wind_from_deg": wc.get("wind_direction_10m"),
        })

    sea = [p for p in out_points if p["wave_height"] is not None]
    doc = {
        "title": "風と波 — 日本近海",
        "fetched_at_jst": fetched_at,
        "model_time_jst": {
            "wave": sorted({m["current"]["time"] for m in marine}),
            "wind": sorted({w["current"]["time"] for w in wind}),
        },
        "units": {
            "wave_height": "m", "period": "s", "direction": "deg（来る方角、北=0 時計回り）",
            "wind_speed_kn": "kn", "wind_from_deg": "deg（吹いてくる方角）",
        },
        "models": {
            "wave": "Open-Meteo Marine API の既定（Best match）。どのモデルが使われたかは応答に含まれず不明",
            "wind": "Open-Meteo Forecast API の既定（Best match）。どのモデルが使われたかは応答に含まれず不明",
        },
        "source": "Weather data by Open-Meteo.com (CC BY 4.0)",
        "source_urls": [MARINE_URL, WIND_URL],
        "grid": {"lat": [LATS.start, LATS.stop - 1], "lon": [LONS.start, LONS.stop - 1], "step_deg": 1},
        "count": {"all": len(out_points), "sea": len(sea)},
        "points": out_points,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"wrote {OUT.name}: {len(out_points)} points, sea {len(sea)}, wave time {doc['model_time_jst']['wave']}")


if __name__ == "__main__":
    main()
