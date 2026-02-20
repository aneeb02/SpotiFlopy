import os
import csv
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
# Paths
# -------------------------
BASE_PATH = Path.home() / "Desktop" / "Songs"
BASE_PATH.mkdir(parents=True, exist_ok=True)

SONGS_TRACKER = BASE_PATH / "songs.csv"
if not SONGS_TRACKER.exists():
    with open(SONGS_TRACKER, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Artist", "Album", "Track", "Track Number"])  # header

# -------------------------
# Helpers
# -------------------------

def sanitize(text: str) -> str:
    """Remove filesystem-invalid characters."""
    return "".join(c for c in text if c not in r'\/:*?"<>|').strip()


def search_youtube(query: str) -> str:
    """Return first YouTube result URL."""
    with YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=False)
        if not info["entries"]:
            raise ValueError(f"No results for {query}")
        return f"https://www.youtube.com/watch?v={info['entries'][0]['id']}"


def get_liked_songs():
    """Return list of (track_name, artist_name, album_name, track_number)."""
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


def already_downloaded(artist: str, album: str, track_number: int, track_name: str) -> bool:
    file_path = BASE_PATH / sanitize(artist) / sanitize(album) / f"{track_number:02d} - {sanitize(track_name)}.mp3"
    return file_path.exists()


def save_to_csv(artist: str, album: str, track_name: str, track_number: int):
    with open(SONGS_TRACKER, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([artist, album, track_name, track_number])


def download_song(track_name: str, artist: str, album: str, track_number: int):
    query = f"{track_name} {artist} official audio"
    youtube_url = search_youtube(query)

    artist_folder = BASE_PATH / sanitize(artist)
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
            {
                "key": "FFmpegMetadata"
            },
            {
                "key": "EmbedThumbnail"
            }
        ],
        "quiet": False,
        "addmetadata": True,
        "embedthumbnail": True,
        "ffmpeg_postprocessor_args": ["-af", "loudnorm"]  # normalize volume
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])


# -------------------------
# Main
# -------------------------

def main():
    liked_songs = get_liked_songs()
    print(f"\nFound {len(liked_songs)} liked songs.\n")

    for track_name, artist, album, track_number in liked_songs:
        try:
            if already_downloaded(artist, album, track_number, track_name):
                print(f"Skipping (already exists): {track_number:02d} - {track_name} - {artist}")
                continue

            print(f"Downloading: {track_number:02d} - {track_name} - {artist}")
            download_song(track_name, artist, album, track_number)
            save_to_csv(artist, album, track_name, track_number)

        except Exception as e:
            print(f"Failed: {track_number:02d} - {track_name} - {artist} -> {e}")


if __name__ == "__main__":
    main()