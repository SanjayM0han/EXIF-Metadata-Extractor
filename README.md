# 📸 EXIF Metadata Extractor & Privacy Analyzer

A modern desktop application to **extract, analyze, export, and sanitize EXIF metadata from images**, with a strong focus on **privacy risk assessment**.  
Built using **Python**, **CustomTkinter**, and **Pillow**, this tool is suitable for cybersecurity learning, digital forensics, and privacy awareness demonstrations.

---

## ✨ Features

### 🔍 Metadata Extraction
- Extracts common EXIF fields:
  - Camera Make & Model
  - Capture Date & Time
  - Exposure, ISO, Focal Length
  - Software information
- Displays raw metadata in a readable format

### 📍 GPS Analysis
- Detects embedded GPS coordinates
- Converts GPS data to latitude & longitude
- One-click **Open in Google Maps** (if GPS exists)

### 🔐 Privacy Risk Analyzer
- Calculates a **Privacy Risk Score (0–10)** based on:
  - GPS location presence
  - Device identification (Make & Model)
  - Timestamp correlation
  - Editing software traces
  - Sensitive identifiers (serial numbers, ownership tags)
- Displays:
  - Risk level: **LOW / MEDIUM / HIGH**
  - Clear visual indicators
- Automatically resets risk when **no EXIF metadata is present**

### 🧹 Metadata Removal (Privacy Cleaner)
- Removes **all EXIF metadata** from an image
- Saves a cleaned copy (original remains untouched)
- Includes **Before vs After metadata comparison**

### 📂 Bulk Upload (Folder Processing)
- Select a folder containing images
- Processes all supported images automatically
- Extracts **full metadata per image**
- Generates:
  - One consolidated **JSON report**
  - Optional **CSV export** for spreadsheets

### 📤 Export Options
- Export current image metadata as:
  - JSON
  - CSV
  - PDF report

### 🔒 Read-Only / Safe Mode
- Prevents metadata modification or removal
- Ideal for forensic or demonstration use

---

## 🖼️ Supported Image Formats
- `.jpg`
- `.jpeg`
- `.png` *(limited EXIF support)*
- `.bmp` *(limited EXIF support)*
- `.heic` *(if supported by system codecs)*

> Note: EXIF metadata is natively supported mainly by **JPEG / TIFF** formats.

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **CustomTkinter** – modern GUI
- **Pillow (PIL)** – image handling
- **piexif** – EXIF removal
- **ReportLab** – PDF generation

---

## 📦 Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/sanjaym0han/EXIF-Metadata-Extractor.git
cd EXIF-Metadata-Extractor
```
## 🛠️ Setup & Installation

### 2️⃣ Create Virtual Environment
```bash
python -m venv venv
```
## Activate the Virtual Environment

### Windows

```bash
venv\Scripts\activate
```
### Linux / macOS
```bash
source venv/bin/activate
```

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```
## ▶️ Run the Application

```bash
python src/gui.py
```
