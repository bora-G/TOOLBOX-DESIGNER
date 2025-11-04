import cv2
import numpy as np
import ezdxf
import tkinter as tk
from tkinter import filedialog, messagebox
from scipy.interpolate import splprep, splev
import os

# Varsayılan sabit ayarlar (Pro Mode kapalıysa kullanılır)
DEFAULT_USE_SPLINE = True
DEFAULT_EPSILON = 0.0025
DEFAULT_SCALE_FIX_X = 1.10
DEFAULT_SCALE_FIX_Y = 1.10

def browse_file():
    file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
    entry_file.delete(0, tk.END)
    entry_file.insert(0, file_path)

def start_processing():
    try:
        file_path = entry_file.get()
        ref_w = float(entry_width.get())
        ref_h = float(entry_height.get())
        filename = entry_output.get()

        if pro_mode.get():
            use_spline_mode = spline_check.get()
            epsilon_val = float(entry_epsilon.get())
            scale_fix_x = float(entry_scale_x.get())
            scale_fix_y = float(entry_scale_y.get())
        else:
            use_spline_mode = DEFAULT_USE_SPLINE
            epsilon_val = DEFAULT_EPSILON
            scale_fix_x = DEFAULT_SCALE_FIX_X
            scale_fix_y = DEFAULT_SCALE_FIX_Y

        process_image(file_path, ref_w, ref_h, filename, use_spline_mode, epsilon_val, scale_fix_x, scale_fix_y)
    except Exception as e:
        messagebox.showerror("Hata", str(e))

def process_image(img_path, ref_w_mm, ref_h_mm, output_filename, use_spline, epsilon, scale_x, scale_y):
    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        messagebox.showerror("Hata", "Görsel yüklenemedi!")
        return

    h, w = img.shape[:2]

    if img.shape[2] == 4:
        alpha = img[:, :, 3]
        _, mask = cv2.threshold(alpha, 0, 255, cv2.THRESH_BINARY)
    else:
        gray = cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY_INV)

    kernel = np.ones((3, 3), np.uint8)
    clean_mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    if len(contours) == 0:
        messagebox.showerror("Hata", "Kontur bulunamadı!")
        return

    ref_contour = None
    min_dist = float('inf')
    for cnt in contours:
        x, y, w_box, h_box = cv2.boundingRect(cnt)
        center_x = x + w_box // 2
        center_y = y + h_box // 2
        dist = ((center_x - w)**2 + (center_y - h)**2)**0.5
        if dist < min_dist:
            min_dist = dist
            ref_contour = cnt
            ref_rect = (w_box, h_box)

    if ref_contour is None:
        messagebox.showerror("Hata", "Referans kutu bulunamadı!")
        return

    ref_w_px, ref_h_px = ref_rect
    mm_per_px_x = ref_w_mm / ref_w_px
    mm_per_px_y = ref_h_mm / ref_h_px

    img_debug = img.copy()
    x, y, rw, rh = cv2.boundingRect(ref_contour)
    cv2.rectangle(img_debug, (x, y), (x + rw, y + rh), (0, 255, 0, 255), 2)
    cv2.imshow("Referans Kutusu", img_debug)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    os.makedirs("output", exist_ok=True)
    doc = ezdxf.new()
    msp = doc.modelspace()

    min_area_threshold = 500

    for cnt in contours:
        if np.array_equal(cnt, ref_contour):
            continue
        if cv2.contourArea(cnt) < min_area_threshold:
            continue

        if use_spline:
            pts = cnt[:, 0, :]
            if len(pts) < 5:
                continue
            x = pts[:, 0]
            y = h - pts[:, 1]
            try:
                tck, u = splprep([x, y], s=40.0, per=True)
                unew = np.linspace(0, 1.0, num=150)
                out = splev(unew, tck)
                scaled_points = [(x * mm_per_px_x * scale_x, y * mm_per_px_y * scale_y) for x, y in zip(out[0], out[1])]
            except:
                continue
        else:
            eps = epsilon * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, eps, True)
            scaled_points = [(pt[0][0] * mm_per_px_x * scale_x, (h - pt[0][1]) * mm_per_px_y * scale_y) for pt in approx]

        msp.add_lwpolyline(scaled_points, close=True)

    dxf_path = f"output/{output_filename}.dxf"
    doc.saveas(dxf_path)
    messagebox.showinfo("Başarılı", f"DXF dosyası oluşturuldu:\n{dxf_path}")

