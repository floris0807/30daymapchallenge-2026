# 30DayMapChallenge 2026

Daily maps for [#30DayMapChallenge](https://30daymapchallenge.com/) 2026.
毎日1枚の地図を作っています。

Live: https://floris0807.github.io/30daymapchallenge-2026/

| Day | Theme | Map | Data |
|---|---|---|---|
| 13 | Interactions | [風と波 — 日本近海](https://floris0807.github.io/30daymapchallenge-2026/day13-interactions/) | Open-Meteo Marine / Forecast API |
| 14 | Borgesian map | [砂の地図 — Tabula Arenae](https://floris0807.github.io/30daymapchallenge-2026/day14-borgesian/) | Procedural terrain (fBm noise), no external data |
| 15 | Inside out | [足の下の星座 — Planisphaerium Subterraneum](https://floris0807.github.io/30daymapchallenge-2026/day15-insideout/) | USGS FDSN event API (M4.5+, 2006–2025), Natural Earth |

## Stack
- [MapLibre GL JS](https://maplibre.org/) + [OpenFreeMap](https://openfreemap.org/) for real-world maps; plain WebGL2 shaders for generated ones; d3-geo + Canvas 2D for custom projections
- Each day is a single static folder: `index.html`, plus a data snapshot and the script that fetched it when real data is used
- `tools/` holds the capture and encoding scripts (headless Chrome via CDP, ffmpeg)

## Credits
- Weather data by [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0)
- Basemap © OpenFreeMap © OpenMapTiles © OpenStreetMap contributors
- Earthquake catalog: USGS Earthquake Hazards Program (FDSN event web service)
- Coastlines: Natural Earth (public domain), via world-atlas
- Fonts: IM Fell English, Shippori Mincho B1 (SIL Open Font License 1.1, via Google Fonts)
