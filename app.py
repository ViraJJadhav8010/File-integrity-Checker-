import os
import re
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, Response
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from database.database import get_connection, init_db
from services.hash_service import (
    compute_md5, compute_sha256, format_file_size,
    get_file_metadata, get_file_type_description
)
from services.integrity_service import (
    get_dashboard_stats, get_all_file_hashes,
    store_or_update_hash, delete_file_hash,
    verify_file_integrity, get_audit_history,
    generate_csv_report
)

# -------------------------------------------------------------
# Initialize Flask Application
# -------------------------------------------------------------
app = Flask(__name__)
app.config.from_object(Config)

# Ensure database tables exist and migrations are applied
with app.app_context():
    try:
        init_db()
    except Exception as db_init_err:
        print(f"[Warning] Database initialization during startup: {db_init_err}")

# -------------------------------------------------------------
# Authentication Decorator
# -------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access the forensics monitoring system.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

# Context processor for global template variables
@app.context_processor
def inject_global_data():
    return {
        "current_user": session.get("username", "Analyst"),
        "full_name": session.get("full_name", "Forensic Analyst"),
        "now_year": datetime.now().year
    }

# -------------------------------------------------------------
# Route: Landing Page & Root
# -------------------------------------------------------------
@app.route("/")
@app.route("/index")
@app.route("/index.html")
@app.route("/home")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

# -------------------------------------------------------------
# Route: Operator Login
# -------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        identifier = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not identifier or not password:
            flash("Please provide both username and password.", "danger")
            return render_template("login.html", username=identifier)

        conn = get_connection()
        if not conn:
            flash("Unable to connect to security database. Verify MySQL service.", "danger")
            return render_template("login.html", username=identifier)

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            # Allow login by either username, email, or full_name
            cursor.execute("""
                SELECT id, full_name, username, email, password 
                FROM register 
                WHERE username = %s OR email = %s OR full_name = %s 
                LIMIT 1
            """, (identifier, identifier, identifier))
            user = cursor.fetchone()

            if user:
                stored_pass = user["password"]
                authenticated = False

                # Check hashed password first
                if stored_pass.startswith(("scrypt:", "pbkdf2:")):
                    authenticated = check_password_hash(stored_pass, password)
                else:
                    # Backwards compatibility check for legacy plain-text passwords
                    if stored_pass == password:
                        authenticated = True
                        # Auto-upgrade stored plain-text password to secure hash
                        new_hash = generate_password_hash(password)
                        cursor.execute("UPDATE register SET password = %s WHERE id = %s", (new_hash, user["id"]))
                        conn.commit()

                if authenticated:
                    session["user_id"] = user["id"]
                    session["username"] = user["username"] or user["full_name"]
                    session["full_name"] = user["full_name"]
                    session["email"] = user["email"] or f"{user['id']}@forensics.local"

                    flash(f"Welcome back, {session['full_name']}! Forensics session initialized.", "success")
                    next_url = request.args.get("next")
                    return redirect(next_url or url_for("dashboard"))
                else:
                    flash("Invalid credentials. Access denied.", "danger")
            else:
                flash("Operator not found in database.", "danger")

        except Exception as err:
            flash(f"Database authentication error: {err}", "danger")
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    return render_template("login.html")

# -------------------------------------------------------------
# Route: Operator Registration
# -------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # Validations
        if not all([full_name, username, email, password, confirm_password]):
            flash("All registration fields are required.", "danger")
            return render_template("register.html", full_name=full_name, username=username, email=email)

        # Username format check (alphanumeric, underscore, dash, min 3 chars)
        if not re.match(r"^[a-zA-Z0-9_\-\. ]{3,50}$", username):
            flash("Username must be between 3 and 50 characters and contain valid characters.", "danger")
            return render_template("register.html", full_name=full_name, username=username, email=email)

        # Email format check
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            flash("Please enter a valid email address.", "danger")
            return render_template("register.html", full_name=full_name, username=username, email=email)

        # Password matching & length
        if password != confirm_password:
            flash("Passwords do not match. Please re-enter.", "danger")
            return render_template("register.html", full_name=full_name, username=username, email=email)

        if len(password) < 6:
            flash("Password must be at least 6 characters in length.", "danger")
            return render_template("register.html", full_name=full_name, username=username, email=email)

        conn = get_connection()
        if not conn:
            flash("Database connection failed. Cannot register operator.", "danger")
            return render_template("register.html", full_name=full_name, username=username, email=email)

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            # Check for duplicate username
            cursor.execute("SELECT id FROM register WHERE username = %s OR full_name = %s LIMIT 1", (username, username))
            if cursor.fetchone():
                flash("Username is already registered. Please choose another.", "warning")
                return render_template("register.html", full_name=full_name, email=email)

            # Check for duplicate email
            cursor.execute("SELECT id FROM register WHERE email = %s LIMIT 1", (email,))
            if cursor.fetchone():
                flash("Email address is already in use by another operator.", "warning")
                return render_template("register.html", full_name=full_name, username=username)

            # Securely hash the password
            hashed_pw = generate_password_hash(password)

            cursor.execute("""
                INSERT INTO register (full_name, username, email, password)
                VALUES (%s, %s, %s, %s)
            """, (full_name, username, email, hashed_pw))
            conn.commit()

            flash(f"Account for '{username}' created successfully! You can now log in.", "success")
            return redirect(url_for("login"))

        except Exception as err:
            flash(f"Registration failed: {err}", "danger")
            return render_template("register.html", full_name=full_name, username=username, email=email)
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    return render_template("register.html")

