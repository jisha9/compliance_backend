# backend/app.py → MySQL VERSION

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from dotenv import load_dotenv
import pymysql
from pymysql.cursors import DictCursor

from models.user import User, init_db
from utils.compliance_rules import get_requirements

# ==================== ENV & DB HELPER ====================

load_dotenv()  # loads .env file if present

def get_db_connection():
    """
    Create a new MySQL connection using env vars.
    Used here for the delete-document endpoint.
    (User model will use similar logic inside models/user.py)
    """
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "myuser"),
        password=os.getenv("DB_PASSWORD", "mypassword"),
        database=os.getenv("DB_NAME", "compliance_app"),
        charset="utf8mb4",
        cursorclass=DictCursor,
    )
    return conn

# ==================== FLASK APP ====================

app = Flask(__name__)
app.secret_key = "compliance-final-2025"
CORS(app, supports_credentials=True)

# Uploads folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

init_db()
login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# ==================== AUTH ====================

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    if User.create(data.get("username"), data.get("password")):
        return jsonify({"message": "Registered"})
    return jsonify({"error": "Username taken"}), 400

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    user = User.validate(data.get("username"), data.get("password"))
    if user:
        login_user(user)
        return jsonify({"message": "Logged in", "username": user.username})
    return jsonify({"error": "Wrong credentials"}), 401

@app.route("/api/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out"})

# ==================== CHECK ====================

@app.route("/api/check", methods=["POST"])
@login_required
def check():
    data = request.get_json() or {}
    result = get_requirements(
        data.get("country"),
        data.get("entityType"),
        data.get("productCategory")
    )
    return jsonify(result)

# ==================== UPLOAD ====================

@app.route("/api/upload", methods=["POST"])
@login_required
def upload_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    doc_name = request.form.get("document_name")
    full_filename = f"{current_user.id}_{doc_name.replace(' ', '_')}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], full_filename)
    file.save(filepath)

    # Save only prefix in DB
    prefix = f"{current_user.id}_{doc_name.replace(' ', '_')}_"
    User.save_document(
        current_user.id,
        request.form.get("country"),
        request.form.get("entity"),
        request.form.get("product"),
        doc_name,
        prefix
    )

    return jsonify({"message": "Uploaded"})

# ==================== DELETE ====================

@app.route("/api/delete-document", methods=["POST"])
@login_required
def delete_document():
    data = request.get_json() or {}
    doc_name = data.get("document_name")
    if not doc_name:
        return jsonify({"error": "No document name"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM documents WHERE user_id = %s AND document_name = %s",
                (current_user.id, doc_name),
            )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Deleted"})

@app.route("/api/my-documents", methods=["GET"])
@login_required
def my_documents():
    uploaded = User.get_uploaded_docs(current_user.id)
    return jsonify({"uploaded": uploaded})

# ==================== FINAL ROUTES: PREVIEW & DOWNLOAD ====================

@app.route("/download/<doc_name>")
@login_required
def preview_file(doc_name):
    prefix = f"{current_user.id}_{doc_name.replace(' ', '_')}_"
    for f in os.listdir(app.config['UPLOAD_FOLDER']):
        if f.startswith(prefix):
            return send_from_directory(app.config['UPLOAD_FOLDER'], f, as_attachment=False)
    return "File not found", 404

@app.route("/download-attachment/<doc_name>")
@login_required
def download_file_route(doc_name):
    prefix = f"{current_user.id}_{doc_name.replace(' ', '_')}_"
    for f in os.listdir(app.config['UPLOAD_FOLDER']):
        if f.startswith(prefix):
            return send_from_directory(app.config['UPLOAD_FOLDER'], f, as_attachment=True)
    return "File not found", 404

# ==================== RUN ====================

if __name__ == "__main__":
    print("COMPLIANCE ADVISOR - FINAL VERSION (MySQL)")
    print("Preview → /download/Name")
    print("Download → /download-attachment/Name")
    print("http://localhost:5000")
    app.run(port=5000, debug=True)
