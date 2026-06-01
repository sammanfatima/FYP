import cv2
import mediapipe as mp
from mediapipe.python.solutions.face_mesh_connections import FACEMESH_TESSELATION
import time

class FaceDetector:
    def __init__(self, staticMode=False, maxFaces=1, minDetectionCon=0.5, minTrackCon=0.5):
        self.staticMode = staticMode
        self.maxFaces = maxFaces
        self.minDetectionCon = minDetectionCon
        self.minTrackCon = minTrackCon

        self.mpDraw = mp.solutions.drawing_utils
        self.mpFaceMesh = mp.solutions.face_mesh
        # Initialize FaceMesh with named parameters (more robust)
        self.FaceMesh = self.mpFaceMesh.FaceMesh(
            static_image_mode=self.staticMode,
            max_num_faces=self.maxFaces,
            refine_landmarks=True,
            min_detection_confidence=self.minDetectionCon,
            min_tracking_confidence=self.minTrackCon
        )
        self.drawspec = self.mpDraw.DrawingSpec(thickness=1, circle_radius=1)

    def findFaceMesh(self, img, draw=True):
        faces = []
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # convert to RGB
        self.results = self.FaceMesh.process(img_rgb)

        if self.results.multi_face_landmarks:
            for face_landmarks in self.results.multi_face_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(
                        img, face_landmarks, FACEMESH_TESSELATION, self.drawspec, self.drawspec
                    )
                face = []
                for id, landmark in enumerate(face_landmarks.landmark):
                    ih, iw, ic = img.shape
                    x, y = int(landmark.x * iw), int(landmark.y * ih)
                    # Optional: draw landmark ID
                    # cv2.putText(img, str(id), (x, y), cv2.FONT_HERSHEY_PLAIN, 0.5, (0, 255, 0), 1)
                    face.append([x, y])
                faces.append(face)
        return img, faces


def main():
    previous_time = 0
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    detector = FaceDetector()

    while True:
        success, img = cap.read()
        if not success:
            break

        img, faces = detector.findFaceMesh(img, draw=False)

        if len(faces) != 0:
            print(len(faces[0]))

        # calculating FPS
        current_time = time.time()
        fps = 1 / (current_time - previous_time)
        previous_time = current_time

        # putting fps on the screen
        cv2.putText(img, f'FPS: {int(fps)}', (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 65), 3)

        cv2.imshow("Image", img)
        if cv2.waitKey(1) & 0xFF == 27:  # press Esc to exit
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
