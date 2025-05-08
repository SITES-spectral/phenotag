# OpenCV Camera Calibration and 3D

## Camera Calibration

```python
import numpy as np
import cv2 as cv
import glob

# Termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# Prepare object points (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((6*7,3), np.float32)
objp[:,:2] = np.mgrid[0:7,0:6].T.reshape(-1,2)

# Arrays to store object points and image points from all the images
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane

# Get list of calibration images
images = glob.glob('*.jpg')

for fname in images:
    img = cv.imread(fname)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    
    # Find the chess board corners
    ret, corners = cv.findChessboardCorners(gray, (7,6), None)
    
    # If found, add object points, image points (after refining them)
    if ret == True:
        objpoints.append(objp)
        
        corners2 = cv.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
        imgpoints.append(corners2)
        
        # Draw and display the corners
        cv.drawChessboardCorners(img, (7,6), corners2, ret)
        cv.imshow('img', img)
        cv.waitKey(500)
        
cv.destroyAllWindows()

# Calibration
ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

# Undistort an image
img = cv.imread('test.jpg')
h, w = img.shape[:2]
newcameramtx, roi = cv.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))

# Undistort
dst = cv.undistort(img, mtx, dist, None, newcameramtx)

# Crop the image
x, y, w, h = roi
dst = dst[y:y+h, x:x+w]
cv.imwrite('calibrated.png', dst)
```

## Stereo Depth Mapping

```python
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt

imgL = cv.imread('tsukuba_l.png', cv.IMREAD_GRAYSCALE)
imgR = cv.imread('tsukuba_r.png', cv.IMREAD_GRAYSCALE)

stereo = cv.StereoBM.create(numDisparities=16, blockSize=15)
disparity = stereo.compute(imgL,imgR)
plt.imshow(disparity,'gray')
plt.show()
```

## Pose Estimation

### Setting up Kalman Filter

```python
def initKalmanFilter(KF, nStates, nMeasurements, nInputs, dt):
    KF.init(nStates, nMeasurements, nInputs, CV_64F)
    
    cv.setIdentity(KF.processNoiseCov, cv.Scalar::all(1e-5))
    cv.setIdentity(KF.measurementNoiseCov, cv.Scalar::all(1e-4))
    cv.setIdentity(KF.errorCovPost, cv.Scalar::all(1))
    
    # Dynamic model
    # [1 0 0 dt  0  0 dt2   0   0 0 0 0  0  0  0   0   0   0]
    # [0 1 0  0 dt  0   0 dt2   0 0 0 0  0  0  0   0   0   0]
    # [0 0 1  0  0 dt   0   0 dt2 0 0 0  0  0  0   0   0   0]
    # ...
    
    # Position
    KF.transitionMatrix.at<double>(0,3) = dt
    KF.transitionMatrix.at<double>(1,4) = dt
    KF.transitionMatrix.at<double>(2,5) = dt
    # More initializations...
    
    # Measurement model
    KF.measurementMatrix.at<double>(0,0) = 1  # x
    KF.measurementMatrix.at<double>(1,1) = 1  # y
    KF.measurementMatrix.at<double>(2,2) = 1  # z
    KF.measurementMatrix.at<double>(3,9) = 1  # roll
    KF.measurementMatrix.at<double>(4,10) = 1 # pitch
    KF.measurementMatrix.at<double>(5,11) = 1 # yaw
```

### Pose Estimation with ArUco Markers

```python
import numpy as np
import cv2 as cv
import cv2.aruco as aruco

# Load camera parameters
with np.load('camera_params.npz') as X:
    mtx, dist = [X[i] for i in ('mtx', 'dist')]

# Define ArUco dictionary and parameters
aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
parameters = aruco.DetectorParameters_create()

# Capture video
cap = cv.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    # Convert to grayscale
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    
    # Detect markers
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    
    if ids is not None:
        # Draw detected markers
        aruco.drawDetectedMarkers(frame, corners, ids)
        
        # Estimate pose for each marker
        rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(corners, 0.05, mtx, dist)
        
        for i in range(len(ids)):
            # Draw axis for each marker
            aruco.drawAxis(frame, mtx, dist, rvecs[i], tvecs[i], 0.03)
            
    # Display the frame
    cv.imshow('Frame', frame)
    
    if cv.waitKey(1) & 0xFF == ord('q'):
        break
        
cap.release()
cv.destroyAllWindows()
```

## Face Detection and Recognition

### Face Detection using DNN

```python
import cv2 as cv
import numpy as np

# Load the DNN model
modelFile = "models/opencv_face_detector_uint8.pb"
configFile = "models/opencv_face_detector.pbtxt"
net = cv.dnn.readNetFromTensorflow(modelFile, configFile)

# Read image
img = cv.imread("test.jpg")
h, w, _ = img.shape

# Preprocess
blob = cv.dnn.blobFromImage(img, 1.0, (300, 300), [104, 117, 123], False, False)
net.setInput(blob)
detections = net.forward()

# Process detections
for i in range(detections.shape[2]):
    confidence = detections[0, 0, i, 2]
    if confidence > 0.5:
        x1 = int(detections[0, 0, i, 3] * w)
        y1 = int(detections[0, 0, i, 4] * h)
        x2 = int(detections[0, 0, i, 5] * w)
        y2 = int(detections[0, 0, i, 6] * h)
        
        cv.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"Face: {confidence:.2f}"
        cv.putText(img, label, (x1, y1-10), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

cv.imshow("Face Detection", img)
cv.waitKey(0)
```

### Face Recognition using DNN

```python
# Extract face feature embedding
recognizer = cv.FaceRecognizerSF.create("models/face_recognition_sface.onnx", "")
face_feature = recognizer.feature(aligned_face)

# Match two face features
cosineScore = recognizer.match(feature1, feature2, cv.FaceRecognizerSF.DisType.FR_COSINE)
l2Score = recognizer.match(feature1, feature2, cv.FaceRecognizerSF.DisType.FR_NORM_L2)
```