import os
import uuid
import json
import base64
import sqlite3
import requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_file, session
from flask_session import Session

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure app settings from environment variables
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SESSION_TYPE'] = os.getenv('SESSION_TYPE')
app.config['SESSION_FILE_DIR'] = os.getenv('SESSION_FILE_DIR')
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# Initialize Flask-Session
Session(app)

# Database path
DATABASE_PATH = os.getenv('DATABASE_PATH')
SESSION_FILE_DIR = os.getenv('SESSION_FILE_DIR')

# Create necessary directories
os.makedirs(SESSION_FILE_DIR, exist_ok=True)
os.makedirs('static/generated_images', exist_ok=True)

def init_db():
    """Initialize the SQLite database and create the images table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            prompt TEXT NOT NULL,
            model TEXT NOT NULL,
            size TEXT NOT NULL,
            quality TEXT,
            response_format TEXT NOT NULL,
            image_path TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create admin table for admin panel
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def save_image_to_server(image_data, format, filename_prefix):
    """
    Save image data to the server.
    
    Args:
        image_data: Image data (URL, data URL, or base64)
        format: Format of the image data ('url' or 'b64_json')
        filename_prefix: Prefix for the filename
    
    Returns:
        str: Relative path to the saved image
    """
    filename = f"{filename_prefix}_{uuid.uuid4().hex}.png"
    filepath = os.path.join('static/generated_images', filename)
    
    if format == 'url':
        # Handle different types of URLs
        if image_data.startswith('data:image'):
            # Handle data URL (data:image/png;base64,...)
            header, encoded = image_data.split(',', 1)
            image_bytes = base64.b64decode(encoded)
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
        else:
            # Handle regular URL
            response = requests.get(image_data)
            with open(filepath, 'wb') as f:
                f.write(response.content)
    elif format == 'b64_json':
        # Handle base64 data
        if image_data:
            image_bytes = base64.b64decode(image_data)
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
        else:
            # If b64_json is None, we can't save the image
            raise ValueError("Base64 data is None")
    
    return f"/static/generated_images/{filename}"

# Initialize the database when the app starts
init_db()

@app.route('/')
def index():
    """Render the main page with image generation form and history."""
    # Get available models from environment
    models = os.getenv('OPENAI_MODELS', 'dall-e-2,dall-e-3').split(',')
    
    # Get images for current session
    images = []
    if 'sid' in session:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT prompt, model, size, quality, image_path, timestamp 
            FROM images 
            WHERE session_id = ? 
            ORDER BY timestamp DESC
        ''', (session['sid'],))
        images = cursor.fetchall()
        conn.close()
    
    # Convert to list of dictionaries for template
    image_data = []
    for img in images:
        image_data.append({
            'prompt': img[0],
            'model': img[1],
            'size': img[2],
            'quality': img[3],
            'image_path': img[4],
            'timestamp': img[5]
        })
    
    return render_template('index.html', models=models, images=image_data)

@app.route('/generate_image', methods=['POST'])
def generate_image():
    """Generate an image using OpenAI's DALL-E API."""
    try:
        # Get parameters from request
        data = request.get_json()
        prompt = data.get('prompt')
        model = data.get('model')
        n = int(data.get('n', 1))
        size = data.get('size')
        quality = data.get('quality', 'standard')
        
        # Validate parameters
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Ensure session ID exists
        if 'sid' not in session:
            session['sid'] = str(uuid.uuid4())
            session.permanent = True
        
        # Prepare request to OpenAI API
        api_key = os.getenv('OPENAI_API_KEY')
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': model,
            'prompt': prompt,
            'n': n,
            'size': size
        }
        
        # Add quality parameter for DALL-E 3
        if model == 'dall-e-3':
            payload['quality'] = quality
        
        # Make request to OpenAI API
        api_endpoint = os.getenv('OPENAI_API_ENDPOINT', 'https://api.openai.com/v1/images/generations')
        response = requests.post(
            api_endpoint,
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            return jsonify({'error': f'OpenAI API error: {response.text}'}), response.status_code
        
        # Process API response
        api_response = response.json()
        generated_images = []
        
        # Save images and metadata to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        for image in api_response['data']:
            try:
                # Auto-detect image data format
                image_data = None
                image_format = None
                
                # Check for URL data
                if image.get('url'):
                    image_data = image['url']
                    image_format = 'url'
                # Check for base64 data
                elif image.get('b64_json'):
                    image_data = image['b64_json']
                    image_format = 'b64_json'
                
                # If we found image data, save it
                if image_data and image_format:
                    # Save image to server
                    image_path = save_image_to_server(
                        image_data, 
                        image_format, 
                        'generated_image'
                    )
                    
                    # Save metadata to database
                    cursor.execute('''
                        INSERT INTO images 
                        (session_id, prompt, model, size, quality, response_format, image_path)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        session['sid'], 
                        prompt, 
                        model, 
                        size, 
                        quality, 
                        image_format, 
                        image_path
                    ))
                    
                    # Add to response
                    generated_images.append({
                        'prompt': prompt,
                        'model': model,
                        'size': size,
                        'quality': quality,
                        'image_path': image_path
                    })
                else:
                    # No image data found
                    print("No image data found in API response")
                    continue
            except Exception as e:
                # If there's an error saving this image, continue with others
                print(f"Error saving image: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return jsonify({'images': generated_images})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export_session')
def export_session():
    """Export current session images as JSON file."""
    try:
        if 'sid' not in session:
            return jsonify({'error': 'No session found'}), 400
        
        # Get images for current session
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT prompt, model, size, quality, response_format, image_path, timestamp 
            FROM images 
            WHERE session_id = ? 
            ORDER BY timestamp DESC
        ''', (session['sid'],))
        
        images = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        image_data = []
        for img in images:
            image_data.append({
                'prompt': img[0],
                'model': img[1],
                'size': img[2],
                'quality': img[3],
                'response_format': img[4],
                'image_path': img[5],
                'timestamp': img[6]
            })
        
        # Create JSON file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'image_history_{timestamp}.json'
        filepath = os.path.join('static/generated_images', filename)
        
        with open(filepath, 'w') as f:
            json.dump(image_data, f, indent=2)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/import_session', methods=['POST'])
def import_session():
    """Import session images from JSON file."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Ensure session ID exists
        if 'sid' not in session:
            session['sid'] = str(uuid.uuid4())
            session.permanent = True
        
        # Parse JSON data
        image_data = json.load(file)
        
        # Save to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        imported_count = 0
        for img in image_data:
            # Check if image file exists
            if os.path.exists(img['image_path'].replace('/static/', 'static/')):
                cursor.execute('''
                    INSERT INTO images 
                    (session_id, prompt, model, size, quality, response_format, image_path, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session['sid'],
                    img['prompt'],
                    img['model'],
                    img['size'],
                    img['quality'],
                    img['response_format'],
                    img['image_path'],
                    img['timestamp'] if 'timestamp' in img else datetime.now().isoformat()
                ))
                imported_count += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': f'Successfully imported {imported_count} images',
            'imported_count': imported_count
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin')
def admin():
    """Admin panel to view and manage images."""
    # Simple password protection (in a real app, you'd want proper authentication)
    admin_password = os.getenv('ADMIN_PASSWORD')
    provided_password = request.args.get('password')
    
    if not provided_password or provided_password != admin_password:
        return jsonify({'error': 'Unauthorized access'}), 401
    
    # Get all images from database
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, session_id, prompt, model, size, quality, image_path, timestamp 
        FROM images 
        ORDER BY timestamp DESC
    ''')
    
    images = cursor.fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    image_data = []
    for img in images:
        image_data.append({
            'id': img[0],
            'session_id': img[1],
            'prompt': img[2],
            'model': img[3],
            'size': img[4],
            'quality': img[5],
            'image_path': img[6],
            'timestamp': img[7]
        })
    
    return jsonify({'images': image_data})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
