from flask import Blueprint, render_template, request, redirect, url_for
import uuid
import yt_dlp
import os

main = Blueprint("main", __name__)

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@main.route('/', methods=['GET', 'POST'])
def home():
    success = None
    error = None

    if request.method == 'POST':
        url = request.form.get('url')
        format_option = request.form.get('format', 'best')
        subtitles = 'subtitles' in request.form
        metadata = 'metadata' in request.form
        thumbnail = 'thumbnail' in request.form

        video_title, filename = download_video(
            url=url,
            format_option=format_option,
            subtitles=subtitles,
            metadata=metadata,
            thumbnail=thumbnail
        )

        if video_title and filename:
            success = f"Download complete: {video_title} ({filename})"
        else:
            error = "Something went wrong with the download. Please check the URL or format."

        # Redirect to the same page to prevent resubmission
        return redirect(url_for('main.home', _anchor='form'))

    return render_template("index.html", success=success, error=error)



def download_video(url, format_option, subtitles, metadata, thumbnail):
    uid = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_FOLDER, f"{uid}.%(ext)s")

    options = {
        'format': format_option,
        'outtmpl': output_template,
        'quiet': True,
        'noplaylist': True,
        'merge_output_format': 'mp4',
    }

    if subtitles:
        options.update({
            'writesubtitles': True,
            'subtitleslangs': ['en', 'all'],
            'embedsubtitles': True
        })

    if metadata:
        options['addmetadata'] = True

    if thumbnail:
        options['writethumbnail'] = True
        options['embedthumbnail'] = True

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            # Extract video information
            info = ydl.extract_info(url, download=False)  # Don't download, just extract info
            video_title = info.get('title', 'Unknown Title')  # Get video title

            # Download the video
            ydl.extract_info(url, download=True)

            # Return video title and filename for success message
            filename = ydl.prepare_filename(info)
            return video_title, os.path.basename(filename)  # Return both title and filename
    except Exception as e:
        print("Error:", e)
        return None, None
