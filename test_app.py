from browse_app import app

if __name__ == "__main__":
    app.run('127.0.0.1', 8888,
            debug=True, threaded=True)