# VisionFlow

VisionFlow is a backend application designed for image recognition and notification systems. It uses the Flask framework and integrates PostgreSQL for data management. The application also leverages Redis for managing camera image processing and allocation. All environments are configured and managed using Docker.

## Table of Contents

- [Project Overview](#project-overview)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Setup Steps](#setup-steps)
- [Redis Functionality](#redis-functionality)
- [API Documentation](#api-documentation)
  - [User Authentication API](#user-authentication-api)
  - [Camera Management API](#camera-management-api)
  - [Notification Management API](#notification-management-api)
  - [LINE Token Management API](#line-token-management-api)
  - [Email Recipient Management API](#email-recipient-management-api)
  - [Image Processing and Streaming API](#image-processing-and-streaming-api)
- [Usage Examples](#usage-examples)
- [Notes](#notes)
- [License](#license)
- [Contributions & Contact](#contributions--contact)

## Project Overview

VisionFlow is a backend application aimed at handling image recognition and notification systems. The application provides user authentication, camera management, notification delivery, and integrations with LINE and email services for sending notifications.

## Quick Start

### Prerequisites

Before starting, ensure you have the following tools installed:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Setup Steps

1. Clone this project to your local environment:

    ```bash
    git clone https://github.com/yourusername/VisionFlow.git
    cd VisionFlow
    ```

2. Create a `.env` file to configure your environment variables (optional):

    ```bash
    touch .env
    ```

    Add the following content to the `.env` file:

    ```env
    DATABASE_URL=postgresql://user:password@db:5432/vision_notify
    SECRET_KEY=your_secret_key
    REDIS_URL=redis://redis:6379/0
    ```

3. Start the services using Docker Compose:

    ```bash
    docker-compose up --build
    ```

    This will automatically download the necessary Docker images, install dependencies, and start the Flask application at `http://localhost:5000`.

4. If you need to migrate the database (on the first run or when updating models):

    ```bash
    docker-compose exec backend flask db upgrade
    ```

5. To configure Redis with multiple worker nodes, use `docker-compose-redis.yaml`:

    ```bash
    docker-compose -f docker-compose-redis.yaml up --build
    ```

    This will start Redis services and multiple worker nodes to handle image recognition and camera allocation.

## Redis Functionality

### Image Processing

VisionFlow uses Redis to manage the camera image data stream. Camera images are stored in Redis and distributed to different worker nodes for processing. Each processed image is stored with a different Redis key for subsequent use.

1. **Image Storage and Retrieval**:
   - The latest image from each camera is stored in Redis under the key `camera_{camera_id}_latest_frame`.
   - The processed result after image recognition is retrieved using the key `camera_{camera_id}_boxed_image`.

2. **Image Recognition Workflow**:
   - When a camera captures an image, it is stored in Redis with the key `camera_{camera_id}_latest_frame`.
   - A worker retrieves the image from Redis for recognition processing and stores the processed result in `camera_{camera_id}_boxed_image`.

### Camera Allocation

To effectively manage image processing for multiple cameras, VisionFlow configures multiple worker nodes. These nodes help distribute the workload, improving system efficiency. Each worker retrieves camera images from Redis for processing, ensuring system stability and scalability.

## API Documentation

### User Authentication API

- **Register a New User**

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

- **Add a New Camera**

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

- **Create a New Notification**

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

- **Add a New LINE Token**

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

- **Add a New Email Recipient**

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

- **Get the Latest Snapshot from a Camera**

    ```http
    GET /get_snapshot/<camera_id>
    ```

    **Response:**

    Returns a JPEG image data stream.

- **Get an Image by Path**

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

    Returns the real-time image stream from a camera.

- **Get Recognized Image Stream**

    ```http
    GET /recognized_stream/<ID>
    ```

    **Response:**

    Returns the recognized image stream from a camera.

- **Display Snapshot with Rectangles**

    ```http
    GET /snapshot_ui/<ID>
    ```

    **Response:**

    Displays the camera snapshot along with the marked rectangles (focus areas). Once set, the model will focus only on the specified areas.

- **Manage Rectangles (Focus Areas)**

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

    - POST: `Rectangles saved successfully`
    - GET: Returns all the rectangles for the camera.
    - DELETE: `All rectangles cleared successfully`

## Usage Examples

Here are some examples of how to use the VisionFlow API:

1. **Register a New User and Login**

    ```bash
    curl -X POST http://localhost:5000/register -H "Content-Type: application/json" -d '{"username": "user1", "email": "user1@example.com", "password": "password123"}'
    curl -X POST http://localhost:5000/login -H "Content-Type: application/json" -d '{"username": "user1", "password": "password123"}'
    ```

2. **Add a New Camera**

    ```bash
    curl -X POST http://localhost:5000/cameras -H "Content-Type: application/json" -d '{"name": "Camera 1", "stream_url": "http://camera-stream-url", "location": "Entrance"}'
    ```

3. **Create a New Notification**

    ```bash
    curl -X POST http://localhost:5000/notifications -H "Content-Type: application/json" -d '{"account_uuid": "your-account-uuid", "camera_id": 1, "message": "Detected event", "image_path": "/path/to/image.jpg"}'
    ```

4. **Get Camera Status**

    ```bash
    curl -X GET http://localhost:5000/camera_status
    ```

5. **Get Real-time Image Stream**

    ```bash
    curl -X GET http://localhost:5000/get_stream/1
    ```

6. **Get Recognized Image Stream**

    ```bash
    curl -X GET http://localhost:5000/recognized_stream/1
    ```

7. **Manage Rectangles (Focus Areas)**

    - Save rectangles:

        ```bash
        curl -X POST http://localhost:5000/rectangles/1 -H "Content-Type: application/json" -d '[{"x": 100, "y": 200, "width": 50, "height": 60}]'
        ```

    - Get all rectangles:

        ```bash
        curl -X GET http://localhost:5000/rectangles/1
        ```

    - Clear all rectangles:

        ```bash
        curl -X DELETE http://localhost:5000/rectangles/1
        ```

## Notes

1. **Environment Variables**: Ensure that `DATABASE_URL`, `SECRET_KEY`, and `REDIS_URL` are correctly set in the `.env` file.
2. **Database Migration**: After updating models, run `flask db migrate` and `flask db upgrade` to apply database migrations.
3. **Redis Configuration**: Redis is used for managing image data storage and processing. Ensure that it is properly running and connected with worker nodes.
4. **Docker**: Use Docker Compose to manage the start and stop of the application, especially when running multiple worker nodes.
5. **Backup**: Regularly backup your PostgreSQL database and Redis data to prevent data loss.
6. **Model Path**: Replace the model with your own model (located in `\object_recognition\app.py`).

## License

This project is licensed under the [MIT License](LICENSE).

## Contributions & Contact

If you have any questions or would like to contribute, please feel free to contact me. Your input is very valuable and will help improve this project. You can open an issue or submit a pull request on GitHub. Alternatively, you can reach me directly using the contact details below.

Contact: sky328423@gmail.com
