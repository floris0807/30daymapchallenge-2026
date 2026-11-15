"""USGS 地震カタログから日本周辺の M4.5 以上・20 年ぶんを 1 回で取って data.json に絞って保存する。
件数は事前に count で 14,243 件（上限 2 万件以内）を確認済み。何度も叩かないこと。
  python3 -I fetch_data.py <出力 data.json>
"""
import json, sys, urllib.request, urllib.parse

Q = dict(format='geojson', starttime='2006-01-01', endtime='2026-01-01',
         minlatitude=24, maxlatitude=48, minlongitude=122, maxlongitude=150,
         minmagnitude=4.5, orderby='time-asc')
url = 'https://earthquake.usgs.gov/fdsnws/event/1/query?' + urllib.parse.urlencode(Q)
req = urllib.request.Request(url, headers={'User-Agent': 'map-proto/0.1'})
fc = json.load(urllib.request.urlopen(req, timeout=300))

rows = []
for f in fc['features']:
    lon, lat, dep = f['geometry']['coordinates']
    p = f['properties']
    if dep is None or p['mag'] is None:
        continue
    # [経度, 緯度, 深さkm, 規模, 年(小数), USGS id] … id は最深イベントを元記録と突き合わせるため
    rows.append([round(lon, 3), round(lat, 3), round(dep, 2), round(p['mag'], 1),
                 round(1970 + p['time'] / 1000 / 86400 / 365.2425, 3), f['id']])
deepest = max(fc['features'], key=lambda f: f['geometry']['coordinates'][2] or -1)
meta = dict(source='USGS Earthquake Hazards Program, FDSN event API', query=Q,
            fetched=len(fc['features']), kept=len(rows),
            deepest=dict(id=deepest['id'], place=deepest['properties']['place'],
                         depth=deepest['geometry']['coordinates'][2], mag=deepest['properties']['mag'],
                         time=deepest['properties']['time']))
json.dump(dict(meta=meta, quakes=rows), open(sys.argv[1], 'w'), ensure_ascii=False, separators=(',', ':'))
print(json.dumps(meta, ensure_ascii=False, indent=1))
