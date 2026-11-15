#!/usr/bin/env python3
"""Build epg.xml: one guide file holding only the channels in uk-freeview.m3u."""
import gzip, re, urllib.request

SOURCES = [
    "https://raw.githubusercontent.com/dp247/Freeview-EPG/master/epg.xml",
    "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/master/SamsungTVPlus/gb.xml.gz",
]

def fetch(url):
    data = urllib.request.urlopen(url, timeout=180).read()
    if url.endswith(".gz"):
        data = gzip.decompress(data)
    return data.decode("utf-8")

wanted = set(re.findall(r'tvg-id="([^"]+)"', open("uk-freeview.m3u", encoding="utf-8").read()))
channels, programmes, seen = [], [], set()
for url in SOURCES:
    xml = fetch(url)
    for m in re.finditer(r'<channel id="([^"]*)".*?</channel>', xml, re.S):
        if m.group(1) in wanted and m.group(1) not in seen:
            seen.add(m.group(1)); channels.append(m.group(0))
    for m in re.finditer(r'<programme\b[^>]*?channel="([^"]*)"[^>]*>.*?</programme>', xml, re.S):
        if m.group(1) in wanted:
            programmes.append(m.group(0))

if len(seen) < len(wanted) * 0.8 or len(programmes) < 1000:
    raise SystemExit(f"Guide looks incomplete ({len(seen)}/{len(wanted)} channels, {len(programmes)} programmes); keeping the old file.")

with open("epg.xml", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<tv generator-info-name="uk-freeview-iptv">\n')
    f.write("\n".join(channels) + "\n" + "\n".join(programmes) + "\n</tv>\n")
print(f"{len(seen)}/{len(wanted)} channels, {len(programmes)} programmes; missing: {sorted(wanted - seen)}")
