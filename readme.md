# Scheduled Power Outages Platform

Live Demo: [https://apagonesrd.com](https://apagonesrd.com)

## 📖 Description

Unexpected power outages are a huge painpoint in the Dominican Republic. This projects provides a full-stack platform that scrapes official government websites for scheduled power outages and presents the data to users in a clean, searchable, and accessible web UI.

This information allows users to be more prepared by knowing the day, time, province, and sectors affected.

## 🏗️ Architecture

This project is a fully containerized, multi-container application built for a production-ready cloud deployment.

The application is managed by a single `docker-compose.yml` file and consists of three main services:

1. **Frontend (Nginx):** A production `nginx` container that serves the static `build` files from the React application. It also acts as a reverse proxy.
2. **Backend (FastAPI):** The Python API server that manages all business logic, scraping, and database communication.
3. **Database (PostgreSQL):** A dedicated Postgres container for persistent data storage.

All API requests from the browser (`/outages/`) are routed by Nginx to the backend container, creating a secure and efficient single point of entry.

## 🚀 Tech Stack

- **Frontend**: React, Nginx
- **Backend**: Python, FastAPI, SQLModel
- **Databse**: PostgreSQL
- **Scraping**: BeautifulSoup, Google Gemini API
- **DevOps**: Docker, Docker Compose
- **Deployment**: AWS

## 🏃 Getting Started (Running Locally)

This project is designed to be run with Docker. The recommended setup will build all containers and run the entire application with a single command.

#### 1. Prerequisites

- Docker & Docker Compose
- Git

**2. Recommended setup (Docker)**

1. **Clone the repository:**
```Bash
git clone https://github.com/richiedlrsa/power-outages-website
cd power-outages-website
```

2. **Open the `docker-compose.yaml` and edit your environment variables:**

`db`

```
POSTGRES_USER: your_postgres_username
POSTGRES_PASSWORD: your_postgres_password
POSTGRES_DB: outages
```

`backend`

```
- DATABASE_URL=postgresql+psycopg://your_postgres_username:your_postgres_password@db:5432/outages
- GEMINI_API_KEY=your_gemini_api_key
```

3. **Build and run the application:**

```Bash
docker-compose up -d --build
```

* `up`: Starts the container
* `-d`: Runs them in detached (background) mode 
* `--build`: Forces Docker to build your new images from your Dockerfiles 

4. **You're live!** 
* **Website**: `http://localhost` (or the port you set in `docker-compose.yml`) 
* **Backend API**: `http://localhost/outages/`

## 🛠️ Manual Local Setup (No Docker)

**Backend**

1. Navigate to the `backend` folder: `cd backend`
2. Create a virtual environment: `python -m venv .venv`
3. Activate it: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up your environment variable: `export GEMINI_API_KEY=...` `export DATABASE_URL=...`
6. Run the API: `uvicorn main:app --host 0.0.0.0 --port 8080 --reload`

**Frontend**

1. Navigate to the frontend folder: `cd frontend`
2. Install dependencies: `npm install`
3. Run the dev server: `npm run dev`
4. Your frontend will be on `http://localhost:5173`

**Note:** The frontend will likely fail to connect to the backend due to CORS errors, which the Docker/Nginx setup is designed to solve.

## 🧪 Testing

This project includes a comprehensive test suite built with `pytest` to ensure reliability.

The tests are structured to run in an isolated environment against a dedicated test dabase, ensuring that local development and production data are never affected.

**Test Environment Setup**

The test suite is designed to run agains a separate test database.

to run the test suite, set up your environment variables: `export GEMINI_API_KEY=...` `export DATABASE_URL=...`. Ensure that the database url points to the testing database.

**Test Coverage Overview**

The suite is structured to test all critical components of the API:
* `TestEdeeste` / `TestEdenorte` / `TestEdesure` (Unit Test):

- These files contain unit tests for each specific scraping class.
- They test the logic for finding the corect download links (PDFs, CSVs) for the current week,
- They test the data extraction logic `(_extract_from_pdf, _extract_from_csv)` to ensure raw data is read correctly.
- They test the `_organize_data` methods to validate that raw data is correctly transformed into the application's data models.
- They confirm that custom `ScrapeError` exceptions are raised if data is not available.

* `TestOutageEndpoint` (Integration Test):

- This is a full integration test for the FastAPI API.
- It uses a `pytest` fixture to create an isolated `SQLModel` session for the test run.
- It populates the test database with sample `DB_DATA` before running the test.
- It uses the `TestClient` to make a live `GET /outages/` request to the API.
- It asserts a `200 OK` status code and validates the entire structure of the JSON response (checking keys, data types, and list contents) to ensure the API is serving data correctly.
- It tears down all test data from the database after the test completes.