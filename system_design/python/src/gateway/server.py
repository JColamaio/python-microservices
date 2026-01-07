import io
import json
import os

import gridfs
import pika
from auth_svc import access
from bson.objectid import ObjectId
from flask import Flask, request, send_file
from flask_pymongo import PyMongo
from storage import util

server = Flask(__name__)

# MongoDB configuration
mongo_host = os.environ.get("MONGO_HOST", "host.minikube.internal")
mongo_port = os.environ.get("MONGO_PORT", "27017")
server.config["MONGO_URI"] = f"mongodb://{mongo_host}:{mongo_port}/videos"

mongo_videos = PyMongo(server)
fs_videos = gridfs.GridFS(mongo_videos.db)

# Secondary MongoDB connection for mp3s
mongo_mp3s = PyMongo(server, uri=f"mongodb://{mongo_host}:{mongo_port}/mp3s")
fs_mp3s = gridfs.GridFS(mongo_mp3s.db)

# RabbitMQ connection
rabbitmq_host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
channel = connection.channel()


@server.route("/login", methods=["POST"])
def login():
    """Proxy login request to authentication service."""
    token, err = access.login(request)

    if not err:
        return token
    else:
        return err


@server.route("/upload", methods=["POST"])
def upload():
    """Handle video file upload for authenticated admin users."""
    access_data, err = access.validate_token(request)

    if err:
        return err

    access_data = json.loads(access_data)

    if not access_data.get("admin"):
        return "not authorized", 401

    if len(request.files) != 1:
        return "exactly 1 file required", 400

    for _, f in request.files.items():
        err = util.upload(f, fs_videos, channel, access_data)

        if err:
            return err

    return "success", 200


@server.route("/download", methods=["GET"])
def download():
    """Download converted MP3 file by file ID."""
    access_data, err = access.validate_token(request)

    if err:
        return err

    access_data = json.loads(access_data)

    if not access_data.get("admin"):
        return "not authorized", 401

    fid = request.args.get("fid")
    if not fid:
        return "file id required", 400

    try:
        mp3_file = fs_mp3s.get(ObjectId(fid))
        return send_file(
            io.BytesIO(mp3_file.read()),
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name=f"{fid}.mp3",
        )
    except Exception:
        return "file not found", 404


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)
