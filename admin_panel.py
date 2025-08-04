import os
import sqlite3
from flask import Blueprint, render_template, request, jsonify, current_app
from PIL import Image
import math

# Create a blueprint for the admin panel
admin_bp = Blueprint('admin', __name__)

def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(current_app.config.get('DATABASE_PATH', 'database.db'))
    conn.row_factory = sqlite3.Row
    return conn

def generate_thumbnail(image_path, thumbnail_path, size=(200, 200)):
    """
    Generate a thumbnail for the given image.
    
    Args:
        image_path: Path to the original image
        thumbnail_path: Path where the thumbnail should be saved
        size: Tuple of (width, height) for the thumbnail
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for PNG files with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Create thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            img.save(thumbnail_path, 'JPEG', quality=80)
            return True
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return False

@admin_bp.route('/admin')
def admin_gallery():
    """Admin gallery to view all generated images."""
    # Check password protection
    admin_password = current_app.config.get('ADMIN_PASSWORD')
    provided_password = request.args.get('password')
    
    if not provided_password or provided_password != admin_password:
        return "Unauthorized access. Please provide the correct password.", 401
    
    # Get filter parameters
    session_id = request.args.get('session_id', '')
    prompt = request.args.get('prompt', '')
    model = request.args.get('model', '')
    
    # Get unique session IDs and models for dropdowns
    conn = get_db_connection()
    session_ids = conn.execute('SELECT DISTINCT session_id FROM images ORDER BY session_id').fetchall()
    models = conn.execute('SELECT DISTINCT model FROM images ORDER BY model').fetchall()
    conn.close()
    
    # Convert to lists
    session_id_list = [row[0] for row in session_ids]
    model_list = [row[0] for row in models]
    
    # Get pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    # Build query with filters
    query = "SELECT * FROM images WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM images WHERE 1=1"
    params = []
    
    if session_id:
        query += " AND session_id = ?"
        count_query += " AND session_id = ?"
        params.append(session_id)
    
    if prompt:
        query += " AND prompt LIKE ?"
        count_query += " AND prompt LIKE ?"
        params.append(f"%{prompt}%")
    
    if model:
        query += " AND model = ?"
        count_query += " AND model = ?"
        params.append(model)
    
    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    
    # Get total count
    conn = get_db_connection()
    count_params = params.copy()
    total_count = conn.execute(count_query, count_params).fetchone()[0]
    
    # Add pagination params
    params.extend([per_page, (page - 1) * per_page])
    
    # Get images for current page
    images = conn.execute(query, params).fetchall()
    conn.close()
    
    # Calculate pagination
    total_pages = math.ceil(total_count / per_page)
    
    # Convert to list of dictionaries
    image_data = []
    for img in images:
        # Generate thumbnail if it doesn't exist
        thumbnail_path = img['image_path'].replace('/static/generated_images/', '/static/thumbnails/thumb_')
        thumbnail_full_path = thumbnail_path.replace('/static/', 'static/')
        
        if not os.path.exists(thumbnail_full_path):
            original_path = img['image_path'].replace('/static/', 'static/')
            os.makedirs(os.path.dirname(thumbnail_full_path), exist_ok=True)
            generate_thumbnail(original_path, thumbnail_full_path)
        
        image_data.append({
            'id': img['id'],
            'session_id': img['session_id'],
            'prompt': img['prompt'],
            'model': img['model'],
            'size': img['size'],
            'quality': img['quality'],
            'image_path': img['image_path'],
            'thumbnail_path': thumbnail_path,
            'timestamp': img['timestamp']
        })
    
    return render_template('admin_gallery.html', 
                          images=image_data,
                          current_page=page,
                          total_pages=total_pages,
                          total_count=total_count,
                          session_id=session_id,
                          prompt=prompt,
                          model=model,
                          session_id_list=session_id_list,
                          model_list=model_list)

@admin_bp.route('/admin/delete_image/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    """Delete an image from the database and file system."""
    # Check password protection
    admin_password = current_app.config.get('ADMIN_PASSWORD')
    provided_password = request.args.get('password')
    
    if not provided_password or provided_password != admin_password:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 401
    
    try:
        conn = get_db_connection()
        image = conn.execute('SELECT image_path FROM images WHERE id = ?', (image_id,)).fetchone()
        
        if image:
            # Delete from database
            conn.execute('DELETE FROM images WHERE id = ?', (image_id,))
            conn.commit()
            
            # Delete image files
            image_path = image['image_path'].replace('/static/', 'static/')
            thumbnail_path = image_path.replace('generated_images/', 'thumbnails/thumb_')
            
            if os.path.exists(image_path):
                os.remove(image_path)
            
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            
            conn.close()
            return jsonify({'success': True, 'message': 'Image deleted successfully'})
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Image not found'}), 404
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
