# main_face_fixed.py - Sistem Face Recognition yang sudah diperbaiki
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import os
import aiofiles
from datetime import datetime
import cv2
import numpy as np
import base64
from io import BytesIO
import tempfile

# Import simple face recognition
from face_recognition_simple import face_system

app = FastAPI(title="Face Recognition Attendance System")

# Setup
os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database
def init_db():
    conn = sqlite3.connect('face_attendance.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nim TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        program TEXT,
        face_registered BOOLEAN DEFAULT 0,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nim TEXT,
        name TEXT,
        course TEXT,
        attendance_date DATE,
        attendance_time TIME,
        confidence REAL,
        method TEXT DEFAULT 'FACE',
        face_image_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (nim) REFERENCES students(nim)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL
    )
    ''')
    
    # Insert sample courses
    cursor.executemany(
        "INSERT OR IGNORE INTO courses (code, name) VALUES (?, ?)",
        [
            ('CS101', 'Algoritma Pemrograman'),
            ('CS102', 'Basis Data'),
            ('CS103', 'Struktur Data'),
            ('CS104', 'Pemrograman Web'),
            ('CS105', 'Kecerdasan Buatan')
        ]
    )
    
    # Insert sample students
    cursor.executemany(
        "INSERT OR IGNORE INTO students (nim, name, program, face_registered) VALUES (?, ?, ?, ?)",
        [
            ('240210500024', 'Zalda Nur Hasana', 'Teknik Komputer', 0),
            ('240210500048', 'Elsa Khairunisa', 'Teknik Komputer', 0),
            ('240210502053', 'Afifa Azza Ayuningtias', 'Teknik Komputer', 0),
            ('240210502026', 'Nur Insyirah Apriany R', 'Teknik Komputer', 0)
        ]
    )
    
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect('face_attendance.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def home():
    """Homepage"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM students")
    total_students = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM attendance")
    total_attendance = cursor.fetchone()['count']
    
    today = datetime.now().date().isoformat()
    cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE attendance_date = ?", (today,))
    today_attendance = cursor.fetchone()['count']
    
    conn.close()
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Face Recognition Attendance</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px 20px;
            }}
            .header {{
                text-align: center;
                color: white;
                margin-bottom: 60px;
                padding: 40px;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }}
            .header h1 {{
                font-size: 3.5rem;
                margin-bottom: 20px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            .header p {{
                font-size: 1.3rem;
                opacity: 0.9;
                max-width: 800px;
                margin: 0 auto;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 25px;
                margin-bottom: 50px;
            }}
            .stat-card {{
                background: rgba(255, 255, 255, 0.95);
                padding: 30px;
                border-radius: 20px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                transition: transform 0.3s, box-shadow 0.3s;
                border: 3px solid;
            }}
            .stat-card:hover {{
                transform: translateY(-10px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            }}
            .stat-card:nth-child(1) {{ border-color: #2196F3; }}
            .stat-card:nth-child(2) {{ border-color: #4CAF50; }}
            .stat-card:nth-child(3) {{ border-color: #FF9800; }}
            .stat-card:nth-child(4) {{ border-color: #9C27B0; }}
            
            .stat-value {{
                font-size: 3.5rem;
                font-weight: bold;
                margin: 20px 0;
            }}
            .stat-card:nth-child(1) .stat-value {{ color: #2196F3; }}
            .stat-card:nth-child(2) .stat-value {{ color: #4CAF50; }}
            .stat-card:nth-child(3) .stat-value {{ color: #FF9800; }}
            .stat-card:nth-child(4) .stat-value {{ color: #9C27B0; }}
            
            .stat-label {{
                color: #666;
                font-size: 1.2rem;
                font-weight: 500;
            }}
            
            .menu {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 30px;
            }}
            .menu-card {{
                background: white;
                padding: 40px 30px;
                border-radius: 20px;
                text-align: center;
                text-decoration: none;
                color: #333;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                transition: all 0.3s;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 200px;
            }}
            .menu-card:hover {{
                transform: translateY(-10px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.2);
                background: #f8f9fa;
            }}
            .menu-icon {{
                font-size: 3rem;
                margin-bottom: 20px;
            }}
            .menu-card h3 {{
                font-size: 1.5rem;
                margin-bottom: 10px;
                color: #2196F3;
            }}
            .menu-card p {{
                color: #666;
                line-height: 1.5;
            }}
            
            .face-system-status {{
                background: rgba(255, 255, 255, 0.1);
                padding: 30px;
                border-radius: 15px;
                margin-top: 50px;
                color: white;
                text-align: center;
            }}
            .face-system-status h3 {{
                margin-bottom: 15px;
                font-size: 1.5rem;
            }}
            
            @media (max-width: 768px) {{
                .container {{
                    padding: 20px;
                }}
                .header h1 {{
                    font-size: 2.5rem;
                }}
                .stat-value {{
                    font-size: 2.5rem;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🧠 Face Recognition Attendance System</h1>
                <p>Sistem absensi otomatis menggunakan teknologi pengenalan wajah untuk kemudahan dan keakuratan presensi mahasiswa</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{total_students}</div>
                    <div class="stat-label">Total Mahasiswa</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-value">{total_attendance}</div>
                    <div class="stat-label">Total Absensi</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-value">{today_attendance}</div>
                    <div class="stat-label">Absensi Hari Ini</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-value">{len(face_system.known_faces)}</div>
                    <div class="stat-label">Wajah Terdaftar</div>
                </div>
            </div>
            
            <div class="menu">
                <a href="/register" class="menu-card">
                    <div class="menu-icon">📸</div>
                    <h3>Registrasi Wajah</h3>
                    <p>Daftarkan wajah mahasiswa baru ke sistem pengenalan</p>
                </a>
                
                <a href="/attendance" class="menu-card">
                    <div class="menu-icon">✅</div>
                    <h3>Absensi Wajah</h3>
                    <p>Lakukan absensi dengan pengenalan wajah otomatis</p>
                </a>
                
                <a href="/students" class="menu-card">
                    <div class="menu-icon">👨‍🎓</div>
                    <h3>Data Mahasiswa</h3>
                    <p>Kelola data mahasiswa dan lihat riwayat absensi</p>
                </a>
                
                <a href="/reports" class="menu-card">
                    <div class="menu-icon">📊</div>
                    <h3>Laporan & Analitik</h3>
                    <p>Lihat laporan kehadiran dan statistik presensi</p>
                </a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/register")
async def register_page():
    """Halaman registrasi wajah"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Registrasi Wajah</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
                padding: 40px 20px;
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            .header h1 {
                color: #2196F3;
                font-size: 2.8rem;
                margin-bottom: 15px;
            }
            .header p {
                color: #666;
                font-size: 1.2rem;
                max-width: 700px;
                margin: 0 auto;
            }
            .back-btn {
                display: inline-flex;
                align-items: center;
                padding: 12px 25px;
                background: #666;
                color: white;
                text-decoration: none;
                border-radius: 50px;
                margin-bottom: 30px;
                font-weight: 500;
                transition: background 0.3s;
            }
            .back-btn:hover {
                background: #555;
            }
            .registration-container {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 40px;
                background: white;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            }
            @media (max-width: 768px) {
                .registration-container {
                    grid-template-columns: 1fr;
                }
            }
            .form-section {
                padding: 40px;
            }
            .camera-section {
                background: #f8f9fa;
                padding: 40px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            }
            .form-group {
                margin-bottom: 25px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #333;
                font-size: 1.1rem;
            }
            input, select {
                width: 100%;
                padding: 15px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                font-size: 16px;
                transition: border-color 0.3s;
                font-family: inherit;
            }
            input:focus, select:focus {
                border-color: #2196F3;
                outline: none;
                box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
            }
            .camera-box {
                width: 100%;
                max-width: 400px;
                margin-bottom: 30px;
            }
            video {
                width: 100%;
                border-radius: 15px;
                border: 3px solid #2196F3;
                background: #000;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            .camera-controls {
                display: flex;
                gap: 15px;
                margin-top: 20px;
                flex-wrap: wrap;
                justify-content: center;
            }
            .btn {
                padding: 15px 30px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            }
            .btn-primary {
                background: #2196F3;
                color: white;
            }
            .btn-primary:hover {
                background: #1976D2;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(33, 150, 243, 0.4);
            }
            .btn-secondary {
                background: #4CAF50;
                color: white;
            }
            .btn-secondary:hover {
                background: #45a049;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4);
            }
            .btn-capture {
                background: #FF9800;
                color: white;
            }
            .btn-capture:hover {
                background: #F57C00;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(255, 152, 0, 0.4);
            }
            .btn:disabled {
                background: #ccc;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            .preview-box {
                width: 100%;
                max-width: 200px;
                margin: 20px auto;
                display: none;
            }
            canvas {
                width: 100%;
                border-radius: 10px;
                border: 2px solid #4CAF50;
                display: none;
            }
            .result {
                margin-top: 30px;
                padding: 25px;
                border-radius: 15px;
                text-align: center;
                display: none;
                animation: fadeIn 0.5s;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .success {
                background: linear-gradient(135deg, #d4edda, #c3e6cb);
                color: #155724;
                border: 2px solid #c3e6cb;
            }
            .error {
                background: linear-gradient(135deg, #f8d7da, #f5c6cb);
                color: #721c24;
                border: 2px solid #f5c6cb;
            }
            .instructions {
                background: #e3f2fd;
                padding: 20px;
                border-radius: 10px;
                margin-top: 30px;
                border-left: 4px solid #2196F3;
            }
            .instructions h4 {
                margin-top: 0;
                color: #1976D2;
            }
            .instructions ul {
                margin: 10px 0;
                padding-left: 20px;
            }
            .instructions li {
                margin-bottom: 8px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn">← Kembali ke Dashboard</a>
            
            <div class="header">
                <h1>📸 Registrasi Wajah Mahasiswa</h1>
                <p>Daftarkan wajah mahasiswa ke sistem untuk memungkinkan absensi otomatis dengan pengenalan wajah</p>
            </div>
            
            <div class="registration-container">
                <div class="form-section">
                    <h2 style="color: #2196F3; margin-bottom: 30px;">Informasi Mahasiswa</h2>
                    
                    <form id="registerForm">
                        <div class="form-group">
                            <label for="nim">Nomor Induk Mahasiswa (NIM) *</label>
                            <input type="text" id="nim" required 
                                   placeholder="Contoh: 20230001">
                        </div>
                        
                        <div class="form-group">
                            <label for="name">Nama Lengkap *</label>
                            <input type="text" id="name" required 
                                   placeholder="Nama lengkap sesuai KTP">
                        </div>
                        
                        <div class="form-group">
                            <label for="program">Program Studi</label>
                            <select id="program">
                                <option value="">Pilih Program Studi</option>
                                <option value="Teknik Komputer">Teknik Komputer</option>
                                <option value="PTIK">PTIK</option>
                            </select>
                        </div>
                        
                        <div class="instructions">
                            <h4>📋 Petunjuk Pengambilan Foto:</h4>
                            <ul>
                                <li>Pastikan wajah terlihat jelas</li>
                                <li>Pencahayaan cukup (tidak silau/gelap)</li>
                                <li>Wajah menghadap kamera lurus</li>
                                <li>Hindari menggunakan kacamata gelap</li>
                                <li>Ekspresi wajah netral (tidak tertawa/cemberut)</li>
                            </ul>
                        </div>
                        
                        <input type="hidden" id="photoData">
                        
                        <div style="margin-top: 40px;">
                            <button type="submit" class="btn btn-secondary" style="width: 100%; padding: 18px;">
                                ✅ REGISTRASI WAJAH
                            </button>
                        </div>
                    </form>
                    
                    <div id="result" class="result"></div>
                </div>
                
                <div class="camera-section">
                    <h2 style="color: #FF9800; margin-bottom: 30px; text-align: center;">Pengambilan Foto</h2>
                    
                    <div class="camera-box">
                        <video id="video" autoplay></video>
                    </div>
                    
                    <div class="camera-controls">
                        <button type="button" id="startCamera" class="btn btn-primary">
                            🎥 Start Camera
                        </button>
                        
                        <button type="button" id="capture" class="btn btn-capture" disabled>
                            📸 Ambil Foto
                        </button>
                        
                        <button type="button" id="uploadFile" class="btn">
                            📁 Upload File
                        </button>
                    </div>
                    
                    <div class="preview-box" id="previewBox">
                        <h4 style="margin-bottom: 10px; color: #4CAF50;">Preview:</h4>
                        <canvas id="canvas"></canvas>
                    </div>
                    
                    <input type="file" id="fileInput" accept="image/*" style="display: none;">
                </div>
            </div>
        </div>
        
        <script>
            // Elements
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const startCameraBtn = document.getElementById('startCamera');
            const captureBtn = document.getElementById('capture');
            const uploadFileBtn = document.getElementById('uploadFile');
            const fileInput = document.getElementById('fileInput');
            const photoData = document.getElementById('photoData');
            const previewBox = document.getElementById('previewBox');
            const resultDiv = document.getElementById('result');
            const registerForm = document.getElementById('registerForm');
            
            let stream = null;
            
            // Start camera
            startCameraBtn.addEventListener('click', async () => {
                try {
                    stream = await navigator.mediaDevices.getUserMedia({
                        video: {
                            width: { ideal: 640 },
                            height: { ideal: 480 },
                            facingMode: "user"
                        },
                        audio: false
                    });
                    
                    video.srcObject = stream;
                    captureBtn.disabled = false;
                    startCameraBtn.disabled = true;
                    startCameraBtn.textContent = "🎥 Camera Active";
                    startCameraBtn.style.background = "#4CAF50";
                    
                } catch (err) {
                    alert("❌ Tidak dapat mengakses kamera: " + err.message);
                    resultDiv.textContent = "❌ Error: Kamera tidak dapat diakses";
                    resultDiv.className = "result error";
                    resultDiv.style.display = 'block';
                }
            });
            
            // Capture photo
            captureBtn.addEventListener('click', () => {
                const context = canvas.getContext('2d');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                context.drawImage(video, 0, 0);
                
                // Show preview
                canvas.style.display = 'block';
                previewBox.style.display = 'block';
                
                // Convert to base64
                const imageData = canvas.toDataURL('image/jpeg', 0.9);
                photoData.value = imageData;
                
                resultDiv.textContent = "✅ Foto berhasil diambil! Silakan lanjutkan registrasi.";
                resultDiv.className = "result success";
                resultDiv.style.display = 'block';
            });
            
            // Upload file
            uploadFileBtn.addEventListener('click', () => {
                fileInput.click();
            });
            
            fileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (event) => {
                        photoData.value = event.target.result;
                        
                        // Create image element to show preview
                        const img = new Image();
                        img.src = event.target.result;
                        img.onload = () => {
                            const context = canvas.getContext('2d');
                            canvas.width = img.width;
                            canvas.height = img.height;
                            context.drawImage(img, 0, 0);
                            
                            // Show preview
                            canvas.style.display = 'block';
                            previewBox.style.display = 'block';
                            
                            resultDiv.textContent = "✅ Foto berhasil diupload! Silakan lanjutkan registrasi.";
                            resultDiv.className = "result success";
                            resultDiv.style.display = 'block';
                        };
                    };
                    reader.readAsDataURL(file);
                }
            });
            
            // Handle form submission
            registerForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const nim = document.getElementById('nim').value;
                const name = document.getElementById('name').value;
                const program = document.getElementById('program').value;
                const photo = photoData.value;
                
                if (!photo) {
                    resultDiv.textContent = "❌ Error: Silakan ambil atau upload foto terlebih dahulu";
                    resultDiv.className = "result error";
                    resultDiv.style.display = 'block';
                    return;
                }
                
                try {
                    const response = await fetch('/api/register', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            nim: nim,
                            name: name,
                            program: program,
                            photo: photo.split(',')[1] // Remove data URL prefix
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        resultDiv.textContent = "✅ " + data.message;
                        resultDiv.className = "result success";
                        resultDiv.style.display = 'block';
                        
                        // Reset form after successful registration
                        setTimeout(() => {
                            registerForm.reset();
                            photoData.value = '';
                            canvas.style.display = 'none';
                            previewBox.style.display = 'none';
                            resultDiv.style.display = 'none';
                            
                            // Stop camera if running
                            if (stream) {
                                stream.getTracks().forEach(track => track.stop());
                                stream = null;
                            }
                            
                            // Reset camera button
                            startCameraBtn.disabled = false;
                            startCameraBtn.textContent = "🎥 Start Camera";
                            startCameraBtn.style.background = "";
                            captureBtn.disabled = true;
                        }, 2000);
                    } else {
                        resultDiv.textContent = "❌ Error: " + data.detail;
                        resultDiv.className = "result error";
                        resultDiv.style.display = 'block';
                    }
                } catch (error) {
                    resultDiv.textContent = "❌ Error: Gagal mengirim data ke server";
                    resultDiv.className = "result error";
                    resultDiv.style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    """)

@app.post("/api/register")
async def api_register(data: dict):
    """API untuk registrasi wajah"""
    try:
        nim = data.get('nim')
        name = data.get('name')
        program = data.get('program', '')
        photo_base64 = data.get('photo')
        
        if not all([nim, name, photo_base64]):
            raise HTTPException(status_code=400, detail="Data tidak lengkap")
        
        # Decode base64 image
        image_data = base64.b64decode(photo_base64)
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Gambar tidak valid")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_path = temp_file.name
            cv2.imwrite(temp_path, image)
        
        try:
            # Register student in database first
            conn = get_db()
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    "INSERT INTO students (nim, name, program) VALUES (?, ?, ?)",
                    (nim, name, program)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                raise HTTPException(status_code=400, detail=f"NIM {nim} sudah terdaftar")
            
            # Register face using face_system
            register_result = face_system.register_face(nim, name, temp_path)
            
            if not register_result.get('success'):
                # Rollback database if face registration fails
                conn.rollback()
                conn.close()
                raise HTTPException(status_code=400, detail=register_result.get('message', 'Gagal mendaftarkan wajah'))
            
            # Update face_registered status in database
            cursor.execute(
                "UPDATE students SET face_registered = 1 WHERE nim = ?",
                (nim,)
            )
            conn.commit()
            conn.close()
            
            return {
                "message": f"Mahasiswa {name} berhasil didaftarkan dengan wajah terdaftar",
                "face_id": register_result.get('face_id')
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/students")
async def students_page():
    """Halaman data mahasiswa"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all students with their attendance info
    cursor.execute("""
        SELECT s.*, 
               COUNT(a.id) as attendance_count,
               MAX(a.attendance_date) as last_attendance
        FROM students s
        LEFT JOIN attendance a ON s.nim = a.nim
        GROUP BY s.id
        ORDER BY s.registration_date DESC
    """)
    
    students = cursor.fetchall()
    conn.close()
    
    # Generate students HTML table
    students_html = ""
    for student in students:
        face_status = "✅ Terdaftar" if student['face_registered'] else "❌ Belum"
        last_attendance = student['last_attendance'] if student['last_attendance'] else "Belum ada"
        program = student['program'] if student['program'] else "-"
        
        students_html += f"""
        <tr>
            <td>{student['nim']}</td>
            <td>{student['name']}</td>
            <td>{program}</td>
            <td>{face_status}</td>
            <td>{student['registration_date'].split()[0] if student['registration_date'] else '-'}</td>
            <td>{student['attendance_count']}</td>
            <td>{last_attendance}</td>
            <td>
                <button onclick="viewAttendance('{student['nim']}', '{student['name']}')" 
                        class="btn-small btn-info">📊 Lihat Absensi</button>
                <button onclick="deleteStudent('{student['nim']}')" 
                        class="btn-small btn-danger">🗑️ Hapus</button>
            </td>
        </tr>
        """
    
    if not students_html:
        students_html = """
        <tr>
            <td colspan="8" style="text-align: center; padding: 40px;">
                <p style="color: #666; font-size: 1.2rem;">Belum ada data mahasiswa.</p>
                <a href="/register" class="btn btn-primary">Daftarkan Mahasiswa Baru</a>
            </td>
        </tr>
        """
    
    total_students = len(students)
    registered_faces = sum(1 for s in students if s['face_registered'])
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Mahasiswa</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                min-height: 100vh;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
                flex-wrap: wrap;
                gap: 20px;
            }}
            .header h1 {{
                color: #2196F3;
                font-size: 2.5rem;
                margin: 0;
            }}
            .back-btn {{
                display: inline-flex;
                align-items: center;
                padding: 12px 25px;
                background: #666;
                color: white;
                text-decoration: none;
                border-radius: 50px;
                font-weight: 500;
                transition: background 0.3s;
            }}
            .back-btn:hover {{
                background: #555;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: white;
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                border-left: 5px solid #2196F3;
            }}
            .stat-value {{
                font-size: 2.5rem;
                font-weight: bold;
                color: #2196F3;
                margin: 10px 0;
            }}
            .stat-label {{
                color: #666;
                font-size: 1rem;
            }}
            .table-container {{
                background: white;
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                margin-top: 20px;
                overflow-x: auto;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th {{
                background: #2196F3;
                color: white;
                padding: 15px;
                text-align: left;
                font-weight: 600;
            }}
            td {{
                padding: 12px 15px;
                border-bottom: 1px solid #eee;
            }}
            tr:hover {{
                background: #f8f9fa;
            }}
            .btn-small {{
                padding: 6px 12px;
                font-size: 14px;
                border-radius: 6px;
                margin: 2px;
                border: none;
                cursor: pointer;
            }}
            .btn-info {{
                background: #17a2b8;
                color: white;
            }}
            .btn-danger {{
                background: #dc3545;
                color: white;
            }}
            .modal {{
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 1000;
                justify-content: center;
                align-items: center;
            }}
            .modal-content {{
                background: white;
                padding: 30px;
                border-radius: 15px;
                max-width: 800px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
            }}
            .modal-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }}
            .close {{
                font-size: 30px;
                cursor: pointer;
                color: #666;
            }}
            .close:hover {{
                color: #333;
            }}
            .attendance-item {{
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 10px;
                margin-bottom: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn">← Kembali ke Dashboard</a>
            
            <div class="header">
                <h1>👨‍🎓 Data Mahasiswa</h1>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{total_students}</div>
                    <div class="stat-label">Total Mahasiswa</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{registered_faces}</div>
                    <div class="stat-label">Wajah Terdaftar</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(face_system.known_faces)}</div>
                    <div class="stat-label">Wajah di Sistem</div>
                </div>
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>NIM</th>
                            <th>Nama</th>
                            <th>Program Studi</th>
                            <th>Status Wajah</th>
                            <th>Tanggal Daftar</th>
                            <th>Jumlah Absen</th>
                            <th>Absen Terakhir</th>
                            <th>Aksi</th>
                        </tr>
                    </thead>
                    <tbody>
                        {students_html}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Modal untuk melihat absensi -->
        <div id="attendanceModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 id="modalTitle">Riwayat Absensi</h2>
                    <span class="close" onclick="closeModal()">&times;</span>
                </div>
                <div id="attendanceContent">
                    <!-- Data absensi akan dimuat di sini -->
                </div>
            </div>
        </div>
        
        <script>
            function viewAttendance(nim, name) {{
                document.getElementById('modalTitle').textContent = 'Riwayat Absensi - ' + name + ' (NIM: ' + nim + ')';
                
                fetch('/api/attendance/' + nim)
                    .then(response => response.json())
                    .then(data => {{
                        let html = '';
                        if (data.length > 0) {{
                            data.forEach(att => {{
                                const course = att.course || 'Tidak ada mata kuliah';
                                const date = att.attendance_date || '';
                                const time = att.attendance_time || '';
                                const confidence = att.confidence || '0';
                                
                                html += `
                                <div class="attendance-item">
                                    <strong>${'{course}'}</strong><br>
                                    <small>Tanggal: ${'{date}'} ${'{time}'}</small><br>
                                    <small>Confidence: ${'{confidence}'}%</small>
                                </div>
                                `;
                            }});
                        }} else {{
                            html = '<p style="text-align: center; color: #666;">Belum ada riwayat absensi.</p>';
                        }}
                        
                        document.getElementById('attendanceContent').innerHTML = html;
                        document.getElementById('attendanceModal').style.display = 'flex';
                    }});
            }}
            
            function closeModal() {{
                document.getElementById('attendanceModal').style.display = 'none';
            }}
            
            async function deleteStudent(nim) {{
                if (confirm('Apakah Anda yakin ingin menghapus mahasiswa ini?')) {{
                    try {{
                        const response = await fetch('/api/students/' + nim, {{
                            method: 'DELETE'
                        }});
                        
                        if (response.ok) {{
                            alert('Mahasiswa berhasil dihapus!');
                            location.reload();
                        }} else {{
                            alert('Gagal menghapus mahasiswa.');
                        }}
                    }} catch (error) {{
                        alert('Terjadi kesalahan: ' + error.message);
                    }}
                }}
            }}
            
            // Close modal when clicking outside
            window.onclick = function(event) {{
                if (event.target.classList.contains('modal')) {{
                    closeModal();
                }}
            }}
        </script>
    </body>
    </html>
    """)

@app.get("/api/attendance/{nim}")
async def get_student_attendance(nim: str):
    """API untuk mendapatkan riwayat absensi mahasiswa"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM attendance 
        WHERE nim = ? 
        ORDER BY attendance_date DESC, attendance_time DESC
        LIMIT 50
    """, (nim,))
    
    attendance = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in attendance]

@app.delete("/api/students/{nim}")
async def delete_student(nim: str):
    """API untuk menghapus mahasiswa"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Delete attendance records first
        cursor.execute("DELETE FROM attendance WHERE nim = ?", (nim,))
        
        # Delete student
        cursor.execute("DELETE FROM students WHERE nim = ?", (nim,))
        
        # Remove from face system
        result = face_system.remove_face(nim)
        if not result.get('success'):
            print(f"Warning: Failed to remove face data for NIM {nim}")
        
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        
        if deleted:
            return {"message": f"Mahasiswa dengan NIM {nim} berhasil dihapus"}
        else:
            raise HTTPException(status_code=404, detail="Mahasiswa tidak ditemukan")
            
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Gagal menghapus mahasiswa: {str(e)}")

@app.get("/attendance")
async def attendance_page():
    """Halaman absensi wajah"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Absensi Wajah</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 40px 20px;
            }
            .back-btn {
                display: inline-flex;
                align-items: center;
                padding: 12px 25px;
                background: #666;
                color: white;
                text-decoration: none;
                border-radius: 50px;
                margin-bottom: 30px;
                font-weight: 500;
            }
            .back-btn:hover {
                background: #555;
            }
            .attendance-container {
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.1);
                text-align: center;
            }
            .camera-box {
                width: 100%;
                max-width: 500px;
                margin: 0 auto 30px;
            }
            video {
                width: 100%;
                border-radius: 15px;
                border: 3px solid #2196F3;
                background: #000;
            }
            .btn {
                padding: 15px 30px;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 18px;
                cursor: pointer;
                margin: 10px;
            }
            .btn:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            .result {
                margin-top: 30px;
                padding: 20px;
                border-radius: 10px;
                display: none;
            }
            .success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .select-course {
                margin: 20px 0;
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #ddd;
                width: 200px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn">← Kembali ke Dashboard</a>
            
            <div class="attendance-container">
                <h1>✅ Absensi Wajah</h1>
                <p>Lakukan absensi dengan pengenalan wajah otomatis</p>
                
                <div class="camera-box">
                    <video id="video" autoplay></video>
                </div>
                
                <div>
                    <select id="courseSelect" class="select-course">
                        <option value="CS101">Algoritma Pemrograman</option>
                        <option value="CS102">Basis Data</option>
                        <option value="CS103">Struktur Data</option>
                        <option value="CS104">Pemrograman Web</option>
                        <option value="CS105">Kecerdasan Buatan</option>
                    </select>
                </div>
                
                <button id="startCamera" class="btn">🎥 Start Camera</button>
                <button id="takeAttendance" class="btn" disabled>📷 Ambil Absensi</button>
                
                <div id="result" class="result"></div>
            </div>
        </div>
        
        <script>
            const video = document.getElementById('video');
            const startCameraBtn = document.getElementById('startCamera');
            const takeAttendanceBtn = document.getElementById('takeAttendance');
            const resultDiv = document.getElementById('result');
            const courseSelect = document.getElementById('courseSelect');
            
            let stream = null;
            
            startCameraBtn.addEventListener('click', async () => {
                try {
                    stream = await navigator.mediaDevices.getUserMedia({
                        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
                        audio: false
                    });
                    
                    video.srcObject = stream;
                    takeAttendanceBtn.disabled = false;
                    startCameraBtn.disabled = true;
                    startCameraBtn.textContent = "🎥 Camera Active";
                    resultDiv.style.display = 'none';
                } catch (err) {
                    resultDiv.textContent = "❌ Tidak dapat mengakses kamera: " + err.message;
                    resultDiv.className = "result error";
                    resultDiv.style.display = 'block';
                }
            });
            
            takeAttendanceBtn.addEventListener('click', async () => {
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                const context = canvas.getContext('2d');
                context.drawImage(video, 0, 0);
                
                const imageData = canvas.toDataURL('image/jpeg', 0.9);
                const course = courseSelect.value;
                
                resultDiv.textContent = "⏳ Memproses pengenalan wajah...";
                resultDiv.className = "result";
                resultDiv.style.display = 'block';
                
                try {
                    const response = await fetch('/api/face-attendance', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            photo: imageData.split(',')[1],
                            course: course
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        resultDiv.textContent = `✅ Absensi berhasil! ${data.name} (${data.nim}) telah hadir. Confidence: ${data.confidence}%`;
                        resultDiv.className = "result success";
                    } else {
                        resultDiv.textContent = "❌ " + data.detail;
                        resultDiv.className = "result error";
                    }
                } catch (error) {
                    resultDiv.textContent = "❌ Error: Gagal mengambil absensi";
                    resultDiv.className = "result error";
                }
            });
        </script>
    </body>
    </html>
    """)

@app.post("/api/face-attendance")
async def api_face_attendance(data: dict):
    """API untuk absensi wajah"""
    try:
        photo_base64 = data.get('photo')
        course = data.get('course', 'CS101')
        
        if not photo_base64:
            raise HTTPException(status_code=400, detail="Foto tidak ditemukan")
        
        # Decode base64 image
        image_data = base64.b64decode(photo_base64)
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Gambar tidak valid")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_path = temp_file.name
            cv2.imwrite(temp_path, image)
        
        try:
            # Recognize face menggunakan fungsi yang ada
            result = face_system.recognize_face(temp_path, threshold=0.6)
            
            print(f"Recognition result: {result}")  # Debug log
            
            if result.get('success') and result.get('recognized_count', 0) > 0:
                # Ambil hasil pertama yang berhasil
                for face_result in result.get('results', []):
                    if face_result.get('success'):
                        nim = face_result.get('nim')
                        name = face_result.get('name')
                        confidence = face_result.get('confidence', 0)
                        
                        # Record attendance
                        conn = get_db()
                        cursor = conn.cursor()
                        
                        now = datetime.now()
                        attendance_date = now.date().isoformat()
                        attendance_time = now.time().strftime('%H:%M:%S')
                        
                        cursor.execute("""
                            INSERT INTO attendance (nim, name, course, attendance_date, attendance_time, confidence)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (nim, name, course, attendance_date, attendance_time, confidence))
                        
                        conn.commit()
                        conn.close()
                        
                        return {
                            "success": True,
                            "nim": nim,
                            "name": name,
                            "confidence": confidence,
                            "message": f"Absensi berhasil untuk {name}"
                        }
                
                # Jika tidak ada yang recognized
                raise HTTPException(status_code=404, detail="Wajah tidak dikenali")
            else:
                raise HTTPException(status_code=404, detail=result.get('message', 'Wajah tidak dikenali. Pastikan wajah sudah terdaftar.'))
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in face attendance: {str(e)}")
        print(f"Traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error sistem: {str(e)}")

@app.get("/reports")
async def reports_page():
    """Halaman laporan"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) as total FROM attendance")
    total_attendance = cursor.fetchone()['total']
    
    today = datetime.now().date().isoformat()
    cursor.execute("SELECT COUNT(*) as today FROM attendance WHERE attendance_date = ?", (today,))
    today_attendance = cursor.fetchone()['today']
    
    # Get recent attendance
    cursor.execute("""
        SELECT a.*, s.program 
        FROM attendance a
        LEFT JOIN students s ON a.nim = s.nim
        ORDER BY a.created_at DESC
        LIMIT 10
    """)
    recent_attendance = cursor.fetchall()
    
    conn.close()
    
    # Generate recent attendance HTML
    recent_html = ""
    for att in recent_attendance:
        recent_html += f"""
        <div class="attendance-item">
            <strong>{att['name']} ({att['nim']})</strong><br>
            <small>{att['course']} • {att['attendance_date']} {att['attendance_time']}</small><br>
            <small>Confidence: {att['confidence']}%</small>
        </div>
        """
    
    if not recent_html:
        recent_html = "<p style='text-align: center; color: #666;'>Belum ada data absensi.</p>"
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Laporan & Analitik</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                min-height: 100vh;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            .back-btn {{
                display: inline-flex;
                align-items: center;
                padding: 12px 25px;
                background: #666;
                color: white;
                text-decoration: none;
                border-radius: 50px;
                margin-bottom: 30px;
                font-weight: 500;
            }}
            .back-btn:hover {{
                background: #555;
            }}
            .reports-container {{
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }}
            .stat-card {{
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                background: #f8f9fa;
                border-left: 4px solid #2196F3;
            }}
            .stat-value {{
                font-size: 2.5rem;
                font-weight: bold;
                color: #2196F3;
                margin: 10px 0;
            }}
            .recent-attendance {{
                margin-top: 40px;
            }}
            .attendance-item {{
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 10px;
                margin-bottom: 10px;
                background: #f8f9fa;
            }}
            .section-title {{
                color: #2196F3;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #e3f2fd;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn">← Kembali ke Dashboard</a>
            
            <div class="reports-container">
                <h1>📊 Laporan & Analitik</h1>
                <p>Statistik dan analisis kehadiran mahasiswa</p>
                
                <div class="stats">
                    <div class="stat-card">
                        <h3>Total Absensi</h3>
                        <div class="stat-value">{total_attendance}</div>
                        <p>Total kehadiran keseluruhan</p>
                    </div>
                    <div class="stat-card">
                        <h3>Absensi Hari Ini</h3>
                        <div class="stat-value">{today_attendance}</div>
                        <p>Kehadiran pada {datetime.now().strftime('%d %B %Y')}</p>
                    </div>
                    <div class="stat-card">
                        <h3>Wajah Terdaftar</h3>
                        <div class="stat-value">{len(face_system.known_faces)}</div>
                        <p>Total wajah dalam sistem</p>
                    </div>
                </div>
                
                <div class="recent-attendance">
                    <h2 class="section-title">Absensi Terbaru</h2>
                    {recent_html}
                </div>
            </div>
        </div>
    </body>
    </html>
    """)

# ============================================
# TAMBAHAN ENDPOINT UNTUK POSTMAN CRUD (TANPA MENGUBAH KODE DI ATAS)
# ============================================

from pydantic import BaseModel
from typing import Optional
import json

# Model untuk update data (PUT)
class StudentUpdate(BaseModel):
    name: Optional[str] = None
    program: Optional[str] = None

# 1. GET ALL STUDENTS (JSON API) - Untuk Postman
@app.get("/api/students")
async def get_all_students_api():
    """API untuk mendapatkan semua data mahasiswa dalam format JSON (untuk Postman)"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.*, 
               COUNT(a.id) as attendance_count,
               MAX(a.attendance_date) as last_attendance
        FROM students s
        LEFT JOIN attendance a ON s.nim = a.nim
        GROUP BY s.id
        ORDER BY s.registration_date DESC
    """)
    
    students = cursor.fetchall()
    conn.close()
    
    students_list = []
    for student in students:
        students_list.append({
            "id": student['id'],
            "nim": student['nim'],
            "name": student['name'],
            "program": student['program'] or "",
            "face_registered": bool(student['face_registered']),
            "registration_date": student['registration_date'],
            "attendance_count": student['attendance_count'],
            "last_attendance": student['last_attendance'] or "Belum ada"
        })
    
    return {
        "status": "success",
        "count": len(students_list),
        "data": students_list
    }

# 2. GET SINGLE STUDENT BY NIM (JSON API) - Untuk Postman
@app.get("/api/students/{nim}")
async def get_student_by_nim_api(nim: str):
    """API untuk mendapatkan data mahasiswa berdasarkan NIM (untuk Postman)"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.*, 
               COUNT(a.id) as attendance_count,
               MAX(a.attendance_date) as last_attendance
        FROM students s
        LEFT JOIN attendance a ON s.nim = a.nim
        WHERE s.nim = ?
        GROUP BY s.id
    """, (nim,))
    
    student = cursor.fetchone()
    conn.close()
    
    if not student:
        raise HTTPException(status_code=404, detail=f"Mahasiswa dengan NIM {nim} tidak ditemukan")
    
    return {
        "status": "success",
        "data": {
            "id": student['id'],
            "nim": student['nim'],
            "name": student['name'],
            "program": student['program'] or "",
            "face_registered": bool(student['face_registered']),
            "registration_date": student['registration_date'],
            "attendance_count": student['attendance_count'],
            "last_attendance": student['last_attendance'] or "Belum ada"
        }
    }

# 3. UPDATE STUDENT (PUT) - Untuk Postman
@app.put("/api/students/{nim}")
async def update_student_api(nim: str, student_data: StudentUpdate):
    """API untuk mengupdate data mahasiswa (untuk Postman)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Cek apakah mahasiswa ada
        cursor.execute("SELECT * FROM students WHERE nim = ?", (nim,))
        student = cursor.fetchone()
        
        if not student:
            raise HTTPException(status_code=404, detail=f"Mahasiswa dengan NIM {nim} tidak ditemukan")
        
        # Update fields yang diberikan
        update_fields = []
        update_values = []
        
        if student_data.name is not None:
            update_fields.append("name = ?")
            update_values.append(student_data.name)
        
        if student_data.program is not None:
            update_fields.append("program = ?")
            update_values.append(student_data.program)
        
        # Jika ada field yang diupdate
        if update_fields:
            update_values.append(nim)  # untuk WHERE clause
            query = f"UPDATE students SET {', '.join(update_fields)} WHERE nim = ?"
            cursor.execute(query, update_values)
            conn.commit()
            
            return {
                "status": "success",
                "message": f"Data mahasiswa {nim} berhasil diupdate",
                "data": {
                    "nim": nim,
                    "name": student_data.name if student_data.name else student['name'],
                    "program": student_data.program if student_data.program else student['program'],
                    "updated_fields": [field.split()[0] for field in update_fields]
                }
            }
        else:
            return {
                "status": "success",
                "message": "Tidak ada data yang diupdate",
                "data": {
                    "nim": nim,
                    "name": student['name'],
                    "program": student['program']
                }
            }
            
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal mengupdate mahasiswa: {str(e)}")
    finally:
        conn.close()

# 4. REGISTER WITH FORM-DATA (POST) - Alternatif untuk Postman
@app.post("/api/register-form")
async def register_student_form(
    nim: str = Form(...),
    name: str = Form(...),
    program: str = Form(""),
    foto: UploadFile = File(...)
):
    """API untuk registrasi dengan form-data (untuk Postman)"""
    try:
        # Baca file upload
        contents = await foto.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Gambar tidak valid")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_path = temp_file.name
            cv2.imwrite(temp_path, image)
        
        try:
            # Register student in database first
            conn = get_db()
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    "INSERT INTO students (nim, name, program) VALUES (?, ?, ?)",
                    (nim, name, program)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                raise HTTPException(status_code=400, detail=f"NIM {nim} sudah terdaftar")
            
            # Register face using face_system
            register_result = face_system.register_face(nim, name, temp_path)
            
            if not register_result.get('success'):
                # Rollback database if face registration fails
                conn.rollback()
                conn.close()
                raise HTTPException(status_code=400, detail=register_result.get('message', 'Gagal mendaftarkan wajah'))
            
            # Update face_registered status in database
            cursor.execute(
                "UPDATE students SET face_registered = 1 WHERE nim = ?",
                (nim,)
            )
            conn.commit()
            conn.close()
            
            return {
                "status": "success",
                "message": f"Mahasiswa {name} berhasil didaftarkan dengan wajah terdaftar",
                "data": {
                    "nim": nim,
                    "name": name,
                    "program": program,
                    "face_id": register_result.get('face_id')
                }
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error server: {str(e)}")

# 5. FACE ATTENDANCE WITH FORM-DATA (POST) - Alternatif untuk Postman
@app.post("/api/face-attendance-form")
async def face_attendance_form(
    image: UploadFile = File(...),
    course: str = Form("CS101")
):
    """API untuk absensi dengan form-data (untuk Postman)"""
    try:
        # Baca file upload
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        image_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image_cv is None:
            raise HTTPException(status_code=400, detail="Gambar tidak valid")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_path = temp_file.name
            cv2.imwrite(temp_path, image_cv)
        
        try:
            # Recognize face
            result = face_system.recognize_face(temp_path, threshold=0.6)
            
            if result.get('success') and result.get('recognized_count', 0) > 0:
                # Ambil hasil pertama
                for face_result in result.get('results', []):
                    if face_result.get('success'):
                        nim = face_result.get('nim')
                        name = face_result.get('name')
                        confidence = face_result.get('confidence', 0)
                        
                        # Record attendance
                        conn = get_db()
                        cursor = conn.cursor()
                        
                        now = datetime.now()
                        attendance_date = now.date().isoformat()
                        attendance_time = now.time().strftime('%H:%M:%S')
                        
                        cursor.execute("""
                            INSERT INTO attendance (nim, name, course, attendance_date, attendance_time, confidence)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (nim, name, course, attendance_date, attendance_time, confidence))
                        
                        conn.commit()
                        conn.close()
                        
                        return {
                            "status": "success",
                            "message": f"Absensi berhasil untuk {name}",
                            "data": {
                                "nim": nim,
                                "name": name,
                                "confidence": confidence,
                                "course": course,
                                "attendance_date": attendance_date,
                                "attendance_time": attendance_time
                            }
                        }
                
                # Jika tidak ada yang recognized
                raise HTTPException(status_code=404, detail="Wajah tidak dikenali")
            else:
                raise HTTPException(status_code=404, detail=result.get('message', 'Wajah tidak dikenali. Pastikan wajah sudah terdaftar.'))
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sistem: {str(e)}")

# 6. CREATE STUDENT WITHOUT PHOTO (POST) - Untuk testing
@app.post("/api/students")
async def create_student_without_photo(
    nim: str = Form(...),
    name: str = Form(...),
    program: str = Form("")
):
    """API untuk membuat mahasiswa tanpa foto (untuk testing Postman)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Cek apakah NIM sudah terdaftar
        cursor.execute("SELECT * FROM students WHERE nim = ?", (nim,))
        existing = cursor.fetchone()
        
        if existing:
            raise HTTPException(status_code=400, detail=f"NIM {nim} sudah terdaftar")
        
        # Insert new student
        cursor.execute(
            "INSERT INTO students (nim, name, program) VALUES (?, ?, ?)",
            (nim, name, program)
        )
        conn.commit()
        
        return {
            "status": "success",
            "message": f"Mahasiswa {name} berhasil didaftarkan (tanpa foto)",
            "data": {
                "nim": nim,
                "name": name,
                "program": program,
                "face_registered": False
            }
        }
            
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail=f"NIM {nim} sudah terdaftar")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal mendaftarkan mahasiswa: {str(e)}")
    finally:
        conn.close()

# 7. TEST ENDPOINT - Untuk cek server
@app.get("/api/test")
async def test_api():
    """Endpoint test untuk Postman"""
    return {
        "status": "success",
        "message": "API berjalan dengan baik",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "GET /api/students": "Get all students",
            "GET /api/students/{nim}": "Get student by NIM",
            "POST /api/register": "Register with JSON (base64 photo)",
            "POST /api/register-form": "Register with form-data (file upload)",
            "PUT /api/students/{nim}": "Update student data",
            "DELETE /api/students/{nim}": "Delete student",
            "POST /api/face-attendance": "Face attendance with JSON",
            "POST /api/face-attendance-form": "Face attendance with form-data",
            "GET /api/attendance/{nim}": "Get student attendance"
        }
    }

# ============================================
# DOKUMENTASI ENDPOINT UNTUK POSTMAN
# ============================================
@app.get("/api-docs")
async def api_docs():
    """Dokumentasi API untuk Postman"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Documentation for Postman</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { color: #2196F3; }
            .endpoint { 
                background: #f5f5f5; 
                padding: 20px; 
                margin: 15px 0; 
                border-left: 4px solid #2196F3;
                border-radius: 8px;
            }
            .method { 
                display: inline-block; 
                padding: 5px 10px; 
                border-radius: 4px; 
                font-weight: bold; 
                color: white; 
                margin-right: 10px;
            }
            .get { background: #4CAF50; }
            .post { background: #2196F3; }
            .put { background: #FF9800; }
            .delete { background: #F44336; }
            pre { 
                background: #2d2d2d; 
                color: #f8f8f2; 
                padding: 15px; 
                border-radius: 8px; 
                overflow-x: auto;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📚 API Documentation for Postman</h1>
            <p>Berikut adalah endpoint yang tersedia untuk testing di Postman:</p>
            
            <div class="endpoint">
                <span class="method get">GET</span> <strong>/api/students</strong>
                <p>Get all students data in JSON format</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <strong>/api/students/{nim}</strong>
                <p>Get single student by NIM</p>
                <p>Example: <code>/api/students/240210502062</code></p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <strong>/api/register</strong>
                <p>Register student with JSON (base64 photo)</p>
                <pre>
{
    "nim": "240210502062",
    "name": "M Faris Ghazy Zulkifli",
    "program": "Teknik Komputer",
    "photo": "base64_string_here"
}
                </pre>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <strong>/api/register-form</strong>
                <p>Register student with form-data (file upload)</p>
                <p>Body: form-data with fields: <code>nim</code>, <code>name</code>, <code>program</code>, <code>foto</code> (file)</p>
            </div>
            
            <div class="endpoint">
                <span class="method put">PUT</span> <strong>/api/students/{nim}</strong>
                <p>Update student data</p>
                <pre>
{
    "name": "New Name",
    "program": "New Program"
}
                </pre>
            </div>
            
            <div class="endpoint">
                <span class="method delete">DELETE</span> <strong>/api/students/{nim}</strong>
                <p>Delete student by NIM</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <strong>/api/face-attendance</strong>
                <p>Face attendance with JSON (base64 photo)</p>
                <pre>
{
    "photo": "base64_string_here",
    "course": "CS101"
}
                </pre>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <strong>/api/face-attendance-form</strong>
                <p>Face attendance with form-data (file upload)</p>
                <p>Body: form-data with fields: <code>image</code> (file), <code>course</code></p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <strong>/api/attendance/{nim}</strong>
                <p>Get student attendance history</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <strong>/api/test</strong>
                <p>Test API connection</p>
            </div>
            
            <h2>🚀 Quick Test with curl:</h2>
            <pre>
# Test API
curl http://localhost:8000/api/test

# Get all students
curl http://localhost:8000/api/students

# Get single student
curl http://localhost:8000/api/students/240210502062

# Delete student
curl -X DELETE http://localhost:8000/api/students/240210502062
            </pre>
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("🚀 Face Recognition Attendance System with Complete CRUD API")
    print("=" * 70)
    print(f"📊 Registered faces in system: {len(face_system.known_faces)}")
    print(f"🌐 Server running at: http://localhost:8000")
    print(f"📖 API Docs at: http://localhost:8000/api-docs")
    print(f"🔌 Swagger UI at: http://localhost:8000/docs")
    print("\n📚 CRUD Endpoints for Postman:")
    print("  GET    /api/students           - Get all students")
    print("  GET    /api/students/{nim}     - Get student by NIM")
    print("  POST   /api/register           - Register with JSON")
    print("  POST   /api/register-form      - Register with form-data")
    print("  PUT    /api/students/{nim}     - Update student")
    print("  DELETE /api/students/{nim}     - Delete student")
    print("  POST   /api/face-attendance    - Face attendance (JSON)")
    print("  POST   /api/face-attendance-form - Face attendance (form-data)")
    print("  GET    /api/attendance/{nim}   - Get attendance")
    print("  GET    /api/test               - Test API")
    print("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
