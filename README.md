# KC4CA Image Generator

A Flask web application that leverages various AI image generation models to generate images from text prompts. The application allows users to generate images, persistently store them and their metadata in a SQLite3 database linked to user sessions, and manage their image history.

## Features

- Generate images using various AI models (DALL-E, Qwen, Flux, etc.)
- Store generated images and metadata in a SQLite3 database
- Session-based image management
- Export and import image history as JSON files
- Responsive web interface with modern UI
- Thumbnail support for reduced bandwidth usage
- Admin panel for managing all images
- Modular architecture with separate admin gallery

## Prerequisites

- Python 3.7 or higher
- API key for the image generation service
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
   Edit the `.env` file with your actual API key and other configurations

## Configuration

Edit the `.env` file to configure the application:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_API_ENDPOINT=https://api.kc4ca.com.tr/v1/images/generations
SECRET_KEY=your_secret_key_here
OPENAI_MODELS=gpt-image-1,qwen-image,imagen-4,flux.1-krea-dev,flux.1-kontext-pro,flux.1-kontext-max,v1/gpt-image-1
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

The admin panel provides a gallery view of all generated images with filtering and deletion capabilities.

## Project Structure

```
image_generator/
├── .env
├── .gitignore
├── app.py                 (Main Flask application)
├── admin_panel.py         (Admin panel blueprint)
├── requirements.txt
├── database.db            (SQLite3 database file)
├── static/
│   ├── css/
│   │   ├── style.css
│   │   ├── error.css
│   │   └── modal.css
│   ├── js/
│   │   └── main.js
│   ├── generated_images/  (Directory for storing generated image files)
│   └── thumbnails/        (Directory for storing image thumbnails)
└── templates/
    ├── index.html         (Main application template)
    └── admin_gallery.html (Admin gallery template)
```

## Dependencies

- Flask: Web framework
- python-dotenv: Environment variable management
- requests: HTTP library for API calls
- Flask-Session: Server-side session management
- Pillow: Image processing library

## License

This project is licensed under the MIT License.
