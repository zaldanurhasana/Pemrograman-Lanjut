import numpy as np
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib

X = np.load("X_train.npy")
y = np.load("y_train.npy", allow_pickle=True)

clf = Pipeline([
    ("scaler", StandardScaler()),
    ("svm", SVC(kernel="rbf", C=10, gamma="scale",
                probability=True, class_weight="balanced"))
])

# Karena data < 5 → gunakan cv=2 saja
scores = cross_val_score(clf, X, y, cv=2, scoring="accuracy")
print("CV acc mean:", scores.mean(), "±", scores.std())

clf.fit(X, y)
joblib.dump(clf, "facenet_svm.joblib")

print("\n✓ Model disimpan sebagai facenet_svm.joblib")