def show_info():
    messagebox.showinfo("Fotoğraf Çekim Kuralları", 
        "- Ölçek kare, siyah renkte ve sağ alt köşede olmak zorunda.\n"
        "- Ölçeğin etrafında bir şey olmamasına özen gösterin.\n"
        "- Fotoğrafın çekildiği arka plan tek renk, mümkünse yeşil olsun.\n"
        "- Fotoğrafı olabildiğince tepeden dik bir şekilde çekin.")

def toggle_pro_mode():
    state = "normal" if pro_mode.get() else "disabled"
    entry_epsilon.configure(state=state)
    entry_scale_x.configure(state=state)
    entry_scale_y.configure(state=state)
    spline_check_btn.configure(state=state)

# GUI
root = tk.Tk()
root.title("Toolbox DXF Oluşturucu (Pro Mod Destekli)")

tk.Label(root, text="📂 PNG Görsel:").grid(row=0, column=0, sticky="e")
entry_file = tk.Entry(root, width=50)
entry_file.grid(row=0, column=1)
tk.Button(root, text="Gözat", command=browse_file).grid(row=0, column=2)

tk.Label(root, text="🔹 Referans Genişliği (mm):").grid(row=1, column=0, sticky="e")
entry_width = tk.Entry(root)
entry_width.grid(row=1, column=1, sticky="w")

tk.Label(root, text="🔹 Referans Yüksekliği (mm):").grid(row=2, column=0, sticky="e")
entry_height = tk.Entry(root)
entry_height.grid(row=2, column=1, sticky="w")

tk.Label(root, text="📁 Çıktı Dosya Adı:").grid(row=3, column=0, sticky="e")
entry_output = tk.Entry(root)
entry_output.insert(0, "output_spline")
entry_output.grid(row=3, column=1, sticky="w")

# Pro Mode toggle
pro_mode = tk.BooleanVar()
tk.Checkbutton(root, text="🔧 Pro Mod", variable=pro_mode, command=toggle_pro_mode).grid(row=4, column=1, sticky="w")

# Pro Ayarlar
tk.Label(root, text="Spline ile çizilsin mi?").grid(row=5, column=0, sticky="e")
spline_check = tk.BooleanVar()
spline_check.set(DEFAULT_USE_SPLINE)
spline_check_btn = tk.Checkbutton(root, variable=spline_check)
spline_check_btn.grid(row=5, column=1, sticky="w")

tk.Label(root, text="Epsilon Değeri:").grid(row=6, column=0, sticky="e")
entry_epsilon = tk.Entry(root)
entry_epsilon.insert(0, str(DEFAULT_EPSILON))
entry_epsilon.grid(row=6, column=1, sticky="w")

tk.Label(root, text="SCALE_FIX_X:").grid(row=7, column=0, sticky="e")
entry_scale_x = tk.Entry(root)
entry_scale_x.insert(0, str(DEFAULT_SCALE_FIX_X))
entry_scale_x.grid(row=7, column=1, sticky="w")

tk.Label(root, text="SCALE_FIX_Y:").grid(row=8, column=0, sticky="e")
entry_scale_y = tk.Entry(root)
entry_scale_y.insert(0, str(DEFAULT_SCALE_FIX_Y))
entry_scale_y.grid(row=8, column=1, sticky="w")

# Başlangıçta Pro ayarlarını kilitle
toggle_pro_mode()

tk.Button(root, text="Kurallar", command=show_info).grid(row=9, column=0, pady=5)
tk.Button(root, text="DXF OLUŞTUR", command=start_processing, bg="#4CAF50", fg="white").grid(row=9, column=1, pady=10)

root.mainloop()
