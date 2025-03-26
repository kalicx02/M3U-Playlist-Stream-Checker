# M3U-Playlist-Stream-Checker

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.6%2B-brightgreen.svg)
![FFmpeg](https://img.shields.io/badge/dependency-FFmpeg-red.svg)

An advanced Python tool for checking the availability and quality of streams in M3U playlists. This tool verifies if each stream URL is accessible and creates a new M3U file containing only the active streams.

![M3U-Playlist-Stream-Checker Screenshot](coming soon)

## Features

- ✅ **Stream availability verification**: Checks if each stream in the playlist is working
- 📊 **Detailed media information**: Video codec, resolution, framerate, and audio details
- 🔍 **Low framerate detection**: Identifies channels with framerates at or below a configurable threshold
- ⏱️ **Timeout configuration**: Set how long to wait for each stream
- 🧵 **Multi-threaded processing**: Check multiple streams concurrently
- 🎨 **Colorful terminal output**: Clear visual indicators of checking progress and results
- 📋 **Comprehensive report**: Detailed statistics and quality analysis
- 🔄 **Filtered M3U generation**: Create a new playlist with only working streams
- 📏 **Resolution categorization**: Classify streams by resolution quality

## Requirements

- Python 3.6+
- FFmpeg/FFprobe

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/M3U-Playlist-Stream-Checker.git
   cd M3U-Playlist-Stream-Checker
   ```

2. Install required Python packages:
   ```bash
   pip install requests
   ```
   
3. Install FFmpeg/FFprobe:
   - **Ubuntu/Debian**:
     ```bash
     sudo apt install ffmpeg
     ```
   - **macOS** (using Homebrew):
     ```bash
     brew install ffmpeg
     ```
   - **Windows**: Download from [FFmpeg official website](https://ffmpeg.org/download.html)

## Usage

### Basic Usage

```bash
python m3u_check.py playlist.m3u
```

This will check all streams in `playlist.m3u` and create a new file `playlist_working.m3u` with all streams (marking which ones work).

### Advanced Options

```bash
python m3u_check.py playlist.m3u -o filtered.m3u -t 10 --threads 20 --verbose --only-working
```

### Command Line Arguments

| Argument | Short | Description |
|----------|-------|-------------|
| `--output` | `-o` | Output M3U file path (default: input_file_working.m3u) |
| `--timeout` | `-t` | Timeout in seconds for each stream check (default: 5) |
| `--threads` | | Number of concurrent threads (default: 10) |
| `--verbose` | `-v` | Show verbose output |
| `--only-working` | | Only include working streams in output file |
| `--low-fps` | | Threshold for low framerate detection in fps (default: 30) |
| `--min-resolution` | | Minimum resolution for high-quality streams (default: 1280x720) |

## Output Example

```
======================================================
 M3U-Playlist-Stream-Checker Report
======================================================

Overall Statistics:
  Total streams: 150
  Working streams: 132
  Failed streams: 18
  Success rate: 88.0%
  Processing time: 45.23 seconds

Stream Quality:
  Low framerate streams (<= 30 fps): 24
  High resolution streams (>= 1280x720): 98
  Low resolution streams (< 1280x720): 34

Top Channel Groups:
  Sports: 45 channels
  Movies: 32 channels
  News: 27 channels
  Entertainment: 22 channels
  Documentary: 14 channels

Output:
  Output file: playlist_working.m3u
  Streams included: Working only

======================================================

Low Framerate Channels (<= 30 fps):
----------------------------------------
  Sports Channel 1 - 25.0 fps - 1920x1080
  News 24/7 - 25.0 fps - 1280x720
  Movie Classics - 24.0 fps - 1920x1080
  ...
```

## How It Works

1. **Parse M3U file**: The script reads the M3U playlist and extracts stream information.
2. **Check streams concurrently**: Using multi-threading, it verifies each stream's availability.
3. **Extract media info**: For working streams, it uses FFprobe to gather detailed information.
4. **Generate report**: A comprehensive report summarizes the results.
5. **Create filtered playlist**: Generates a new M3U file with only working streams (optional).

## Advanced Usage Examples

### Check with increased timeout for slow connections

```bash
python m3u_check.py playlist.m3u --timeout 15
```

### Use more threads for faster processing

```bash
python m3u_check.py playlist.m3u --threads 30
```

### Detect streams with framerates below 25 FPS

```bash
python m3u_check.py playlist.m3u --low-fps 25
```

### Only consider streams 1080p or higher as high resolution

```bash
python m3u_check.py playlist.m3u --min-resolution 1920x1080
```
