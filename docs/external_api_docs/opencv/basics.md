# OpenCV Basics

## Installation

```python
# Using pip
pip install opencv-python

# For full package with contrib modules
pip install opencv-python-contrib
```

## Core Operations

### Loading and Saving Images

```python
import cv2
import numpy as np

# Reading an image
img = cv2.imread('image.jpg')  # BGR format by default
img_gray = cv2.imread('image.jpg', cv2.IMREAD_GRAYSCALE)  # Grayscale

# Saving an image
cv2.imwrite('output.jpg', img)
```

### Displaying Images

```python
# Create a window and display an image
cv2.imshow('Window Title', img)

# Wait for a key press (0 means wait indefinitely)
cv2.waitKey(0)

# Close all windows
cv2.destroyAllWindows()
```

### Accessing and Modifying Pixels

```python
# Access a pixel's BGR value at coordinates (100, 100)
px = img[100, 100]
print(px)  # [Blue, Green, Red] values

# Access only the Blue channel value at the same location
blue = img[100, 100, 0]
print(blue)

# Modify a pixel
img[100, 100] = [255, 0, 0]  # Set to blue
```

### Color Space Conversions

```python
# Convert BGR to Grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Convert BGR to HSV
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Convert BGR to RGB (for displaying with matplotlib)
rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
```

### Basic Image Manipulation

```python
# Resize an image
resized = cv2.resize(img, (width, height))
# With interpolation method
resized = cv2.resize(img, (width, height), interpolation=cv2.INTER_CUBIC)

# Rotate an image
rows, cols = img.shape[:2]
rotation_matrix = cv2.getRotationMatrix2D((cols/2, rows/2), 90, 1)
rotated = cv2.warpAffine(img, rotation_matrix, (cols, rows))

# Flip an image
# 0: flip vertically, 1: flip horizontally, -1: flip both
flipped = cv2.flip(img, 1)
```

### Type Conversions for Display

```python
# Convert float32 image to uint8 for display
img8u = (img * 255).astype(np.uint8)
cv2.imshow('Window', img8u)
cv2.waitKey(0)
```