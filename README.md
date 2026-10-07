# File Integrity Checker - Digital Forensics & File Security

A modern, professional **Digital Forensics File Integrity Monitoring Dashboard** built in Python and Tkinter with MySQL persistence. The application monitors critical files using cryptographic MD5 hashing to detect unauthorized alterations, replacements, or forensic tampering in real-time.

---

## 🛡️ Core Capabilities

- **Digital Forensics Audit Dashboard**: Clean dark cybersecurity theme featuring system status metrics, cryptographic baselines, and live file tracking.
- **Operator Authentication**: Secure login and registration with credential validation in MySQL and show/hide password toggles.
- **Cryptographic Hash Computation**: Instant MD5 hash generation (RFC 1321) with file attribute inspection (size, extension, path).
- **Baseline Integrity Registry**: Store, update, and manage trusted baseline signatures in MySQL (`file_hashes`).
- **Tamper & Alteration Detection**: Prominent forensic verification cards identifying safe (🟢) and tampered (🔴) files with diff comparison.
- **Automated Background Scheduler**: Multithreaded periodic integrity verification at custom intervals without freezing the UI.
- **Forensics Reports & Audit History**: Searchable and filterable history table with text/CSV audit report exporting.

---

## 🎨 Design System & Theme

The user interface follows a professional **Cybersecurity / Digital Forensics** command center aesthetic:

| Component | Color Code | Forensic Meaning |
|---|---|---|
| **Deep Dark Background** | `#090d16` | Security command console backdrop |
| **Card & Surface Navy** | `#111d35` | Elevated panels & inspection containers |
| **Cyber Cyan Accent** | `#00e5ff` | Primary highlight, focus rings, cryptographic data |
| **Action Blue** | `#2563eb` | Primary operator buttons & navigation |
| **Safe / Verified Green** | `#10b981` | Cryptographic match (100% integrity preserved) |
| **Tamper / Violation Red** | `#ef4444` | Unauthorized file alteration detected |
| **Warning Orange** | `#f59e0b` | Unregistered files & alert conditions |

---

## 📁 Project Architecture

```
File Integrity Checker/
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies (mysql-connector-python, Pillow)
├── README.md                   # Complete documentation
├── assets/                     # UI graphics & icons
│   ├── Cyber.jpg               # Cyber command center wallpaper
│   └── shield_icon.png         # Vector security shield icon
├── auth/                       # Operator Authentication
│   ├── __init__.py
│   ├── login.py                # Centered login card & credential authentication
│   └── register.py             # Operator registration & validation
├── checker/                    # Core Forensics Engine & Dashboard
│   ├── __init__.py
│   └── integrity_checker.py    # 6-view digital forensics command dashboard
├── config/                     # Configuration
│   ├── __init__.py
│   └── database.py             # MySQL connector & connection pool
└── utils/                      # Utilities & Shared Styling
    ├── __init__.py
    ├── hash_utils.py           # Chunked cryptographic MD5 computation
    └── ui_theme.py             # Cybersecurity dark theme components & helpers
```

---

## 🗄️ Database Setup

Ensure MySQL server is running. Create the database and tables:

```sql
CREATE DATABASE file_integrity;
USE file_integrity;

-- Operator Accounts Table
CREATE TABLE register (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100),
    dob DATE,
    gender VARCHAR(10),
    age INT,
    password VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cryptographic Baseline Table (created automatically by the app)
CREATE TABLE file_hashes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_name VARCHAR(255),
    file_hash VARCHAR(32),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Database credentials are configured in `config/database.py`:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "file_integrity"
}
```

---

## 🚀 Installation & Launch

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python main.py
   ```

---

## 👥 Authors & Academic Credits

- **Viraj Jadhav**
- **Pawar Neha**
- **Bhosale Shivneri**
