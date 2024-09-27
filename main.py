import tkinter as tk
from video_navigator import VideoNavigatorApp

if __name__ == "__main__":
    def load_playlist_from_navigator(playlist_path):
        print("The playlist path is: ", playlist_path)

    root = tk.Tk()
    root.geometry("800x800")
    app = VideoNavigatorApp(root, load_playlist_callback=load_playlist_from_navigator)
    root.mainloop()

