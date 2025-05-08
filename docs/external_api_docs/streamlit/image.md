# st.image

## Overview

`st.image` displays an image or list of images in a Streamlit app. It supports various input formats and provides options for customizing the display.

## Syntax

```python
st.image(
    image,
    caption=None,
    width=None,
    use_column_width=None,
    clamp=False,
    channels="RGB",
    output_format="auto"
)
```

## Parameters

- **image** (numpy.ndarray, [numpy.ndarray], BytesIO, str, or [str]): 
  - The image to display. Can be:
    - NumPy array representing an image
    - List of NumPy arrays, each representing an image
    - PIL.Image
    - BytesIO object containing the image data
    - String with the filename or URL of the image
    - List of strings with filenames or URLs

- **caption** (str or list of str, optional):
  - Image caption. If image is a list, caption should be a list of strings of the same length.
  - Default: None

- **width** (int, optional):
  - Image width in pixels.
  - Default: None (auto)

- **use_column_width** (bool or str, optional):
  - If "auto", image will scale to column width if dimensions exceed column width.
  - If True, image will be forced to scale to column width.
  - If False, image will be displayed at actual resolution or `width` if specified.
  - Default: None

- **clamp** (bool, optional):
  - If True, clamp pixel values to the valid 0-255 range.
  - Default: False

- **channels** (str, optional):
  - Color channels used in the image. One of:
    - "RGB" (Red, Green, Blue)
    - "BGR" (Blue, Green, Red)
  - Default: "RGB"

- **output_format** (str, optional):
  - Output format to use. One of:
    - "JPEG"
    - "PNG"
    - "auto" (PNG for images with transparency, otherwise JPEG)
  - Default: "auto"

## Returns

None

## Examples

### Display an image from a file

```python
import streamlit as st
from PIL import Image

# Display an image from a file
st.image("path/to/image.jpg", caption="Image from file")
```

### Display an image with custom width

```python
import streamlit as st
from PIL import Image

# Display an image with custom width of 300 pixels
st.image("path/to/image.jpg", width=300)
```

### Display an image with column width

```python
import streamlit as st
from PIL import Image

# Display an image that scales to column width
st.image("path/to/image.jpg", use_column_width=True)
```

### Display an image from a URL

```python
import streamlit as st

# Display an image from a URL
st.image("https://example.com/image.jpg", caption="Image from URL")
```

### Display multiple images

```python
import streamlit as st
from PIL import Image

# Display multiple images with captions
images = ["path/to/image1.jpg", "path/to/image2.jpg", "path/to/image3.jpg"]
captions = ["Image 1", "Image 2", "Image 3"]
st.image(images, caption=captions, width=200)
```

### Display a NumPy array as an image

```python
import streamlit as st
import numpy as np
from PIL import Image

# Create a simple NumPy array image (red square)
arr = np.zeros((100, 100, 3), dtype=np.uint8)
arr[:, :, 0] = 255  # Red channel set to maximum

# Display the NumPy array as an image
st.image(arr, caption="NumPy Array Image")
```

### Display an image with BGR channels

```python
import streamlit as st
import cv2

# Read an image with OpenCV (which uses BGR channel ordering)
img = cv2.imread("path/to/image.jpg")

# Display the BGR image by specifying the channels parameter
st.image(img, channels="BGR")
```

### Display an image with transparency (PNG)

```python
import streamlit as st
import numpy as np
from PIL import Image

# Create an RGBA image with transparency
img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))  # Semi-transparent red

# Display the image, automatically using PNG format for transparency
st.image(img)

# Or force JPEG format (will lose transparency)
st.image(img, output_format="JPEG")
```

## Common Issues

1. **Image Not Displaying**:
   - Ensure the image path is correct
   - Verify the image file exists and is not corrupted
   - Check that the image format is supported

2. **Color Channels**:
   - If using OpenCV to read images, remember that OpenCV uses BGR channel ordering by default
   - Use `channels="BGR"` parameter or convert the image using `cv2.cvtColor(img, cv2.COLOR_BGR2RGB)`

3. **Memory Issues with Large Images**:
   - Large images may cause memory issues
   - Consider resizing large images before displaying them

4. **File Not Found Errors**:
   - Use absolute paths or ensure relative paths are correct based on the working directory
   - For URLs, ensure the URL is accessible and correctly formatted