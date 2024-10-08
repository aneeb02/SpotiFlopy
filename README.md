# SpotiFlopy
Automatically download all your liked songs on Spotify, without paying a dime.

## **Features** 🚀
- Automatically fetches and downloads your Spotify Liked Songs.
- Downloads audio from YouTube using `yt-dlp`.
- Stores downloaded MP3s in a folder on your desktop.

---

## **How It Works** ⚙️
1. The script uses the Spotify API to get all your Liked Songs.
2. It compares your Liked Songs with songs already downloaded.
3. New songs are searched on YouTube and downloaded in MP3 format using `yt-dlp`.
4. The downloaded songs are saved to the **Songs** folder on your desktop.

---

## **Installation Instructions** 🔧

### 1. Clone the Repository:
```bash
git clone https://github.com/yourusername/yourprojectname.git
cd yourprojectname
```

## 2. Install Dependencies:
Make sure you have Python 3 installed. Then install the required packages:
```bash
pip install -r requirements.txt
```

## 3. Set Up Spotify API Credentials:
1. Create a .env file in the root directory of the project.
2. Add your Spotify API credentials in the .env file:

```env
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
SPOTIPY_REDIRECT_URI=http://localhost:8888/callback/
```
## 4. Run the script
```bash
python main.py
```


