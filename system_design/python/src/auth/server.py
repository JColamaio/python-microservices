import datetime
import os

import jwt
from flask import Flask, jsonify, request
from flask_mysqldb import MySQL

server = Flask(__name__)
mysql = MySQL(server)

# MySQL configuration from environment
server.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
server.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
server.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
server.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")
server.config["MYSQL_PORT"] = int(os.environ.get("MYSQL_PORT", 3306))


def create_jwt(username, secret, is_admin):
    """Generate a JWT token with user claims and 24h expiration."""
    return jwt.encode(
        {
            "username": username,
            "exp": datetime.datetime.now(tz=datetime.timezone.utc)
            + datetime.timedelta(days=1),
            "iat": datetime.datetime.now(tz=datetime.timezone.utc),
            "admin": is_admin,
        },
        secret,
        algorithm="HS256",
    )


@server.route("/login", methods=["POST"])
def login():
    """Authenticate user credentials against MySQL and return JWT."""
    auth = request.authorization
    if not auth:
        return "missing credentials", 401

    cur = mysql.connection.cursor()
    res = cur.execute(
        "SELECT email, password FROM user WHERE email=%s", (auth.username,)
    )

    if res > 0:
        user_row = cur.fetchone()
        email = user_row[0]
        password = user_row[1]

        if auth.username != email or auth.password != password:
            return "invalid credentials", 401
        else:
            return create_jwt(auth.username, os.environ.get("JWT_SECRET"), True)
    else:
        return "invalid credentials", 401


@server.route("/validate", methods=["POST"])
def validate():
    """Validate JWT token from Authorization header."""
    encoded_jwt = request.headers.get("Authorization")

    if not encoded_jwt:
        return "missing credentials", 401

    # Extract token from "Bearer <token>" format
    parts = encoded_jwt.split(" ")
    if len(parts) != 2:
        return "invalid token format", 401

    token = parts[1]

    try:
        decoded = jwt.decode(token, os.environ.get("JWT_SECRET"), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return "token expired", 401
    except jwt.InvalidTokenError:
        return "not authorized", 403

    return jsonify(decoded), 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=5000)
