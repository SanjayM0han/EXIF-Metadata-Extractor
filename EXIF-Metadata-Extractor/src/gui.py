import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import webbrowser
import json
import os
import csv
import piexif
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from extractor import extract_exif
from gps_utils import extract_gps, get_lat_long


class ModernEXIF_GUI(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        super().__init__()
        self.title("EXIF Metadata Extractor")
        self.geometry("1150x800")

        # ---- STATE VARIABLES (ORDER MATTERS) ----
        self.last_metadata = {}
        self.original_metadata = {}
        self.cleaned_metadata = {}
        self.current_coords = None
        self.current_image_path = None
        self.safe_mode = ctk.BooleanVar(value=True)

        self.build_ui()
        self.mainloop()


    # -------------------------------------------------
    # BUILD UI
    # -------------------------------------------------
    def build_ui(self):
        ctk.CTkLabel(
            self,
            text="📸 EXIF Metadata Extractor",
            font=("Segoe UI", 26, "bold")
        ).pack(pady=20)

        main = ctk.CTkFrame(self, corner_radius=15)
        main.pack(padx=20, pady=10, fill="both", expand=True)

        # LEFT PANEL
        left = ctk.CTkFrame(main, width=350, corner_radius=15)
        left.pack(side="left", fill="y", padx=15, pady=15)
        ctk.CTkCheckBox(
            left,
            text="Read-Only / Safe Mode",
            variable=self.safe_mode
        ).pack(pady=6)

        ctk.CTkLabel(left, text="Image Preview", font=("Segoe UI", 18, "bold")).pack(pady=10)

        self.preview_area = ctk.CTkLabel(
            left, text="No Image Selected",
            width=300, height=300,
            fg_color=("gray20", "gray80"),
            corner_radius=12
        )
        self.preview_area.pack(pady=10)
        
        ctk.CTkButton(left, text="Select Image", command=self.select_image, width=200).pack(pady=8)
        ctk.CTkButton(left, text="Bulk Upload Folder", command=self.open_bulk_upload, width=200).pack(pady=8)
        ctk.CTkButton(left, text="Remove Metadata (Privacy Cleaner)", command=self.remove_metadata, width=200).pack(pady=8)
        ctk.CTkButton(left, text="Export CSV", command=self.export_csv).pack(pady=6)

        self.privacy_label = ctk.CTkLabel(left, text="Privacy Risk: Unknown", font=("Segoe UI", 14, "bold"))
        self.privacy_label.pack(pady=10)

        self.map_btn = ctk.CTkButton(left, text="Open in Google Maps", command=self.open_google_maps, state="disabled")
        self.map_btn.pack(pady=6)

        self.export_btn = ctk.CTkButton(left, text="Export JSON", command=self.export_json, state="disabled")
        self.export_btn.pack(pady=6)

        self.pdf_btn = ctk.CTkButton(left, text="Export PDF", command=self.export_pdf, state="disabled")
        self.pdf_btn.pack(pady=6)

        # RIGHT PANEL
        right = ctk.CTkFrame(main, corner_radius=15)
        right.pack(side="right", fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(right, text="Extracted Metadata", font=("Segoe UI", 20, "bold")).pack(pady=10)

        self.metadata_box = ctk.CTkTextbox(right, width=650, height=540, font=("Consolas", 14))
        self.metadata_box.pack(padx=10, pady=10)

    # -------------------------------------------------
    # IMAGE HANDLING
    # -------------------------------------------------
    def load_image(self, path):
        self.current_image_path = path
        try:
            img = Image.open(path)
            img.thumbnail((300, 300))

            ctk_img = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=(300, 300)
            )

            self.preview_area.configure(image=ctk_img, text="")
            self.preview_area.image = ctk_img

            # 🔥 THIS WAS THE MISSING LINK
            self.extract_metadata(path)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image:\n{e}")

    def select_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.jpg;*.jpeg;*.png;*.bmp;*.heic")]
        )
        if path:
            self.load_image(path)
    def handle_drop(self, event):
        # Windows sends paths wrapped in {}
        path = event.data.strip("{}")

        # Handle only files (not folders)
        if os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if ext in (".jpg", ".jpeg", ".png", ".bmp", ".heic"):
                self.load_image(path)
            else:
                messagebox.showwarning(
                    "Unsupported File",
                    "Please drop a valid image file."
                )

    def open_bulk_upload(self):
        BulkUploadWindow(self)



    def show_metadata_comparison(self):
        win = ctk.CTkToplevel(self)
        win.title("Metadata Comparison – Before vs After")
        win.geometry("900x500")

        box = ctk.CTkTextbox(win, font=("Consolas", 12))
        box.pack(expand=True, fill="both", padx=15, pady=15)

        box.insert("end", "=== BEFORE (Original Metadata) ===\n\n")
        for k, v in self.original_metadata.items():
            box.insert("end", f"{k}: {v}\n")

        box.insert("end", "\n\n=== AFTER (Cleaned Metadata) ===\n\n")
        if not self.cleaned_metadata:
            box.insert("end", "All metadata removed successfully.")
        else:
            for k, v in self.cleaned_metadata.items():
                box.insert("end", f"{k}: {v}\n")


    def export_csv(self):
        if not self.last_metadata:
            messagebox.showwarning("No Data", "No metadata to export")
            return

        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Field", "Value"])
            for k, v in self.last_metadata.items():
                writer.writerow([k, v])

        messagebox.showinfo("Success", "CSV exported successfully")


    # -------------------------------------------------
    # METADATA EXTRACTION
    # -------------------------------------------------
    def extract_metadata(self, path):
        exif = extract_exif(path)

        # ---------- HARD RESET (prevents stale UI/state) ----------
        self.metadata_box.delete("1.0", "end")
        self.last_metadata.clear()
        self.current_coords = None
        self.map_btn.configure(state="disabled")

        # ---------- NO EXIF CASE ----------
        if not exif or not isinstance(exif, dict) or len(exif) == 0:
            self.metadata_box.insert(
                "end",
                "No EXIF metadata found.\n"
            )

            # 🔴 CRITICAL: force privacy risk reset
            self.calculate_privacy_risk(None)

            self.export_btn.configure(state="disabled")
            self.pdf_btn.configure(state="disabled")
            return   # ⛔ STOP — do NOT continue


        # ---------- DISPLAY IMPORTANT METADATA ----------
        keys = [
            "Make", "Model", "DateTimeOriginal",
            "ExposureTime", "FNumber",
            "ISOSpeedRatings", "FocalLength",
            "Software"
        ]

        self.metadata_box.insert("end", "IMPORTANT METADATA\n\n")

        for k in keys:
            if k in exif:
                v = exif[k]

                if isinstance(v, bytes):
                    v = v.decode(errors="ignore")
                elif isinstance(v, tuple) and len(v) == 2 and v[1] != 0:
                    v = v[0] / v[1]

                self.last_metadata[k] = v
                self.metadata_box.insert("end", f"{k:20}: {v}\n")


        # ---------- GPS METADATA ----------
        self.metadata_box.insert("end", "\nGPS METADATA\n\n")

        gps = extract_gps(exif)
        if gps:
            lat, lon = get_lat_long(gps)
            if lat is not None and lon is not None:
                self.current_coords = (lat, lon)
                self.last_metadata["GPSLatitude"] = lat
                self.last_metadata["GPSLongitude"] = lon
                self.metadata_box.insert(
                    "end",
                    f"Latitude : {lat}\nLongitude: {lon}\n"
                )
                self.map_btn.configure(state="normal")
            else:
                self.metadata_box.insert("end", "GPS metadata corrupted\n")
        else:
            self.metadata_box.insert("end", "No GPS metadata\n")


        # ---------- PRIVACY RISK (ONLY NOW) ----------
        self.calculate_privacy_risk(exif)

        # ---------- EXPORTS ----------
        self.export_btn.configure(state="normal")
        self.pdf_btn.configure(state="normal")


        # -------------------------------------------------
        # PRIVACY RISK SCORING
        # -------------------------------------------------
    def calculate_privacy_risk(self, exif):
        """
        Calculates privacy risk ONLY if valid EXIF metadata exists.
        Resets state completely if EXIF is empty or missing.
        """

        # ---------- HARD RESET (prevents state leakage) ----------
        self.current_coords = None

        # EXIF missing or empty → ZERO risk
        if not exif or not isinstance(exif, dict) or len(exif) == 0:
            self.privacy_label.configure(
                text="🟢 Privacy Risk: 0/10 (LOW)"
            )

            self.map_btn.configure(state="disabled")

            # Store explicit zero-risk state
            self.last_metadata["PrivacyRiskScore"] = 0
            self.last_metadata["PrivacyRiskLevel"] = "LOW"
            self.last_metadata["PrivacyRiskReasons"] = [
                "No EXIF metadata present"
            ]

            return  # ⛔ STOP HERE — do NOT continue


        # ---------- ACTUAL RISK ANALYSIS ----------
        score = 0
        reasons = []

        # --- GPS (highest risk) ---
        gps = extract_gps(exif)
        lat, lon = get_lat_long(gps) if gps else (None, None)
        if lat is not None and lon is not None:
            score += 6
            reasons.append("Exact GPS location present")
            self.current_coords = (lat, lon)
            self.map_btn.configure(state="normal")
        else:
            self.map_btn.configure(state="disabled")

        # --- Device identity ---
        if "Make" in exif or "Model" in exif:
            score += 2
            reasons.append("Camera make/model present")

        # --- Time correlation ---
        if "DateTimeOriginal" in exif:
            score += 1
            reasons.append("Original capture time present")

        # --- Software fingerprint ---
        if "Software" in exif:
            score += 1
            reasons.append("Editing software identified")

        # --- Sensitive identifiers ---
        sensitive_tags = {
            "Artist",
            "OwnerName",
            "Copyright",
            "BodySerialNumber",
            "LensSerialNumber"
        }

        for tag in sensitive_tags:
            if tag in exif:
                score += 2
                reasons.append(f"Sensitive identifier: {tag}")

        # --- Clamp score ---
        score = min(score, 10)

        # --- Risk level ---
        if score >= 7:
            level = "HIGH"
            emoji = "🔴"
        elif score >= 4:
            level = "MEDIUM"
            emoji = "🟡"
        else:
            level = "LOW"
            emoji = "🟢"

        # ---------- FINAL UI + STATE UPDATE ----------
        self.privacy_label.configure(
            text=f"{emoji} Privacy Risk: {score}/10 ({level})"
        )

        self.last_metadata["PrivacyRiskScore"] = score
        self.last_metadata["PrivacyRiskLevel"] = level
        self.last_metadata["PrivacyRiskReasons"] = reasons


    # -------------------------------------------------
    # BULK UPLOAD FOLDER (FIXED VERSION)
    # -------------------------------------------------
    def bulk_upload_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        report = {}
        for file in os.listdir(folder):
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".heic")):
                path = os.path.join(folder, file)
                exif = extract_exif(path)
                if exif:
                    gps = extract_gps(exif)
                    lat, lon = get_lat_long(gps) if gps else (None, None)
                    report[file] = {
                        "Make": exif.get("Make"),
                        "Model": exif.get("Model"),
                        "GPSLatitude": lat,
                        "GPSLongitude": lon
                    }

        save = filedialog.asksaveasfilename(defaultextension=".json")
        if save:
            with open(save, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=4)
            messagebox.showinfo("Bulk Upload", "Folder processed successfully!")

    # -------------------------------------------------
    # METADATA REMOVAL (PRIVACY CLEANER)
    # -------------------------------------------------
    def remove_metadata(self):
        if self.safe_mode.get():
            messagebox.showwarning(
                "Safe Mode Enabled",
                "Disable Safe Mode to remove metadata."
            )
            return

        if not self.current_image_path:
            messagebox.showwarning("No Image", "Select an image first")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            title="Save Clean Image"
        )
        if not save_path:
            return

        try:
            # Save original snapshot BEFORE cleaning
            self.original_metadata = self.last_metadata.copy()

            piexif.remove(self.current_image_path, save_path)

            # Read cleaned metadata
            cleaned_exif = extract_exif(save_path)
            self.cleaned_metadata = cleaned_exif if cleaned_exif else {}

            messagebox.showinfo(
                "Metadata Removed",
                "Metadata removed successfully!\nOpening comparison view."
            )

            self.show_metadata_comparison()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # -------------------------------------------------
    # EXPORTS
    # -------------------------------------------------
    def open_google_maps(self):
        if self.current_coords:
            lat, lon = self.current_coords
            webbrowser.open(f"https://www.google.com/maps?q={lat},{lon}")

    def export_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.last_metadata, f, indent=4)
            messagebox.showinfo("Success", "JSON exported")

    def export_pdf(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf")
        if not path:
            return
        if self.safe_mode.get():
            messagebox.showwarning(
                "Safe Mode",
                "Exporting modified data is disabled in Safe Mode."
            )
            return

        c = canvas.Canvas(path, pagesize=A4)
        text = c.beginText(40, 800)
        text.setFont("Helvetica", 10)
        text.textLine("EXIF METADATA REPORT\n")

        for k, v in self.last_metadata.items():
            text.textLine(f"{k}: {v}")

        c.drawText(text)
        c.showPage()
        c.save()
        messagebox.showinfo("Success", "PDF exported")

class BulkUploadWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Bulk Upload – Folder Processing")
        self.geometry("800x550")
        self.parent = parent
        self.resizable(False, False)

        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(
            self,
            text="📂 Bulk Upload Folder",
            font=("Segoe UI", 22, "bold")
        ).pack(pady=15)

        ctk.CTkButton(
            self,
            text="Select Folder",
            command=self.process_folder,
            width=220,
            height=40
        ).pack(pady=10)

        self.status_box = ctk.CTkTextbox(
            self,
            width=720,
            height=360,
            font=("Consolas", 13)
        )
        self.status_box.pack(padx=20, pady=15)

    def process_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        self.status_box.delete("1.0", "end")
        self.status_box.insert("end", f"📁 Selected Folder:\n{folder}\n\n")

        bulk_report = {}
        image_count = 0

        for file in sorted(os.listdir(folder)):
            if not file.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".heic")):
                continue

            image_count += 1
            path = os.path.join(folder, file)
            self.status_box.insert("end", f"🔍 Processing: {file}\n")
            self.status_box.see("end")
            self.update_idletasks()

            exif = extract_exif(path)

            if not exif:
                bulk_report[file] = {"Error": "No EXIF metadata found"}
                continue

            image_data = {}

            # ---- FULL EXIF ----
            for key, val in exif.items():
                if isinstance(val, bytes):
                    val = val.decode(errors="ignore")
                if isinstance(val, tuple) and len(val) == 2 and val[1] != 0:
                    val = val[0] / val[1]
                image_data[key] = val

            # ---- GPS ----
            gps = extract_gps(exif)
            lat, lon = get_lat_long(gps) if gps else (None, None)
            image_data["GPSLatitude"] = lat
            image_data["GPSLongitude"] = lon

            # ---- PRIVACY RISK SCORE ----
            score = 0
            if gps:
                score += 5
            if "Model" in exif:
                score += 2
            if "DateTimeOriginal" in exif:
                score += 2
            if "Software" in exif:
                score += 1

            level = "LOW"
            if score >= 7:
                level = "HIGH"
            elif score >= 4:
                level = "MEDIUM"

            image_data["PrivacyRiskScore"] = score
            image_data["PrivacyRiskLevel"] = level

            bulk_report[file] = image_data

        self.status_box.insert(
            "end",
            f"\n✅ Total Images Processed: {image_count}\n"
        )

        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            title="Save Consolidated Bulk Metadata"
        )

        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(bulk_report, f, indent=4)

            messagebox.showinfo(
                "Bulk Upload Complete",
                f"Processed {image_count} images\n\nConsolidated JSON exported successfully!"
            )
            csv_path = save_path.replace(".json", ".csv")

            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                headers_written = False

                for img, data in bulk_report.items():
                    if not headers_written:
                        writer.writerow(["Image"] + list(data.keys()))
                        headers_written = True
                    writer.writerow([img] + list(data.values()))

if __name__ == "__main__":
    ModernEXIF_GUI()
