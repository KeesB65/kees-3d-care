
# LAS Color Transfer Tool (GUI)

This Python tool transfers RGB color from a source `.las` file (with color) to a target `.las` file (without color), based on nearest-neighbor matching. It uses a graphical interface for file selection and progress control.

## 🎯 Use Case

You may use this tool to:
- Transfer RGB color from a detailed scan to a filtered or downsampled point cloud
- Match color to a cleaned point cloud without repeating image projection
- Reduce processing time with a sampling slider (1–100%)

---

## 🖥️ Windows Installation Instructions

### 1. ✅ Install Python 3.10.9 (recommended)

> ⚠️ Do **not** use Python 3.11 or 3.12 — some libraries used in this tool may fail to install or function.  
> 🔗 Download Python 3.10.9 (64-bit):  
> [https://www.python.org/ftp/python/3.10.9/python-3.10.9-amd64.exe](https://www.python.org/ftp/python/3.10.9/python-3.10.9-amd64.exe)

During setup:
- ✅ Check the box: “Add Python to PATH”
- ✅ Choose: Customize installation → Select `pip` and `tkinter` features

---

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

### 3. Run the Tool

```powershell
python transfer_colors_las.py
```

You will be prompted to:
1. Select the **target LAS file** (without color)
2. Select the **source LAS file** (with RGB color)
3. Choose where to **save** the output `.las` file
4. Use a **slider** to select how many points to color (default: 100%)

---

### 💾 Output

The resulting `.las` file contains original XYZ from the target and RGB colors from the source.

> ℹ️ The result can now be further processed in tools like **CloudCompare**.
