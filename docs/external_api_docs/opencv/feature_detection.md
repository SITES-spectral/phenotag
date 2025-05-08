# OpenCV Feature Detection

## Corner Detection

### Harris Corner Detector

```python
import numpy as np
import cv2 as cv

filename = 'chessboard.png'
img = cv.imread(filename)
gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

gray = np.float32(gray)
dst = cv.cornerHarris(gray, 2, 3, 0.04)

# Result is dilated for marking the corners, not important
dst = cv.dilate(dst, None)

# Threshold for an optimal value, it may vary depending on the image.
img[dst > 0.01 * dst.max()] = [0, 0, 255]

cv.imshow('dst', img)
if cv.waitKey(0) & 0xff == 27:
    cv.destroyAllWindows()
```

### Shi-Tomasi Corner Detector

```python
corners = cv2.goodFeaturesToTrack(gray, 25, 0.01, 10)
corners = np.int0(corners)

for i in corners:
    x, y = i.ravel()
    cv2.circle(img, (x, y), 3, 255, -1)
```

## Feature Descriptors and Matching

### Scale-Invariant Feature Transform (SIFT)

```python
sift = cv2.SIFT_create()
keypoints, descriptors = sift.detectAndCompute(gray, None)

# Draw keypoints
img_keypoints = cv2.drawKeypoints(img, keypoints, None, flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
```

### Speeded-Up Robust Features (SURF)

```python
# Note: SURF is patented, you might need to use contrib modules
surf = cv2.xfeatures2d.SURF_create(400)
keypoints, descriptors = surf.detectAndCompute(gray, None)
```

### Oriented FAST and Rotated BRIEF (ORB)

```python
orb = cv2.ORB_create()
keypoints, descriptors = orb.detectAndCompute(gray, None)
```

### Feature Matching

```python
# Brute-Force Matcher
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
matches = bf.match(descriptors1, descriptors2)

# Sort matches by distance
matches = sorted(matches, key=lambda x: x.distance)

# Draw first 10 matches
img_matches = cv2.drawMatches(img1, keypoints1, img2, keypoints2, matches[:10], None, flags=2)
```

### FLANN Based Matcher

```python
# FLANN parameters
FLANN_INDEX_KDTREE = 1
index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
search_params = dict(checks=50)

flann = cv2.FlannBasedMatcher(index_params, search_params)
matches = flann.knnMatch(descriptors1, descriptors2, k=2)

# Apply ratio test
good_matches = []
for m, n in matches:
    if m.distance < 0.7 * n.distance:
        good_matches.append(m)
```

## Contour Detection and Analysis

### Finding Contours

```python
# First, get a binary image
ret, thresh = cv2.threshold(gray, 127, 255, 0)
contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# Draw all contours
img_contours = cv2.drawContours(img.copy(), contours, -1, (0, 255, 0), 3)
```

### Contour Properties

```python
# Calculate properties for each contour
for cnt in contours:
    # Calculate area
    area = cv2.contourArea(cnt)
    
    # Calculate perimeter
    perimeter = cv2.arcLength(cnt, True)
    
    # Calculate circularity
    circularity = 4 * np.pi * area / (perimeter * perimeter)
    
    # Get bounding rectangle
    x, y, w, h = cv2.boundingRect(cnt)
    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    # Get minimum enclosing circle
    (x, y), radius = cv2.minEnclosingCircle(cnt)
    center = (int(x), int(y))
    radius = int(radius)
    cv2.circle(img, center, radius, (0, 255, 0), 2)
    
    # Calculate solidity
    hull = cv2.convexHull(cnt)
    hull_area = cv2.contourArea(hull)
    solidity = float(area) / hull_area if hull_area > 0 else 0
```

## Optical Flow

### Dense Optical Flow

```python
import numpy as np
import cv2 as cv
import argparse

cap = cv.VideoCapture('video.mp4')

ret, frame1 = cap.read()
prvs = cv.cvtColor(frame1, cv.COLOR_BGR2GRAY)
hsv = np.zeros_like(frame1)
hsv[..., 1] = 255

while(1):
    ret, frame2 = cap.read()
    if not ret:
        print('No frames grabbed!')
        break

    next = cv.cvtColor(frame2, cv.COLOR_BGR2GRAY)

    flow = cv.calcOpticalFlowFarneback(prvs, next, None, 0.5, 3, 15, 3, 5, 1.2, 0)

    mag, ang = cv.cartToPolar(flow[..., 0], flow[..., 1])
    hsv[..., 0] = ang*180/np.pi/2
    hsv[..., 2] = cv.normalize(mag, None, 0, 255, cv.NORM_MINMAX)
    bgr = cv.cvtColor(hsv, cv.COLOR_HSV2BGR)

    cv.imshow('frame2', bgr)
    k = cv.waitKey(30) & 0xff
    if k == 27:
        break
    prvs = next

cv.destroyAllWindows()
```

### Sparse Optical Flow (Lucas-Kanade)

```python
# params for ShiTomasi corner detection
feature_params = dict(maxCorners=100, qualityLevel=0.3, minDistance=7, blockSize=7)

# Parameters for lucas kanade optical flow
lk_params = dict(winSize=(15, 15), maxLevel=2, 
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

# Create random colors
color = np.random.randint(0, 255, (100, 3))

# Take first frame and find corners in it
old_frame = cv2.imread('frame1.jpg')
old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)

# Create a mask image for drawing purposes
mask = np.zeros_like(old_frame)

# Read the next frame
frame = cv2.imread('frame2.jpg')
frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# Calculate optical flow
p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)

# Select good points
good_new = p1[st==1]
good_old = p0[st==1]

# Draw the tracks
for i, (new, old) in enumerate(zip(good_new, good_old)):
    a, b = new.ravel()
    c, d = old.ravel()
    mask = cv2.line(mask, (int(a), int(b)), (int(c), int(d)), color[i].tolist(), 2)
    frame = cv2.circle(frame, (int(a), int(b)), 5, color[i].tolist(), -1)
    
img = cv2.add(frame, mask)
cv2.imshow('frame', img)
```