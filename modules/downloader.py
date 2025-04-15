import os
import re
import yt_dlp
from modules.progress import update_progress

DOWNLOAD_FOLDER = "downloads"

def download_video(
    url,
    format_option,
    subtitles,
    metadata,
    thumbnail,
    audio_only=False,
    custom_filename="",
    custom_dir="",
    resolution="",
    chapters=False,
    restrictfilenames=False,
    keep_original=False,
):
    os.makedirs(os.path.join(DOWNLOAD_FOLDER, custom_dir), exist_ok=True)

    def hook(d):
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        if d["status"] == "downloading":
            percent = ansi_escape.sub("", d.get("_percent_str", "0%")).strip()
            title = os.path.basename(d.get("filename", "Downloading..."))
            update_progress(status="downloading", percent=percent, title=title)
        elif d["status"] == "finished":
            update_progress(status="done", percent="100%")

    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        video_title = info.get("title", "video")

    if custom_filename:
        safe_name = "".join(c for c in custom_filename if c.isalnum() or c in (" ", "-", "_")).rstrip()
    else:
        safe_name = "".join(c for c in video_title if c.isalnum() or c in (" ", "-", "_")).rstrip()

    output_template = os.path.join(DOWNLOAD_FOLDER, custom_dir, f"{safe_name}.%(ext)s")

    options = {
        "format": format_option,
        "outtmpl": output_template,
        "quiet": True,
        "noplaylist": True,
        "concurrent_fragment_download": 10,
        "progress_hooks": [hook],
    }

    if resolution:
        options["format"] = f"bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]"

    if audio_only:
        options.update({
            "format": "bestaudio",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "merge_output_format": "mp3",
        })
    else:
        options["merge_output_format"] = "mp4"

    if subtitles:
        options.update({
            "writesubtitles": True,
            "subtitleslangs": ["en", "all"],
            "embedsubtitles": True,
        })

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
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return video_title, filename
    except Exception as e:
        update_progress(status="error", error=str(e))
        return None, None
