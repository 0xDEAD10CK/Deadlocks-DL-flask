from app import create_app
from app.cli.terminal_interface import run_terminal_app
import webbrowser
import threading
import inquirer



app = create_app()

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == '__main__':
    choice = inquirer.prompt([
        inquirer.List(
            'mode',
            message="How do you want to use the downloader?",
            choices=["Web UI", "Terminal (CLI)"],
        )
    ])

    if choice and choice['mode'] == "Web UI":
        app = create_app()
        threading.Timer(1, open_browser).start()
        app.run(debug=True)
    else:
        run_terminal_app()
