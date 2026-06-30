# desktop-camera-app-
Digital Camera

A desktop camera application built in Python with a Tkinter interface. It turns a regular webcam into a small photo-and-video studio: live preview, real-time filters, decorative frames, a self-timer, burst mode, video recording, and a built-in gallery — all in one window.

The whole application is a single Python script. Once the dependencies are installed, you run one file and the camera opens.

Overview

I built this to go beyond a basic "open the webcam" demo and put together something that actually feels like a camera app you'd want to use. The focus was on the details that make capturing a photo enjoyable — seeing your filter applied live before you shoot, a countdown timer for group shots, framing options for the final image, and a gallery strip so you can review what you just took without leaving the app.

The code is organized into clearly labelled sections (settings, colours, filters, frames, camera core, video recorder, saving, histogram, and the main app), which keeps it readable and easy to extend.

Features


Live camera preview with support for switching between multiple connected cameras (built-in and external USB).
Ten real-time filters: none, grayscale, sepia, blur, sharpen, vivid, cool, warm, negative, and sketch — applied live in the preview, not just on the saved file.
Four decorative frames: polaroid, vignette, and filmstrip, plus a clean no-frame option, drawn onto the captured photo.
Self-timer with selectable delays (3, 5, or 10 seconds) and an on-screen countdown.
Burst mode that captures a rapid sequence of shots in one press.
Video recording saved to a dedicated videos folder.
Image adjustments for brightness, contrast, and zoom via live sliders.
Live histogram showing the tonal distribution of the current frame.
Built-in gallery with scrollable thumbnails and a click-to-preview panel.
Configurable settings at the top of the file — save folders, default camera, preview size, JPEG quality, timer options, and burst behavior — all easy to change in one place.


Tech Stack


Python 3
Tkinter for the graphical interface
OpenCV (opencv-python) for camera capture and video
Pillow (PIL) for image processing and filters
NumPy for array operations
