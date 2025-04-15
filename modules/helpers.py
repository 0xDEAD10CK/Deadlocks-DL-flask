import threading
from modules.downloader import download_video
from modules.progress import update_progress

def run_download_thread(**kwargs):
    update_progress(percent="0%", status="downloading", title="", error=None)

    def task():
        title, filename = download_video(**kwargs)
        if filename:
            update_progress(status="done", percent="100%", title=title)
        else:
            update_progress(status="error", error="Download failed.")

    thread = threading.Thread(target=task)
    thread.start()
