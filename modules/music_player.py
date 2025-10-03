import yt_dlp
import subprocess

def search_youtube_music(query, max_results=5):
    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist',
        'default_search': 'ytsearch',
        'skip_download': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            search_result = ydl.extract_info(query, download=False)
            entries = search_result.get('entries', [])
            return entries[:max_results]
        except Exception as e:
            print(f"❌ YouTube Search Failed: {e}")
            return []

def play_music_from_url(url):
    global music_process
    try:

        music_process = subprocess.Popen(["mpv", "--no-video", url],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        print("🎵 Now playing...")
    except Exception as e:
        print(f"🚫 Error playing music: {e}")

def stop_music():
    global music_process
    if music_process and music_process.poll() is None:
        music_process.terminate()
        print("🛑 Music stopped.")
        music_process = None
        return True
    else:
        print("⚠️ No music is currently playing.")
        return False