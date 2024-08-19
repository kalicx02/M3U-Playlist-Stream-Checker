import requests
import sys
import os

# ANSI escape codes for colors
class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

def check_stream(url):
    """Check if the stream URL is accessible."""
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def process_playlist(input_file, output_file):
    """Process the M3U playlist and save active streams to the output file."""
    with open(input_file, 'r') as file:
        lines = file.readlines()
    
    # Check if the output file exists and remove it if it does
    if os.path.exists(output_file):
        os.remove(output_file)

    with open(output_file, 'w') as file:
        i = 0
        while i < len(lines):
            if lines[i].startswith('#EXTINF'):
                stream_info = lines[i].strip()
                url = lines[i + 1].strip()
                if check_stream(url):
                    file.write(f"{stream_info}\n{url}\n")
                    print(f"{Color.GREEN}Active stream found: {stream_info} - {url}{Color.RESET}")
                else:
                    print(f"{Color.YELLOW}Inactive stream: {stream_info} - {url}{Color.RESET}")
                i += 2
            else:
                i += 1

def main():
    if len(sys.argv) != 2:
        print(f"{Color.RED}Usage: python3 m3u_check.py <input_playlist.m3u>{Color.RESET}")
        sys.exit(1)

    input_playlist = sys.argv[1]
    output_playlist = 'active_streams.m3u'

    if not os.path.exists(input_playlist):
        print(f"{Color.RED}Input file '{input_playlist}' does not exist.{Color.RESET}")
        sys.exit(1)

    process_playlist(input_playlist, output_playlist)
    print(f"{Color.GREEN}Active streams have been saved to {output_playlist}{Color.RESET}")

if __name__ == "__main__":
    main()
