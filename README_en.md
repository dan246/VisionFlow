# VisionFlow

[Chinese](./README.md) | [EN](./README_en.md)

**VisionFlow** is a backend application designed for image recognition and notification systems.  
The project is built using the **Flask** framework, with **PostgreSQL** as the database for data management. It integrates **Redis** to handle and distribute camera image processing effectively.  
All environments are managed and configured via **Docker** for seamless deployment.

This project serves as a personal learning journal, exploring the integration of image recognition and backend systems from theoretical understanding to practical application.

---

## Features Overview

### Login Interface
![Login Interface](./readme_image/login.PNG)

### Registration Interface
![Registration Interface](./readme_image/register.PNG)

### Recognition Stream
![Recognition Stream](./readme_image/stream_interface.PNG)

### Camera Management
![Camera Management](./readme_image/camera_management.PNG)

### Detection Area Drawing
![Detection Area Drawing](./readme_image/detection_area.PNG)

---

## Quick Start

### Prerequisites

Before you begin, ensure you have the following tools installed:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Setup Steps

1. Clone the repository to your local environment:

    ```bash
    git clone https://github.com/yourusername/VisionFlow.git
    cd VisionFlow
    ```

2. Start the service using Docker Compose:

    ```bash
    docker-compose -f docker-compose.yaml -f docker-compose-redis.yaml up -d
    ```

    This will automatically download the required Docker images, install dependencies, and start the Flask application at `http://localhost:5000`.

3. If database migration is needed (e.g., during the first run or after model updates):

    ```bash
    docker-compose exec backend flask db upgrade
    ```

4. Configure Redis and multiple worker nodes:

    ```bash
    docker-compose -f docker-compose-redis.yaml up -d
    ```

5. Update the `objectrecognition` module with your model's URL or PATH, ensuring the file is named `best.pt`.

---

## API Documentation

For detailed API usage, please refer to the [API Documentation](./API_Doc.md).

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Contributions & Contact

If you have any questions or wish to contribute to this project, feel free to contact me.

Email: sky328423@gmail.com
