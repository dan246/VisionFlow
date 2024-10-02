# VisionFlow

[Chinese](https://github.com/dan246/VisionFlow/blob/main/README.md) | [EN](https://github.com/dan246/VisionFlow/blob/main/README_en.md)

VisionFlow is a backend application designed for image recognition and notification systems. This project utilizes the Flask framework and leverages PostgreSQL for data management. Redis is integrated to handle the processing and distribution of camera images. All environments can be configured and managed using Docker.

## Table of Contents

- [Project Introduction](#project-introduction)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Setup Steps](#setup-steps)
- [Redis Features](#redis-features)
  - [Image Processing](#image-processing)
  - [Image Recognition and Annotation](#image-recognition-and-annotation)
  - [Camera Allocation](#camera-allocation)
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
- [References](#references)

## Project Introduction

VisionFlow is a backend application aimed at handling operations related to image recognition and notification systems. The application provides functionalities for user authentication, camera management, notification sending, as well as integration with LINE and email notifications.

## Quick Start

### Prerequisites

Before you begin, ensure you have the following tools installed:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Setup Steps

1. **Clone the Project to Your Local Environment:**

    ```bash
    git clone https://github.com/yourusername/VisionFlow.git
    cd VisionFlow
    ```

2. **Start the Services Using Docker Compose:**

    ```bash
    docker-compose -f docker-compose.yaml -f docker-compose-redis.yaml up -d
    ```

    This command will automatically download the required Docker images, install the necessary packages, and start the Flask application on `http://localhost:5000`.

3. **Migrate the Database (Run during First Setup or After Model Updates):**
    1. **Enter the Container:**
        ```bash
        docker-compose exec -it backend 
        ```
    2. **Follow the Instructions in `update_db.txt`:**
        - Execute the commands as specified in the `update_db.txt` file to migrate the database.

4. **Configure Redis and Multiple Worker Nodes:**

    If you need to set up Redis with multiple worker nodes, use the `docker-compose-redis.yaml` file:

    ```bash
    docker-compose -f docker-compose-redis.yaml up -d
    ```

    This will start the Redis service along with multiple worker nodes to handle image recognition and camera allocation tasks.

5. **Replace Models in `objectrecognition`:**

    Replace the models with your own model URLs, ensuring the files are named `best.pt`. You can set multiple model URLs without worrying about `.pt` models being overwritten.

## Redis Features

### Image Processing

VisionFlow uses Redis to manage camera image data. Camera images are stored in Redis and distributed to different worker nodes for processing. Each image, after recognition, is stored as a separate Redis key for subsequent use.

1. **Image Storage and Retrieval:**
   - The latest image from each camera is stored in Redis using the key `camera_{camera_id}_latest_frame`.
   - Access the processed image results via `camera_{camera_id}_boxed_image`.

2. **Image Recognition Workflow:**
   - When a camera captures an image, it is stored in Redis with the key `camera_{camera_id}_latest_frame`.
   - Workers extract the image from Redis for recognition processing and store the processed image result in `camera_{camera_id}_boxed_image`.

### Image Recognition and Annotation

VisionFlow integrates the [Supervision](https://github.com/roboflow/supervision) library to perform image recognition and annotation. Supervision provides various annotation tools such as `BoxAnnotator`, `RoundBoxAnnotator`, and `LabelAnnotator`, enabling intuitive visualization of recognition results on images.

In the `MainApp` class, we utilize the following Supervision functionalities:

- **Annotators:**
  - `BoxAnnotator`: Draws rectangular boxes around detected objects.
  - `RoundBoxAnnotator`: Draws rounded rectangular boxes around detected objects.
  - `LabelAnnotator`: Annotates detected objects with text labels, including class names and confidence scores.
  - `TraceAnnotator`: Tracks the movement trajectory of objects.

- **Trackers:**
  - Utilizes `ByteTrack` to track objects within images, ensuring each object has a unique ID across multiple frames for easier analysis and annotation.

- **Recognition Process:**
  1. Perform object detection using the YOLO model.
  2. Convert detection results to Supervision's `Detections` format.
  3. Update the tracker to obtain the latest object states.
  4. Filter detection results based on target labels.
  5. Use annotators to draw detection boxes and labels on the image.
  6. Save the annotated image and notify the relevant systems.

These features ensure the system can efficiently and accurately process and annotate image data from multiple cameras, enhancing overall user experience and system stability.

### Camera Allocation

To efficiently manage image processing from multiple cameras, VisionFlow configures multiple worker nodes. These nodes distribute the processing workload, enhancing system efficiency. Each worker extracts camera images from Redis for processing, ensuring system stability and scalability.

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

- **Get All Cameras List**

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

- **Get Latest Snapshot from a Camera**

    ```http
    GET /get_snapshot/<camera_id>
    ```

    **Response:**

    Returns a JPEG image data stream directly.

- **Retrieve Image from a Specific Path**

    ```http
    GET /image/<path:image_path>
    ```

    **Response:**

    Returns the image file from the specified path.

- **Get Live Image Stream**

    ```http
    GET /get_stream/<int:ID>
    ```

    **Response:**

    Returns a live image stream from the specified camera.

- **Get Live Image Stream with Recognition**

    ```http
    GET /recognized_stream/<ID>
    ```

    **Response:**

    Returns a live image stream that has been processed for recognition.

- **Display Camera Snapshot and Rectangle Areas**

    ```http
    GET /snapshot_ui/<ID>
    ```

    **Response:**

    Displays the camera snapshot along with drawn rectangle areas (focus areas) using an HTML template. After setting, the model will only focus on the areas within the rectangles.

- **Manage Rectangle Areas**

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

    - **POST:** `Rectangles saved`
    - **GET:** Returns all rectangle areas for the specified camera.
    - **DELETE:** `All rectangles cleared`

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
    curl -X GET http://localhost:15440/camera_status
    ```

5. **Get Live Image Stream from a Camera**

    ```bash
    curl -X GET http://localhost:15440/get_stream/1
    ```

6. **Get Live Image Stream with Recognition**

    ```bash
    curl -X GET http://localhost:15440/recognized_stream/1
    ```

7. **Manage Rectangle Areas**

    - **Save Rectangle Areas:**

        ```bash
        curl -X POST http://localhost:15440/rectangles/1 -H "Content-Type: application/json" -d '[{"x": 100, "y": 200, "width": 50, "height": 60}]'
        ```

    - **Get All Rectangle Areas:**

        ```bash
        curl -X GET http://localhost:15440/rectangles/1
        ```

    - **Clear All Rectangle Areas:**

        ```bash
        curl -X DELETE http://localhost:15440/rectangles/1
        ```

## Notes

1. **Environment Variables:** If needed, ensure that `DATABASE_URL`, `SECRET_KEY`, and `REDIS_URL` are correctly set in the `.env` file. Defaults are provided in the code, so you can skip this step if necessary.

2. **Database Migration:** To update the database or add new tables, after modifying `web/models/`, execute `flask db migrate` and `flask db upgrade` to update the database schema.

3. **Redis Configuration:** Use Redis to manage image data storage and processing. Ensure Redis is running properly and connected to worker nodes.

4. **Docker Startup:** Use Docker Compose to manage the application’s startup and shutdown, especially when needing to start multiple worker nodes.

5. **Data Backup:** Regularly back up your PostgreSQL database and Redis data to prevent data loss.

6. **Model Paths:** Replace models with your own models (located in `object_recognition/app.py`).

## License

This project is licensed under the [MIT License](LICENSE).

## Contributions & Contact

If you have any questions or would like to contribute to this project, please feel free to contact me. Your feedback is highly valuable and will help improve the project. You can open an issue or submit a pull request on GitHub. Alternatively, you can reach me directly through the contact details provided below.

### Contact & Contributions

If you have any questions or would like to contribute to this project, please feel free to contact me. Your feedback is highly valuable and will help improve the project. You can open an issue or submit a pull request on GitHub. Alternatively, you can reach me directly through the contact details provided below.

sky328423@gmail.com

## References

- [Supervision by Roboflow](https://github.com/roboflow/supervision)
