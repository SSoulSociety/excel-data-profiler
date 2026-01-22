from tkinter import Tk, filedialog

def pick_excel_file() -> str | None:
    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Excel dosyası seç",
        filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")]
    )
    root.destroy()
    return file_path if file_path else None
