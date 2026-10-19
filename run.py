"""Local lab runner. Put TLS and rate limiting at a reverse proxy for production."""

from waitress import serve

from app import create_app

if __name__ == "__main__":
    serve(create_app(), host="127.0.0.1", port=5001, threads=4)
