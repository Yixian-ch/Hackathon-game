Bundled songs live here (paths are relative to index.html). Referenced by the SONGS array in index.html:
  songs/belle_U.mp3
  songs/bocci.mp3
  songs/Metro.mp3
Edit titles, artists and BPM hints in the SONGS array at the top of block (4) "SONG LIBRARY" in index.html.

Loading: over http(s) (itch.io, python3 -m http.server) the game fetches the audio directly.
When index.html is double-clicked (file://) Chrome blocks fetch, so the game loads songs/<file>.js instead:
a base64 copy of the audio written by  python3 tools/bundle_songs.py  (re-run it after adding or replacing a song).
Keep songs as MP3/OGG; a bundle is about 1.33x the audio size. The original FLACs are not used by the game.
