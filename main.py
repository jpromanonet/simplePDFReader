import tkinter as tk
from tkinter import filedialog
from pdf2image import convert_from_path, pdfinfo_from_path
from PIL import Image, ImageTk

class PDFViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple PDF Reader")
        self.current_page = 0
        self.page_count = 0
        self.pdf_path = None
        self.poppler_path = r"C:\poppler\Library\bin"
        self.current_image = None
        self.zoom = 0.8  # 🔥 Default zoom set to 80%
        self.dark_mode = False  

        # 🖥 Set window to large size
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.geometry(f"{int(screen_width * 0.8)}x{int(screen_height * 0.8)}+{int(screen_width * 0.1)}+{int(screen_height * 0.1)}")

        # Scrollable Canvas Setup
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

        # Canvas window for image (will be centered)
        self.image_container = self.canvas.create_image(0, 0, anchor='n')  # Anchor at the **top (n)** to avoid cutting top

        # Buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=4)

        tk.Button(btn_frame, text="Open PDF", command=self.open_pdf).pack(side="left", padx=2)
        tk.Button(btn_frame, text="<< Prev", command=self.prev_page).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Next >>", command=self.next_page).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Zoom +", command=self.zoom_in).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Zoom -", command=self.zoom_out).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Dark Mode", command=self.toggle_dark_mode).pack(side="left", padx=2)

        self.page_entry = tk.Entry(btn_frame, width=5)
        self.page_entry.pack(side="left", padx=2)
        tk.Button(btn_frame, text="Go", command=self.go_to_page).pack(side="left", padx=2)

    def open_pdf(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if filepath:
            self.pdf_path = filepath
            self.current_page = 0
            self.page_count = int(pdfinfo_from_path(filepath, poppler_path=self.poppler_path)['Pages'])
            self.zoom = 0.8  # 🔥 Reset zoom to 80% every time a new PDF is opened
            self.root.after(100, self.fit_to_width)

    def fit_to_width(self):
        """Automatically adjust zoom to fit width properly when the window is resized"""
        if self.pdf_path:
            temp_image = convert_from_path(
                self.pdf_path,
                dpi=150,
                first_page=1,
                last_page=1,
                poppler_path=self.poppler_path
            )[0]

            canvas_width = self.canvas.winfo_width()
            if canvas_width > 0:  
                self.zoom = 0.8  # Ensure default zoom is always 80%

            self.load_page_image()
            self.show_page()

    def load_page_image(self):
        if self.pdf_path:
            try:
                page_image = convert_from_path(
                    self.pdf_path,
                    dpi=150,
                    first_page=self.current_page + 1,
                    last_page=self.current_page + 1,
                    poppler_path=self.poppler_path
                )[0]
                self.current_image = page_image
            except Exception as e:
                print("Error loading page:", e)

    def show_page(self):
        if self.current_image:
            target_width = int(self.current_image.width * self.zoom)
            target_height = int(self.current_image.height * self.zoom)
            resized = self.current_image.resize((target_width, target_height), Image.LANCZOS)
            img = ImageTk.PhotoImage(resized)

            self.canvas.image = img  
            self.canvas.itemconfig(self.image_container, image=img)

            # **Ensure full page is visible**
            canvas_width = self.canvas.winfo_width()
            x = canvas_width // 2  # Center horizontally
            y = 0  # Start at the **top** so you can see the whole page
            self.canvas.coords(self.image_container, x, y)

            # **Fix scrolling issue (Make full page scrollable)**
            self.canvas.config(scrollregion=(0, 0, max(canvas_width, target_width), max(target_height, self.canvas.winfo_height())))

            self.root.title(f"Simple PDF Reader - Page {self.current_page + 1} of {self.page_count} - Zoom {int(self.zoom * 100)}%")

    def scroll_down(self, event=None):
        """Scroll down using the Down Arrow key, move to next page at the bottom"""
        _, _, _, y2 = self.canvas.bbox("all")
        scroll_pos = self.canvas.yview()[0]

        if scroll_pos >= 0.95 and self.current_page < self.page_count - 1:
            self.next_page()
        else:
            self.canvas.yview_scroll(1, "units")

        # If scrollbar is at the end, trigger next page
        if self.v_scroll.get()[1] >= 1.0 and self.current_page < self.page_count - 1:
            self.next_page()

    def scroll_up(self, event=None):
        """Scroll up using the Up Arrow key, move to previous page at the top"""
        current_scroll = self.canvas.yview()[0]

        if current_scroll <= 0.05 and self.current_page > 0:
            self.prev_page()
        else:
            self.canvas.yview_scroll(-1, "units")

    def next_page(self, event=None):
        if self.current_page < self.page_count - 1:
            self.current_page += 1
            self.load_page_image()
            self.show_page()
            self.canvas.yview_moveto(0)  # Move to the top of the new page

    def prev_page(self, event=None):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page_image()
            self.show_page()
            self.canvas.yview_moveto(0)  # Move to the top of the new page

    def on_resize(self, event):
        """Resize properly while keeping everything visible"""
        if self.current_image:
            self.fit_to_width()

    def zoom_in(self):
        self.zoom += 0.1
        self.show_page()

    def zoom_out(self):
        if self.zoom > 0.2:
            self.zoom -= 0.1
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
        """Fix dark mode background issue"""
        self.dark_mode = not self.dark_mode
        bg_color = "black" if self.dark_mode else "gray"
        self.root.configure(bg=bg_color)
        self.canvas.configure(bg=bg_color)

root = tk.Tk()
viewer = PDFViewer(root)
root.mainloop()
