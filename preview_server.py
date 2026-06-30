"""Browser-preview launcher: runs only the Flask layer (no native webview window)
so the UI can be inspected in a normal browser during development."""
import app

if __name__ == "__main__":
    app.app.run(debug=False, port=5000, threaded=True, use_reloader=False)
