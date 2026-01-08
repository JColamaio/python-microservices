import os
import sys

import gridfs
import pika
from convert import to_mp3
from pymongo import MongoClient


def main():
    """Main consumer loop for video conversion queue."""
    mongo_host = os.environ.get("MONGO_HOST", "host.minikube.internal")
    mongo_port = int(os.environ.get("MONGO_PORT", 27017))

    client = MongoClient(mongo_host, mongo_port)
    db_videos = client.videos
    db_mp3s = client.mp3s

    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    # RabbitMQ connection
    rabbitmq_host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()

    def callback(ch, method, properties, body):
        err = to_mp3.start(body, fs_videos, fs_mp3s, ch)
        if err:
            print(f"Conversion error: {err}")
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    video_queue = os.environ.get("VIDEO_QUEUE", "video")
    channel.basic_consume(queue=video_queue, on_message_callback=callback)

    print("Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(0)
