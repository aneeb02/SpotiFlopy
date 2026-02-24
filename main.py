import os
import csv
import json
from pathlib import Path
from yt_dlp import YoutubeDL
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# -------------------------
# Spotify Auth
# -------------------------
scope = "user-library-read"

load_dotenv()
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope=scope
))

# -------------------------
# Config
# -------------------------

DEFAULT_BASE_PATH = Path.home() / "Desktop" / "Songs"
CONFIG_FILE = Path.home() / ".spotiflopy_config.json"


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(config: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


def choose_download_folder(force_change=False) -> Path:
    config = load_config()

    # If folder already saved and not forcing change
    if not force_change and "base_path" in config:
        saved_path = Path(config["base_path"])
        print(f"📁 Using saved download folder: {saved_path}")
        saved_path.mkdir(parents=True, exist_ok=True)
        return saved_path

    print("\n📁 Download Folder Setup")
    print(f"Default folder: {DEFAULT_BASE_PATH}")

    user_input = input("Enter custom download folder path (or press Enter to use default): ").strip()

    if user_input:
        folder = Path(os.path.expanduser(user_input))
    else:
        folder = DEFAULT_BASE_PATH

    folder.mkdir(parents=True, exist_ok=True)

    config["base_path"] = str(folder)
    save_config(config)

    print(f"✅ Downloads will be saved to: {folder}\n")
    return folder


# -------------------------
# Helpers
# -------------------------

def sanitize(text: str) -> str:
    """
    Safe filename sanitizer.
    - Replaces slashes with dash instead of removing them
    - Removes invalid filesystem characters
    - Prevents accidental folder creation from '/'
    """

    if not text:
        return "unknown"

    # Replace forward and backward slashes with dash
    text = text.replace("/", " - ")
    text = text.replace("\\", " - ")

    # Remove other invalid characters
    invalid_chars = r':*?"<>|'
    text = "".join(c for c in text if c not in invalid_chars)

    # Clean extra spaces/dashes
    text = " ".join(text.split())
    text = text.strip(" -")

    return text.strip()


def search_youtube(query: str) -> str:
    with YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=False)
        if not info["entries"]:
            raise ValueError(f"No results for {query}")
        return f"https://www.youtube.com/watch?v={info['entries'][0]['id']}"


def get_liked_songs():
    results = sp.current_user_saved_tracks(limit=50)
    songs = []

    while results:
        for item in results["items"]:
            track = item["track"]
            song = track["name"]
            artist = track["artists"][0]["name"]
            album = track["album"]["name"]
            track_number = track["track_number"]
            songs.append((song, artist, album, track_number))
        results = sp.next(results) if results["next"] else None

    return songs


def already_downloaded(base_path: Path, artist: str, album: str, track_number: int, track_name: str) -> bool:
    file_path = base_path / sanitize(artist) / sanitize(album) / f"{track_number:02d} - {sanitize(track_name)}.mp3"
    return file_path.exists()


def save_to_csv(csv_path: Path, artist: str, album: str, track_name: str, track_number: int):
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([artist, album, track_name, track_number])


def download_song(base_path: Path, track_name: str, artist: str, album: str, track_number: int):
    query = f"{track_name} {artist} official audio"
    youtube_url = search_youtube(query)

    artist_folder = base_path / sanitize(artist)
    album_folder = artist_folder / sanitize(album)
    album_folder.mkdir(parents=True, exist_ok=True)

    output_template = str(album_folder / f"{track_number:02d} - {sanitize(track_name)}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            },
            {"key": "FFmpegMetadata"},
            {"key": "EmbedThumbnail"}
        ],
        "quiet": False,
        "addmetadata": True,
        "embedthumbnail": True,
        "ffmpeg_postprocessor_args": ["-af", "loudnorm"]
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])


# -------------------------
# Main
# -------------------------

def main():
    change = "--change-folder" in os.sys.argv
    base_path = choose_download_folder(force_change=change)

    songs_tracker = base_path / "songs.csv"
    if not songs_tracker.exists():
        with open(songs_tracker, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Artist", "Album", "Track", "Track Number"])

    liked_songs = get_liked_songs()
    print(f"\nFound {len(liked_songs)} liked songs.\n")

    for track_name, artist, album, track_number in liked_songs:
        try:
            if already_downloaded(base_path, artist, album, track_number, track_name):
                print(f"Skipping: {track_number:02d} - {track_name} - {artist}")
                continue

            print(f"Downloading: {track_number:02d} - {track_name} - {artist}")
            download_song(base_path, track_name, artist, album, track_number)
            save_to_csv(songs_tracker, artist, album, track_name, track_number)

        except Exception as e:
            print(f"Failed: {track_number:02d} - {track_name} - {artist} -> {e}")


if __name__ == "__main__":
    main()