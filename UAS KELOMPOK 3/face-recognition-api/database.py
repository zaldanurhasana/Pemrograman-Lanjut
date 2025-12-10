# database.py - SQLite database sederhana
import sqlite3
import json
from datetime import datetime
import os

class Database:
    def __init__(self, db_path="attendance.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Dapatkan koneksi database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Untuk mengakses kolom dengan nama
        return conn
    
    def init_db(self):
        """Inisialisasi database dan tabel"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabel Mahasiswa
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nim TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            study_program TEXT,
            face_embedding TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tabel Mata Kuliah
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            semester INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tabel Sesi/Kelas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            session_date DATE NOT NULL,
            session_number INTEGER,
            topic TEXT,
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
        ''')
        
        # Tabel Absensi
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            session_id INTEGER,
            check_in_time TIMESTAMP NOT NULL,
            confidence REAL,
            status TEXT DEFAULT 'present',
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (session_id) REFERENCES sessions(id),
            UNIQUE(student_id, session_id)
        )
        ''')
        
        # Buat indeks untuk performa
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_nim ON students(nim)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendances_student ON attendances(student_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendances_session ON attendances(session_id)')
        
        conn.commit()
        conn.close()
        
        print("✅ Database initialized successfully")
    
    # ===== CRUD Mahasiswa =====
    def add_student(self, nim, name, study_program, embedding=None):
        """Tambah mahasiswa baru"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO students (nim, name, study_program, face_embedding)
            VALUES (?, ?, ?, ?)
            ''', (nim, name, study_program, json.dumps(embedding) if embedding else None))
            
            conn.commit()
            student_id = cursor.lastrowid
            return student_id
        except sqlite3.IntegrityError:
            print(f"⚠️ Mahasiswa dengan NIM {nim} sudah ada")
            return None
        finally:
            conn.close()
    
    def get_all_students(self):
        """Ambil semua mahasiswa"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM students ORDER BY nim')
        students = cursor.fetchall()
        
        conn.close()
        return [dict(student) for student in students]
    
    def get_student_by_nim(self, nim):
        """Cari mahasiswa berdasarkan NIM"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM students WHERE nim = ?', (nim,))
        student = cursor.fetchone()
        
        conn.close()
        return dict(student) if student else None
    
    def get_student_by_id(self, student_id):
        """Cari mahasiswa berdasarkan ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
        student = cursor.fetchone()
        
        conn.close()
        return dict(student) if student else None
    
    def update_student(self, student_id, name=None, study_program=None, embedding=None):
        """Update data mahasiswa"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name:
            updates.append("name = ?")
            params.append(name)
        if study_program:
            updates.append("study_program = ?")
            params.append(study_program)
        if embedding:
            updates.append("face_embedding = ?")
            params.append(json.dumps(embedding))
        
        if updates:
            params.append(student_id)
            cursor.execute(f'''
            UPDATE students 
            SET {', '.join(updates)}
            WHERE id = ?
            ''', params)
            
            conn.commit()
        
        conn.close()
        return True
    
    def delete_student(self, student_id):
        """Hapus mahasiswa"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
        conn.commit()
        
        conn.close()
        return True
    
    # ===== CRUD Mata Kuliah =====
    def add_course(self, code, name, semester=None):
        """Tambah mata kuliah baru"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO courses (code, name, semester)
        VALUES (?, ?, ?)
        ''', (code, name, semester))
        
        conn.commit()
        course_id = cursor.lastrowid
        
        conn.close()
        return course_id
    
    def get_all_courses(self):
        """Ambil semua mata kuliah"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM courses ORDER BY code')
        courses = cursor.fetchall()
        
        conn.close()
        return [dict(course) for course in courses]
    
    def get_course_by_code(self, code):
        """Cari mata kuliah berdasarkan kode"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM courses WHERE code = ?', (code,))
        course = cursor.fetchone()
        
        conn.close()
        return dict(course) if course else None
    
    # ===== CRUD Sesi =====
    def add_session(self, course_id, session_date, session_number=None, topic=None):
        """Tambah sesi kuliah"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO sessions (course_id, session_date, session_number, topic)
        VALUES (?, ?, ?, ?)
        ''', (course_id, session_date, session_number, topic))
        
        conn.commit()
        session_id = cursor.lastrowid
        
        conn.close()
        return session_id
    
    def get_today_sessions(self):
        """Ambil sesi hari ini"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
        SELECT s.*, c.code as course_code, c.name as course_name
        FROM sessions s
        JOIN courses c ON s.course_id = c.id
        WHERE date(s.session_date) = ?
        ORDER BY s.session_date
        ''', (today,))
        
        sessions = cursor.fetchall()
        
        conn.close()
        return [dict(session) for session in sessions]
    
    def get_sessions_by_course(self, course_id):
        """Ambil sesi berdasarkan mata kuliah"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM sessions 
        WHERE course_id = ?
        ORDER BY session_date
        ''', (course_id,))
        
        sessions = cursor.fetchall()
        
        conn.close()
        return [dict(session) for session in sessions]
    
    # ===== CRUD Absensi =====
    def add_attendance(self, student_id, session_id, confidence=None):
        """Tambah absensi"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        check_in_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Cek apakah sudah absen
        cursor.execute('''
        SELECT id FROM attendances 
        WHERE student_id = ? AND session_id = ?
        ''', (student_id, session_id))
        
        existing = cursor.fetchone()
        
        if existing:
            print(f"⚠️ Mahasiswa sudah absen untuk sesi ini")
            return None
        
        # Tambah absensi
        cursor.execute('''
        INSERT INTO attendances (student_id, session_id, check_in_time, confidence)
        VALUES (?, ?, ?, ?)
        ''', (student_id, session_id, check_in_time, confidence))
        
        conn.commit()
        attendance_id = cursor.lastrowid
        
        conn.close()
        return attendance_id
    
    def get_attendance_by_session(self, session_id):
        """Ambil absensi berdasarkan sesi"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT a.*, s.nim, s.name, s.study_program
        FROM attendances a
        JOIN students s ON a.student_id = s.id
        WHERE a.session_id = ?
        ORDER BY a.check_in_time
        ''', (session_id,))
        
        attendances = cursor.fetchall()
        
        conn.close()
        return [dict(attendance) for attendance in attendances]
    
    def get_student_attendance(self, student_id, course_id=None):
        """Ambil riwayat absensi mahasiswa"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
        SELECT a.*, c.code as course_code, c.name as course_name, 
               se.session_date, se.session_number, se.topic
        FROM attendances a
        JOIN sessions se ON a.session_id = se.id
        JOIN courses c ON se.course_id = c.id
        WHERE a.student_id = ?
        '''
        
        params = [student_id]
        
        if course_id:
            query += ' AND se.course_id = ?'
            params.append(course_id)
        
        query += ' ORDER BY a.check_in_time DESC'
        
        cursor.execute(query, params)
        attendances = cursor.fetchall()
        
        conn.close()
        return [dict(attendance) for attendance in attendances]
    
    # ===== Statistics =====
    def get_statistics(self):
        """Ambil statistik sistem"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total mahasiswa
        cursor.execute('SELECT COUNT(*) as count FROM students')
        stats['total_students'] = cursor.fetchone()['count']
        
        # Total mata kuliah
        cursor.execute('SELECT COUNT(*) as count FROM courses')
        stats['total_courses'] = cursor.fetchone()['count']
        
        # Total absensi hari ini
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
        SELECT COUNT(*) as count 
        FROM attendances 
        WHERE date(check_in_time) = ?
        ''', (today,))
        stats['today_attendance'] = cursor.fetchone()['count']
        
        # Absensi per mata kuliah
        cursor.execute('''
        SELECT c.code, c.name, COUNT(a.id) as attendance_count
        FROM courses c
        LEFT JOIN sessions s ON c.id = s.course_id
        LEFT JOIN attendances a ON s.id = a.session_id
        GROUP BY c.id
        ''')
        stats['attendance_by_course'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return stats

# Singleton instance
db = Database()