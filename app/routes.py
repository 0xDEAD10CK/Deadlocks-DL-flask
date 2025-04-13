from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import uuid
import yt_dlp
import os
import re
import threading  # Import threading to handle background tasks
from modules.playlist import is_playlist  # Import the is_playlist function from the modules

# Create a Flask Blueprint for the main routes
main = Blueprint("main", __name__)

# Define the folder where downloads will be saved
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)  # Ensure the folder exists

# Global dictionary to track the progress of the current download
download_progress = {
    "percent": "0%",  # Percentage of download completed
    "status": "idle",  # Current status: 'idle', 'downloading', 'done', or 'error'
    "title": "",  # Title of the video being downloaded
    "error": None,  # Error message, if any
}


# Background thread function to handle video downloads
def run_download(
    url,
    format_option,
    subtitles,
    metadata,
    thumbnail,
    audio_only=False,
    custom_filename="",
    resolution="",
    chapters=False,
    restrictfilenames=False,
    keep_original=False,
):
    global download_progress

    # Reset progress for the new download
    download_progress = {
        "percent": "0%",
        "status": "downloading",
        "title": "",
        "error": None,
    }

    try:
        # Call the download_video function to perform the download
        video_title, filename = download_video(
            url=url,
            format_option=format_option,
            subtitles=subtitles,
            metadata=metadata,
            thumbnail=thumbnail,
            audio_only=audio_only,
            custom_filename=custom_filename,
            resolution=resolution,
            chapters=chapters,
            restrictfilenames=restrictfilenames,
            keep_original=keep_original,
        )

        # Update progress on success
        if filename:
            download_progress["status"] = "done"
            download_progress["title"] = video_title
            download_progress["percent"] = "100%"
        else:
            download_progress["status"] = "error"
            download_progress["error"] = "Download failed."

    except Exception as e:
        # Handle errors during the download
        download_progress["status"] = "error"
        download_progress["error"] = str(e)


# Route to handle the homepage and video download requests
@main.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        # Reset progress when the page is loaded
        download_progress["status"] = "idle"
        download_progress["percent"] = "0%"
        download_progress["title"] = ""
        download_progress["error"] = None

    if request.method == "POST":
        # Extract form data from the POST request
        url = request.form.get("url")
        format_option = request.form.get("format", "best")
        subtitles = "subtitles" in request.form
        metadata = "metadata" in request.form
        thumbnail = "thumbnail" in request.form
        audio_only = "audio_only" in request.form
        custom_filename = request.form.get("custom_filename", "").strip()
        custom_folder = request.form.get("custom_dir", "").strip()
        resolution = request.form.get("resolution")
        chapters = "chapters" in request.form
        restrictfilenames = "restrictfilenames" in request.form
        keep_original = "keep_original" in request.form

        if is_playlist(url):
            return render_template(
                "index.html",
                success=None,
                error="Playlist detected. Please provide a single video URL. Playlists are not supported."
            )
    
        # Start the download in a background thread
        thread = threading.Thread(
            target=run_download,
            args=(
                url,
                format_option,
                subtitles,
                metadata,
                thumbnail,
                audio_only,
                custom_filename,
                custom_folder,
                resolution,
                chapters,
                restrictfilenames,
                keep_original,
            ),
        )
        thread.start()

        # Render the template with a success message
        return render_template(
            "index.html", success="Download started! Check progress below.", error=None
        )

    # Render the homepage template
    success = request.args.get("success")
    error = request.args.get("error")
    return render_template("index.html", success=success, error=error)


# Function to handle the actual video download using yt_dlp
def download_video(
    url,
    format_option,
    subtitles,
    metadata,
    thumbnail,
    audio_only=False,
    custom_filename="",
    custom_folder="",
    resolution="",
    chapters=False,
    restrictfilenames=False,
    keep_original=False,
):
    global download_progress

    # Reset progress for the new download
    download_progress = {
        "percent": "0%",
        "status": "downloading",
        "title": "",
        "error": None,
    }

    # Hook function to update progress during the download
    def hook(d):
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")  # Regex to remove ANSI escape codes

        if d["status"] == "downloading":
            # Update progress percentage and title
            raw_percent = d.get("_percent_str", "0%")
            clean_percent = ansi_escape.sub("", raw_percent).strip()
            download_progress["percent"] = clean_percent
            download_progress["title"] = os.path.basename(
                d.get("filename", "Downloading...")
            )

        elif d["status"] == "finished":
            # Mark download as complete
            download_progress["percent"] = "100%"
            download_progress["status"] = "done"

    # Fetch video metadata to prepare for download
    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        video_title = info.get("title", "video")
        ext = info.get("ext", "mp4")

    # Prepare the output filename
    if custom_filename:
        safe_name = "".join(
            c for c in custom_filename if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
    else:
        safe_name = "".join(
            c for c in video_title if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()

    output_template = os.path.join(DOWNLOAD_FOLDER, f"{safe_name}.%(ext)s")

    # Configure yt_dlp options for the download
    options = {
        "format": format_option,
        "outtmpl": output_template,
        "quiet": True,
        "noplaylist": True,
        "concurrent_fragment_download": 10,
        "progress_hooks": [hook],
    }

    # Adjust options based on user input
    if resolution:
        options["format"] = (
            f"bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]"
        )

    if audio_only:
        options.update(
            {
                "format": "bestaudio",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
                "merge_output_format": "mp3",
            }
        )
    else:
        options["merge_output_format"] = "mp4"

    if subtitles:
        options.update(
            {
                "writesubtitles": True,
                "subtitleslangs": ["en", "all"],
                "embedsubtitles": True,
            }
        )

    if metadata:
        options["addmetadata"] = True

    if thumbnail:
        options["writethumbnail"] = True
        options["embedthumbnail"] = True

    if chapters:
        options["embedchapters"] = True

    if restrictfilenames:
        options["restrictfilenames"] = True

    if keep_original:
        options["keepvideo"] = True

    try:
        # Perform the download
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return video_title, filename

    except Exception as e:
        # Handle errors during the download
        download_progress["status"] = "error"
        download_progress["error"] = str(e)
        return None


# Endpoint to allow the frontend to fetch the current download progress
@main.route("/progress")
def get_progress():
    return jsonify(download_progress)


