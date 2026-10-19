import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import pytest

from app import add_user, create_app, get_db, init_db


@pytest.fixture(scope="module")
def lab(tmp_path_factory):
    app = create_app({"TESTING": True, "JWT_SECRET_KEY": secrets.token_hex(32),
                      "DATABASE": str(tmp_path_factory.mktemp("db") / "test.sqlite3")})
    with app.app_context():
        init_db()
        add_user("alice", "Alice-Lab-Password-2026!")
        add_user("bob", "Bob-Lab-Password-2026!")
    return app


@pytest.fixture
def client(lab):
    return lab.test_client()


def auth(client, name="alice"):
    password = {"alice": "Alice-Lab-Password-2026!", "bob": "Bob-Lab-Password-2026!"}[name]
    r = client.post("/auth/login", json={"login": name, "password": password})
    assert r.status_code == 200
    return {"Authorization": "Bearer " + r.json["access_token"]}


@pytest.mark.parametrize("path,method", [("/api/data", "get"), ("/api/notes", "post")])
def test_requires_token(client, path, method):
    assert getattr(client, method)(path).status_code == 401


def test_login_and_read(client):
    r = client.get("/api/data", headers=auth(client))
    assert r.status_code == 200
    assert r.json["login"] == "alice"
    assert "password" not in r.get_data(as_text=True)


@pytest.mark.parametrize("login,password", [
    ("alice", "wrong"), ("missing", "wrong"), ("' OR 1=1 --", "anything"),
    ("alice' --", "anything"), ("alice", "a" * 73),
])
def test_bad_credentials_and_sqli(client, login, password):
    assert client.post("/auth/login", json={"login": login, "password": password}).status_code == 401


@pytest.mark.parametrize("payload", [[], {}, {"login": [] , "password": {}},
                                    {"login": "alice", "password": "a", "extra": 1}])
def test_invalid_json_shape(client, payload):
    assert client.post("/auth/login", json=payload).status_code == 400


def test_json_errors(client):
    assert client.post("/auth/login", data="broken", content_type="application/json").status_code == 400
    assert client.post("/auth/login", data="text").status_code == 415
    assert client.post("/auth/login", data="x" * 20000, content_type="application/json").status_code == 413


@pytest.mark.parametrize("kind", ["expired", "signature", "audience", "issuer", "missing_exp", "unknown_user", "none", "future"])
def test_reject_invalid_jwt(client, lab, kind):
    now = datetime.now(timezone.utc)
    claims = {"sub": "1", "exp": now + timedelta(minutes=10), "iat": now, "nbf": now,
              "iss": "work1-api", "aud": "work1-client", "jti": "test-id"}
    key = lab.config["JWT_SECRET_KEY"]
    algorithm = "HS256"
    if kind == "expired":
        claims["exp"] = now - timedelta(seconds=1)
    elif kind == "signature":
        key = secrets.token_hex(32)
    elif kind == "audience":
        claims["aud"] = "other"
    elif kind == "issuer":
        claims["iss"] = "other"
    elif kind == "missing_exp":
        del claims["exp"]
    elif kind == "unknown_user":
        claims["sub"] = "99999"
    elif kind == "none":
        algorithm, key = "none", None
    elif kind == "future":
        claims["nbf"] = now + timedelta(hours=1)
    token = jwt.encode(claims, key, algorithm=algorithm)
    assert client.get("/api/data", headers={"Authorization": "Bearer " + token}).status_code == 401


def test_xss_and_stored_sql_and_ownership(client):
    headers = auth(client)
    title = "<script>alert('xss')</script>"
    body = "'); DROP TABLE users; -- <img src=x onerror=alert(1)> & \""
    r = client.post("/api/notes", headers=headers, json={"title": title, "body": body})
    assert r.status_code == 201
    assert "<script>" not in r.json["title"]
    assert "&lt;script&gt;" in r.json["title"]
    assert "&lt;img" in r.json["body"]
    note_id = r.json["id"]
    alice_notes = client.get("/api/data", headers=headers).json["notes"]
    assert next(n for n in alice_notes if n["id"] == note_id) == r.json
    assert note_id not in [n["id"] for n in client.get("/api/data", headers=auth(client, "bob")).json["notes"]]
    assert client.get("/api/data", headers=auth(client)).status_code == 200


@pytest.mark.parametrize("payload", [{"title": "", "body": "x"}, {"title": "x" * 101, "body": ""},
                                    {"title": "x", "body": "x" * 2001}, {"title": 1, "body": []}])
def test_note_validation(client, payload):
    assert client.post("/api/notes", headers=auth(client), json=payload).status_code == 400


def test_password_storage(lab):
    with lab.app_context():
        rows = get_db().execute("SELECT password_hash FROM users ORDER BY id").fetchall()
        hashed = rows[0]["password_hash"]
        assert hashed.startswith(b"$2b$12$")
        assert bcrypt.checkpw(b"Alice-Lab-Password-2026!", hashed)
        assert hashed != b"Alice-Lab-Password-2026!"


def test_security_headers(client):
    r = client.get("/api/data")
    assert r.mimetype == "application/json"
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["Cache-Control"] == "no-store"
    assert "default-src 'none'" in r.headers["Content-Security-Policy"]


def test_startup_rejects_weak_key():
    with pytest.raises(RuntimeError):
        create_app({"JWT_SECRET_KEY": "short"})
