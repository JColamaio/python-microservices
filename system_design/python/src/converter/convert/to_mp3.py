import json
import os
import tempfile

import moviepy.editor as mp
from bson.objectid import ObjectId


def start(message, fs_videos, fs_mp3s, channel):
    """
    Convert video to MP3 format.
    Downloads video from GridFS, converts using moviepy, uploads result.
    Returns error string on failure, None on success.
    """
    try:
        message = json.loads(message)
    except json.JSONDecodeError as e:
        return f"invalid message format: {str(e)}"

    video_fid = message.get("video_fid")
    if not video_fid:
        return "missing video_fid in message"

    # Create temp files for video and audio processing
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf_video:
        temp_video_path = tf_video.name

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf_audio:
        temp_audio_path = tf_audio.name

    try:
        # Download video from GridFS
        video_file = fs_videos.get(ObjectId(video_fid))
        with open(temp_video_path, "wb") as f:
            f.write(video_file.read())

        # Extract audio and save as MP3
        video = mp.VideoFileClip(temp_video_path)
        audio = video.audio
        audio.write_audiofile(temp_audio_path)
        audio.close()
        video.close()

        # Upload MP3 to GridFS
        with open(temp_audio_path, "rb") as f:
            mp3_fid = fs_mp3s.put(
                f,
                filename=f"{video_fid}.mp3",
            )

        # Publish notification message
        message["mp3_fid"] = str(mp3_fid)
        channel.basic_publish(
            exchange="",
            routing_key=os.environ.get("MP3_QUEUE", "mp3"),
            body=json.dumps(message),
        )

    except Exception as e:
        return f"conversion failed: {str(e)}"

    finally:
        # Cleanup temp files
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

    return None
