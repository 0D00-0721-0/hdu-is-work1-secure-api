"""Work 1: authenticated, owner-scoped notes API."""

import os
import re
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps
from html import escape
from pathlib import Path

import bcrypt
import click
import jwt
from flask import Flask, current_app, g, jsonify, request
from werkzeug.exceptions import HTTPException


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=5)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def init_db():
    get_db().executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL UNIQUE,
            password_hash BLOB NOT NULL
        );
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title TEXT NOT NULL,
            body TEXT NOT NULL
        );
        """
    )
    get_db().commit()


def add_user(login, password):
    if not re.fullmatch(r"[A-Za-z0-9_]{3,32}", login):
        raise ValueError("Login must contain 3-32 ASCII letters, digits or underscores")
    encoded = password.encode("utf-8")
    if len(password) < 12 or len(encoded) > 72:
        raise ValueError("Password must be at least 12 characters and at most 72 UTF-8 bytes")
    hashed = bcrypt.hashpw(encoded, bcrypt.gensalt(rounds=12))
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO users (login, password_hash) VALUES (?, ?)", (login, hashed)
        )
        db.execute(
            "INSERT INTO notes (user_id, title, body) VALUES (?, ?, ?)",
            (cursor.lastrowid, "Welcome", "Your private notes are ready."),
        )


def require_jwt(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        authorization = request.headers.get("Authorization", "").split()
        if len(authorization) != 2 or authorization[0].lower() != "bearer":
            return jsonify(error="Bearer token required"), 401
        try:
            claims = jwt.decode(
                authorization[1],
                current_app.config["JWT_SECRET_KEY"],
                algorithms=["HS256"],
                issuer="work1-api",
                audience="work1-client",
                options={"require": ["sub", "exp", "iat", "nbf", "iss", "aud", "jti"]},
            )
            if not isinstance(claims["sub"], str) or not claims["sub"].isdigit():
                raise jwt.InvalidTokenError("Invalid subject")
            user = get_db().execute(
                "SELECT id, login FROM users WHERE id = ?", (claims["sub"],)
            ).fetchone()
            if user is None:
                raise jwt.InvalidTokenError("Unknown subject")
        except jwt.InvalidTokenError:
            return jsonify(error="Invalid or expired token"), 401
        g.user = user
        return view(*args, **kwargs)

    return wrapped


def json_object():
    data = request.get_json()
    if not isinstance(data, dict):
        return None
    return data


def safe_note(row):
    # Escape at the output boundary; store original text, avoiding double escaping.
    return {"id": row["id"], "title": escape(row["title"], quote=True),
            "body": escape(row["body"], quote=True)}


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY"),
        DATABASE=os.environ.get("DATABASE_PATH", str(Path(app.instance_path) / "work1.sqlite3")),
        MAX_CONTENT_LENGTH=16 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    secret = app.config["JWT_SECRET_KEY"]
    if not isinstance(secret, str) or len(secret.encode("utf-8")) < 32:
        raise RuntimeError("Set JWT_SECRET_KEY to a random secret of at least 32 bytes")
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    # Equal-cost verification also runs for an unknown login.
    dummy_hash = bcrypt.hashpw(os.urandom(32), bcrypt.gensalt(rounds=12))

    @app.teardown_appcontext
    def close_db(_error):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.name), error.code

    @app.cli.command("init-db")
    def init_db_command():
        """Create tables without dropping existing data."""
        init_db()
        click.echo("Database initialized")

    @app.cli.command("create-user")
    @click.option("--login", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True,
                  envvar="LAB_PASSWORD")
    def create_user_command(login, password):
        """Create a user; passwords are never printed."""
        try:
            add_user(login, password)
        except (ValueError, sqlite3.IntegrityError) as error:
            raise click.ClickException(str(error)) from error
        click.echo("User created (bcrypt cost 12)")

    @app.post("/auth/login")
    def login():
        data = json_object()
        if data is None or set(data) != {"login", "password"}:
            return jsonify(error="Expected login and password"), 400
        name, password = data["login"], data["password"]
        if not isinstance(name, str) or not isinstance(password, str):
            return jsonify(error="Credentials must be strings"), 400
        if not 1 <= len(name) <= 128 or not 1 <= len(password.encode("utf-8")) <= 72:
            return jsonify(error="Invalid credentials"), 401
        user = get_db().execute(
            "SELECT id, password_hash FROM users WHERE login = ?", (name,)
        ).fetchone()
        hashed = user["password_hash"] if user else dummy_hash
        valid = bcrypt.checkpw(password.encode("utf-8"), hashed)
        if user is None or not valid:
            return jsonify(error="Invalid credentials"), 401
        now = datetime.now(timezone.utc)
        token = jwt.encode(
            {"sub": str(user["id"]), "iat": now, "nbf": now,
             "exp": now + timedelta(minutes=15), "iss": "work1-api",
             "aud": "work1-client", "jti": str(uuid.uuid4())},
            app.config["JWT_SECRET_KEY"], algorithm="HS256",
        )
        # Bandit B105 treats the standard authentication scheme label as a password.
        return jsonify({"access_token": token, "token_type": "Bearer", "expires_in": 900})  # nosec B105

    @app.get("/api/data")
    @require_jwt
    def data():
        rows = get_db().execute(
            "SELECT id, title, body FROM notes WHERE user_id = ? ORDER BY id", (g.user["id"],)
        ).fetchall()
        return jsonify(login=escape(g.user["login"], quote=True), notes=[safe_note(row) for row in rows])

    @app.post("/api/notes")
    @require_jwt
    def create_note():
        data = json_object()
        if data is None or set(data) != {"title", "body"}:
            return jsonify(error="Expected title and body"), 400
        title, body = data["title"], data["body"]
        if not isinstance(title, str) or not isinstance(body, str):
            return jsonify(error="Note values must be strings"), 400
        if not title.strip() or len(title) > 100 or len(body) > 2000:
            return jsonify(error="Title: 1-100 characters; body: at most 2000 characters"), 400
        db = get_db()
        with db:
            cursor = db.execute(
                "INSERT INTO notes (user_id, title, body) VALUES (?, ?, ?)",
                (g.user["id"], title, body),
            )
        return jsonify(safe_note({"id": cursor.lastrowid, "title": title, "body": body})), 201

    return app
