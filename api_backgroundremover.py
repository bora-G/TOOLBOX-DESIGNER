import cv2
import numpy as np
import ezdxf
import tkinter as tk
from tkinter import filedialog, messagebox
from scipy.interpolate import splprep, splev
import os
import requests

# 🔑 remove.bg API entegrasyonu
def remove_bg(input_path):
    API_KEY = "your-api-key"  # ← kendi API key'ini buraya koy
    output_path = "temp_removed.png"

    with open(input_path, "rb") as img_file:
        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": img_file},
            data={"size": "auto"},
            headers={"X-Api-Key": API_KEY},
        )

    if response.status_code == requests.codes.ok:
        with open(output_path, "wb") as out:
            out.write(response.content)
        return output_path
    else:
        messagebox.showerror("remove.bg Hatası", f"Hata kodu: {response.status_code}\n{response.text}")
        return None

def browse_file():
    file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
    entry_file.delete(0, tk.END)
    entry_file.insert(0, file_path)

def browse_output_folder():
    folder_path = filedialog.askdirectory()
    entry_output_dir.delete(0, tk.END)
    entry_output_dir.insert(0, folder_path)

def start_processing():
    try:
        file_path = entry_file.get()
        ref_w = float(entry_width.get())
        ref_h = float(entry_height.get())
        filename = entry_output.get()
        output_dir = entry_output_dir.get()

        if not output_dir:
            messagebox.showerror("Hata", "Lütfen bir çıktı klasörü seçin!")
            return

        removed_path = remove_bg(file_path)
        if not removed_path:
            return

        process_image(removed_path, ref_w, ref_h, filename, output_dir)

        if os.path.exists(removed_path):
            os.remove(removed_path)

    except Exception as e:
        messagebox.showerror("Hata", str(e))

def process_image(img_path, ref_w_mm, ref_h_mm, output_filename, output_dir):
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

    ref_contour = None
    ref_rect = None
    max_area = 0
    for cnt in contours:
        x, y, w_box, h_box = cv2.boundingRect(cnt)
        if x > 0.6 * w and y > 0.6 * h:
            area = w_box * h_box
            if area > max_area:
                max_area = area
                ref_contour = cnt
                ref_rect = (w_box, h_box)

    if ref_contour is None:
        messagebox.showerror("Hata", "Referans kare bulunamadı!")
        return

    ref_w_px, ref_h_px = ref_rect
    mm_per_px_x = ref_w_mm / ref_w_px
    mm_per_px_y = ref_h_mm / ref_h_px

    os.makedirs(output_dir, exist_ok=True)
    doc = ezdxf.new()
    msp = doc.modelspace()

    min_area_threshold = 500

    for cnt in contours:
        if np.array_equal(cnt, ref_contour):
            continue
        if cv2.contourArea(cnt) < min_area_threshold:
            continue

        pts = cnt[:, 0, :]
        if len(pts) < 5:
            continue

        x = pts[:, 0]
        y = h - pts[:, 1]

        try:
            tck, u = splprep([x, y], s=40.0, per=True)
            unew = np.linspace(0, 1.0, num=150)
            out = splev(unew, tck)
        except:
            continue

        scaled_points = [(x * mm_per_px_x, y * mm_per_px_y) for x, y in zip(out[0], out[1])]
        msp.add_lwpolyline(scaled_points, close=True)

    dxf_path = os.path.join(output_dir, f"{output_filename}.dxf")
    doc.saveas(dxf_path)
    messagebox.showinfo("Başarılı", f"DXF dosyası oluşturuldu:\n{dxf_path}")

# 🎨 GUI

def show_info():
    messagebox.showinfo("Fotoğraf Çekim Kuralları", 
        "- Ölçek kare, siyah renkte ve sağ alt köşede olmak zorunda.\n"
        "- Ölçeğin etrafında bir şey olmamasına özen gösterin.\n"
        "- Fotoğrafın çekildiği arka plan tek renk, mümkünse yeşil olsun.\n"
        "- Fotoğrafı olabildiğince tepeden dik bir şekilde çekin.")

root = tk.Tk()
root.title("Toolbox DXF Oluşturucu (remove.bg + spline destekli)")

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

tk.Label(root, text="📂 Çıktı Klasörü:").grid(row=4, column=0, sticky="e")
entry_output_dir = tk.Entry(root, width=50)
entry_output_dir.grid(row=4, column=1)
tk.Button(root, text="Seç", command=browse_output_folder).grid(row=4, column=2)

tk.Button(root, text="ℹ Kurallar", command=show_info).grid(row=5, column=0, pady=5)

tk.Button(
    root,
    text="🚀 DXF OLUŞTUR",
    command=start_processing,
    bg="white",
    fg="black",
    font=("Arial", 12, "bold"),
    padx=20,
    pady=10,
    relief="groove",
    bd=2,
).grid(row=5, column=1, pady=(20, 10))

root.mainloop()