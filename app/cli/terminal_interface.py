import inquirer
from yt_dlp import YoutubeDL


def run_terminal_app():
    while True:
        url = inquirer.Text('url', message="Enter video URL")
        url = inquirer.prompt([url])['url']

        if not url:
            print("URL is required.")
            continue

        if is_playlist(url):
            confirm = inquirer.confirm("Playlist detected. Continue downloading all items?", default=True)
            if not confirm:
                print("Aborted.")
                return

        questions = [
            inquirer.Confirm('audio_only', message="Download audio only?", default=False),
            inquirer.Text('filename', message="Custom filename (optional)", default=""),
            inquirer.List('resolution', message="Choose resolution", choices=[
                "Best Available", "1080p", "720p", "480p", "360p"
            ]),
            inquirer.Confirm('chapters', message="Include chapters?", default=False),
            inquirer.Confirm('restrict', message="Restrict filenames to ASCII?", default=False),
            inquirer.Confirm('keep_original', message="Keep original file (no merge)?", default=False),
        ]

        answers = inquirer.prompt(questions)

        if not answers or not answers['url']:
            print("URL is required.")
            return

        format_option = "bestaudio/best" if answers['audio_only'] else "best"
        if answers['resolution'] != "Best Available" and not answers['audio_only']:
            format_option = f"bestvideo[height<={answers['resolution']}]+bestaudio/best"

        output_template = answers['filename'] + '.%(ext)s' if answers['filename'] else '%(title)s.%(ext)s'

        options = {
            'format': format_option,
            'outtmpl': f'downloads/{output_template}',
            'noplaylist': True,
            'quiet': False,
            'concurrent_fragment_downloads': 6,
            'restrictfilenames': answers['restrict'],
            'writesubtitles': answers['chapters'],
            'keepvideo': answers['keep_original']
        }

        with YoutubeDL(options) as ydl:
            ydl.download([answers['url']])

def is_playlist(url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,  # Speeds things up, we just want metadata
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info.get('_type') == 'playlist'
        except Exception as e:
            print(f"Error detecting playlist: {e}")
            return False
