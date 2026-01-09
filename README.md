# Video to MP3 Converter - Microservices Architecture

A distributed system for converting video files to MP3 audio format, built with Python microservices.

## Architecture

```
                                    ┌─────────────┐
                                    │    MySQL    │
                                    │  (users db) │
                                    └──────▲──────┘
                                           │
┌──────────┐     ┌──────────────┐    ┌─────┴─────┐
│  Client  │────▶│   Gateway    │───▶│   Auth    │
└──────────┘     │   (8080)     │    │  (5000)   │
                 └──────┬───────┘    └───────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ MongoDB  │  │ RabbitMQ │  │ MongoDB  │
    │ (videos) │  │  (queue) │  │  (mp3s)  │
    └──────────┘  └────┬─────┘  └──────────┘
                       │
                 ┌─────▼─────┐
                 │ Converter │
                 │ (workers) │
                 └───────────┘
```

## Services

### Auth Service
Authentication service with JWT token generation and validation.
- **Port:** 5000
- **Endpoints:**
  - `POST /login` - Authenticate and get JWT token
  - `POST /validate` - Validate JWT token

### Gateway
API Gateway handling client requests and routing.
- **Port:** 8080
- **Endpoints:**
  - `POST /login` - Proxy to auth service
  - `POST /upload` - Upload video for conversion (admin only)
  - `GET /download?fid=<file_id>` - Download converted MP3

### Converter
Background worker consuming video conversion jobs from RabbitMQ.
- Converts video to MP3 using FFmpeg/MoviePy
- Stores results in MongoDB GridFS

## Tech Stack

- **Python 3.10** with Flask
- **MongoDB** with GridFS for file storage
- **MySQL** for user authentication
- **RabbitMQ** for async job processing
- **Kubernetes** for orchestration
- **Docker** for containerization

## Project Structure

```
system_design/python/src/
├── auth/                   # Authentication service
│   ├── server.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manifests/          # K8s manifests
├── gateway/                # API Gateway
│   ├── server.py
│   ├── auth_svc/           # Auth service client
│   ├── storage/            # GridFS utilities
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manifests/
├── converter/              # Video converter worker
│   ├── consumer.py
│   ├── convert/            # Conversion logic
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manifests/
└── rabbit/                 # RabbitMQ manifests
    └── manifests/
```

## Local Development

### Prerequisites
- Docker and Kubernetes (minikube)
- MySQL database with user table
- MongoDB instance
- RabbitMQ instance

### Environment Variables

**Auth Service:**
```
MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_PORT
JWT_SECRET
```

**Gateway:**
```
AUTH_SVC_ADDRESS
MONGO_HOST, MONGO_PORT
RABBITMQ_HOST
```

**Converter:**
```
MONGO_HOST, MONGO_PORT
RABBITMQ_HOST
VIDEO_QUEUE, MP3_QUEUE
```

## Deployment

Apply Kubernetes manifests in order:
```bash
kubectl apply -f system_design/python/src/rabbit/manifests/
kubectl apply -f system_design/python/src/auth/manifests/
kubectl apply -f system_design/python/src/gateway/manifests/
kubectl apply -f system_design/python/src/converter/manifests/
```

## API Usage

### Login
```bash
curl -X POST http://mp3converter.com/login \
  -u email@example.com:password
```

### Upload Video
```bash
curl -X POST http://mp3converter.com/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@video.mp4"
```

### Download MP3
```bash
curl -X GET "http://mp3converter.com/download?fid=<file_id>" \
  -H "Authorization: Bearer <token>" \
  --output audio.mp3
```

## License

MIT
