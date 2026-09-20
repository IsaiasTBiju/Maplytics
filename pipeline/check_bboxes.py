import requests
import time

DISTRICTS = ["Deira, Dubai, United Arab Emirates",
             "Dubai Marina, Dubai, United Arab Emirates",
             "Mirdif, Dubai, United Arab Emirates"]

for query in DISTRICTS:
    resp = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": query, "format": "json", "limit": 1},
        headers={"User-Agent": "maplytics-research-project"}
    )
    data = resp.json()
    if data:
        bbox = data[0]["boundingbox"]  # [south, north, west, east]
        south, north, west, east = map(float, bbox)
        print(f"{query}")
        print(f"  Nominatim bbox: west={west}, south={south}, east={east}, north={north}")
        print(f"  -> ({west}, {south}, {east}, {north})\n")
    else:
        print(f"{query}: no result\n")
    time.sleep(1)  # be polite to Nominatim's free API