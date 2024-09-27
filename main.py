import tkinter as tk
from video_navigator import VideoNavigatorApp

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x800")
    app = VideoNavigatorApp(root)
    root.mainloop()
