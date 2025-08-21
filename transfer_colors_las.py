
import tkinter as tk
from tkinter import filedialog
import numpy as np
import laspy
from scipy.spatial import cKDTree
import os
from tqdm import tqdm

# === GUI Setup
root = tk.Tk()
root.withdraw()

print("📂 Kies DOEL puntenwolk zonder kleur (.las)")
target_path = filedialog.askopenfilename(title="Puntenwolk zonder kleur", filetypes=[("LAS bestanden", "*.las")])

print("📂 Kies GEKLEURDE puntenwolk (.las)")
source_path = filedialog.askopenfilename(title="Gekleurde LAS-bestand", filetypes=[("LAS bestanden", "*.las")])

print("💾 Kies waar je de output wilt opslaan")
output_path = filedialog.asksaveasfilename(title="Opslaan als", defaultextension=".las", filetypes=[("LAS bestanden", "*.las")])
if not output_path:
    print("❌ Geen uitvoerbestand geselecteerd. Afgebroken.")
    exit()

# === Laad target om aantal punten te weten
target_las = laspy.read(target_path)
tgt_xyz_full = np.vstack((target_las.x, target_las.y, target_las.z)).T
num_total = len(tgt_xyz_full)

# === Slider venster voor nauwkeurigheid (percentage punten)
slider_window = tk.Toplevel()
slider_window.title("Kies nauwkeurigheid / aantal punten")

label_var = tk.StringVar()
label = tk.Label(slider_window, textvariable=label_var)
label.pack(pady=10)

percent_var = tk.IntVar(value=100)
slider = tk.Scale(slider_window, from_=1, to=100, orient="horizontal", variable=percent_var)
slider.pack(padx=20)

def update_label(val):
    pct = int(val)
    num_sample = int((pct / 100) * num_total)
    estimated_seconds = int(num_sample / 100000 * 10)
    hrs, rem = divmod(estimated_seconds, 3600)
    mins, secs = divmod(rem, 60)
    label_var.set(f"{pct}% van {num_total} punten → {num_sample} punten\nGeschatte tijd: {hrs}h {mins}m {secs}s")

slider.config(command=update_label)
update_label(percent_var.get())

def confirm():
    slider_window.destroy()

btn = tk.Button(slider_window, text="Bevestig", command=confirm)
btn.pack(pady=10)
slider_window.wait_window()
sample_percent = percent_var.get()

# === Downsampling van target points
num_sample = int((sample_percent / 100) * num_total)
tgt_indices = np.random.choice(num_total, num_sample, replace=False)
tgt_xyz = tgt_xyz_full[tgt_indices]

# === Laad source punten
print("📥 Lees source (met kleur)...")
source_las = laspy.read(source_path)
src_xyz = np.vstack((source_las.x, source_las.y, source_las.z)).T
src_rgb = np.vstack((source_las.red, source_las.green, source_las.blue)).T // 256

# === Zoek dichtstbijzijnde kleuren
print("🔍 Bepaal kleuren via nearest neighbor...")
tree = cKDTree(src_xyz)
r_full = np.zeros(num_total, dtype=np.uint16)
g_full = np.zeros(num_total, dtype=np.uint16)
b_full = np.zeros(num_total, dtype=np.uint16)

for i, idx in enumerate(tqdm(tgt_indices, desc="🎨 Overdracht", unit="punt")):
    tgt_pt = tgt_xyz_full[idx]
    dist, nearest_idx = tree.query(tgt_pt)
    r, g, b = src_rgb[nearest_idx]
    r_full[idx] = r * 256
    g_full[idx] = g * 256
    b_full[idx] = b * 256

# === Schrijf nieuwe LAS
print(f"💾 Schrijf output naar {output_path}")
new_las = laspy.create(point_format=target_las.header.point_format, file_version=target_las.header.version)
new_las.x = target_las.x
new_las.y = target_las.y
new_las.z = target_las.z
new_las.red = r_full
new_las.green = g_full
new_las.blue = b_full

new_las.write(output_path)
print("✅ Klaar: kleuren overgezet naar gekozen outputbestand")
print("ℹ️  De gegenereerde .las file kan nu verder verwerkt worden in tools zoals CloudCompare.")
