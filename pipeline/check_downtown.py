import requests

resp = requests.get(
    "https://nominatim.openstreetmap.org/search",
    params={"q": "Downtown Dubai, Dubai, United Arab Emirates", "format": "json", "limit": 1},
    headers={"User-Agent": "maplytics-research-project"}
)
data = resp.json()
if data:
    bbox = data[0]["boundingbox"]
    south, north, west, east = map(float, bbox)
    print(f"west={west}, south={south}, east={east}, north={north}")
    print(f"-> ({west}, {south}, {east}, {north})")
else:
    print("no result")