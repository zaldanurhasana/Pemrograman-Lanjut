# config.py - Konfigurasi sistem
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Aplikasi
    APP_NAME = "Student Attendance System"
    VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "True") == "True"
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./attendance.db")
    
    # JWT
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 jam
    
    # Face Recognition
    FACE_MODEL_PATH = "models/facenet.pth"
    SVM_MODEL_PATH = "models/face_classifier.joblib"
    FACE_DETECTION_THRESHOLD = 0.6
    MIN_FACE_SIZE = 30
    EMBEDDING_SIZE = 512
    
    # Paths
    UPLOAD_DIR = "uploads"
    STUDENT_IMAGES_DIR = "uploads/students"
    ATTENDANCE_IMAGES_DIR = "uploads/attendance"
    
    # Absensi
    LATE_THRESHOLD = "08:15"  # Batas telat
    ABSENT_THRESHOLD = "09:00"  # Batas absen
    
    # Email (opsional)
    SMTP_SERVER = os.getenv("SMTP_SERVER", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    EMAIL_USER = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

settings = Settings()

# Buat direktori jika belum ada
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.STUDENT_IMAGES_DIR, exist_ok=True)
os.makedirs(settings.ATTENDANCE_IMAGES_DIR, exist_ok=True)
os.makedirs("models", exist_ok=True)