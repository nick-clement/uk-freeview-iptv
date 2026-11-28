#!/usr/bin/env python3
"""Check every stream in uk-freeview.m3u and print a status per channel."""
import re, urllib.request, concurrent.futures as cf
L = open(__import__("sys").argv[1] if len(__import__("sys").argv)>1 else "uk-freeview.m3u", encoding="utf-8").read().splitlines()
ents = [(re.search(r'tvg-chno="(\d+)"', L[i]).group(1), L[i].rsplit(",", 1)[1], L[i + 1])
        for i in range(len(L) - 1) if L[i].startswith("#EXTINF")]
UA = {"User-Agent": "Mozilla/5.0 (AppleTV; tvOS 18) AppleCoreMedia"}
def check(e):
    no, name, url = e
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20)
        body = r.read(4000).decode("utf-8", "ignore")
        ok = "#EXTM3U" in body
        return no, name, f"{r.status}{'' if ok else ' not-a-playlist'}", r.geturl()
    except urllib.error.HTTPError as x:
        return no, name, str(x.code), url
    except Exception as x:
        return no, name, "ERR " + type(x).__name__ + " " + str(x)[:60], url
with cf.ThreadPoolExecutor(16) as ex:
    for no, name, st, u in sorted(ex.map(check, ents), key=lambda r: int(r[0])):
        print(f"{no}\t{name}\t{st}\t{u[:110]}")