# -------------------------------------------------------------
# Route: Operator Logout
# -------------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out of the forensics monitoring console.", "info")
    return redirect(url_for("login"))

# -------------------------------------------------------------
# Route: Forensics Dashboard
# -------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    stats = get_dashboard_stats()
    search_q = request.args.get("q", "").strip()
    files = get_all_file_hashes(search_query=search_q)
    return render_template("dashboard.html", stats=stats, files=files, search_q=search_q)

# -------------------------------------------------------------
# Route: Browse File & Hash Generation
# -------------------------------------------------------------
@app.route("/browse", methods=["GET", "POST"])
@login_required
def browse_file():
    file_metadata = None

    if request.method == "POST":
        if "file" not in request.files:
            flash("No file was uploaded in request.", "warning")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("Please choose a file to analyze.", "warning")
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            if not filename:
                filename = f"file_{int(datetime.now().timestamp())}.bin"

            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)

            file_metadata = get_file_metadata(save_path, original_filename=file.filename)
            flash(f"File '{file.filename}' analyzed successfully. MD5 cryptographic checksum calculated.", "success")

    return render_template("browse_file.html", file_metadata=file_metadata)

# -------------------------------------------------------------
# Route: Store Baseline Hash
# -------------------------------------------------------------
@app.route("/store-hash", methods=["GET", "POST"])
@login_required
def store_hash():
    file_info = None

    if request.method == "POST":
        # Check if storing directly via file upload OR via form parameters
        file = request.files.get("file")
        file_name = request.form.get("file_name", "").strip()
        file_hash = request.form.get("file_hash", "").strip()
        file_size = request.form.get("file_size", "")
        file_type = request.form.get("file_type", "")

        if file and file.filename != "":
            filename = secure_filename(file.filename) or "unnamed_file.bin"
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)

            meta = get_file_metadata(save_path, original_filename=file.filename)
            if meta:
                file_name = meta["file_name"]
                file_hash = meta["md5_hash"]
                file_size = meta["formatted_size"]
                file_type = meta["file_type"]
                file_info = meta

        if not file_name or not file_hash:
            flash("File name and valid hash are required to establish a baseline.", "danger")
            return render_template("store_hash.html", file_info=file_info)

        # Store baseline in MySQL
        res = store_or_update_hash(file_name, file_hash, file_size=file_size, file_type=file_type)
        if res["success"]:
            flash(res["message"], "success")
        else:
            flash(f"Failed to store baseline: {res['message']}", "danger")

        return redirect(url_for("dashboard"))

    # If GET with query parameters from browse page
    pre_name = request.args.get("name")
    pre_hash = request.args.get("hash")
    pre_size = request.args.get("size")
    pre_type = request.args.get("type")

    if pre_name and pre_hash:
        file_info = {
            "file_name": pre_name,
            "md5_hash": pre_hash,
            "formatted_size": pre_size or "N/A",
            "file_type": pre_type or "Unknown"
        }

    return render_template("store_hash.html", file_info=file_info)

# -------------------------------------------------------------
# Route: Check File Integrity
# -------------------------------------------------------------
@app.route("/check-integrity", methods=["GET", "POST"])
@login_required
def check_integrity():
    result = None
    pre_file = request.args.get("file")

    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("Please select a file to verify its integrity.", "warning")
            return redirect(request.url)

        filename = secure_filename(file.filename) or "target_file.bin"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)

        current_hash = compute_md5(save_path)
        if not current_hash:
            flash("Unable to calculate cryptographic checksum for this file.", "danger")
            return render_template("check_integrity.html")

        # Run integrity verification against MySQL baseline
        result = verify_file_integrity(
            file_name=file.filename,
            current_hash=current_hash,
            checked_by=session.get("username", "Analyst")
        )

        if result["status"] == "VERIFIED":
            flash(f"File '{file.filename}' verified safe! Cryptographic checksum matches baseline.", "success")
        elif result["status"] == "MODIFIED":
            flash(f"ALERT: Integrity violation detected on '{file.filename}'!", "danger")
        else:
            flash(result["message"], "warning")

    return render_template("check_integrity.html", result=result, pre_file=pre_file)

