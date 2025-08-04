# KC4CA Image Generator

A Flask web application that leverages OpenAI's DALL-E models to generate images from text prompts. The application allows users to generate images, persistently store them and their metadata in a SQLite3 database linked to user sessions, and manage their image history.

## Features

- Generate images using OpenAI's DALL-E 2 and DALL-E 3 models
- Store generated images and metadata in a SQLite3 database
- Session-based image management
- Export and import image history as JSON files
- Responsive web interface with modern UI
- Admin panel for managing all images

## Prerequisites

- Python 3.7 or higher
- OpenAI API key
- pip (Python package installer)

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd openai-image-generator-website
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Rename `.env.example` to `.env`
   - Update the values in `.env` with your actual OpenAI API key and other configurations

## Configuration

Edit the `.env` file to configure the application:

```env
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
OPENAI_MODELS=dall-e-2,dall-e-3
SESSION_TYPE=filesystem
SESSION_FILE_DIR=./flask_session
DATABASE_PATH=database.db
ADMIN_PASSWORD=your_admin_password_here
```

## Usage

1. Start the Flask application:
   ```
   python app.py
   ```

2. Open your web browser and navigate to `http://localhost:5000`

3. Enter a text prompt and select your desired options to generate images

4. Use the "Export Session" button to download your image history as a JSON file

5. Use the "Import Session" button to restore a previously exported image history

## Admin Panel

Access the admin panel by navigating to `http://localhost:5000/admin?password=your_admin_password_here`

The admin panel provides a JSON view of all generated images in the database.

## Project Structure

```
image_generator/
├── .env
├── app.py
├── requirements.txt
├── database.db          (SQLite3 database file)
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
│   └── generated_images/  (Directory for storing generated image files locally)
└── templates/
    └── index.html
```

## Dependencies

- Flask: Web framework
- python-dotenv: Environment variable management
- requests: HTTP library for API calls
- Flask-Session: Server-side session management

## License

This project is licensed under the MIT License.
