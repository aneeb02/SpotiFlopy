import csv
import os
from pathlib import Path

from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

scope = "user-library-read"

load_dotenv()
client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                               client_secret=client_secret,
                                               redirect_uri=redirect_uri,
                                               scope=scope))

SONGS_TRACKER = "songs.csv"
DESKTOP_PATH = Path.home() / "Desktop" / "Songs"

# Ensure the Songs folder exists
DESKTOP_PATH.mkdir(parents=True, exist_ok=True)

def getLikedSongs():  # Get all liked songs on Spotify
    results = sp.current_user_saved_tracks(limit=50)
    all_tracks = []
    
    while results:
        for item in results['items']:
            track = item['track']
            song_name = track['name']
            artist_name = track['artists'][0]['name']
            all_tracks.append(f"{song_name} by {artist_name}")
        if results['next']:
            results = sp.next(results)
        else:
            break
    return all_tracks

def getDownloadedSongs():  # Read CSV and get already downloaded songs
    if not os.path.exists(SONGS_TRACKER):
        return []
    downloaded_songs = []
    with open(SONGS_TRACKER, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            if len(row) < 2:
                continue  # Skip rows that don't have both song name and artist
            song_name = row[0].strip() 
            artist_name = row[1].strip() 
            downloaded_songs.append(f"{song_name} by {artist_name}")
    return downloaded_songs  

def getNewSong(song, artist):  # Add the new song into the CSV file
    with open(SONGS_TRACKER, 'a', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([song, artist])

def downloadSong(song, artist):  # Download song from YouTube
    song_query = f"{song} by {artist}"
    search = VideosSearch(song_query, limit=1)
    
    result = search.result()['result'][0]
    youtube_url = result['link']
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(DESKTOP_PATH / f"{song_query}.%(ext)s"),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

def main():
    liked_songs = getLikedSongs()  # Fetch liked songs from Spotify
    downloaded_songs = getDownloadedSongs()  # Fetch already downloaded songs
    
    # Get newly added songs into a new list
    new_songs = [song for song in liked_songs if song not in downloaded_songs]
    print('\nNew Songs:', new_songs)
    
    # Download new songs and track them in the CSV
    for song in new_songs:
        try:
            song_name, artist_name = song.split(' by ', 1)
            downloadSong(song_name, artist_name)
            getNewSong(song_name, artist_name)
        except Exception as e:
            print(f"Failed to download {song}: {e}")

if __name__ == '__main__':
    main()
