# File Integrity Checker

## Project Description

File Integrity Checker is a Python-based security application
that detects unauthorized modifications to files.

The application calculates the MD5 hash of a selected file
and stores the hash in a MySQL database.

When the file is checked again, the application calculates
the current MD5 hash and compares it with the previously
stored hash.

If both hashes are the same, the file has not been modified.

If the hashes are different, the application reports that
the file has been modified.

## Technologies Used

- Python
- Tkinter
- MySQL
- MySQL Connector
- Pillow
- MD5 Hashing
- Multithreading

## Features

1. User Registration
2. User Login
3. File Selection
4. MD5 Hash Generation
5. Store File Hash
6. Check File Integrity
7. Detect File Modification
8. Scheduled Integrity Checking
9. MySQL Database
10. Graphical User Interface

## Project Structure

File_Integrity_Checker/

├── main.py
├── requirements.txt
├── README.md
│
├── config/
│   ├── __init__.py
│   └── database.py
│
├── auth/
│   ├── __init__.py
│   ├── login.py
│   └── register.py
│
├── checker/
│   ├── __init__.py
│   └── integrity_checker.py
│
├── utils/
│   ├── __init__.py
│   └── hash_utils.py
│
└── assets/
    └── Cyber.jpg

## Database

Create the database using:

CREATE DATABASE file_integrity;

Then select the database:

USE file_integrity;

Create the registration table:

CREATE TABLE register (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100),
    dob DATE,
    gender VARCHAR(20),
    age INT,
    password VARCHAR(255)
);

The file_hashes table is automatically created by the
application.

## MySQL Configuration

Edit:

config/database.py

Example:

host = localhost
user = root
password = 8010
database = file_integrity

Change the password according to your MySQL configuration.

## Installation

Install the required libraries:

pip install -r requirements.txt

## Run

Run the application from the project folder:

python main.py

## Working

1. Register a new user.
2. Login using the registered username and password.
3. Select a file.
4. Click Store Hash.
5. The MD5 hash is stored in MySQL.
6. Modify the file.
7. Select the file again.
8. Click Check Integrity.
9. The application compares the current hash with the stored hash.
10. If the hashes differ, a modification alert is displayed.

## Purpose

This project demonstrates basic file integrity monitoring
using cryptographic hashing and database storage.