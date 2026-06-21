import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import datetime
import os
import sys
import json
import math

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageDraw, ImageFont
except ImportError as e:
    print(f"\n  Missing library: {e}")
    print("  Run this to install everything:\n")
    print("  pip install opencv-python pillow numpy\n")
    sys.exit(1)


# ==============================================================
#  SECTION 1 — SETTINGS
#  Change these to customise the camera app behaviour.
# ==============================================================

SAVE_FOLDER       = "photos"          # folder where photos are saved
VIDEO_FOLDER      = "videos"          # folder where videos are saved
DEFAULT_CAMERA    = 0                 # 0 = built-in webcam, 1 = external USB cam
PREVIEW_WIDTH     = 800               # preview window width in pixels
PREVIEW_HEIGHT    = 600               # preview window height in pixels
PHOTO_QUALITY     = 95               # JPEG quality 1-100 (95 is great)
TIMER_OPTIONS     = [0, 3, 5, 10]    # self-timer options in seconds
BURST_COUNT       = 5                 # how many photos burst mode takes
BURST_DELAY       = 0.3              # seconds between burst shots


# ==============================================================
#  SECTION 2 — COLOURS (same style as the other projects)
# ==============================================================

BG        = "#2d1a1e"
SURFACE   = "#3d2229"
CARD      = "#4a2a33"
BORDER    = "#6b3a47"
ACCENT    = "#ffb6c1"
ACCENT_LO = "#e8829a"
GREEN     = "#c8e6c9"
RED       = "#ff6b8a"
AMBER     = "#ffcc80"
PURPLE    = "#ce93d8"
CYAN      = "#f48fb1"
TEXT_PRI  = "#fff0f3"
TEXT_SEC  = "#f8bbd0"
TEXT_MUT  = "#c48b9f"


# ==============================================================
#  SECTION 3 — FILTERS
#  Add new filters here. Each filter is a function that takes
#  a PIL Image and returns a modified PIL Image.
# ==============================================================

def filter_none(img):
    return img

def filter_grayscale(img):
    try:
        return img.convert("L").convert("RGB")
    except Exception as e:
        print(f"Grayscale filter error: {e}")
        return img

def filter_sepia(img):
    try:
        gray = img.convert("L")
        sepia = Image.merge("RGB", [
            gray.point(lambda p: min(255, int(p * 1.1))),
            gray.point(lambda p: min(255, int(p * 0.9))),
            gray.point(lambda p: min(255, int(p * 0.7))),
        ])
        return sepia
    except Exception as e:
        print(f"Sepia filter error: {e}")
        return img

def filter_blur(img):
    try:
        return img.filter(ImageFilter.GaussianBlur(radius=3))
    except Exception as e:
        print(f"Blur filter error: {e}")
        return img

def filter_sharpen(img):
    try:
        return img.filter(ImageFilter.SHARPEN)
    except Exception as e:
        print(f"Sharpen filter error: {e}")
        return img

def filter_vivid(img):
    try:
        img = ImageEnhance.Color(img).enhance(1.8)
        img = ImageEnhance.Contrast(img).enhance(1.3)
        img = ImageEnhance.Brightness(img).enhance(1.1)
        return img
    except Exception as e:
        print(f"Vivid filter error: {e}")
        return img

def filter_cool(img):
    try:
        r, g, b = img.split()
        r = r.point(lambda p: max(0, p - 20))
        b = b.point(lambda p: min(255, p + 30))
        return Image.merge("RGB", (r, g, b))
    except Exception as e:
        print(f"Cool filter error: {e}")
        return img

def filter_warm(img):
    try:
        r, g, b = img.split()
        r = r.point(lambda p: min(255, p + 30))
        b = b.point(lambda p: max(0, p - 20))
        return Image.merge("RGB", (r, g, b))
    except Exception as e:
        print(f"Warm filter error: {e}")
        return img

def filter_negative(img):
    try:
        return Image.eval(img, lambda p: 255 - p)
    except Exception as e:
        print(f"Negative filter error: {e}")
        return img

def filter_sketch(img):
    try:
        gray = img.convert("L")
        blurred = gray.filter(ImageFilter.GaussianBlur(radius=2))
        sketch = Image.fromarray(
            np.clip(
                np.array(gray, dtype=np.int16) - np.array(blurred, dtype=np.int16) + 128,
                0, 255
            ).astype(np.uint8)
        )
        return sketch.convert("RGB")
    except Exception as e:
        print(f"Sketch filter error: {e}")
        return img

FILTERS = {
    "Normal":     filter_none,
    "Grayscale":  filter_grayscale,
    "Sepia":      filter_sepia,
    "Vivid":      filter_vivid,
    "Cool":       filter_cool,
    "Warm":       filter_warm,
    "Blur":       filter_blur,
    "Sharpen":    filter_sharpen,
    "Negative":   filter_negative,
    "Sketch":     filter_sketch,
}


# ==============================================================
#  SECTION 4 — FRAME OVERLAYS (borders/frames drawn on photos)
# ==============================================================

def overlay_none(img):
    return img

def overlay_polaroid(img):
    try:
        w, h  = img.size
        border = 20
        bottom = 60
        frame  = Image.new("RGB", (w + border*2, h + border + bottom), (255, 255, 255))
        frame.paste(img, (border, border))
        return frame
    except Exception as e:
        print(f"Polaroid overlay error: {e}")
        return img

