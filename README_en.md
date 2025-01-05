# VisionFlow

[中文](./README.md) | [English](./README_en.md)

VisionFlow is a backend application designed for image recognition and notification systems. This project is developed using the Flask framework, with PostgreSQL for database management and Redis for handling and distributing camera streams. All environments can be configured and managed via Docker.

This project documents the learning journey from theoretical studies to practical implementation, exploring the integration of image recognition and backend system development.

---

## Feature Interface Showcase

### Login Interface
Users can log in by entering their account credentials to access the management system.
![Login Interface](./readme_image/login.PNG)

### Registration Interface
Provides users with the ability to create new accounts, ensuring flexible user rights management.
![Registration Interface](./readme_image/register.PNG)

### Recognition Stream
Displays real-time recognition results from the camera, including images and detected objects.
- Supports multi-camera stream display.
- Displays object labels based on model output.
![Recognition Stream](./readme_image/stream_interface.PNG)

### Camera Management
Allows users to add, modify, delete cameras, and assign recognition models to each camera.
- Each camera can be bound to a different model.
- Configure camera parameters (e.g., URL, name, location).
![Camera Management](./readme_image/camera_management.PNG)

### Detection Area Drawing (Optional)
Users can draw multiple regions of interest (ROI) and set individual alert durations and notification periods for each region.
- Supports polygonal drawing.
- Allows separate parameter settings for each region.
![Detection Area Drawing](./readme_image/detection_area.PNG)

---

## Quick Start

### Prerequisites

Ensure you have the following tools installed before starting:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Setup Steps

1. Clone the project to your local environment:

    ```bash
    git clone https://github.com/yourusername/VisionFlow.git
    cd VisionFlow
    ```

2. Start the services using Docker Compose:

    ```bash
    docker-compose -f docker-compose.yaml -f docker-compose-redis.yaml up -d
    ```

    This will automatically download the required Docker images, install necessary packages, and launch the Flask application at `http://localhost:5000`.

3. Migrate the database (run on the first launch or after model updates):

    ```bash
    docker-compose exec backend flask db upgrade
    ```

4. Configure Redis and multiple worker nodes:

    ```bash
    docker-compose -f docker-compose-redis.yaml up -d
    ```

5. Update the `objectrecognition` module with your model URL or PATH and ensure the file is named `best.pt`.

6. Verify the application is running:

    Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## API Documentation

For detailed API usage, refer to the [API Documentation](./API_Doc.md).

- Supports APIs for image stream processing.
- Provides interfaces for switching and managing recognition models.
- Offers RESTful APIs for camera management.

---

## Development & Testing

### Local Environment

1. Create a virtual environment and install dependencies:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2. Start the Flask development server:

    ```bash
    flask run
    ```

3. Run tests:

    ```bash
    pytest tests/
    ```

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Contributions & Contact

If you have any questions or would like to contribute to this project, feel free to contact me.

- Email: sky328423@gmail.com
- GitHub Issues: [Issues](https://github.com/yourusername/VisionFlow/issues)

Contributions and suggestions are always welcome!