# -------------------------------------------------------------
# Route: Forensics Audit History & Reports
# -------------------------------------------------------------
@app.route("/history")
@login_required
def history():
    status_filter = request.args.get("status", "ALL")
    search_q = request.args.get("q", "").strip()
    logs = get_audit_history(status_filter=status_filter, search_query=search_q)
    return render_template("history.html", logs=logs, current_filter=status_filter, search_q=search_q)

# -------------------------------------------------------------
# Route: Export History CSV
# -------------------------------------------------------------
@app.route("/export-history")
@login_required
def export_history():
    csv_data = generate_csv_report()
    filename = f"forensics_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# -------------------------------------------------------------
# Route: Operator Profile & Security Credentials
# -------------------------------------------------------------
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session.get("user_id")
    conn = get_connection()
    if not conn:
        flash("Database error connecting to user profile.", "danger")
        return redirect(url_for("dashboard"))

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        if request.method == "POST":
            action = request.form.get("action")
            
            if action == "update_info":
                new_name = request.form.get("full_name", "").strip()
                new_email = request.form.get("email", "").strip()

                if not new_name or not new_email:
                    flash("Full name and email cannot be empty.", "warning")
                else:
                    cursor.execute("""
                        UPDATE register 
                        SET full_name = %s, email = %s 
                        WHERE id = %s
                    """, (new_name, new_email, user_id))
                    conn.commit()
                    session["full_name"] = new_name
                    session["email"] = new_email
                    flash("Operator profile information updated successfully.", "success")

            elif action == "change_password":
                curr_pass = request.form.get("current_password", "").strip()
                new_pass = request.form.get("new_password", "").strip()
                confirm_pass = request.form.get("confirm_password", "").strip()

                cursor.execute("SELECT password FROM register WHERE id = %s", (user_id,))
                user_record = cursor.fetchone()

                if not user_record:
                    flash("User record not found.", "danger")
                else:
                    stored_hash = user_record["password"]
                    is_valid = False
                    if stored_hash.startswith(("scrypt:", "pbkdf2:")):
                        is_valid = check_password_hash(stored_hash, curr_pass)
                    else:
                        is_valid = (stored_hash == curr_pass)

                    if not is_valid:
                        flash("Current password is incorrect.", "danger")
                    elif new_pass != confirm_pass:
                        flash("New password and confirmation do not match.", "danger")
                    elif len(new_pass) < 6:
                        flash("New password must be at least 6 characters.", "danger")
                    else:
                        new_hashed = generate_password_hash(new_pass)
                        cursor.execute("UPDATE register SET password = %s WHERE id = %s", (new_hashed, user_id))
                        conn.commit()
                        flash("Security credentials updated. Password changed successfully.", "success")

        # Fetch latest user details and activity
        cursor.execute("SELECT id, full_name, username, email, created_at FROM register WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) AS count FROM audit_logs WHERE checked_by = %s", (session.get("username"),))
        user_audits = cursor.fetchone()["count"]

        return render_template("profile.html", user=user_data, user_audits=user_audits)

    except Exception as err:
        flash(f"Profile error: {err}", "danger")
        return redirect(url_for("dashboard"))
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass

# -------------------------------------------------------------
# REST API Endpoints
# -------------------------------------------------------------
@app.route("/api/stats")
@login_required
def api_stats():
    return jsonify(get_dashboard_stats())

@app.route("/api/delete-baseline/<int:file_id>", methods=["POST"])
@login_required
def api_delete_baseline(file_id):
    success = delete_file_hash(file_id)
    if success:
        return jsonify({"success": True, "message": "Baseline record deleted."})
    return jsonify({"success": False, "message": "Failed to delete baseline record."}), 400

# -------------------------------------------------------------
# Error Handlers
# -------------------------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    return render_template(
        "error.html",
        error_title="404 - Endpoint Not Found",
        error_message="The requested forensics endpoint does not exist. Please return to the security console."
    ), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template(
        "error.html",
        error_title="500 - Internal Server Error",
        error_message="A server exception occurred while processing forensics telemetry."
    ), 500

# -------------------------------------------------------------
# Application Runner
# -------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
