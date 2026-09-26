#!/usr/bin/env python3
"""Make bundled songs loadable when index.html is opened by double-click (file://).

Chrome blocks fetch() on file:// pages, but it still loads <script src="..."> from the same folder.
This script writes songs/<file>.js next to each audio file, containing the audio as base64:
    window.SONG_BUNDLE = window.SONG_BUNDLE || {}; window.SONG_BUNDLE["belle_U.mp3"] = "....";
The game tries fetch() first and falls back to these bundles automatically.

Usage:  python3 tools/bundle_songs.py            # bundles every mp3/ogg/wav/m4a in songs/
        python3 tools/bundle_songs.py songs/a.mp3 songs/b.mp3
Re-run it whenever you add or replace a song. Keep songs as MP3/OGG (a bundle is ~1.33x the audio size).
"""
import base64, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONGS = os.path.join(ROOT, 'songs')
files = sys.argv[1:] or [os.path.join(SONGS, f) for f in sorted(os.listdir(SONGS)) if f.lower().endswith(('.mp3', '.ogg', '.wav', '.m4a'))]
for path in files:
    name = os.path.basename(path)
    with open(path, 'rb') as fh:
        b64 = base64.b64encode(fh.read()).decode('ascii')
    out = path + '.js'
    with open(out, 'w') as fh:
        fh.write('window.SONG_BUNDLE = window.SONG_BUNDLE || {}; window.SONG_BUNDLE[%s] = "%s";\n' % (json.dumps(name), b64))
    print('%-28s -> %-32s %.1f MB' % (name, os.path.basename(out), os.path.getsize(out) / 1e6))
