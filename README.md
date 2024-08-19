# M3U-Playlist-Stream-Checker
- This Python script checks the availability of streams listed in an M3U playlist file. 
- It verifies if each stream URL is accessible and creates a new M3U file containing only the active streams.

## Requirements
- Python 3.x,
- requests library (pip install requests)

## Usage
python3 m3u_check.py <input_playlist.m3u>

## Output
Active streams will be saved in active_streams.m3u, and status messages will be displayed in the terminal.
