import joblib
from utils_facenet import embed_from_path
import numpy as np

clf = joblib.load("facenet_knn.joblib")

def predict_image(path, unknown_threshold=0.70):
    print(f"\nMemprediksi gambar: {path}")

    emb = embed_from_path(path)
    if emb is None:
        print("❌ Wajah tidak terdeteksi!")
        return

    proba = clf.predict_proba([emb])[0]
    idx = np.argmax(proba)

    label = clf.classes_[idx]
    confidence = float(proba[idx])

    if confidence < unknown_threshold:
        print(f"Prediksi: UNKNOWN (conf={confidence:.3f})")
    else:
        print(f"Prediksi: {label} (conf={confidence:.3f})")

if __name__ == "__main__":
    predict_image("data/val/Zalda/z1.jpg")
