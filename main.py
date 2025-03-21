import tkinter as tk
from tkinter import filedialog, ttk
from pdf2image import convert_from_path, pdfinfo_from_path
from PIL import Image, ImageTk

class PDFViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple PDF Reader")
        self.tabs = {}  # Store open PDFs in a dictionary

        # 🖥 Set window to large size
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.geometry(f"{int(screen_width * 0.8)}x{int(screen_height * 0.8)}+{int(screen_width * 0.1)}+{int(screen_height * 0.1)}")

        # Main frame for canvas
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
        self.root.bind("<Configure>", self.on_resize)  # ✅ Fixed missing method

        # Canvas window for image (will be centered)
        self.image_container = self.canvas.create_image(0, 0, anchor='n')

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

        # Tabs at the bottom
        self.tab_frame = tk.Frame(root)
        self.tab_frame.pack(side="bottom", fill="x")

        self.tab_control = ttk.Notebook(self.tab_frame)
        self.tab_control.pack(fill="x")

        # Default values
        self.current_page = 0
        self.page_count = 0
        self.pdf_path = None
        self.poppler_path = r"C:\poppler\Library\bin"
        self.current_image = None
        self.zoom = 0.8
        self.dark_mode = False  

    def open_pdf(self):
        """Opens a new PDF and creates a new tab."""
        filepath = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if filepath:
            file_name = filepath.split("/")[-1]

            if file_name in self.tabs:
                self.tab_control.select(self.tabs[file_name]['tab'])  # Switch to existing tab
                return

            # Create a new tab
            new_tab = tk.Frame(self.tab_control)
            self.tab_control.add(new_tab, text=file_name)
            self.tab_control.select(new_tab)

            self.tabs[file_name] = {
                "frame": new_tab,
                "pdf_path": filepath,
                "current_page": 0,
                "zoom": 0.8
            }

            self.pdf_path = filepath
            self.current_page = 0
            self.page_count = int(pdfinfo_from_path(filepath, poppler_path=self.poppler_path)['Pages'])
            self.zoom = 0.8
            self.root.after(100, self.fit_to_width)

    def on_resize(self, event):
        """Resize the PDF display properly when the window resizes."""
        if self.pdf_path:
            self.fit_to_width()

    def fit_to_width(self):
        """Automatically adjust zoom to fit width properly."""
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
                self.zoom = 0.8  # Default to 80% zoom

            self.load_page_image()
            self.show_page()

    def load_page_image(self):
        """Loads and renders the current page."""
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
        """Displays the current PDF page in the viewer."""
        if self.current_image:
            target_width = int(self.current_image.width * self.zoom)
            target_height = int(self.current_image.height * self.zoom)
            resized = self.current_image.resize((target_width, target_height), Image.LANCZOS)
            img = ImageTk.PhotoImage(resized)

            self.canvas.image = img  
            self.canvas.itemconfig(self.image_container, image=img)

            canvas_width = self.canvas.winfo_width()
            x = canvas_width // 2
            y = 0
            self.canvas.coords(self.image_container, x, y)

            self.canvas.config(scrollregion=(0, 0, max(canvas_width, target_width), max(target_height, self.canvas.winfo_height())))

            self.root.title(f"Simple PDF Reader - Page {self.current_page + 1} of {self.page_count} - Zoom {int(self.zoom * 100)}%")

    def next_page(self, event=None):
        """Go to the next page."""
        if self.current_page < self.page_count - 1:
            self.current_page += 1
            self.load_page_image()
            self.show_page()
            self.canvas.yview_moveto(0)

    def prev_page(self, event=None):
        """Go to the previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page_image()
            self.show_page()
            self.canvas.yview_moveto(0)

    def scroll_down(self, event=None):
        """Scroll down, moving to the next page if at the bottom."""
        if self.canvas.yview()[1] >= 1.0 and self.current_page < self.page_count - 1:
            self.next_page()
        else:
            self.canvas.yview_scroll(1, "units")

    def scroll_up(self, event=None):
        """Scroll up, moving to the previous page if at the top."""
        if self.canvas.yview()[0] <= 0.0 and self.current_page > 0:
            self.prev_page()
        else:
            self.canvas.yview_scroll(-1, "units")

    def zoom_in(self):
        """Increase zoom."""
        self.zoom += 0.1
        self.show_page()

    def zoom_out(self):
        """Decrease zoom."""
        if self.zoom > 0.2:
            self.zoom -= 0.1
            self.show_page()

    def go_to_page(self):
        """Jump to a specific page."""
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
        """Toggle dark mode."""
        self.dark_mode = not self.dark_mode
        bg_color = "black" if self.dark_mode else "gray"
        self.root.configure(bg=bg_color)
        self.canvas.configure(bg=bg_color)

root = tk.Tk()
viewer = PDFViewer(root)
root.mainloop()
