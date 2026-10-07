import io
import csv
from datetime import datetime
from database.database import get_connection

def get_dashboard_stats():
    """Returns real-time dashboard metrics from MySQL database."""
    conn = get_connection()
    if not conn:
        return {"total_files": 0, "verified_files": 0, "modified_files": 0, "total_checks": 0}

    cursor = conn.cursor()
    try:
        # Total registered baseline files
        cursor.execute("SELECT COUNT(*) FROM file_hashes")
        total_files = cursor.fetchone()[0]

        # Total verified audits
        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE status = 'VERIFIED'")
        verified_files = cursor.fetchone()[0]

        # Total modified / tampered audits
        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE status = 'MODIFIED'")
        modified_files = cursor.fetchone()[0]

        # Total integrity audits performed
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        total_checks = cursor.fetchone()[0]

        return {
            "total_files": total_files,
            "verified_files": verified_files,
            "modified_files": modified_files,
            "total_checks": total_checks
        }
    except Exception as err:
        print(f"[Integrity Service Error] Stats query failed: {err}")
        return {"total_files": 0, "verified_files": 0, "modified_files": 0, "total_checks": 0}
    finally:
        cursor.close()
        conn.close()

def get_all_file_hashes(search_query=None):
    """Retrieves all registered files from file_hashes with latest audit status."""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                fh.id,
                fh.file_name,
                fh.file_hash,
                fh.file_size,
                fh.file_type,
                al.status AS latest_status,
                al.checked_at AS last_checked
            FROM file_hashes fh
            LEFT JOIN (
                SELECT a1.file_name, a1.status, a1.checked_at
                FROM audit_logs a1
                INNER JOIN (
                    SELECT file_name, MAX(checked_at) AS max_time
                    FROM audit_logs
                    GROUP BY file_name
                ) a2 ON a1.file_name = a2.file_name AND a1.checked_at = a2.max_time
            ) al ON fh.file_name = al.file_name
        """
        params = []
        if search_query:
            query += " WHERE fh.file_name LIKE %s OR fh.file_hash LIKE %s"
            params.extend([f"%{search_query}%", f"%{search_query}%"])

        query += " ORDER BY fh.id DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return rows
    except Exception as err:
        print(f"[Integrity Service Error] Get file hashes failed: {err}")
        return []
    finally:
        cursor.close()
        conn.close()

def store_or_update_hash(file_name, file_hash, file_size=None, file_type=None):
    """Stores a new cryptographic baseline or updates an existing baseline in MySQL."""
    conn = get_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed."}

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM file_hashes WHERE file_name = %s", (file_name,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE file_hashes 
                SET file_hash = %s, file_size = %s, file_type = %s 
                WHERE file_name = %s
            """, (file_hash, file_size, file_type, file_name))
            conn.commit()
            return {
                "success": True,
                "action": "updated",
                "message": f"Cryptographic baseline hash updated successfully for '{file_name}'."
            }
        else:
            cursor.execute("""
                INSERT INTO file_hashes (file_name, file_hash, file_size, file_type)
                VALUES (%s, %s, %s, %s)
            """, (file_name, file_hash, file_size, file_type))
            conn.commit()
            return {
                "success": True,
                "action": "stored",
                "message": f"Cryptographic baseline hash stored successfully for '{file_name}'."
            }
    except Exception as err:
        print(f"[Integrity Service Error] Store hash failed: {err}")
        return {"success": False, "message": str(err)}
    finally:
        cursor.close()
        conn.close()

def delete_file_hash(file_id):
    """Deletes a baseline hash record by ID."""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM file_hashes WHERE id = %s", (file_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as err:
        print(f"[Integrity Service Error] Delete hash failed: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

def verify_file_integrity(file_name, current_hash, checked_by="Analyst"):
    """
    Compares current calculated hash against stored MySQL baseline.
    Logs verification attempt in audit_logs.
    """
    conn = get_connection()
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not conn:
        return {
            "status": "ERROR",
            "match": False,
            "message": "Database connection error.",
            "file_name": file_name,
            "baseline_hash": None,
            "current_hash": current_hash,
            "timestamp": timestamp_str
        }

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT file_hash FROM file_hashes WHERE file_name = %s", (file_name,))
        row = cursor.fetchone()

        if not row:
            # File is not registered in baseline database
            return {
                "status": "NOT_FOUND",
                "match": False,
                "message": f"'{file_name}' has no baseline hash stored in the database. Please store its hash first.",
                "file_name": file_name,
                "baseline_hash": None,
                "current_hash": current_hash,
                "timestamp": timestamp_str
            }

        baseline_hash = row[0]

        if current_hash.lower() == baseline_hash.lower():
            status = "VERIFIED"
            match = True
            msg = "File has not been modified. Cryptographic checksum matches the stored baseline."
        else:
            status = "MODIFIED"
            match = False
            msg = "File has been modified or tampered with! Cryptographic hash does not match baseline."

        # Insert audit record into audit_logs table
        cursor.execute("""
            INSERT INTO audit_logs (file_name, baseline_hash, current_hash, status, checked_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (file_name, baseline_hash, current_hash, status, checked_by))
        conn.commit()

        return {
            "status": status,
            "match": match,
            "message": msg,
            "file_name": file_name,
            "baseline_hash": baseline_hash,
            "current_hash": current_hash,
            "timestamp": timestamp_str
        }
    except Exception as err:
        print(f"[Integrity Service Error] Verify integrity failed: {err}")
        return {
            "status": "ERROR",
            "match": False,
            "message": str(err),
            "file_name": file_name,
            "baseline_hash": None,
            "current_hash": current_hash,
            "timestamp": timestamp_str
        }
    finally:
        cursor.close()
        conn.close()

def get_audit_history(status_filter=None, search_query=None, limit=150):
    """Retrieves forensic audit history from audit_logs table."""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT id, file_name, baseline_hash, current_hash, status, checked_by, checked_at FROM audit_logs WHERE 1=1"
        params = []

        if status_filter and status_filter.upper() != "ALL":
            query += " AND status = %s"
            params.append(status_filter.upper())

        if search_query:
            query += " AND (file_name LIKE %s OR current_hash LIKE %s OR baseline_hash LIKE %s)"
            params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])

        query += " ORDER BY checked_at DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return rows
    except Exception as err:
        print(f"[Integrity Service Error] Get audit history failed: {err}")
        return []
    finally:
        cursor.close()
        conn.close()

def generate_csv_report():
    """Generates a downloadable CSV string of all audit history."""
    records = get_audit_history(limit=500)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Audit ID", "Target File", "Baseline MD5 Hash", "Current MD5 Hash", "Integrity Status", "Auditor", "Timestamp"])

    for r in records:
        writer.writerow([
            r["id"],
            r["file_name"],
            r["baseline_hash"] or "N/A",
            r["current_hash"],
            r["status"],
            r["checked_by"],
            r["checked_at"].strftime("%Y-%m-%d %H:%M:%S") if r["checked_at"] else "N/A"
        ])

    return output.getvalue()
