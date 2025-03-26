#!/usr/bin/env python3
"""
M3U-Playlist-Stream-Checker
---------------------------
An advanced tool for checking the availability and quality of streams in M3U playlists.
Features:
- Stream availability verification
- Detailed media information (codec, resolution, framerate, audio)
- Low framerate detection
- Timeout configuration
- Colorful terminal output
- Concurrent stream checking
- Output filtering options
- Statistics reporting

Usage: python3 m3u_check.py <input_playlist.m3u> [options]
"""

import os
import sys
import re
import time
import json
import argparse
import concurrent.futures
import subprocess
from urllib.parse import urlparse
import requests
from datetime import datetime

# Terminal colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class StreamChecker:
    def __init__(self, args):
        self.input_file = args.input_file
        self.output_file = args.output or self._get_default_output_filename(args.input_file)
        self.timeout = args.timeout
        self.max_workers = args.threads
        self.verbose = args.verbose
        self.only_working = args.only_working
        self.low_fps_threshold = args.low_fps
        self.min_resolution = args.min_resolution
        self.streams = []
        self.results = {
            "working": [],
            "not_working": [],
            "low_framerate": [],
            "high_resolution": [],
            "low_resolution": []
        }
        self.stats = {
            "total": 0,
            "working": 0,
            "failed": 0,
            "low_framerate": 0,
            "start_time": time.time()
        }

    def _get_default_output_filename(self, input_file):
        """Generate a default output filename based on the input file."""
        filename, ext = os.path.splitext(input_file)
        return f"{filename}_working{ext}"

    def parse_m3u(self):
        """Parse the M3U playlist file and extract stream information."""
        print(f"{Colors.HEADER}{Colors.BOLD}Parsing M3U playlist: {self.input_file}{Colors.ENDC}")
        
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                content = f.readlines()
        except UnicodeDecodeError:
            # Try with Latin-1 encoding if UTF-8 fails
            with open(self.input_file, 'r', encoding='latin-1') as f:
                content = f.readlines()
        except Exception as e:
            print(f"{Colors.RED}Error opening playlist file: {str(e)}{Colors.ENDC}")
            sys.exit(1)
        
        if not content or not content[0].strip() == '#EXTM3U':
            print(f"{Colors.RED}Error: Not a valid M3U file{Colors.ENDC}")
            sys.exit(1)
            
        current_stream = None
        
        for line in content:
            line = line.strip()
            
            if not line or line.startswith('#EXTM3U'):
                continue
                
            if line.startswith('#EXTINF:'):
                # Extract stream name from the EXTINF line
                name_match = re.search(r'#EXTINF:.*?,(.*)', line)
                if name_match:
                    stream_name = name_match.group(1).strip()
                    # Extract group-title if available
                    group_match = re.search(r'group-title="([^"]*)"', line)
                    group = group_match.group(1) if group_match else "Unknown"
                    # Create a new stream entry
                    current_stream = {
                        "name": stream_name,
                        "group": group,
                        "extinf": line,
                        "url": None,
                        "working": None,
                        "info": {}
                    }
            elif line.startswith('http') and current_stream:
                # Add URL to the current stream and append it to the list
                current_stream["url"] = line
                self.streams.append(current_stream)
                current_stream = None
        
        self.stats["total"] = len(self.streams)
        print(f"{Colors.GREEN}Found {self.stats['total']} streams in playlist{Colors.ENDC}")

    def check_stream(self, stream):
        """Check if a stream is working and get its media information."""
        stream_name = stream["name"]
        stream_url = stream["url"]
        
        if self.verbose:
            print(f"{Colors.CYAN}Checking: {stream_name}{Colors.ENDC}")
        
        # Initialize result
        result = {
            "name": stream_name,
            "url": stream_url,
            "working": False,
            "info": {
                "video_codec": "Unknown",
                "audio_codec": "Unknown",
                "resolution": "Unknown",
                "framerate": 0,
                "audio_bitrate": "Unknown"
            },
            "group": stream["group"],
            "extinf": stream["extinf"]
        }
        
        try:
            # Use FFprobe to get media information with a timeout
            cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", "-timeout", str(self.timeout * 1000000),
                stream_url
            ]
            
            # Execute the command and capture output
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            
            if process.returncode == 0 and process.stdout:
                probe_data = json.loads(process.stdout)
                
                # Stream is working
                result["working"] = True
                
                # Extract media information
                video_stream = next((s for s in probe_data.get("streams", []) if s.get("codec_type") == "video"), None)
                audio_stream = next((s for s in probe_data.get("streams", []) if s.get("codec_type") == "audio"), None)
                
                if video_stream:
                    # Video codec
                    result["info"]["video_codec"] = video_stream.get("codec_name", "Unknown")
                    
                    # Resolution
                    width = video_stream.get("width")
                    height = video_stream.get("height")
                    if width and height:
                        result["info"]["resolution"] = f"{width}x{height}"
                    
                    # Framerate
                    fps_str = video_stream.get("avg_frame_rate", "0/1")
                    if fps_str and "/" in fps_str:
                        num, den = map(int, fps_str.split("/"))
                        if den != 0:
                            result["info"]["framerate"] = round(num / den, 2)
                
                if audio_stream:
                    # Audio codec
                    result["info"]["audio_codec"] = audio_stream.get("codec_name", "Unknown")
                    
                    # Audio bitrate
                    bitrate = audio_stream.get("bit_rate")
                    if bitrate:
                        try:
                            bitrate = int(bitrate) // 1000
                            result["info"]["audio_bitrate"] = f"{bitrate} kbps"
                        except (ValueError, TypeError):
                            pass
                
                self.stats["working"] += 1
                
                # Check if framerate is low
                if result["info"]["framerate"] <= self.low_fps_threshold and result["info"]["framerate"] > 0:
                    self.results["low_framerate"].append(result)
                    self.stats["low_framerate"] += 1
                
                # Categorize by resolution
                if result["info"]["resolution"] != "Unknown":
                    try:
                        width, height = map(int, result["info"]["resolution"].split("x"))
                        min_width, min_height = map(int, self.min_resolution.split("x"))
                        
                        if width >= min_width and height >= min_height:
                            self.results["high_resolution"].append(result)
                        else:
                            self.results["low_resolution"].append(result)
                    except (ValueError, AttributeError):
                        pass
                
                self.results["working"].append(result)
                stream_status = f"{Colors.GREEN}✓ Working{Colors.ENDC}"
            else:
                # Stream is not working
                result["working"] = False
                self.stats["failed"] += 1
                self.results["not_working"].append(result)
                stream_status = f"{Colors.RED}✗ Failed{Colors.ENDC}"
                
            if self.verbose:
                print(f"  {stream_status} - {stream_name}")
                if result["working"]:
                    info = result["info"]
                    print(f"    Resolution: {Colors.YELLOW}{info['resolution']}{Colors.ENDC}, "
                          f"FPS: {Colors.YELLOW}{info['framerate']}{Colors.ENDC}, "
                          f"Video: {Colors.YELLOW}{info['video_codec']}{Colors.ENDC}, "
                          f"Audio: {Colors.YELLOW}{info['audio_codec']}{Colors.ENDC}")
            
            return result
            
        except subprocess.TimeoutExpired:
            # Timeout occurred
            result["working"] = False
            self.stats["failed"] += 1
            self.results["not_working"].append(result)
            
            if self.verbose:
                print(f"  {Colors.RED}✗ Timeout{Colors.ENDC} - {stream_name}")
            
            return result
            
        except Exception as e:
            # Other errors
            result["working"] = False
            self.stats["failed"] += 1
            self.results["not_working"].append(result)
            
            if self.verbose:
                print(f"  {Colors.RED}✗ Error{Colors.ENDC} - {stream_name} ({str(e)})")
            
            return result

    def check_all_streams(self):
        """Check all streams concurrently using thread pool."""
        print(f"{Colors.HEADER}{Colors.BOLD}Checking {len(self.streams)} streams (Timeout: {self.timeout}s, Threads: {self.max_workers}){Colors.ENDC}")
        print(f"{Colors.BLUE}Low FPS threshold: {self.low_fps_threshold} fps{Colors.ENDC}")
        print(f"{Colors.BLUE}Minimum resolution: {self.min_resolution}{Colors.ENDC}")
        
        progress_count = 0
        progress_total = len(self.streams)
        progress_interval = max(1, progress_total // 20)  # Update progress about 20 times
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all stream checks to the executor
            future_to_stream = {executor.submit(self.check_stream, stream): stream for stream in self.streams}
            
            # Process completed tasks
            for i, future in enumerate(concurrent.futures.as_completed(future_to_stream)):
                future.result()  # Get the result but we don't need to do anything with it
                
                # Update progress periodically
                progress_count += 1
                if not self.verbose and progress_count % progress_interval == 0:
                    percent = (progress_count / progress_total) * 100
                    print(f"{Colors.BLUE}Progress: {progress_count}/{progress_total} ({percent:.1f}%){Colors.ENDC}")

    def write_output_file(self):
        """Write a new M3U file with only working streams."""
        streams_to_write = self.results["working"] if self.only_working else self.streams
        
        if not streams_to_write:
            print(f"{Colors.YELLOW}No streams to write to output file{Colors.ENDC}")
            return
            
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                # Write M3U header
                f.write('#EXTM3U\n')
                
                # Write each stream
                for stream in streams_to_write:
                    if not self.only_working or stream.get("working", False):
                        f.write(f"{stream['extinf']}\n")
                        f.write(f"{stream['url']}\n")
                        
            print(f"{Colors.GREEN}Successfully wrote {len(streams_to_write)} streams to {self.output_file}{Colors.ENDC}")
            
        except Exception as e:
            print(f"{Colors.RED}Error writing output file: {str(e)}{Colors.ENDC}")

    def print_report(self):
        """Print a detailed report of the stream check results."""
        elapsed_time = time.time() - self.stats["start_time"]
        success_rate = (self.stats["working"] / self.stats["total"]) * 100 if self.stats["total"] > 0 else 0
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD} M3U-Playlist-Stream-Checker Report{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        
        # Overall statistics
        print(f"\n{Colors.BOLD}Overall Statistics:{Colors.ENDC}")
        print(f"  Total streams: {Colors.BOLD}{self.stats['total']}{Colors.ENDC}")
        print(f"  Working streams: {Colors.GREEN}{self.stats['working']}{Colors.ENDC}")
        print(f"  Failed streams: {Colors.RED}{self.stats['failed']}{Colors.ENDC}")
        print(f"  Success rate: {Colors.YELLOW}{success_rate:.1f}%{Colors.ENDC}")
        print(f"  Processing time: {Colors.BLUE}{elapsed_time:.2f} seconds{Colors.ENDC}")
        
        # Stream quality
        print(f"\n{Colors.BOLD}Stream Quality:{Colors.ENDC}")
        print(f"  Low framerate streams (<= {self.low_fps_threshold} fps): {Colors.YELLOW}{self.stats['low_framerate']}{Colors.ENDC}")
        print(f"  High resolution streams (>= {self.min_resolution}): {Colors.GREEN}{len(self.results['high_resolution'])}{Colors.ENDC}")
        print(f"  Low resolution streams (< {self.min_resolution}): {Colors.YELLOW}{len(self.results['low_resolution'])}{Colors.ENDC}")
        
        # Top groups
        if self.results["working"]:
            groups = {}
            for stream in self.results["working"]:
                group = stream["group"]
                if group in groups:
                    groups[group] += 1
                else:
                    groups[group] = 1
                    
            print(f"\n{Colors.BOLD}Top Channel Groups:{Colors.ENDC}")
            
            # Get the top 5 groups by count
            top_groups = sorted(groups.items(), key=lambda x: x[1], reverse=True)[:5]
            for group, count in top_groups:
                print(f"  {Colors.CYAN}{group}{Colors.ENDC}: {count} channels")
        
        # Output file information
        print(f"\n{Colors.BOLD}Output:{Colors.ENDC}")
        print(f"  Output file: {Colors.GREEN}{self.output_file}{Colors.ENDC}")
        print(f"  Streams included: {'Working only' if self.only_working else 'All streams'}")
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

    def print_low_framerate_channels(self):
        """Print a list of channels with low framerates."""
        if not self.results["low_framerate"]:
            return
            
        print(f"\n{Colors.YELLOW}{Colors.BOLD}Low Framerate Channels (<= {self.low_fps_threshold} fps):{Colors.ENDC}")
        print(f"{Colors.YELLOW}{'-'*40}{Colors.ENDC}")
        
        # Sort by framerate
        sorted_channels = sorted(self.results["low_framerate"], key=lambda x: x["info"]["framerate"])
        
        for channel in sorted_channels:
            name = channel["name"]
            fps = channel["info"]["framerate"]
            res = channel["info"]["resolution"]
            print(f"  {Colors.YELLOW}{name}{Colors.ENDC} - {fps} fps - {res}")

    def run(self):
        """Run the complete stream checking process."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}M3U-Playlist-Stream-Checker{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
        
        # Parse M3U file
        self.parse_m3u()
        
        # Check all streams
        self.check_all_streams()
        
        # Write output file
        self.write_output_file()
        
        # Print report and statistics
        self.print_report()
        
        # Print low framerate channels if any
        self.print_low_framerate_channels()

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        # Check for FFprobe
        subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print(f"{Colors.RED}Error: FFprobe not found. Please install FFmpeg/FFprobe.{Colors.ENDC}")
        print("Installation instructions:")
        print("  - Ubuntu/Debian: sudo apt install ffmpeg")
        print("  - macOS: brew install ffmpeg")
        print("  - Windows: Download from https://ffmpeg.org/download.html")
        sys.exit(1)

def validate_resolution(value):
    """Validate the resolution parameter."""
    try:
        if not re.match(r'^\d+x\d+$', value):
            raise argparse.ArgumentTypeError("Resolution must be in format WIDTHxHEIGHT")
        return value
    except Exception:
        raise argparse.ArgumentTypeError("Resolution must be in format WIDTHxHEIGHT")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description=f"{Colors.HEADER}M3U-Playlist-Stream-Checker{Colors.ENDC} - "
                    f"Check availability and quality of streams in M3U playlists",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 m3u_check.py playlist.m3u
  python3 m3u_check.py playlist.m3u -o working_channels.m3u -t 5 --threads 20
  python3 m3u_check.py playlist.m3u --verbose --only-working --low-fps 25
"""
    )
    
    parser.add_argument("input_file", help="Input M3U playlist file")
    parser.add_argument("-o", "--output", help="Output M3U file (default: input_file_working.m3u)")
    parser.add_argument("-t", "--timeout", type=int, default=5, help="Timeout in seconds for each stream check (default: 5)")
    parser.add_argument("--threads", type=int, default=10, help="Number of concurrent threads (default: 10)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output")
    parser.add_argument("--only-working", action="store_true", help="Only include working streams in output file")
    parser.add_argument("--low-fps", type=int, default=30, help="Threshold for low framerate detection in fps (default: 30)")
    parser.add_argument("--min-resolution", type=validate_resolution, default="1280x720", 
                        help="Minimum resolution for high-quality streams (default: 1280x720)")
    
    args = parser.parse_args()
    
    # Check for dependencies
    check_dependencies()
    
    # Create and run the stream checker
    checker = StreamChecker(args)
    checker.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Process interrupted by user{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}An error occurred: {str(e)}{Colors.ENDC}")
        sys.exit(1)
