from app import create_app
import webbrowser

app = create_app()

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == '__main__':
    # Open the browser after a short delay to ensure the server is running
    import threading
    threading.Timer(1, open_browser).start()

    # Run the Flask app
    app.run(debug=True)