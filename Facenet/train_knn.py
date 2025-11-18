import numpy as np, joblib
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Load embedding
X = np.load("X_train.npy")
y = np.load("y_train.npy", allow_pickle=True)

# KNN lebih bagus untuk dataset kecil
clf = Pipeline([
    ("scaler", StandardScaler()),
    ("knn", KNeighborsClassifier(n_neighbors=1, metric="euclidean"))
])

clf.fit(X, y)
joblib.dump(clf, "facenet_knn.joblib")

print("Model KNN tersimpan sebagai facenet_knn.joblib")
