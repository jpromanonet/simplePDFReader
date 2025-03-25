import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import os
import sys
import random

class PDFViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("BareReader")
        self.tabs = {}
        self.last_tab = None
        self.used_colors = set()

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.geometry(f"{int(screen_width * 0.8)}x{int(screen_height * 0.8)}+{int(screen_width * 0.1)}+{int(screen_height * 0.1)}")

        self.tab_frame = tk.Frame(root)
        self.tab_frame.pack(side="top", fill="x")
        self.tab_control = ttk.Notebook(self.tab_frame)
        self.tab_control.pack(fill="x")
        self.tab_control.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self.active_tab_data = None

        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(self.canvas_frame, bg="gray")
        self.v_scroll = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.h_scroll = tk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.root.bind("<KeyPress-Up>", self.scroll_up)
        self.root.bind("<KeyPress-Down>", self.scroll_down)
        self.root.bind("<Configure>", self.on_resize)
        self.image_container = self.canvas.create_image(0, 0, anchor='n')

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=4)
        tk.Button(btn_frame, text="Open PDF", command=self.open_pdf).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Close Tab", command=self.confirm_close_current_tab).pack(side="left", padx=2)
        tk.Button(btn_frame, text="<< Prev", command=self.prev_page).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Next >>", command=self.next_page).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Zoom +", command=self.zoom_in).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Zoom -", command=self.zoom_out).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Dark Mode", command=self.toggle_dark_mode).pack(side="left", padx=2)

        self.page_entry = tk.Entry(btn_frame, width=5)
        self.page_entry.pack(side="left", padx=2)
        tk.Button(btn_frame, text="Go", command=self.go_to_page).pack(side="left", padx=2)

        self.root.bind("<MouseWheel>", self.on_mouse_scroll)
        self.root.bind("<Button-4>", self.on_mouse_scroll)
        self.root.bind("<Button-5>", self.on_mouse_scroll)

        self.current_page = 0
        self.page_count = 0
        self.pdf_path = None
        self.current_image = None
        self.zoom = 1.5
        self.dark_mode = False
        self.current_doc = None

    def on_resize(self, event):
        if self.pdf_path:
            self.fit_to_width()

    def open_pdf(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if filepath:
            file_name = os.path.basename(filepath)
            if file_name in self.tabs:
                self.tab_control.select(self.tabs[file_name]['tab'])
                return

            new_tab = tk.Frame(self.tab_control)
            while True:
                color = f'#{random.randint(50,200):02x}{random.randint(50,200):02x}{random.randint(50,200):02x}'
                if color not in self.used_colors:
                    self.used_colors.add(color)
                    break

            tab_color = color
            colors = ["🟥", "🟦", "🟩", "🟨", "🟪", "🟫"]
            emoji = colors[len(self.used_colors) % len(colors)]
            tab_text = f"{emoji} {file_name}"
            self.tab_control.add(new_tab, text=tab_text)
            self.tab_control.select(new_tab)

            color_bar = tk.Frame(new_tab, width=10, bg=tab_color)
            color_bar.pack(side="left", fill="y")

            try:
                doc = fitz.open(filepath)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open PDF.\n\n{e}")
                return

            self.tabs[file_name] = {
                "frame": new_tab,
                "pdf_path": filepath,
                "current_page": 0,
                "zoom": 1.5,
                "color": tab_color,
                "scroll": 0.0,
                "doc": doc
            }

            self.pdf_path = filepath
            self.current_doc = doc
            self.page_count = len(doc)
            self.current_page = 0
            self.zoom = 1.5
            self.load_page_image()
            self.show_page()

    def on_tab_change(self, event):
        selected_tab = event.widget.select()
        if self.last_tab:
            for name, tab_data in self.tabs.items():
                if str(tab_data['frame']) == str(self.last_tab):
                    tab_data['current_page'] = self.current_page
                    tab_data['zoom'] = self.zoom
                    tab_data['scroll'] = self.canvas.yview()[0]
                    break

        for name, tab_data in self.tabs.items():
            if str(tab_data['frame']) == str(selected_tab):
                self.active_tab_data = tab_data
                self.pdf_path = tab_data['pdf_path']
                self.current_doc = tab_data['doc']
                self.current_page = tab_data['current_page']
                self.zoom = tab_data['zoom']
                self.page_count = len(self.current_doc)
                self.load_page_image()
                self.show_page()
                scroll_value = tab_data['scroll']
                self.root.after(50, lambda: self.canvas.yview_moveto(scroll_value))
                break

        self.last_tab = selected_tab

    def close_tab(self, index):
        tab = self.tab_control.tabs()[index]
        for name in list(self.tabs.keys()):
            if str(self.tabs[name]['frame']) == tab:
                self.tabs[name]['doc'].close()
                del self.tabs[name]
                break
        self.tab_control.forget(index)
        if not self.tabs:
            self.pdf_path = None
            self.current_doc = None
            self.current_image = None
            self.canvas.delete(self.image_container)
            self.root.title("BareReader")

    def confirm_close_current_tab(self):
        current_tab = self.tab_control.select()
        if not current_tab:
            return
        for name, tab_data in list(self.tabs.items()):
            if str(tab_data['frame']) == str(current_tab):
                confirm = messagebox.askyesno("Close Tab", f"Do you want to close '{name}'?")
                if confirm:
                    index = self.tab_control.index(current_tab)
                    self.close_tab(index)
                return

    def fit_to_width(self):
        self.load_page_image()
        self.show_page()
        if self.active_tab_data:
            scroll_value = self.active_tab_data['scroll']
            self.root.after(50, lambda: self.canvas.yview_moveto(scroll_value))

    def load_page_image(self):
        if self.current_doc:
            try:
                page = self.current_doc.load_page(self.current_page)
                pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom, self.zoom))
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                self.current_image = image
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load page.\n\n{e}")

    def show_page(self):
        if self.current_image:
            target_width = int(self.current_image.width)
            target_height = int(self.current_image.height)
            resized = self.current_image.resize((target_width, target_height), Image.LANCZOS)
            img = ImageTk.PhotoImage(resized)
            self.canvas.image = img
            self.canvas.itemconfig(self.image_container, image=img)
            canvas_width = self.canvas.winfo_width()
            x = canvas_width // 2
            y = 0
            self.canvas.coords(self.image_container, x, y)
            self.canvas.config(scrollregion=(0, 0, max(canvas_width, target_width), max(target_height, self.canvas.winfo_height())))
            self.root.title(f"BareReader - Page {self.current_page + 1} of {self.page_count} - Zoom {int(self.zoom * 100)}%")

    def next_page(self, event=None):
        if self.current_page < self.page_count - 1:
            self.current_page += 1
            self.load_page_image()
            self.show_page()
            self.canvas.yview_moveto(0)

    def prev_page(self, event=None):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page_image()
            self.show_page()
            self.canvas.yview_moveto(0)

    def scroll_down(self, event=None):
        if self.canvas.yview()[1] >= 1.0 and self.current_page < self.page_count - 1:
            self.next_page()
        else:
            self.canvas.yview_scroll(1, "units")

    def scroll_up(self, event=None):
        if self.canvas.yview()[0] <= 0.0 and self.current_page > 0:
            self.prev_page()
        else:
            self.canvas.yview_scroll(-1, "units")

    def on_mouse_scroll(self, event):
        if event.num == 4 or event.delta > 0:
            self.scroll_up()
        elif event.num == 5 or event.delta < 0:
            self.scroll_down()

    def zoom_in(self):
        self.zoom += 0.1
        self.load_page_image()
        self.show_page()

    def zoom_out(self):
        if self.zoom > 0.2:
            self.zoom -= 0.1
            self.load_page_image()
            self.show_page()

    def go_to_page(self):
        try:
            page = int(self.page_entry.get()) - 1
            if 0 <= page < self.page_count:
                self.current_page = page
                self.load_page_image()
                self.show_page()
                self.canvas.yview_moveto(0)
        except ValueError:
            pass

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        bg_color = "black" if self.dark_mode else "gray"
        self.root.configure(bg=bg_color)
        self.canvas.configure(bg=bg_color)

root = tk.Tk()
viewer = PDFViewer(root)
root.mainloop()
