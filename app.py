# backend/app.py → FINAL TESTED & WORKING VERSION (Dec 2025)

import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv

from models.user import User, init_db
from utils.compliance_rules import get_requirements

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-compliance-2025")
'''CORS(app,origins=["http://isha-alb-160568039.us-west-1.elb.amazonaws.com:5100","http://127.0.0.1:5100"], supports_credentials=True)
'''
# In app.py - replace your current CORS line with:
# allow both your dev ports (5100 for one frontend, 5173 for Vite)
CORS(app, origins=[
    "http://isha-alb-160568039.us-west-1.elb.amazonaws.com:5100",
    "http://localhost:5100",
    "http://127.0.0.1:5100",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
], supports_credentials=True)

# Uploads folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize DB + Login Manager
init_db()
login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id)) if user_id else None

# ==================== AUTH ====================

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    if User.create(username, password):
        return jsonify({"message": "Registered successfully"})
    return jsonify({"error": "Username already taken"}), 400

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    user = User.validate(data.get("username"), data.get("password"))
    if user:
        login_user(user)
        return jsonify({"message": "Logged in", "username": user.username})
    return jsonify({"error": "Invalid credentials"}), 401

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

# ==================== UPLOAD (NOW SAVES FULL FILENAME) ====================

@app.route("/api/upload", methods=["POST"])
@login_required
def upload_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    doc_name = request.form.get("document_name") or "unnamed"
    safe_doc_name = doc_name.replace(' ', '_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_filename = f"{current_user.id}_{safe_doc_name}_{timestamp}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], full_filename)
    file.save(filepath)

    # Save the FULL filename in DB (critical!)
    User.save_document(
        current_user.id,
        request.form.get("country"),
        request.form.get("entity_type") or request.form.get("entity"),
        request.form.get("product_category") or request.form.get("product"),
        doc_name,
        full_filename                      # ← This matches your new models/user.py
    )
    return jsonify({"message": "Uploaded successfully"})

# ==================== MY DOCUMENTS ====================

@app.route("/api/my-documents", methods=["GET"])
@login_required
def my_documents():
    docs = User.get_uploaded_docs(current_user.id)
    # Return just the document names for your frontend (exactly what it expects)
    return jsonify({"uploaded": [d["document_name"] for d in docs]})

# ==================== DOWNLOAD / PREVIEW (NOW 100% RELIABLE) ====================

@app.route("/download/<doc_name>")
@login_required
def preview_file(doc_name):
    docs = User.get_uploaded_docs(current_user.id)
    matching = [d for d in docs if d["document_name"] == doc_name]
    if not matching:
        return "File not found", 404
    filename = matching[0]["file_path"]
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(full_path):
        return "File not found", 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)

@app.route("/download-attachment/<doc_name>")
@login_required
def download_file_route(doc_name):
    docs = User.get_uploaded_docs(current_user.id)
    matching = [d for d in docs if d["document_name"] == doc_name]
    if not matching:
        return "File not found", 404
    filename = matching[0]["file_path"]
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(full_path):
        return "File not found", 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# ==================== DELETE ====================

@app.route("/api/delete-document", methods=["POST"])
@login_required
def delete_document():
    data = request.get_json() or {}
    doc_name = data.get("document_name")
    if not doc_name:
        return jsonify({"error": "document_name required"}), 400

    # Delete file from disk
    docs = User.get_uploaded_docs(current_user.id)
    matching = [d for d in docs if d["document_name"] == doc_name]
    if matching:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], matching[0]["file_path"])
        if os.path.exists(file_path):
            os.remove(file_path)

    # Delete from DB
    User.delete_document(current_user.id, doc_name)
    return jsonify({"message": "Deleted successfully"})

# ==================== HEALTH ====================

@app.route("/health")
def health():
    return "OK", 200

# ==================== RUN ====================

'''if __name__ == "__main__":
    print("\nCOMPLIANCE ADVISOR IS RUNNING!")
    print("→ Register: POST /api/register")
    print("→ Login   : POST /api/login")
    print("→ Visit your frontend (usually http://localhost:3000)\n")
    app.run(host="0.0.0.0", port=5000, debug=True)'''
    
if __name__ == "__main__":
    print("\n" + "="*50)
    print("COMPLIANCE ADVISOR BACKEND API")
    print("="*50)
    print("✅ BACKEND: http://localhost:5000")
    print("✅ ALLOWS FRONTEND: http://localhost:5100")
    print("\n📋 API ENDPOINTS:")
    print("  • POST   /api/register")
    print("  • POST   /api/login")
    print("  • POST   /api/check")
    print("  • POST   /api/upload")
    print("  • GET    /api/my-documents")
    print("  • GET    /download/<doc_name>")
    print("  • POST   /api/delete-document")
    print("  • GET    /health")
    print("\n🚀 FRONTEND SETUP:")
    print("  - Run frontend on: http://localhost:5100")
    print("  - Make API calls to: http://localhost:5000")
    print("\n🌐 PRODUCTION (ALB):")
    print("  - Frontend: http://isha-alb-160568039.us-west-1.elb.amazonaws.com:5100")
    print("  - API calls route to backend:5000")
    print("="*50 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=True)