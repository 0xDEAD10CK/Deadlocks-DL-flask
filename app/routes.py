from flask import Blueprint, render_template, request, jsonify
from modules.helpers import run_download_thread
from modules.progress import get_progress, update_progress
from modules.playlist import is_playlist

main = Blueprint("main", __name__)

@main.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        update_progress(status="idle", percent="0%", title="", error=None)

    if request.method == "POST":
        form = request.form
        url = form.get("url")
        if is_playlist(url):
            return render_template("index.html", error="Playlists are not supported.")

        run_download_thread(
            url=url,
            format_option=form.get("format", "best"),
            subtitles="subtitles" in form,
            metadata="metadata" in form,
            thumbnail="thumbnail" in form,
            audio_only="audio_only" in form,
            custom_filename=form.get("custom_filename", "").strip(),
            custom_dir=form.get("custom_dir", "").strip(),
            resolution=form.get("resolution"),
            chapters="chapters" in form,
            restrictfilenames="restrictfilenames" in form,
            keep_original="keep_original" in form,
        )

        return render_template("index.html", success="Download started!")

    return render_template("index.html")

@main.route("/progress")
def progress():
    return jsonify(get_progress())
