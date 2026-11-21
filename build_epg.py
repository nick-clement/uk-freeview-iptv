#!/usr/bin/env python3
"""Build epg.xml: one guide file holding only the channels in uk-freeview.m3u.

Listings from the previous epg.xml are kept where the sources no longer cover
that time, so a late or short source update never leaves channels blank.
"""
import datetime, gzip, os, re, urllib.request

SOURCES = [
    "https://raw.githubusercontent.com/dp247/Freeview-EPG/master/epg.xml",
    "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/master/SamsungTVPlus/gb.xml.gz",
]
KEEP_PAST_HOURS = 6

def fetch(url):
    data = urllib.request.urlopen(url, timeout=180).read()
    if url.endswith(".gz"):
        data = gzip.decompress(data)
    return data.decode("utf-8")

def times(prog):
    s = re.search(r'start="(\d{14})', prog).group(1)
    e = re.search(r'stop="(\d{14})', prog).group(1)
    return s, e

CH = re.compile(r'<channel id="([^"]*)".*?</channel>', re.S)
PR = re.compile(r'<programme\b[^>]*?channel="([^"]*)"[^>]*>.*?</programme>', re.S)

wanted = set(re.findall(r'tvg-id="([^"]+)"', open("uk-freeview.m3u", encoding="utf-8").read()))
channels, seen, new = [], set(), {}
for url in SOURCES:
    xml = fetch(url)
    for m in CH.finditer(xml):
        if m.group(1) in wanted and m.group(1) not in seen:
            seen.add(m.group(1)); channels.append(m.group(0))
    for m in PR.finditer(xml):
        if m.group(1) in wanted:
            new.setdefault(m.group(1), []).append(m.group(0))

total_new = sum(len(v) for v in new.values())
if len(seen) < len(wanted) * 0.8 or total_new < 1000:
    raise SystemExit(f"Guide looks incomplete ({len(seen)}/{len(wanted)} channels, {total_new} programmes); keeping the old file.")

# Merge in old listings that fall outside the time the new data covers.
old = {}
if os.path.exists("epg.xml"):
    oldxml = open("epg.xml", encoding="utf-8").read()
    for m in CH.finditer(oldxml):
        if m.group(1) in wanted and m.group(1) not in seen:
            seen.add(m.group(1)); channels.append(m.group(0))
    for m in PR.finditer(oldxml):
        if m.group(1) in wanted:
            old.setdefault(m.group(1), []).append(m.group(0))

cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=KEEP_PAST_HOURS)).strftime("%Y%m%d%H%M%S")
programmes, kept = [], 0
for ch in sorted(wanted):
    fresh = new.get(ch, [])
    if fresh:
        lo = min(times(p)[0] for p in fresh); hi = max(times(p)[1] for p in fresh)
    else:
        lo = hi = None
    merged = list(fresh)
    for p in old.get(ch, []):
        s, e = times(p)
        if lo is None or e <= lo or s >= hi:
            merged.append(p); kept += 1
    merged = [p for p in merged if times(p)[1] > cutoff]
    merged.sort(key=lambda p: times(p)[0])
    programmes += merged

with open("epg.xml", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<tv generator-info-name="uk-freeview-iptv">\n')
    f.write("\n".join(channels) + "\n" + "\n".join(programmes) + "\n</tv>\n")
print(f"{len(seen)}/{len(wanted)} channels, {len(programmes)} programmes ({kept} kept from the previous file)")
