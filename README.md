RecipeApp
This project is a FastAPI-based web application designed for managing and discovering recipes. It features a modular structure with dedicated routing for authentication and recipe management, utilizing SQLAlchemy for database interactions and Jinja2 for template rendering.

Project Structure
Based on the provided files, the application is organized as follows:

app/main.py: The entry point of the FastAPI application. It configures the app, mounts static files, includes routers, and manages the initial database metadata creation.

app/routers/: Contains the logic for different application segments, specifically auth.py for user authentication and recipe.py for recipe-related operations.

app/static/: Stores static assets like CSS and JavaScript files.

app/templates/: Contains HTML templates for the user interface (e.g., home, login, register, and recipe pages).

Dockerfile & docker-compose.yml: Configuration files for containerizing the application.

Features
AI Integration: The project includes dependencies for langchain and google-generativeai, suggesting capabilities for AI-driven features or discovery.

Authentication: Dedicated authentication routing and models to manage user access.

Recipe Management: Tools to view, add, and edit recipes through a web interface.

Database Support: Uses SQLAlchemy with PostgreSQL (psycopg2-binary) support and Alembic for migrations.

Getting Started
Prerequisites
Docker and Docker Compose installed on your machine.

Installation & Setup
Build and Run with Docker:
The easiest way to get the application running is using Docker Compose. This will build the image based on the provided Dockerfile and start the service.

Bash
docker-compose up --build
Access the Application:
Once the container is running, the application will be available at http://localhost:80.

The root URL (/) will automatically redirect you to the main recipe page (/recipe/recipe-page).

Manual Setup (Optional)
If you prefer to run the application locally without Docker:

Install Dependencies:

Bash
pip install -r requirements.txt
Run the Server:

Bash
uvicorn app.main:app --host 0.0.0.0 --port 80 --reload
Technologies Used
Backend: FastAPI, Uvicorn

Database: SQLAlchemy, Alembic, PostgreSQL

Templates: Jinja2, Markdown

AI/ML: LangChain, Google Generative AI

Containerization: Docker
