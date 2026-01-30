from __future__ import annotations
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .utils import ensure_dir
from .core import generate_reports


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Excel Data Profiler")
        self.geometry("820x520")

        self.project_root = os.path.dirname(os.path.dirname(__file__))
        self.output_dir = os.path.join(self.project_root, "output")
        self.template_dir = os.path.join(self.project_root, "templates")

        ensure_dir(self.output_dir)

        # State
        self.excel_path_var = tk.StringVar(value="")
        self.sample_threshold_var = tk.IntVar(value=200_000)
        self.sample_n_each_var = tk.IntVar(value=5_000)

        # Gelecek özellikler için checkbox (şimdilik sadece UI'de duracak)
        self.future_header_detect_var = tk.BooleanVar(value=False)
        self.future_business_summary_var = tk.BooleanVar(value=False)

        # Tema durumu
        self.is_dark_mode = False

        # Style nesnesi
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.out_xlsx = None
        self.out_html = None

        self._build_ui()

    def _build_ui(self):
        # Üst alan
        top = ttk.Frame(self, padding=12)
        top.pack(fill="x")

        ttk.Label(top, text="Excel dosyasi:").grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(top, textvariable=self.excel_path_var, width=72)
        entry.grid(row=0, column=1, padx=8)

        ttk.Button(top, text="Sec...", command=self.pick_file).grid(row=0, column=2)

        # Tema degistirme butonu (top olustuktan sonra!)
        ttk.Button(top, text="Dark / Light", command=self.toggle_theme).grid(row=0, column=3, padx=8)

        # Ayarlar
        settings = ttk.LabelFrame(self, text="Ayarlar", padding=12)
        settings.pack(fill="x", padx=12, pady=(0, 8))

        ttk.Label(settings, text="Ornekleme esigi (satir >):").grid(row=0, column=0, sticky="w")
        ttk.Entry(settings, textvariable=self.sample_threshold_var, width=12).grid(row=0, column=1, padx=8, sticky="w")

        ttk.Label(settings, text="Ilk/Rastgele/Son satir sayisi:").grid(row=0, column=2, sticky="w")    
        ttk.Entry(settings, textvariable=self.sample_n_each_var, width=12).grid(row=0, column=3, padx=8, sticky="w")

        # Gelecek ozellikler
        ttk.Separator(settings).grid(row=1, column=0, columnspan=4, sticky="ew", pady=10)

        ttk.Label(settings, text="Gelecek ozellikler (simdilik UI'de):").grid(row=2, column=0, sticky="w")
        ttk.Checkbutton(settings, text="Karisik header satiri bul (v1.1)", variable=self.future_header_detect_var).grid(row=3, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(settings, text="Is ozeti uret (v1.2)", variable=self.future_business_summary_var).grid(row=3, column=2, columnspan=2, sticky="w")

        # Butonlar + progress
        actions = ttk.Frame(self, padding=(12, 0))
        actions.pack(fill="x")

        self.run_btn = ttk.Button(actions, text="Raporu Olustur", command=self.run_report)
        self.run_btn.pack(side="left")

        self.progress = ttk.Progressbar(actions, mode="indeterminate")
        self.progress.pack(side="left", padx=10, fill="x", expand=True)

        ttk.Button(actions, text="Output klasorunu ac", command=self.open_output).pack(side="right")

        # Log alani
        log_frame = ttk.LabelFrame(self, text="Log", padding=8)
        log_frame.pack(fill="both", expand=True, padx=12, pady=12)

        self.log_text = tk.Text(log_frame, height=12)
        self.log_text.pack(fill="both", expand=True)

        # Alt butonlar
        bottom = ttk.Frame(self, padding=(12, 0, 12, 12))
        bottom.pack(fill="x")

        ttk.Button(bottom, text="Excel raporunu ac", command=self.open_xlsx).pack(side="left")
        ttk.Button(bottom, text="HTML raporunu ac", command=self.open_html).pack(side="left", padx=8)

        self.summary_lbl = ttk.Label(bottom, text="Hazir.")
        self.summary_lbl.pack(side="right")

        # Baslangicta tema uygula
        self.apply_theme()


    def apply_theme(self):
        if self.is_dark_mode:
            # DARK THEME
            self.configure(bg="#1e1e1e")

            self.style.configure("TFrame", background="#1e1e1e")
            self.style.configure("TLabel", background="#1e1e1e", foreground="#ffffff")
            self.style.configure("TButton", background="#2d2d2d", foreground="#ffffff")
            self.style.configure("TLabelframe", background="#1e1e1e", foreground="#ffffff")
            self.style.configure("TLabelframe.Label", background="#1e1e1e", foreground="#ffffff")

            self.log_text.configure(
            bg="#111111",
            fg="#00ff88",
            insertbackground="#ffffff"
        )
        else:
            # LIGHT THEME
            self.configure(bg="#f0f0f0")

            self.style.configure("TFrame", background="#f0f0f0")
            self.style.configure("TLabel", background="#f0f0f0", foreground="#000000")
            self.style.configure("TButton", background="#e0e0e0", foreground="#000000")
            self.style.configure("TLabelframe", background="#f0f0f0", foreground="#000000")
            self.style.configure("TLabelframe.Label", background="#f0f0f0", foreground="#000000")

            self.log_text.configure(
                bg="#ffffff",
                fg="#000000",
                insertbackground="#000000"
            )

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def pick_file(self):
        path = filedialog.askopenfilename(
            title="Excel dosyasi seç",
            filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")]
        )
        if path:
            self.excel_path_var.set(path)

    def log(self, msg: str):
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.update_idletasks()

    def set_busy(self, busy: bool):
        if busy:
            self.run_btn.config(state="disabled")
            self.progress.start(10)
        else:
            self.progress.stop()
            self.run_btn.config(state="normal")

    def run_report(self):
        excel_path = self.excel_path_var.get().strip()
        if not excel_path or not os.path.exists(excel_path):
            messagebox.showerror("Hata", "Lütfen geçerli bir Excel dosyasi seç.")
            return

        try:
            threshold = int(self.sample_threshold_var.get())
            n_each = int(self.sample_n_each_var.get())
        except Exception:
            messagebox.showerror("Hata", "Örnekleme ayarlari sayi olmali.")
            return

        self.log_text.delete("1.0", "end")
        self.summary_lbl.config(text="Çalişiyor...")
        self.set_busy(True)

        # UI donmasın diye ayrı thread
        t = threading.Thread(
            target=self._run_report_worker,
            args=(excel_path, threshold, n_each),
            daemon=True
        )
        t.start()

    def _run_report_worker(self, excel_path: str, threshold: int, n_each: int):
        try:
            result = generate_reports(
                excel_path=excel_path,
                output_dir=self.output_dir,
                template_dir=self.template_dir,
                sample_threshold=threshold,
                sample_n_each=n_each,
                log_cb=lambda m: self.after(0, self.log, m)
            )
            self.out_xlsx = result["out_xlsx"]
            self.out_html = result["out_html"]
            s = result["summary"]
            text = f"Sheet={s['sheet_sayisi']} | Satır={s['toplam_satir']} | WARN={s['warn']} | ERROR={s['error']}"
            self.after(0, self.summary_lbl.config, {"text": text})
        except Exception as e:
            self.after(0, messagebox.showerror, "Hata", str(e))
            self.after(0, self.summary_lbl.config, {"text": "Hata oluştu."})
        finally:
            self.after(0, self.set_busy, False)

    def open_output(self):
        os.startfile(self.output_dir)

    def open_xlsx(self):
        if self.out_xlsx and os.path.exists(self.out_xlsx):
            os.startfile(self.out_xlsx)
        else:
            messagebox.showinfo("Bilgi", "Önce rapor üretmelisin.")

    def open_html(self):
        if self.out_html and os.path.exists(self.out_html):
            os.startfile(self.out_html)
        else:
            messagebox.showinfo("Bilgi", "Önce rapor üretmelisin.")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