def overlay_vignette(img):
    try:
        w, h = img.size
        mask = Image.new("L", (w, h), 255)
        draw = ImageDraw.Draw(mask)
        steps = 60
        for i in range(steps):
            alpha = int(255 * (i / steps) ** 2)
            shrink = i * 4
            draw.ellipse(
                [shrink, shrink, w - shrink, h - shrink],
                fill=min(255, alpha + 140)
            )
        img_array = np.array(img).astype(np.float32)
        mask_array = np.array(mask).astype(np.float32) / 255.0
        for c in range(3):
            img_array[:, :, c] = img_array[:, :, c] * mask_array
        return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
    except Exception as e:
        print(f"Vignette overlay error: {e}")
        return img

def overlay_filmstrip(img):
    try:
        w, h = img.size
        strip_w = 30
        strip = Image.new("RGB", (w + strip_w * 2, h), (20, 20, 20))
        strip.paste(img, (strip_w, 0))
        draw = ImageDraw.Draw(strip)
        hole_w, hole_h = 12, 18
        for y in range(10, h, 35):
            draw.rectangle([7, y, 7 + hole_w, y + hole_h], fill=(240, 230, 180))
            draw.rectangle([w + strip_w + 11, y, w + strip_w + 11 + hole_w, y + hole_h], fill=(240, 230, 180))
        return strip
    except Exception as e:
        print(f"Filmstrip overlay error: {e}")
        return img

OVERLAYS = {
    "None":       overlay_none,
    "Polaroid":   overlay_polaroid,
    "Vignette":   overlay_vignette,
    "Film Strip": overlay_filmstrip,
}


# ==============================================================
#  SECTION 5 — CAMERA CORE
#  Handles opening, reading, and closing the camera.
# ==============================================================

class Camera:

    def __init__(self, camera_index=DEFAULT_CAMERA):
        self.index    = camera_index
        self.cap      = None
        self.is_open  = False
        self.lock     = threading.Lock()

    def open(self):
        try:
            self.cap = cv2.VideoCapture(self.index)
            if not self.cap.isOpened():
                raise RuntimeError(f"Camera {self.index} could not be opened.")
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  PREVIEW_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, PREVIEW_HEIGHT)
            self.is_open = True
        except Exception as e:
            self.is_open = False
            raise RuntimeError(f"Failed to open camera: {e}")

    def read_frame(self):
        if not self.is_open or self.cap is None:
            return None
        try:
            with self.lock:
                ret, frame = self.cap.read()
            if not ret or frame is None:
                return None
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return frame
        except Exception as e:
            print(f"Frame read error: {e}")
            return None

    def close(self):
        try:
            self.is_open = False
            if self.cap:
                self.cap.release()
                self.cap = None
        except Exception as e:
            print(f"Camera close error: {e}")

    def set_resolution(self, width, height):
        try:
            if self.cap:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        except Exception as e:
            print(f"Resolution set error: {e}")

    def list_available(self):
        available = []
        for i in range(5):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    available.append(i)
                    cap.release()
            except Exception:
                pass
        return available


# ==============================================================
#  SECTION 6 — VIDEO RECORDER
# ==============================================================

class VideoRecorder:

    def __init__(self):
        self.writer      = None
        self.is_recording = False
        self.start_time  = None
        self.filename    = None

    def start(self, filename, fps=20.0, size=(PREVIEW_WIDTH, PREVIEW_HEIGHT)):
        try:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.writer = cv2.VideoWriter(filename, fourcc, fps, size)
            if not self.writer.isOpened():
                raise RuntimeError("Could not open video writer.")
            self.is_recording = True
            self.start_time   = time.time()
            self.filename     = filename
        except Exception as e:
            self.is_recording = False
            raise RuntimeError(f"Failed to start recording: {e}")

    def write_frame(self, frame_rgb):
        if not self.is_recording or self.writer is None:
            return
        try:
            bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            self.writer.write(bgr)
        except Exception as e:
            print(f"Video write error: {e}")

    def stop(self):
        try:
            self.is_recording = False
            if self.writer:
                self.writer.release()
                self.writer = None
            elapsed = time.time() - self.start_time if self.start_time else 0
            self.start_time = None
            return elapsed
        except Exception as e:
            print(f"Stop recording error: {e}")
            return 0

    def elapsed(self):
        if self.is_recording and self.start_time:
            return time.time() - self.start_time
        return 0


# ==============================================================
#  SECTION 7 — PHOTO SAVING
# ==============================================================

def ensure_folder(folder):
    try:
        os.makedirs(folder, exist_ok=True)
    except PermissionError:
        raise PermissionError(f"No permission to create folder: {folder}")
    except Exception as e:
        raise RuntimeError(f"Could not create folder: {e}")


def save_photo(frame_rgb, active_filter, active_overlay, folder=SAVE_FOLDER):
    try:
        ensure_folder(folder)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename  = os.path.join(folder, f"photo_{timestamp}.jpg")

        img = Image.fromarray(frame_rgb)

        filter_fn  = FILTERS.get(active_filter,  filter_none)
        overlay_fn = OVERLAYS.get(active_overlay, overlay_none)

        img = filter_fn(img)
        img = overlay_fn(img)

        img.save(filename, "JPEG", quality=PHOTO_QUALITY)
        return filename

    except PermissionError as e:
        raise PermissionError(f"Cannot save photo — permission denied: {e}")
    except OSError as e:
        raise OSError(f"Disk error saving photo: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to save photo: {e}")


