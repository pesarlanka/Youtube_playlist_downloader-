import os
import re
from pytubefix import Playlist, YouTube
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_fixed

# Function to sanitize filenames
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '-', filename)


def download_playlist(playlist_url, resolution="720p"):
    playlist = Playlist(playlist_url)
    playlist_name = sanitize_filename(re.sub(r'\W+', '-', playlist.title))

    if not os.path.exists(playlist_name):
        os.mkdir(playlist_name)

    for index, video in enumerate(tqdm(playlist.videos, desc="Downloading playlist", unit="video"), start=1):
        yt = YouTube(video.watch_url, on_progress_callback=progress_function)
        video_stream = yt.streams.filter(res=resolution, file_extension="mp4").first()
        audio_stream = yt.streams.get_audio_only()

        video_filename = sanitize_filename(f"{index}. {yt.title}.mp4")
        video_path = os.path.join(playlist_name, video_filename)

        if os.path.exists(video_path):
            print(f"{video_filename} already exists")
            continue

        if not video_stream:
            print(f"Desired resolution {resolution} not available. Skipping video: {yt.title}")
            continue

        print(f"Downloading video for {yt.title} in {resolution}")
        download_with_retries(video_stream, "video.mp4")

        print(f"Downloading audio for {yt.title}")
        download_with_retries(audio_stream, "audio.mp4")

        # Merge video and audio
        os.system(
            f"ffmpeg -y -i video.mp4 -i audio.mp4 -c:v copy -c:a aac -strict experimental {sanitize_filename('final.mp4')} -loglevel quiet -stats")
        os.rename("final.mp4", video_path)
        os.remove("video.mp4")
        os.remove("audio.mp4")

        print(f"Downloaded: {yt.title}")
        print("----------------------------------")


@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
def download_with_retries(stream, filename):
    stream.download(filename=filename)


def progress_function(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    print(f"Downloading... {percentage_of_completion:.2f}% complete", end="\r")


if __name__ == "__main__":
    playlist_url = input("Enter the playlist URL: ")
    download_playlist(playlist_url, resolution="720p")