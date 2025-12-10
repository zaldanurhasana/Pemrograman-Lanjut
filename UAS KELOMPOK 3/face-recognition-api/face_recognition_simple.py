# face_recognition_simple.py - Face recognition dengan OpenCV (Fixed)
import cv2
import numpy as np
import os
import pickle
from PIL import Image
import hashlib
from datetime import datetime

class SimpleFaceRecognition:
    def __init__(self):
        # Face detector menggunakan Haar Cascade
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Cek apakah opencv-contrib terinstall untuk face module
        try:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            self.has_face_module = True
        except AttributeError:
            print("⚠️ OpenCV face module tidak tersedia. Menggunakan metode sederhana.")
            self.recognizer = None
            self.has_face_module = False
        
        self.known_faces = {}  # {face_id: {"name": str, "nim": str}}
        self.face_encodings = {}  # {face_id: face_encoding}
        self.model_path = "models/simple_face_model.pkl"
        
        os.makedirs("models", exist_ok=True)
        os.makedirs("dataset", exist_ok=True)
        
        self.load_model()
    
    def load_model(self):
        """Load model jika ada"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.known_faces = data.get('known_faces', {})
                    self.face_encodings = data.get('face_encodings', {})
                print(f"✅ Loaded {len(self.known_faces)} known faces")
                return True
        except Exception as e:
            print(f"⚠️ Error loading model: {e}")
        
        return False
    
    def save_model(self):
        """Save model"""
        try:
            data = {
                'known_faces': self.known_faces,
                'face_encodings': self.face_encodings
            }
            with open(self.model_path, 'wb') as f:
                pickle.dump(data, f)
            print(f"✅ Model saved with {len(self.known_faces)} faces")
            return True
        except Exception as e:
            print(f"❌ Error saving model: {e}")
            return False
    
    def extract_face_features(self, face_image):
        """
        Ekstrak fitur sederhana dari wajah
        Menggunakan histogram dan fitur sederhana
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            
            # Resize untuk konsistensi
            resized = cv2.resize(gray, (100, 100))
            
            # Flatten dan normalize
            flattened = resized.flatten()
            normalized = flattened / 255.0
            
            # Simple features: histogram dan moments
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = hist.flatten()
            hist = hist / hist.sum() if hist.sum() > 0 else hist
            
            moments = cv2.moments(gray)
            hu_moments = cv2.HuMoments(moments).flatten()
            
            # Combine features
            features = np.concatenate([
                normalized,
                hist,
                hu_moments
            ])
            
            return features
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            return None
    
    def detect_faces(self, image_array):
        """Deteksi wajah dalam gambar"""
        # Convert ke grayscale
        gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
        
        # Deteksi wajah
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        return faces, gray
    
    def register_face(self, nim: str, name: str, image_path: str):
        """Registrasi wajah baru"""
        try:
            # Baca gambar
            image = cv2.imread(image_path)
            if image is None:
                return {"success": False, "message": "Gambar tidak valid"}
            
            # Deteksi wajah
            faces, gray = self.detect_faces(image)
            
            if len(faces) == 0:
                return {"success": False, "message": "Tidak ada wajah terdeteksi"}
            
            if len(faces) > 1:
                return {"success": False, "message": "Lebih dari satu wajah terdeteksi"}
            
            x, y, w, h = faces[0]
            
            # Crop wajah
            face_roi = image[y:y+h, x:x+w]
            
            # Ekstrak fitur
            features = self.extract_face_features(face_roi)
            
            if features is None:
                return {"success": False, "message": "Gagal mengekstrak fitur wajah"}
            
            # Generate face ID
            face_id = f"{nim}_{hashlib.md5(name.encode()).hexdigest()[:8]}"
            
            # Simpan ke dataset
            dataset_path = f"dataset/{face_id}"
            os.makedirs(dataset_path, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            face_image_path = f"{dataset_path}/{timestamp}.jpg"
            cv2.imwrite(face_image_path, face_roi)
            
            # Simpan ke memory
            self.known_faces[face_id] = {
                "nim": nim,
                "name": name,
                "face_id": face_id
            }
            
            self.face_encodings[face_id] = features
            
            # Save model
            self.save_model()
            
            return {
                "success": True,
                "message": f"Wajah {name} berhasil diregistrasi",
                "face_id": face_id,
                "face_location": (int(x), int(y), int(w), int(h))
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def compare_faces(self, features1, features2, threshold=0.7):
        """
        Bandingkan dua fitur wajah menggunakan cosine similarity
        """
        try:
            # Cosine similarity
            dot_product = np.dot(features1, features2)
            norm1 = np.linalg.norm(features1)
            norm2 = np.linalg.norm(features2)
            
            if norm1 == 0 or norm2 == 0:
                return 0
            
            similarity = dot_product / (norm1 * norm2)
            return similarity
            
        except:
            return 0
    
    def recognize_face(self, image_path: str, threshold: float = 0.6):
        """Mengenali wajah dari gambar"""
        try:
            # Baca gambar
            image = cv2.imread(image_path)
            if image is None:
                return {"success": False, "message": "Gambar tidak valid"}
            
            # Deteksi wajah
            faces, gray = self.detect_faces(image)
            
            if len(faces) == 0:
                return {
                    "success": False,
                    "message": "Tidak ada wajah terdeteksi",
                    "faces_detected": 0
                }
            
            results = []
            
            for (x, y, w, h) in faces:
                # Crop wajah
                face_roi = image[y:y+h, x:x+w]
                
                # Ekstrak fitur
                features = self.extract_face_features(face_roi)
                
                if features is None:
                    results.append({
                        "success": False,
                        "message": "Gagal mengekstrak fitur",
                        "face_location": (int(x), int(y), int(w), int(h))
                    })
                    continue
                
                # Bandingkan dengan semua wajah yang dikenal
                best_match = None
                best_similarity = 0
                
                for face_id, known_features in self.face_encodings.items():
                    similarity = self.compare_faces(features, known_features)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = face_id
                
                # Check threshold
                if best_match and best_similarity >= threshold:
                    face_data = self.known_faces.get(best_match, {})
                    
                    results.append({
                        "success": True,
                        "name": face_data.get("name", "Unknown"),
                        "nim": face_data.get("nim", "unknown"),
                        "confidence": round(best_similarity * 100, 2),
                        "face_location": (int(x), int(y), int(w), int(h)),
                        "similarity": round(best_similarity, 4),
                        "face_id": best_match
                    })
                else:
                    results.append({
                        "success": False,
                        "message": "Wajah tidak dikenali",
                        "face_location": (int(x), int(y), int(w), int(h)),
                        "similarity": round(best_similarity, 4) if best_similarity > 0 else 0
                    })
            
            # Check if any face was recognized
            recognized = any(r.get('success', False) for r in results)
            
            return {
                "success": recognized,
                "results": results,
                "faces_detected": len(faces),
                "recognized_count": sum(1 for r in results if r.get('success', False))
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def get_registered_faces(self):
        """Get list of registered faces"""
        return {
            "count": len(self.known_faces),
            "faces": list(self.known_faces.values())
        }
    
    def remove_face(self, nim: str):
        """Hapus wajah dari sistem"""
        try:
            faces_to_remove = []
            
            for face_id, face_data in self.known_faces.items():
                if face_data.get("nim") == nim:
                    faces_to_remove.append(face_id)
            
            for face_id in faces_to_remove:
                self.known_faces.pop(face_id, None)
                self.face_encodings.pop(face_id, None)
                
                # Hapus folder dataset
                dataset_path = f"dataset/{face_id}"
                if os.path.exists(dataset_path):
                    import shutil
                    shutil.rmtree(dataset_path)
            
            # Save model
            self.save_model()
            
            return {
                "success": True,
                "message": f"Wajah dengan NIM {nim} dihapus",
                "removed_count": len(faces_to_remove)
            }
                
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

# Global instance
face_system = SimpleFaceRecognition()