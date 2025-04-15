download_progress = {
    "percent": "0%",
    "status": "idle",
    "title": "",
    "error": None,
}

def get_progress():
    return download_progress

def update_progress(percent=None, status=None, title=None, error=None):
    if percent is not None:
        download_progress["percent"] = percent
    if status is not None:
        download_progress["status"] = status
    if title is not None:
        download_progress["title"] = title
    if error is not None:
        download_progress["error"] = error
