# OpenCV Image Processing

## Image Filtering

### Convolution with Custom Kernel

```python
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt

img = cv.imread('opencv_logo.png')
assert img is not None, "file could not be read, check with os.path.exists()"

kernel = np.ones((5,5),np.float32)/25
dst = cv.filter2D(img,-1,kernel)

plt.subplot(121),plt.imshow(img),plt.title('Original')
plt.xticks([]), plt.yticks([])
plt.subplot(122),plt.imshow(dst),plt.title('Averaging')
plt.xticks([]), plt.yticks([])
plt.show()
```

### Blurring (Smoothing)

```python
# Average/Box filter
blur = cv2.blur(img, (5, 5))

# Gaussian blur
gaussian = cv2.GaussianBlur(img, (5, 5), 0)

# Median blur (good for salt-and-pepper noise)
median = cv2.medianBlur(img, 5)

# Bilateral filter (preserves edges)
bilateral = cv2.bilateralFilter(img, 9, 75, 75)
```

## Thresholding

### Simple Thresholding

```python
# Convert to grayscale first
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Apply simple threshold
ret, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

# Different thresholding types
cv2.THRESH_BINARY  # Binary threshold
cv2.THRESH_BINARY_INV  # Inverted binary
cv2.THRESH_TRUNC  # Truncated threshold
cv2.THRESH_TOZERO  # Threshold to zero
cv2.THRESH_TOZERO_INV  # Inverted threshold to zero
```

### Adaptive Thresholding

```python
# Adaptive mean thresholding
adaptive_mean = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)

# Adaptive Gaussian thresholding
adaptive_gaussian = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY, 11, 2)
```

### Otsu's Thresholding

```python
# Otsu's thresholding
ret, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
```

## Morphological Operations

### Basic Operations

```python
# Define a kernel
kernel = np.ones((5, 5), np.uint8)

# Erosion - shrinks foreground
erosion = cv2.erode(img, kernel, iterations=1)

# Dilation - expands foreground
dilation = cv.dilate(img, kernel, iterations=1)

# Opening - erosion followed by dilation
opening = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)

# Closing - dilation followed by erosion
closing = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)

# Morphological gradient - dilation minus erosion
gradient = cv2.morphologyEx(img, cv2.MORPH_GRADIENT, kernel)

# Top hat - difference between input and opening
tophat = cv2.morphologyEx(img, cv2.MORPH_TOPHAT, kernel)

# Black hat - difference between closing and input
blackhat = cv2.morphologyEx(img, cv2.MORPH_BLACKHAT, kernel)
```

## Edge Detection

### Canny Edge Detector

```python
edges = cv2.Canny(gray, 100, 200)  # lower and upper thresholds
```

### Sobel and Laplacian

```python
# Sobel edge detector
sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=5)  # x direction
sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)  # y direction
sobel = cv2.magnitude(sobelx, sobely)  # combined magnitude

# Laplacian
laplacian = cv2.Laplacian(gray, cv2.CV_64F)
```

## Histogram Operations

```python
# Calculate histogram
hist = cv2.calcHist([gray], [0], None, [256], [0, 256])

# Equalize histogram
equ = cv2.equalizeHist(gray)

# CLAHE (Contrast Limited Adaptive Histogram Equalization)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
cl1 = clahe.apply(gray)
```

## Template Matching

```python
# Apply template matching
res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

# For TM_SQDIFF methods, minimum value gives best match
if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
    top_left = min_loc
else:
    top_left = max_loc
    
bottom_right = (top_left[0] + w, top_left[1] + h)
cv2.rectangle(img, top_left, bottom_right, 255, 2)
```