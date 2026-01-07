import json

import pika


def upload(file, fs, channel, access):
    """
    Store video file in GridFS and publish conversion message to RabbitMQ.
    Returns error tuple on failure, None on success.
    """
    try:
        file_id = fs.put(file)
    except Exception as e:
        return f"internal server error: {str(e)}", 500

    message = {
        "video_fid": str(file_id),
        "mp3_fid": None,
        "username": access["username"],
    }

    try:
        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent),
        )
    except Exception as e:
        # Rollback: remove file from GridFS if queue publish fails
        fs.delete(file_id)
        return f"internal server error: {str(e)}", 500

    return None
