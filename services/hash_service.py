import os
import hashlib
from datetime import datetime

def compute_md5(file_input):
    """
    Computes MD5 hash from either a file path string or a file-like stream.
    Reads in 4096-byte chunks for memory efficiency.
    """
    try:
        hash_md5 = hashlib.md5()
        if isinstance(file_input, str):
            if not os.path.isfile(file_input):
                return None
            with open(file_input, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        else:
            # File-like object (e.g. Werkzeug FileStorage stream)
            pos = file_input.tell() if hasattr(file_input, "tell") else 0
            if hasattr(file_input, "seek"):
                file_input.seek(0)
            for chunk in iter(lambda: file_input.read(4096), b""):
                hash_md5.update(chunk)
            if hasattr(file_input, "seek"):
                file_input.seek(pos)

        return hash_md5.hexdigest()
    except Exception as err:
        print(f"[Hash Service Error] MD5 calculation failed: {err}")
        return None

def compute_sha256(file_input):
    """Computes SHA-256 hash for secondary forensic verification."""
    try:
        hash_sha256 = hashlib.sha256()
        if isinstance(file_input, str):
            if not os.path.isfile(file_input):
                return None
            with open(file_input, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
        else:
            pos = file_input.tell() if hasattr(file_input, "tell") else 0
            if hasattr(file_input, "seek"):
                file_input.seek(0)
            for chunk in iter(lambda: file_input.read(4096), b""):
                hash_sha256.update(chunk)
            if hasattr(file_input, "seek"):
                file_input.seek(pos)

        return hash_sha256.hexdigest()
    except Exception as err:
        print(f"[Hash Service Error] SHA-256 calculation failed: {err}")
        return None

def format_file_size(size_bytes):
    """Formats file size in bytes into human-readable string."""
    try:
        size = float(size_bytes)
        for unit in ["Bytes", "KB", "MB", "GB", "TB"]:
            if size < 1024.0 or unit == "TB":
                return f"{size:.2f} {unit}" if unit != "Bytes" else f"{int(size)} Bytes"
            size /= 1024.0
    except (ValueError, TypeError):
        return "Unknown size"

def get_file_type_description(filename):
    """Returns a user-friendly description of file type based on extension."""
    if not filename or "." not in filename:
        return "Generic Binary File"
    ext = filename.rsplit(".", 1)[1].lower()
    mapping = {
        "txt": "Plain Text Document (.txt)",
        "pdf": "Adobe Acrobat Document (.pdf)",
        "docx": "Microsoft Word Document (.docx)",
        "doc": "Microsoft Word Document (.doc)",
        "xlsx": "Microsoft Excel Spreadsheet (.xlsx)",
        "xls": "Microsoft Excel Spreadsheet (.xls)",
        "csv": "Comma-Separated Values (.csv)",
        "py": "Python Source Code (.py)",
        "c": "C Source Code (.c)",
        "cpp": "C++ Source Code (.cpp)",
        "java": "Java Source Code (.java)",
        "html": "HTML Web Document (.html)",
        "css": "Cascading Style Sheet (.css)",
        "js": "JavaScript File (.js)",
        "json": "JSON Data File (.json)",
        "png": "PNG Image File (.png)",
        "jpg": "JPEG Image File (.jpg)",
        "jpeg": "JPEG Image File (.jpeg)",
        "gif": "GIF Image File (.gif)",
        "zip": "ZIP Archive (.zip)",
        "tar": "TAR Archive (.tar)",
        "gz": "GZIP Archive (.gz)",
        "exe": "Windows Executable (.exe)",
        "dll": "Dynamic Link Library (.dll)",
        "log": "System/Audit Log File (.log)"
    }
    return mapping.get(ext, f"{ext.upper()} File")

def get_file_metadata(file_path, original_filename=None):
    """Extracts forensic metadata from an uploaded or stored file."""
    if not os.path.isfile(file_path):
        return None
    
    file_name = original_filename or os.path.basename(file_path)
    size_bytes = os.path.getsize(file_path)
    md5_hash = compute_md5(file_path)
    sha256_hash = compute_sha256(file_path)
    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")

    return {
        "file_name": file_name,
        "file_path": file_path,
        "size_bytes": size_bytes,
        "formatted_size": format_file_size(size_bytes),
        "file_type": get_file_type_description(file_name),
        "extension": file_name.rsplit(".", 1)[1].lower() if "." in file_name else "none",
        "md5_hash": md5_hash,
        "sha256_hash": sha256_hash,
        "timestamp": mod_time
    }
