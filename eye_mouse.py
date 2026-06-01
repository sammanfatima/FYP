import cv2
import numpy as np
import pyautogui
import random
import time
import joblib
from sklearn.linear_model import LinearRegression
import FaceMeshModule as fm
import os
import csv
from threading import Thread

# -----------------------------
# PyQt5 IMPORTS
# -----------------------------
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
import sys


CALIB_CSV = "calibration_data.csv"
MODEL_FILE = "eye_model_with_bounds.pkl"

class EyeTracker:
    def __init__(self, img_w=640, img_h=480):
        self.img_w = img_w
        self.img_h = img_h
        self.frameR = 160
        self.detector = fm.FaceDetector(staticMode=False, maxFaces=1, minDetectionCon=0.5, minTrackCon=0.5)
        self.cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cam.set(3, img_w)
        self.cam.set(4, img_h)
        self.screen_w, self.screen_h = pyautogui.size()
        self.model = None
        self.bounds = None
        self.blink_threshold = 4
        self.blink_cooldown = 1.0
        self.last_blink_time = 0

    def append_to_csv(self, calib_data):
        file_exists = os.path.isfile(CALIB_CSV)
        with open(CALIB_CSV, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["iris_x", "iris_y", "screen_x", "screen_y"])
            writer.writerows(calib_data)

    def load_full_dataset(self):
        if not os.path.isfile(CALIB_CSV):
            return None
        data = []
        with open(CALIB_CSV, "r") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if not row:
                    continue
                try:
                    data.append([float(row[0]), float(row[1]), float(row[2]), float(row[3])])
                except:
                    continue
        return np.array(data) if data else None

    def calibrate(self, num_points=9):
        print("[INFO] Starting calibration...")
        calib_data = []
        points = self._generate_calibration_points(num_points)
        cv2.namedWindow("Calibration", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("Calibration", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        for i, (screen_x, screen_y) in enumerate(points):
            self._display_calibration_point(screen_x, screen_y)
            pyautogui.moveTo(screen_x, screen_y)
            time.sleep(0.5)
            samples = self._collect_eye_samples(duration=1.0)
            if samples:
                avg_iris = np.mean(samples, axis=0)
                calib_data.append([avg_iris[0], avg_iris[1], screen_x, screen_y])

        cv2.destroyWindow("Calibration")
        if len(calib_data) < 5:
            return False

        self.append_to_csv(calib_data)
        return self.train_model_from_csv()

    def _generate_calibration_points(self, num_points):
        pts = []
        margin = 60
        for _ in range(num_points):
            x = random.randint(margin, self.screen_w - margin)
            y = random.randint(margin, self.screen_h - margin)
            pts.append((x, y))
        return pts

    def _display_calibration_point(self, x, y):
        img = np.zeros((self.screen_h, self.screen_w, 3), np.uint8)
        cv2.circle(img, (x, y), 30, (0, 255, 0), cv2.FILLED)
        cv2.imshow("Calibration", img)

    def _collect_eye_samples(self, duration=1.0):
        samples = []
        t_end = time.time() + duration
        while time.time() < t_end:
            success, frame = self.cam.read()
            if not success:
                continue
            frame = cv2.flip(frame, 1)
            rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            _, faces = self.detector.findFaceMesh(rgb_img, draw=False)
            if faces:
                iris = faces[0][474:478]
                cx = int((iris[0][0] + iris[1][0] + iris[2][0] + iris[3][0]) / 4)
                cy = int((iris[0][1] + iris[1][1] + iris[2][1] + iris[3][1]) / 4)
                samples.append([cx, cy])
            if cv2.waitKey(1) == 27:
                break
        return samples

    def train_model_from_csv(self):
        dataset = self.load_full_dataset()
        if dataset is None or len(dataset) < 5:
            return False
        X = dataset[:, :2]
        y = dataset[:, 2:]
        model = LinearRegression()
        model.fit(X, y)
        min_x = float(np.min(X[:, 0]))
        max_x = float(np.max(X[:, 0]))
        min_y = float(np.min(X[:, 1]))
        max_y = float(np.max(X[:, 1]))
        bounds = {"min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y}
        self.model = model
        self.bounds = bounds
        joblib.dump({"model": model, "bounds": bounds}, MODEL_FILE)
        return True

    def load_model(self):
        if not os.path.isfile(MODEL_FILE):
            return False
        try:
            d = joblib.load(MODEL_FILE)
            self.model = d["model"]
            self.bounds = d["bounds"]
            return True
        except:
            return False

    def _detect_blink_and_click(self, face):
        left_eye = [face[145], face[159]]
        vertical_dist = abs(left_eye[0][1] - left_eye[1][1])

        current_time = time.time()
        if vertical_dist < self.blink_threshold and (current_time - self.last_blink_time) > self.blink_cooldown:
            print("[ACTION] Blink detected — Performing click!")
            pyautogui.click()
            self.last_blink_time = current_time

    def _detect_long_blink(self, face, long_blink_duration=0.5):
        left_eye = [face[145], face[159]]
        vertical_dist = abs(left_eye[0][1] - left_eye[1][1])

        current_time = time.time()
        if vertical_dist < self.blink_threshold:
            if not hasattr(self, "blink_start_time"):
                self.blink_start_time = current_time
        else:
            if hasattr(self, "blink_start_time"):
                blink_duration = current_time - self.blink_start_time
                if blink_duration >= long_blink_duration:
                    print(f"[ACTION] Long blink detected ({blink_duration:.2f}s) — Right Click!")
                    pyautogui.rightClick()
                del self.blink_start_time

    def _detect_double_blink(self, face, double_blink_window=0.6):
        left_eye = [face[145], face[159]]
        vertical_dist = abs(left_eye[0][1] - left_eye[1][1])
        current_time = time.time()

        if not hasattr(self, "blink_times"):
            self.blink_times = []

        if vertical_dist < self.blink_threshold:
            if not hasattr(self, "blink_state") or not self.blink_state:
                self.blink_state = True
                self.blink_times.append(current_time)
        else:
            self.blink_state = False

        self.blink_times = [t for t in self.blink_times if current_time - t <= double_blink_window]

        if len(self.blink_times) >= 2:
            print("[ACTION] Double blink detected!")
            pyautogui.click(x=500, y=300)
            self.blink_times.clear()

    def start_tracking(self):
        if not self.load_model():
            print("No trained model found.")
            return
        while True:
            success, img = self.cam.read()
            if not success:
                continue
            img = cv2.flip(img, 1)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            _, faces = self.detector.findFaceMesh(rgb_img, draw=False)
            if faces:
                face = faces[0]
                iris = face[474:478]
                x = sum([p[0] for p in iris]) / 4.0
                y = sum([p[1] for p in iris]) / 4.0
                sx = np.interp(x, (self.frameR, self.img_w - self.frameR), (0, self.screen_w - 1))
                sy = np.interp(y, (self.frameR, self.img_h - self.frameR), (0, self.screen_h - 1))

                try:
                    pyautogui.moveTo(int(round(sx)), int(round(sy)), _pause=False)
                except:
                    pass

                self._detect_blink_and_click(face)

            cv2.imshow("Eye Tracking", img)
            if cv2.waitKey(1) == 27:
                break

        self.cam.release()
        cv2.destroyAllWindows()


# -----------------------------
# PYQT GUI (Tkinter replaced)
# -----------------------------
class App(QWidget):
    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Eye Tracker")
        self.setGeometry(600, 250, 440, 320)
        self.setStyleSheet("background-color: black;")

        layout = QVBoxLayout()

        header = QLabel("EYE TRACKER CONTROL")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color:#00FF66; font-size:22px; font-weight:bold;")
        layout.addWidget(header)

        btn_track = QPushButton("▶ START TRACKING")
        btn_track.setStyleSheet("""
            QPushButton {
                color:#00FF66; background-color:#111;
                font-size:16px; font-weight:bold;
                padding:12px; border:0;
            }
            QPushButton:hover {
                color:black; background-color:#00FF66;
            }
        """)
        btn_track.clicked.connect(lambda: Thread(target=self.tracker.start_tracking, daemon=True).start())
        layout.addWidget(btn_track)

        btn_calib = QPushButton("◎ RUN CALIBRATION")
        btn_calib.setStyleSheet("""
            QPushButton {
                color:#00FF66; background-color:#111;
                font-size:16px; font-weight:bold;
                padding:12px; border:0;
            }
            QPushButton:hover {
                color:black; background-color:#00FF66;
            }
        """)
        btn_calib.clicked.connect(lambda: Thread(target=self.tracker.calibrate, daemon=True).start())
        layout.addWidget(btn_calib)

        self.setLayout(layout)


tracker = EyeTracker()

app = QApplication(sys.argv)
window = App(tracker)
window.show()
sys.exit(app.exec_())