def add_timestamp_to_frame(frame_rgb, brightness, contrast):
    try:
        img  = Image.fromarray(frame_rgb)
        img  = ImageEnhance.Brightness(img).enhance(brightness)
        img  = ImageEnhance.Contrast(img).enhance(contrast)
        draw = ImageDraw.Draw(img)
        ts   = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        draw.text((10, 10), ts, fill=(255, 255, 255))
        return np.array(img)
    except Exception as e:
        print(f"Timestamp draw error: {e}")
        return frame_rgb


# ==============================================================
#  SECTION 8 — HISTOGRAM
# ==============================================================

def compute_histogram(frame_rgb):
    try:
        img   = Image.fromarray(frame_rgb).convert("L")
        arr   = np.array(img)
        hist, _ = np.histogram(arr, bins=64, range=(0, 256))
        hist  = hist / (hist.max() + 1)
        return hist.tolist()
    except Exception as e:
        print(f"Histogram error: {e}")
        return [0.0] * 64


# ==============================================================
#  SECTION 9 — MAIN APP
# ==============================================================

class DigitalCameraApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Digital Camera")
        self.root.configure(bg=BG)
        self.root.geometry("1100x780")
        self.root.minsize(900, 600)

        self.camera    = Camera()
        self.recorder  = VideoRecorder()
        self.running   = False

        self.active_filter   = tk.StringVar(value="Normal")
        self.active_overlay  = tk.StringVar(value="None")
        self.timer_seconds   = tk.IntVar(value=0)
        self.show_grid       = tk.BooleanVar(value=False)
        self.show_histogram  = tk.BooleanVar(value=True)
        self.show_timestamp  = tk.BooleanVar(value=True)
        self.mirror_mode     = tk.BooleanVar(value=True)
        self.brightness      = tk.DoubleVar(value=1.0)
        self.contrast        = tk.DoubleVar(value=1.0)
        self.zoom_level      = tk.DoubleVar(value=1.0)
        self.camera_index    = tk.IntVar(value=DEFAULT_CAMERA)
        self.mode            = tk.StringVar(value="Photo")

        self.photo_count     = 0
        self.last_photo      = None
        self.timer_running   = False
        self.current_frame   = None
        self.flash_alpha     = 0

        self._build_ui()
        self._start_camera()

    # ----------------------------------------------------------
    #  UI CONSTRUCTION
    # ----------------------------------------------------------

    def _build_ui(self):
        self._build_topbar()
        self._build_savepath_banner()

        content = tk.Frame(self.root, bg=BG)
        content.pack(fill="both", expand=True, padx=10, pady=(4, 4))
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        left = tk.Frame(content, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        right = tk.Frame(content, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")

        self._build_preview(left)
        self._build_controls(right)
        self._build_gallery_panel()
        self._build_statusbar()

    def _build_savepath_banner(self):
        """Prominent banner showing exactly where files are being saved."""
        self._banner_frame = tk.Frame(self.root, bg="#5a1a2e", pady=4)
        self._banner_frame.pack(fill="x")

        left = tk.Frame(self._banner_frame, bg="#5a1a2e")
        left.pack(side="left", padx=10)

        tk.Label(left, text="SAVING TO:", font=("Courier", 8, "bold"),
                 bg="#5a1a2e", fg=ACCENT).pack(side="left", padx=(0, 6))

        self._savepath_var = tk.StringVar(value=os.path.abspath(SAVE_FOLDER))
        self._savepath_lbl = tk.Label(
            left, textvariable=self._savepath_var,
            font=("Courier", 9, "bold"), bg="#5a1a2e", fg="#ffffff",
            cursor="hand2",
        )
        self._savepath_lbl.pack(side="left")
        self._savepath_lbl.bind("<Button-1>", lambda e: self._open_save_folder())

        tk.Label(left, text="  (click to open folder)",
                 font=("Courier", 7), bg="#5a1a2e", fg=TEXT_MUT).pack(side="left")

        right = tk.Frame(self._banner_frame, bg="#5a1a2e")
        right.pack(side="right", padx=10)

        tk.Label(right, text="VIDEOS:", font=("Courier", 8, "bold"),
                 bg="#5a1a2e", fg=ACCENT).pack(side="left", padx=(0, 6))

        self._videopath_lbl = tk.Label(
            right, text=os.path.abspath(VIDEO_FOLDER),
            font=("Courier", 8), bg="#5a1a2e", fg=TEXT_SEC,
            cursor="hand2",
        )
        self._videopath_lbl.pack(side="left")
        self._videopath_lbl.bind("<Button-1>", lambda e: self._open_video_folder())

    def _open_save_folder(self):
        folder = os.path.abspath(SAVE_FOLDER)
        os.makedirs(folder, exist_ok=True)
        try:
            import subprocess, platform
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showinfo("Save Folder", folder)

    def _open_video_folder(self):
        folder = os.path.abspath(VIDEO_FOLDER)
        os.makedirs(folder, exist_ok=True)
        try:
            import subprocess, platform
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showinfo("Video Folder", folder)

    def _build_gallery_panel(self):
        """Horizontal scrollable gallery strip showing recent photos."""
        gallery_outer = tk.Frame(self.root, bg=SURFACE, height=120)
        gallery_outer.pack(fill="x", padx=10, pady=(0, 4))
        gallery_outer.pack_propagate(False)

        header = tk.Frame(gallery_outer, bg=SURFACE)
        header.pack(fill="x", padx=8, pady=(4, 0))

        tk.Label(header, text="RECENT PHOTOS", font=("Courier", 8, "bold"),
                 bg=SURFACE, fg=ACCENT).pack(side="left")

        self._gallery_count_lbl = tk.Label(
            header, text="0 photos",
            font=("Courier", 7), bg=SURFACE, fg=TEXT_MUT)
        self._gallery_count_lbl.pack(side="left", padx=8)

        tk.Button(
            header, text="Refresh", font=("Courier", 7),
            bg=CARD, fg=TEXT_SEC, relief="flat", padx=6, pady=1,
            cursor="hand2", command=self._refresh_gallery,
        ).pack(side="left", padx=4)

        tk.Button(
            header, text="Open Folder", font=("Courier", 7),
            bg=CARD, fg=ACCENT, relief="flat", padx=6, pady=1,
            cursor="hand2", command=self._open_save_folder,
        ).pack(side="right", padx=4)

        scroll_container = tk.Frame(gallery_outer, bg=SURFACE)
        scroll_container.pack(fill="both", expand=True, padx=4, pady=4)

        self._gallery_canvas = tk.Canvas(
            scroll_container, bg=CARD, bd=0,
            highlightthickness=0, height=78,
        )
        h_scroll = tk.Scrollbar(scroll_container, orient="horizontal",
                                command=self._gallery_canvas.xview)
        self._gallery_canvas.configure(xscrollcommand=h_scroll.set)
        h_scroll.pack(side="bottom", fill="x")
        self._gallery_canvas.pack(side="top", fill="both", expand=True)

        self._gallery_inner = tk.Frame(self._gallery_canvas, bg=CARD)
        self._gallery_canvas_window = self._gallery_canvas.create_window(
            (0, 0), window=self._gallery_inner, anchor="nw")

        self._gallery_inner.bind("<Configure>", self._on_gallery_configure)
        self._gallery_thumbs = []

        self._no_photos_lbl = tk.Label(
            self._gallery_inner,
            text="No photos yet - press CAPTURE to take one!",
            font=("Courier", 8), bg=CARD, fg=TEXT_MUT,
        )
        self._no_photos_lbl.pack(padx=20, pady=20)

    def _on_gallery_configure(self, event):
        self._gallery_canvas.configure(
            scrollregion=self._gallery_canvas.bbox("all"))

    def _refresh_gallery(self):
        """Scan the photos folder and rebuild the gallery strip."""
        try:
            folder = SAVE_FOLDER
            if not os.path.isdir(folder):
                for w in self._gallery_inner.winfo_children():
                    w.destroy()
                tk.Label(self._gallery_inner,
                         text=f"Folder not found: {os.path.abspath(folder)}",
                         font=("Courier", 8), bg=CARD, fg=TEXT_MUT).pack(padx=10, pady=20)
                return
            files = sorted(
                [os.path.join(folder, f) for f in os.listdir(folder)
                 if f.lower().endswith((".jpg", ".jpeg", ".png"))],
                key=os.path.getmtime, reverse=True
            )[:20]

            for w in self._gallery_inner.winfo_children():
                w.destroy()
            self._gallery_thumbs.clear()

            if not files:
                tk.Label(self._gallery_inner,
                         text="No photos yet - press CAPTURE to take one!",
                         font=("Courier", 8), bg=CARD, fg=TEXT_MUT).pack(padx=20, pady=20)
                self._gallery_count_lbl.config(text="0 photos")
                return

            self._gallery_count_lbl.config(text=f"{len(files)} photos")

            for path in files:
                cell = tk.Frame(self._gallery_inner, bg=CARD, padx=2, pady=2)
                cell.pack(side="left", padx=3, pady=2)
                try:
                    img = Image.open(path)
                    img.thumbnail((90, 68), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self._gallery_thumbs.append(photo)

                    btn = tk.Label(cell, image=photo, bg=BORDER, cursor="hand2",
                                   relief="flat", bd=2)
                    btn.pack()
                    btn.bind("<Button-1>", lambda e, p=path: self._preview_gallery_photo(p))

                    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
                    tk.Label(cell, text=mtime.strftime("%H:%M:%S"),
                             font=("Courier", 6), bg=CARD, fg=TEXT_MUT).pack()
                except Exception as ex:
                    print(f"Gallery thumb error: {ex}")

        except Exception as e:
            print(f"Gallery refresh error: {e}")

    def _preview_gallery_photo(self, path):
        """Open a full-size preview popup."""
        try:
            win = tk.Toplevel(self.root)
            win.title(os.path.basename(path))
            win.configure(bg=BG)
            win.geometry("820x640")

            img = Image.open(path)
            img.thumbnail((780, 560), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            lbl = tk.Label(win, image=photo, bg=BG)
            lbl.image = photo
            lbl.pack(padx=10, pady=10)

            info = tk.Frame(win, bg=BG)
            info.pack(fill="x", padx=10, pady=(0, 10))
            tk.Label(info, text=f"Path: {path}", font=("Courier", 8),
                     bg=BG, fg=TEXT_SEC, wraplength=700).pack(side="left")
            tk.Button(info, text="Open Folder", font=("Courier", 8),
                      bg=CARD, fg=ACCENT, relief="flat", padx=8, pady=3,
                      cursor="hand2", command=self._open_save_folder).pack(side="right")
        except Exception as e:
            messagebox.showerror("Preview Error", str(e))

    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=SURFACE, height=50)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        left = tk.Frame(bar, bg=SURFACE)
        left.pack(side="left", padx=14, pady=8)

        tk.Label(left, text=" 📷 ", font=("Courier", 16),
                 bg=ACCENT_LO, fg=TEXT_PRI).pack(side="left", padx=(0, 10))

        info = tk.Frame(left, bg=SURFACE)
        info.pack(side="left")
        tk.Label(info, text="Digital Camera",
                 font=("Courier", 13, "bold"), bg=SURFACE, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(info, text="PC + Arduino Compatible",
                 font=("Courier", 8), bg=SURFACE, fg=TEXT_SEC).pack(anchor="w")

        right = tk.Frame(bar, bg=SURFACE)
        right.pack(side="right", padx=14)

        self.photo_counter_lbl = tk.Label(
            right, text="Photos: 0",
            font=("Courier", 9, "bold"), bg=SURFACE, fg=GREEN,
        )
        self.photo_counter_lbl.pack(side="left", padx=(0, 20))

        self.cam_status_lbl = tk.Label(
            right, text="● Connecting…",
            font=("Courier", 9), bg=SURFACE, fg=AMBER,
        )
        self.cam_status_lbl.pack(side="left")

    def _build_preview(self, parent):
        preview_frame = tk.Frame(parent, bg=CARD, relief="flat")
        preview_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            preview_frame,
            bg="#1a0a0f", bd=0, highlightthickness=0,
            cursor="crosshair",
        )
        self.canvas.pack(fill="both", expand=True, padx=2, pady=2)

        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # shutter button at the bottom
        btn_row = tk.Frame(parent, bg=BG)
        btn_row.pack(fill="x", pady=(8, 0))

        # mode selector
        mode_frame = tk.Frame(btn_row, bg=BG)
        mode_frame.pack(side="left")
        for m in ("Photo", "Burst", "Video"):
            rb = tk.Radiobutton(
                mode_frame, text=m, variable=self.mode, value=m,
                font=("Courier", 9), bg=BG, fg=TEXT_SEC,
                selectcolor=CARD, activebackground=BG, activeforeground=TEXT_PRI,
                cursor="hand2",
            )
            rb.pack(side="left", padx=4)

        # shutter
        self.shutter_btn = tk.Button(
            btn_row, text="⬤  CAPTURE",
            font=("Courier", 11, "bold"), bg="#e8829a", fg=TEXT_PRI,
            relief="flat", padx=20, pady=8, cursor="hand2",
            activebackground="#d4607a",
            command=self._on_shutter,
        )
        self.shutter_btn.pack(side="left", padx=12)

        # record / stop
        self.rec_btn = tk.Button(
            btn_row, text="⏺  REC",
            font=("Courier", 10, "bold"), bg=SURFACE, fg=RED,
            relief="solid", bd=1, padx=14, pady=8, cursor="hand2",
            command=self._toggle_recording,
        )
        self.rec_btn.pack(side="left", padx=4)

        self.rec_timer_lbl = tk.Label(
            btn_row, text="",
            font=("Courier", 10, "bold"), bg=BG, fg=RED,
        )
        self.rec_timer_lbl.pack(side="left", padx=6)

        # last photo thumbnail
        thumb_frame = tk.Frame(btn_row, bg=BG)
        thumb_frame.pack(side="right", padx=10)
        tk.Label(thumb_frame, text="Last photo:", font=("Courier", 7),
                 bg=BG, fg=TEXT_MUT).pack(anchor="e")
        self.thumb_canvas = tk.Canvas(
            thumb_frame, width=80, height=60,
            bg=CARD, bd=0, highlightthickness=1,
            highlightbackground=BORDER,
        )
        self.thumb_canvas.pack()

    def _build_controls(self, parent):
        scroll_frame = tk.Frame(parent, bg=BG)
        scroll_frame.pack(fill="both", expand=True)

        def section(title):
            tk.Label(scroll_frame, text=title.upper(),
                     font=("Courier", 7, "bold"), bg=BG, fg=TEXT_MUT).pack(
                anchor="w", padx=6, pady=(10, 2))

        def make_slider(label, variable, lo, hi, step=0.05):
            row = tk.Frame(scroll_frame, bg=BG)
            row.pack(fill="x", padx=6, pady=2)
            tk.Label(row, text=label, font=("Courier", 8),
                     bg=BG, fg=TEXT_SEC, width=12, anchor="w").pack(side="left")
            val_lbl = tk.Label(row, text=f"{variable.get():.2f}",
                               font=("Courier", 8), bg=BG, fg=ACCENT, width=5)
            val_lbl.pack(side="right")
            sl = ttk.Scale(
                row, from_=lo, to=hi, variable=variable, orient="horizontal",
                command=lambda v, lbl=val_lbl, var=variable: lbl.config(
                    text=f"{float(v):.2f}"
                ),
            )
            sl.pack(side="left", fill="x", expand=True, padx=4)

        # ── Camera settings ──
        section("Camera")

        cam_row = tk.Frame(scroll_frame, bg=BG)
        cam_row.pack(fill="x", padx=6, pady=2)
        tk.Label(cam_row, text="Camera index", font=("Courier", 8),
                 bg=BG, fg=TEXT_SEC).pack(side="left")
        for i in range(3):
            tk.Radiobutton(cam_row, text=str(i), variable=self.camera_index, value=i,
                           font=("Courier", 8), bg=BG, fg=TEXT_SEC, selectcolor=CARD,
                           activebackground=BG, cursor="hand2",
                           command=self._switch_camera).pack(side="left", padx=4)

        # ── Adjustments ──
        section("Adjustments")
        make_slider("Brightness", self.brightness,  0.2, 3.0)
        make_slider("Contrast",   self.contrast,    0.2, 3.0)
        make_slider("Zoom",       self.zoom_level,  1.0, 4.0)

        # ── Filters ──
        section("Filter")
        filter_grid = tk.Frame(scroll_frame, bg=BG)
        filter_grid.pack(fill="x", padx=6, pady=2)
        for i, name in enumerate(FILTERS.keys()):
            btn = tk.Radiobutton(
                filter_grid, text=name, variable=self.active_filter, value=name,
                font=("Courier", 8), bg=BG, fg=TEXT_SEC, selectcolor=CARD,
                activebackground=BG, cursor="hand2", indicatoron=True,
            )
            btn.grid(row=i // 2, column=i % 2, sticky="w", padx=4, pady=1)

        # ── Frame overlay ──
        section("Frame Overlay")
        for name in OVERLAYS.keys():
            tk.Radiobutton(
                scroll_frame, text=name, variable=self.active_overlay, value=name,
                font=("Courier", 8), bg=BG, fg=TEXT_SEC, selectcolor=CARD,
                activebackground=BG, cursor="hand2",
            ).pack(anchor="w", padx=10, pady=1)

        # ── Timer ──
        section("Self Timer")
        timer_row = tk.Frame(scroll_frame, bg=BG)
        timer_row.pack(fill="x", padx=6, pady=2)
        for secs in TIMER_OPTIONS:
            label = f"{secs}s" if secs > 0 else "Off"
            tk.Radiobutton(
                timer_row, text=label, variable=self.timer_seconds, value=secs,
                font=("Courier", 8), bg=BG, fg=TEXT_SEC, selectcolor=CARD,
                activebackground=BG, cursor="hand2",
            ).pack(side="left", padx=6)

        # ── Overlays / toggles ──
        section("Display")
        for (label, var) in [
            ("Show Grid",       self.show_grid),
            ("Show Histogram",  self.show_histogram),
            ("Show Timestamp",  self.show_timestamp),
            ("Mirror Mode",     self.mirror_mode),
        ]:
            tk.Checkbutton(
                scroll_frame, text=label, variable=var,
                font=("Courier", 8), bg=BG, fg=TEXT_SEC, selectcolor=CARD,
                activebackground=BG, cursor="hand2",
            ).pack(anchor="w", padx=10, pady=1)

        # ── Histogram display ──
        section("Histogram")
        self.hist_canvas = tk.Canvas(
            scroll_frame, width=200, height=60,
            bg=SURFACE, bd=0, highlightthickness=1,
            highlightbackground=BORDER,
        )
        self.hist_canvas.pack(padx=6, pady=4)

        # ── Save location ──
        section("Save Settings")
        save_row = tk.Frame(scroll_frame, bg=BG)
        save_row.pack(fill="x", padx=6, pady=2)
        tk.Button(
            save_row, text="📁  Change Photo Folder",
            font=("Courier", 8), bg=SURFACE, fg=TEXT_SEC,
            relief="solid", bd=1, padx=6, pady=2, cursor="hand2",
            command=self._change_save_folder,
        ).pack(side="left")

        self.save_folder_lbl = tk.Label(
            scroll_frame, text=f"→ {SAVE_FOLDER}",
            font=("Courier", 7), bg=BG, fg=TEXT_MUT,
        )
        self.save_folder_lbl.pack(anchor="w", padx=10, pady=(0, 4))

    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=SURFACE, height=24)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self.status_lbl = tk.Label(
            bar, text="Ready",
            font=("Courier", 8), bg=SURFACE, fg=TEXT_MUT,
        )
        self.status_lbl.pack(side="left", padx=10)

        self.res_lbl = tk.Label(
            bar, text="",
            font=("Courier", 8), bg=SURFACE, fg=TEXT_MUT,
        )
        self.res_lbl.pack(side="right", padx=10)

    # ----------------------------------------------------------
    #  CAMERA CONTROL
    # ----------------------------------------------------------

    def _start_camera(self):
        try:
            self.camera.open()
            self.running = True
            self.cam_status_lbl.config(text="● Camera Active", fg=GREEN)
            self._set_status("Camera ready")
            threading.Thread(target=self._preview_loop, daemon=True).start()
        except RuntimeError as e:
            self.cam_status_lbl.config(text="● No Camera", fg=RED)
            self._set_status(str(e))
            messagebox.showwarning(
                "Camera Not Found",
                f"{e}\n\nMake sure your webcam is connected.\n"
                "Try changing the camera index in the controls panel.",
            )

    def _switch_camera(self):
        try:
            self.running = False
            time.sleep(0.3)
            self.camera.close()
            self.camera = Camera(self.camera_index.get())
            self._start_camera()
        except Exception as e:
            self._set_status(f"Camera switch error: {e}")

    def _preview_loop(self):
        while self.running:
            try:
                frame = self.camera.read_frame()
                if frame is None:
                    time.sleep(0.05)
                    continue

                self.current_frame = frame.copy()

                # mirror
                if self.mirror_mode.get():
                    frame = np.fliplr(frame)

                # zoom
                zoom = self.zoom_level.get()
                if zoom > 1.0:
                    frame = self._apply_zoom(frame, zoom)

                # brightness / contrast
                frame = add_timestamp_to_frame(
                    frame,
                    self.brightness.get(),
                    self.contrast.get(),
                ) if self.show_timestamp.get() else self._apply_adjustments(frame)

                # live filter preview
                filter_fn = FILTERS.get(self.active_filter.get(), filter_none)
                pil_frame = Image.fromarray(frame)
                pil_frame = filter_fn(pil_frame)
                frame     = np.array(pil_frame)

                # write to video recorder
                if self.recorder.is_recording:
                    self.recorder.write_frame(frame)
                    elapsed = self.recorder.elapsed()
                    self.root.after(0, lambda e=elapsed: self.rec_timer_lbl.config(
                        text=f"{int(e//60):02d}:{int(e%60):02d}"
                    ))

                # update histogram
                if self.show_histogram.get():
                    hist = compute_histogram(frame)
                    self.root.after(0, lambda h=hist: self._draw_histogram(h))

                # draw to canvas
                self.root.after(0, lambda f=frame: self._update_canvas(f))

                # update resolution label
                h, w = frame.shape[:2]
                self.root.after(0, lambda ww=w, hh=h: self.res_lbl.config(
                    text=f"{ww} × {hh}"
                ))

                time.sleep(0.033)  # ~30fps

            except Exception as e:
                print(f"Preview loop error: {e}")
                time.sleep(0.1)

    def _apply_adjustments(self, frame):
        try:
            img = Image.fromarray(frame)
            img = ImageEnhance.Brightness(img).enhance(self.brightness.get())
            img = ImageEnhance.Contrast(img).enhance(self.contrast.get())
            return np.array(img)
        except Exception as e:
            print(f"Adjustment error: {e}")
            return frame

    def _apply_zoom(self, frame, zoom):
        try:
            h, w   = frame.shape[:2]
            new_h  = int(h / zoom)
            new_w  = int(w / zoom)
            y_off  = (h - new_h) // 2
            x_off  = (w - new_w) // 2
            cropped = frame[y_off:y_off+new_h, x_off:x_off+new_w]
            return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
        except Exception as e:
            print(f"Zoom error: {e}")
            return frame

    def _on_canvas_resize(self, event):
        pass

    def _update_canvas(self, frame):
        try:
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()

            if cw < 2 or ch < 2:
                return

            img = Image.fromarray(frame)
            img.thumbnail((cw, ch), Image.LANCZOS)

            # grid overlay
            if self.show_grid.get():
                draw = ImageDraw.Draw(img)
                iw, ih = img.size
                draw.line([(iw//3, 0), (iw//3, ih)], fill=(255,255,255,80), width=1)
                draw.line([(iw*2//3, 0), (iw*2//3, ih)], fill=(255,255,255,80), width=1)
                draw.line([(0, ih//3), (iw, ih//3)], fill=(255,255,255,80), width=1)
                draw.line([(0, ih*2//3), (iw, ih*2//3)], fill=(255,255,255,80), width=1)

            # flash effect
            if self.flash_alpha > 0:
                overlay = Image.new("RGB", img.size, (255, 255, 255))
                img = Image.blend(img, overlay, self.flash_alpha)
                self.flash_alpha = max(0, self.flash_alpha - 0.15)

            # recording indicator
            if self.recorder.is_recording:
                draw = ImageDraw.Draw(img)
                draw.ellipse([8, 8, 22, 22], fill=(220, 30, 30))
                draw.text((28, 10), "REC", fill=(255, 60, 60))

            photo = ImageTk.PhotoImage(img)
            self.canvas.delete("all")

            x = cw // 2
            y = ch // 2
            self.canvas.create_image(x, y, anchor="center", image=photo)
            self.canvas._photo = photo

        except Exception as e:
            print(f"Canvas update error: {e}")

    def _draw_histogram(self, hist):
        try:
            c  = self.hist_canvas
            cw = c.winfo_width()  or 200
            ch = c.winfo_height() or 60
            c.delete("all")

            bar_w = cw / len(hist)
            for i, val in enumerate(hist):
                x0 = i * bar_w
                x1 = x0 + bar_w - 0.5
                y1 = ch
                y0 = ch - val * (ch - 2)
                c.create_rectangle(x0, y0, x1, y1, fill=ACCENT, outline="")

        except Exception as e:
            print(f"Histogram draw error: {e}")

    # ----------------------------------------------------------
    #  CAPTURE
    # ----------------------------------------------------------

    def _on_shutter(self):
        if self.timer_running:
            return

        mode = self.mode.get()

        if mode == "Video":
            self._toggle_recording()
            return

        secs = self.timer_seconds.get()
        if secs > 0:
            self._countdown_then_capture(secs, mode)
        elif mode == "Burst":
            threading.Thread(target=self._burst_capture, daemon=True).start()
        else:
            self._capture_photo()

    def _countdown_then_capture(self, secs, mode):
        self.timer_running = True
        self.shutter_btn.config(state="disabled")

        def tick(remaining):
            if remaining <= 0:
                self.timer_running = False
                self.shutter_btn.config(state="normal")
                self._set_status("Ready")
                if mode == "Burst":
                    threading.Thread(target=self._burst_capture, daemon=True).start()
                else:
                    self._capture_photo()
            else:
                self._set_status(f"Timer: {remaining}s…")
                self.root.after(1000, lambda: tick(remaining - 1))

        tick(secs)

    def _capture_photo(self):
        try:
            if self.current_frame is None:
                self._set_status("No frame available")
                return

            frame = self.current_frame.copy()
            if self.mirror_mode.get():
                frame = np.fliplr(frame)
            if self.zoom_level.get() > 1.0:
                frame = self._apply_zoom(frame, self.zoom_level.get())

            filename = save_photo(
                frame,
                self.active_filter.get(),
                self.active_overlay.get(),
            )

            self.photo_count += 1
            self.last_photo   = filename
            self.flash_alpha  = 0.9

            self.photo_counter_lbl.config(text=f"Photos: {self.photo_count}")
            self._set_status(f"Saved: {os.path.basename(filename)}")
            self._update_thumbnail(frame)
            self._refresh_gallery()

        except (PermissionError, OSError, RuntimeError) as e:
            messagebox.showerror("Save Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")

    def _burst_capture(self):
        self.root.after(0, lambda: self.shutter_btn.config(state="disabled"))
        for i in range(BURST_COUNT):
            self.root.after(0, lambda n=i+1: self._set_status(f"Burst {n}/{BURST_COUNT}…"))
            self._capture_photo()
            time.sleep(BURST_DELAY)
        self.root.after(0, lambda: self.shutter_btn.config(state="normal"))
        self.root.after(0, lambda: self._set_status(f"Burst complete — {BURST_COUNT} photos"))

    def _update_thumbnail(self, frame_rgb):
        try:
            img = Image.fromarray(frame_rgb)
            img.thumbnail((80, 60), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.thumb_canvas.delete("all")
            self.thumb_canvas.create_image(40, 30, anchor="center", image=photo)
            self.thumb_canvas._photo = photo
        except Exception as e:
            print(f"Thumbnail error: {e}")

    # ----------------------------------------------------------
    #  VIDEO
    # ----------------------------------------------------------

    def _toggle_recording(self):
        if self.recorder.is_recording:
            elapsed = self.recorder.stop()
            self.rec_btn.config(text="⏺  REC", fg=RED, bg=SURFACE)
            self.rec_timer_lbl.config(text="")
            self._set_status(f"Video saved ({int(elapsed)}s): {self.recorder.filename}")
        else:
            try:
                ensure_folder(VIDEO_FOLDER)
                ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                fn  = os.path.join(VIDEO_FOLDER, f"video_{ts}.mp4")
                h   = int(self.camera.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                w   = int(self.camera.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                self.recorder.start(fn, fps=20.0, size=(w, h))
                self.rec_btn.config(text="⏹  STOP", fg=TEXT_PRI, bg=RED)
                self._set_status(f"Recording to {fn}…")
            except RuntimeError as e:
                messagebox.showerror("Recording Error", str(e))
            except Exception as e:
                messagebox.showerror("Error", f"Could not start recording: {e}")

    # ----------------------------------------------------------
    #  MISC
    # ----------------------------------------------------------

    def _change_save_folder(self):
        global SAVE_FOLDER
        folder = filedialog.askdirectory(title="Choose Photo Save Folder")
        if folder:
            SAVE_FOLDER = folder
            self.save_folder_lbl.config(text=f"→ {SAVE_FOLDER}")
            self._savepath_var.set(os.path.abspath(SAVE_FOLDER))
            self._set_status(f"Save folder: {SAVE_FOLDER}")
            self._refresh_gallery()

    def _set_status(self, text):
        try:
            self.status_lbl.config(text=text)
        except Exception:
            pass

    def on_close(self):
        try:
            self.running = False
            if self.recorder.is_recording:
                self.recorder.stop()
            self.camera.close()
        except Exception as e:
            print(f"Close error: {e}")
        finally:
            self.root.destroy()


# ==============================================================
#  SECTION 10 — ENTRY POINT
# ==============================================================

def main():
    try:
        root = tk.Tk()
    except tk.TclError as e:
        print(f"Cannot open GUI window: {e}")
        sys.exit(1)

    try:
        app = DigitalCameraApp(root)
        root.protocol("WM_DELETE_WINDOW", app.on_close)
        root.mainloop()
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
