# VisionFlow
[中](https://github.com/dan246/VisionFlow/blob/main/README.md)
[EN](https://github.com/dan246/VisionFlow/blob/main/README_en.md)

VisionFlow is a backend application for image recognition and notification systems. The project uses the Flask framework and PostgreSQL for database management. Redis is integrated to manage the processing and distribution of camera images. All environments can be set up and managed using Docker.

## Table of Contents

- [Project Overview](#project-overview)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Setup Steps](#setup-steps)
- [Redis Features](#redis-features)
- [API Documentation](#api-documentation)
  - [User Authentication API](#user-authentication-api)
  - [Camera Management API](#camera-management-api)
  - [Notification Management API](#notification-management-api)
  - [LINE Token Management API](#line-token-management-api)
  - [Email Recipient Management API](#email-recipient-management-api)
  - [Image Processing and Streaming API](#image-processing-and-streaming-api)
- [Usage Examples](#usage-examples)
- [Notes](#notes)

## Project Overview

VisionFlow is a backend application designed to handle operations related to image recognition and notification systems. It provides user authentication, camera management, notification sending, and features related to LINE and email notifications.

## Quick Start

### Prerequisites

Before you begin, make sure you have the following tools installed:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Setup Steps

1. First, clone this project to your local environment:

    ```bash
    git clone https://github.com/yourusername/VisionFlow.git
    cd VisionFlow
    ```

2. Start the services using Docker Compose:

    ```bash
    docker-compose -f docker-compose.yaml -f docker-compose-redis.yaml up -d
    ```

    This will automatically download the necessary Docker images, install dependencies, and start the Flask application on `http://localhost:5000`.

3. If you need to migrate the database (execute this the first time or after updating models):
    1. Enter the container:
        ```bash
        docker-compose exec -it backend 
        ```
    2. Once inside, follow the steps in `update_db.txt` to complete the migration.

4. If you need to configure Redis with multiple worker nodes, use `docker-compose-redis.yaml`:

    ```bash
    docker-compose -f docker-compose-redis.yaml up -D
    ```

    This will start the Redis service along with multiple worker nodes to handle image recognition and camera distribution tasks.

5. **For object recognition:** Replace the model with your own URL and ensure the file is named `best.pt` (you can configure multiple model URLs, so the `.pt` model won’t be overwritten).

## Redis Features

### Image Processing

VisionFlow uses Redis to manage camera image data. Camera images are stored in Redis and distributed to different worker nodes for processing. Each image, once recognized, is stored as an individual Redis key for future use.

1. **Image Storage and Retrieval**:
   - The latest image from each camera is stored in Redis with the key `camera_{camera_id}_latest_frame`.
   - The recognized image is retrieved via the key `camera_{camera_id}_boxed_image`.

2. **Image Recognition Workflow**:
   - When a camera captures an image, it is stored in Redis with the key `camera_{camera_id}_latest_frame`.
   - A worker fetches the image from Redis for recognition processing and stores the processed result in `camera_{camera_id}_boxed_image`.

### Camera Assignment

To efficiently manage the image processing of multiple cameras, VisionFlow configures multiple worker nodes. These nodes distribute the workload, improving system efficiency. Each worker retrieves images from Redis for processing, ensuring system stability and scalability.

## API Documentation

### User Authentication API

- **Register New User**

    ```http
    POST /register
    ```

    **Request Body:**

    ```json
    {
        "username": "your_username",
        "email": "your_email",
        "password": "your_password"
    }
    ```

    **Response:**

    ```json
    {
        "message": "User registered successfully",
        "account_uuid": "account-uuid-string"
    }
    ```

- **User Login**

    ```http
    POST /login
    ```

    **Request Body:**

    ```json
    {
        "username": "your_username",
        "password": "your_password"
    }
    ```

    **Response:**

    ```json
    {
        "message": "Login successful",
        "account_uuid": "account-uuid-string"
    }
    ```

### Camera Management API

- **Get All Cameras**

    ```http
    GET /cameras
    ```

    **Response:**

    ```json
    [
        {
            "id": 1,
            "name": "Camera 1",
            "stream_url": "http://camera-stream-url",
            "location": "Entrance"
        },
        {
            "id": 2,
            "name": "Camera 2",
            "stream_url": "http://camera-stream-url",
            "location": "Lobby"
        }
    ]
    ```

- **Add New Camera**

    ```http
    POST /cameras
    ```

    **Request Body:**

    ```json
    {
        "name": "Camera 1",
        "stream_url": "http://camera-stream-url",
        "location": "Entrance"
    }
    ```

    **Response:**

    ```json
    {
        "message": "Camera added successfully"
    }
    ```

### Notification Management API

- **Get All Notifications**

    ```http
    GET /notifications
    ```

    **Response:**

    ```json
    [
        {
            "id": 1,
            "account_uuid": "account-uuid-string",
            "camera_id": 1,
            "message": "Detected event",
            "image_path": "/path/to/image.jpg",
            "created_at": "2023-01-01T12:00:00"
        }
    ]
    ```

- **Create New Notification**

    ```http
    POST /notifications
    ```

    **Request Body:**

    ```json
    {
        "account_uuid": "account-uuid-string",
        "camera_id": 1,
        "message": "Detected event",
        "image_path": "/path/to/image.jpg"
    }
    ```

    **Response:**

    ```json
    {
        "message": "Notification created successfully"
    }
    ```

### LINE Token Management API

- **Get All LINE Tokens**

    ```http
    GET /line_tokens
    ```

    **Response:**

    ```json
    [
        {
            "id": 1,
            "account_uuid": "account-uuid-string",
            "token": "line-token-string"
        }
    ]
    ```

- **Add New LINE Token**

    ```http
    POST /line_tokens
    ```

    **Request Body:**

    ```json
    {
        "account_uuid": "account-uuid-string",
        "token": "line-token-string"
    }
    ```

    **Response:**

    ```json
    {
        "message": "Line token added successfully"
    }
    ```

### Email Recipient Management API

- **Get All Email Recipients**

    ```http
    GET /email_recipients
    ```

    **Response:**

    ```json
    [
        {
            "id": 1,
            "account_uuid": "account-uuid-string",
            "email": "recipient@example.com"
        }
    ]
    ```

- **Add New Email Recipient**

    ```http
    POST /email_recipients
    ```

    **Request Body:**

    ```json
    {
        "account_uuid": "account-uuid-string",
        "email": "recipient@example.com"
    }
    ```

    **Response:**

    ```json
    {
        "message": "Email recipient added successfully"
    }
    ```

### Image Processing and Streaming API

- **Get Camera Status**

    ```http
    GET /camera_status
    ```

    **Response:**

    ```json
    {
        "camera_1": "active",
        "camera_2": "inactive",
        ...
    }
    ```

- **Get Latest Camera Snapshot**

    ```http
    GET /get_snapshot/<camera_id>
    ```

    **Response:**

    Returns a JPEG image stream.

- **Get Image by Path**

    ```http
    GET /image/<path:image_path>
    ```

    **Response:**

    Returns the image file at the specified path.

- **Get Real-time Image Stream**

    ```http
    GET /get_stream/<int:ID>
    ```

    **Response:**

    Returns the real-time image stream from the camera.

- **Get Recognized Real-time Image Stream**

    ```http
    GET /recognized_stream/<ID>
    ```

    **Response:**

    Returns the real-time image stream after recognition processing.

- **Display Camera Snapshot with Bounding Boxes**

    ```http
    GET /snapshot_ui/<ID>
    ```

    **Response:**

    Displays the camera snapshot with drawn bounding boxes (regions of interest). Once configured, the model will only focus on the areas inside the boxes.

- **Manage Bounding Boxes**

    ```http
    POST /rectangles/<ID>
    GET /rectangles/<ID>
    DELETE /rectangles/<ID>
    ```

    **Request Body (POST):**

    ```json
    [
        {
            "x": 100,
            "y": 200,
            "width": 50,
            "height": 60
        },
        ...
    ]
    ```

    **Response:**

    - POST: `Bounding boxes saved`
    - GET: Returns all bounding boxes for the camera.
    - DELETE: `All bounding boxes cleared`

## Usage Examples

Here are some examples of how to use the VisionFlow API:

1. **Register a new user and log in**

    ```bash
    curl -X POST http://localhost:5000/register -H "Content-Type: application/json" -d '{"username": "user1", "email": "user1@example.com", "password": "password123"}'
    curl -X POST http://localhost:5000/login -H "Content-Type: application/json" -d '{"username": "user1", "password": "password123"}'
    ```

2. **Add a new camera**

    ```bash
    curl -X POST http://localhost:5000/cameras -H "Content-Type: application/json" -d '{"name": "Camera 1", "stream_url": "http://camera-stream-url", "location": "Entrance"}'
    ```

3. **Create a new notification**

    ```bash
    curl -X POST http://localhost:5000/notifications -H "Content-Type: application/json" -d '{"account_uuid": "your-account-uuid", "camera_id": 1, "message": "Detected event", "image_path": "/path/to/image.jpg"}'
    ```

4. **Get camera status**

    ```bash
    curl -X GET http://localhost:15440/camera_status
    ```

5. **Get real-time image stream**

    ```bash
    curl -X GET http://localhost:15440/get_stream/1
    ```

6. **Get recognized real-time image stream**

    ```bash
    curl -X GET http://localhost:15440/recognized_stream/1
    ```

7. **Manage bounding boxes**

    - Save bounding boxes:

        ```bash
        curl -X POST http://localhost:15440/rectangles/1 -H "Content-Type: application/json" -d '[{"x": 100, "y": 200, "width": 50, "height": 60}]'
        ```

    - Get all bounding boxes:

        ```bash
        curl -X GET http://localhost:15440/rectangles/1
        ```

    - Clear all bounding boxes:

        ```bash
        curl -X DELETE http://localhost:15440/rectangles/1
        ```

## Notes

1. **Environment Variables**: If necessary, ensure that the `DATABASE_URL`, `SECRET_KEY`, and `REDIS_URL` are correctly set in the `.env` file. Default variables are hardcoded in the code, so you may skip this step and run the application directly.

2. **Database Migration**: To update the database or add new tables, modify the models in `\web\models\`, then run `flask db migrate` and `flask db upgrade` to apply the changes.

3. **Redis Configuration**: Use Redis to manage image storage and processing. Ensure it runs properly and is connected to the worker nodes.

4. **Docker Management**: Use Docker Compose to manage the start and stop of the application, especially when using multiple worker nodes.

5. **Data Backup**: Regularly back up your PostgreSQL database and Redis data to prevent data loss.

6. **Model Path**: Replace the model with your own model (located in `\object_recognition\app.py`).

## License

This project is licensed under the [MIT License](LICENSE).

## Contributions & Contact

If you have any questions or contributions, please feel free to contact me. Your input is very welcome and will help improve this project. You can open an issue or submit a pull request on GitHub. Alternatively, you can reach me directly via the contact details provided below.

sky328423@gmail.com
