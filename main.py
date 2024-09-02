import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, Toplevel, Label, Entry, Radiobutton, StringVar, Button
import os
import json
import sys

class VideoNavigatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Navigator")
        self.topics = {}
        self.modified_topics = set()
        self.tree_state = {}

        # Load topic files from topics_list.json
        self.topic_files = self.load_topic_files()
        self.topic_names = [os.path.splitext(os.path.basename(topic_file))[0] for topic_file in self.topic_files]

        # Directory where playlists will be stored
        self.playlist_dir = os.path.join(os.getcwd(), "playlists")
        os.makedirs(self.playlist_dir, exist_ok=True)

        # Load all topics
        self.load_all_topics()

        # Create a Treeview widget with scrollbars
        tree_frame = tk.Frame(root)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Create the treeview
        self.tree = ttk.Treeview(tree_frame)

        # Create vertical scrollbar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side='right', fill='y')

        # Create horizontal scrollbar
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        hsb.pack(side='bottom', fill='x')

        # Configure the treeview to work with the scrollbars
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Build the tree structure dynamically from the loaded data
        self.build_tree_structure()

        # Bind the selection event
        self.tree.bind("<<TreeviewSelect>>", self.on_title_select)

        # Add right-click context menu
        self.tree.bind("<Button-3>", self.show_context_menu)

        # Create a context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="View/Edit Playlist", command=self.view_edit_playlist)
        self.context_menu.add_command(label="Add Subtopic/Title", command=self.add_item)
        self.context_menu.add_command(label="Move Up", command=self.move_up)
        self.context_menu.add_command(label="Move Down", command=self.move_down)
        self.context_menu.add_command(label="Rename Item", command=self.rename_item)
        self.context_menu.add_command(label="Delete Item", command=self.delete_item)
        self.context_menu.add_command(label="Add YouTube Link", command=self.add_youtube_link)
        self.context_menu.add_command(label="Add Playlist", command=self.add_playlist)
        self.context_menu.add_command(label="Populate Playlist", command=self.populate_playlist)
        self.context_menu.add_command(label="Delete Playlist", command=self.delete_playlist)
        self.context_menu.add_command(label="Add New Topic", command=self.add_new_topic)
        self.context_menu.add_command(label="Delete Topic", command=self.delete_topic)

        # Add a text area to display messages
        self.message_area = tk.Text(root, height=5)
        self.message_area.pack(fill=tk.BOTH, expand=False)

        # Handle closing the app to save changes
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def view_edit_playlist(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a title to view/edit its playlist.")
            return

        selected_item = selected_item[0]
        selected_title = self.tree.item(selected_item, "text")
        values = self.tree.item(selected_item, "values")

        if not values or not values[0]:
            messagebox.showwarning("No Playlist", f"No playlist found for '{selected_title}'.")
            return

        playlist_path = values[0]
        if not os.path.exists(playlist_path):
            messagebox.showwarning("Invalid Playlist", f"The playlist path for '{selected_title}' does not exist.")
            return

        with open(playlist_path, "r") as file:
            self.playlist = json.load(file)

        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Edit Playlist: {selected_title}")

        edit_listbox = tk.Listbox(edit_window, width=50, height=20, selectmode=tk.EXTENDED)
        edit_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        for item in self.playlist:
            display_text = item["description"] if item["description"] else item["url"]
            edit_listbox.insert(tk.END, display_text)

        scrollbar_y = tk.Scrollbar(edit_window, orient=tk.VERTICAL, command=edit_listbox.yview)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        edit_listbox.config(yscrollcommand=scrollbar_y.set)

        scrollbar_x = tk.Scrollbar(edit_window, orient=tk.HORIZONTAL, command=edit_listbox.xview)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        edit_listbox.config(xscrollcommand=scrollbar_x.set)

        controls_frame = tk.Frame(edit_window)
        controls_frame.pack(side=tk.RIGHT, fill=tk.Y)

        def move_up():
            selected = list(edit_listbox.curselection())
            if selected:
                if selected[0] > 0:  # Ensure the first selected item is not at the top
                    for index in selected:
                        # Swap each selected item with the one above it
                        self.playlist[index], self.playlist[index - 1] = self.playlist[index - 1], self.playlist[index]
                    refresh_edit_listbox()
                    # Maintain selection after the move
                    new_selection = [i - 1 for i in selected]
                    for i in new_selection:
                        edit_listbox.selection_set(i)
                        edit_listbox.see(i)  # Ensure each moved item is visible

        def move_down():
            selected = list(edit_listbox.curselection())
            if selected:
                if selected[-1] < len(self.playlist) - 1:  # Ensure the last selected item is not at the bottom
                    for index in reversed(selected):
                        # Swap each selected item with the one below it
                        self.playlist[index], self.playlist[index + 1] = self.playlist[index + 1], self.playlist[index]
                    refresh_edit_listbox()
                    # Maintain selection after the move
                    new_selection = [i + 1 for i in selected]
                    for i in new_selection:
                        edit_listbox.selection_set(i)
                        edit_listbox.see(i)  # Ensure each moved item is visible

        def delete_item():
            selected = list(edit_listbox.curselection())
            if selected:
                for index in reversed(selected):  # Reverse to avoid reindexing issues
                    del self.playlist[index]
                refresh_edit_listbox()

        def update_description():
            selected = edit_listbox.curselection()
            if selected:
                index = selected[0]
                new_description = description_entry.get()
                self.playlist[index]["description"] = new_description
                refresh_edit_listbox()

        def refresh_edit_listbox():
            edit_listbox.delete(0, tk.END)
            for item in self.playlist:
                display_text = item["description"] if item["description"] else item["url"]
                edit_listbox.insert(tk.END, display_text)

        def save_changes():
            with open(playlist_path, "w") as file:
                json.dump(self.playlist, file, indent=4)
            edit_window.destroy()

        move_up_button = tk.Button(controls_frame, text="Move Up", command=move_up)
        move_up_button.pack(padx=5, pady=5)

        move_down_button = tk.Button(controls_frame, text="Move Down", command=move_down)
        move_down_button.pack(padx=5, pady=5)

        delete_button = tk.Button(controls_frame, text="Delete", command=delete_item)
        delete_button.pack(padx=5, pady=5)

        description_label = tk.Label(controls_frame, text="Description:")
        description_label.pack(padx=5, pady=5)

        description_entry = tk.Entry(controls_frame)
        description_entry.pack(padx=5, pady=5)

        update_button = tk.Button(controls_frame, text="Update Description", command=update_description)
        update_button.pack(padx=5, pady=5)

        save_button = tk.Button(controls_frame, text="Save and Close", command=save_changes)
        save_button.pack(padx=5, pady=5)


    def load_topic_files(self):
        topics_list_path = "topics_list.json"
        if os.path.exists(topics_list_path):
            with open(topics_list_path, "r") as file:
                return json.load(file)
        return []

    def save_topic_files(self):
        with open("topics_list.json", "w") as file:
            json.dump(self.topic_files, file, indent=4)

    def load_all_topics(self):
        for topic_file in self.topic_files:
            topic_name = os.path.splitext(os.path.basename(topic_file))[0]
            with open(topic_file, "r") as file:
                self.topics[topic_name] = json.load(file)

    def build_tree_structure(self):
        self.save_tree_state()
        self.tree.delete(*self.tree.get_children())  # Clear the tree before rebuilding

        def add_items(parent, items):
            for key, value in items.items():
                if isinstance(value, dict):
                    node = self.tree.insert(parent, "end", text=key, open=False)
                    add_items(node, value)
                else:
                    self.tree.insert(parent, "end", text=key, values=[value])

        for topic, structure in self.topics.items():
            topic_node = self.tree.insert("", "end", text=topic, open=False)
            add_items(topic_node, structure)

        # Restore the tree state to keep it expanded as it was before
        self.restore_tree_state()

    def save_tree_state(self):
        self.tree_state = {}
        self._save_children_state("", self.tree_state)

    def _save_children_state(self, parent, state):
        for item in self.tree.get_children(parent):
            state[item] = {
                "open": self.tree.item(item, "open"),
                "text": self.tree.item(item, "text")
            }
            state[item]["children"] = {}
            self._save_children_state(item, state[item]["children"])

    def restore_tree_state(self):
        self._restore_children_state("", self.tree_state)

    def _restore_children_state(self, parent, state):
        for item in self.tree.get_children(parent):
            item_text = self.tree.item(item, "text")
            for state_item, state_info in state.items():
                if state_info["text"] == item_text:
                    self.tree.item(item, open=state_info["open"])
                    self._restore_children_state(item, state_info["children"])
                    break

    def on_title_select(self, event):
        if not self.tree.selection():
            return

        # Clear the message area before inserting new information
        self.message_area.delete('1.0', tk.END)

        selected_item = self.tree.selection()[0]
        selected_title = self.tree.item(selected_item, "text")

        # Call the determine_item_type method whenever an item is selected
        item_type = self.determine_item_type(selected_item)

        if item_type == "subtopic":
            self.message_area.insert(tk.END, f"Subtopic: {selected_title}\n")
            return  # Do nothing further since it's a subtopic

        values = self.tree.item(selected_item, "values")
        if values:
            playlist_path = values[0]
        else:
            playlist_path = None

        # If the item is a title and has a playlist
        if item_type == "title":
            if playlist_path and os.path.exists(playlist_path):
                self.message_area.insert(tk.END, f"Playlist: {playlist_path}\n")
            else:
                # If no valid playlist is found, display a message
                self.message_area.insert(tk.END, f"No playlist found for '{selected_title}'.\n")

    def add_playlist(self):
        selected_item = self.tree.selection()

        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a title to add a playlist.")
            return

        selected_item = selected_item[0]
        selected_title = self.tree.item(selected_item, "text")
        values = self.tree.item(selected_item, "values")

        if values:
            playlist_path = values[0]
            if playlist_path:
                messagebox.showinfo("Playlist Exists", f"A playlist already exists for '{selected_title}'.")
                return

        folder_selected = filedialog.askdirectory()
        if folder_selected:
            playlist_path = self.create_playlist(folder_selected, selected_title)
            self.update_json_file(selected_item, playlist_path)
            self.message_area.insert(tk.END, f"Created playlist: {playlist_path}\n")

    def create_playlist(self, folder, title):
        videos = []
        for root, _, files in os.walk(folder):
            for filename in files:
                if filename.endswith(('.mp4', '.avi', '.mkv')):
                    video_path = os.path.join(root, filename)
                    videos.append({
                        "url": video_path,
                        "description": filename
                    })

        playlist_path = os.path.join(self.playlist_dir, f"{title}.json")
        with open(playlist_path, "w") as playlist_file:
            json.dump(videos, playlist_file, indent=4)

        return playlist_path

    def populate_playlist(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a title, topic, or subtopic.")
            return

        selected_item = selected_item[0]
        item_type = self.determine_item_type(selected_item)

        if item_type == "title":
            # Check if the title already has a playlist before opening the file dialog
            selected_title = self.tree.item(selected_item, "text").strip()
            values = self.tree.item(selected_item, "values")

            if values and values[0]:  # Check if a playlist already exists
                self.message_area.insert(tk.END, f"Playlist already exists for '{selected_title}'. Skipping.\n")
                return

            # If no playlist exists, proceed with file dialog
            folder_selected = filedialog.askdirectory()
            if folder_selected:
                self.build_playlist_for_title(selected_item, folder_selected)

        elif item_type in ["subtopic", "topic"]:
            folder_selected = filedialog.askdirectory()
            if folder_selected:
                # For subtopic or topic: iterate through all child titles and create playlists if missing
                self.iterate_through_children_and_build_playlists(selected_item, folder_selected)

    def build_playlist_for_title(self, selected_item, base_directory):
        selected_title = self.tree.item(selected_item, "text").strip()
        values = self.tree.item(selected_item, "values")

        if values and values[0]:  # Check if a playlist already exists
            self.message_area.insert(tk.END, f"Playlist already exists for '{selected_title}'. Skipping.\n")
            return

        # Search for a matching directory in the base directory and its subdirectories
        for root, dirs, _ in os.walk(base_directory):
            for dir_name in dirs:
                if dir_name.strip() == selected_title:
                    playlist_path = self.create_playlist(os.path.join(root, dir_name), selected_title)
                    self.update_json_file(selected_item, playlist_path)
                    self.message_area.insert(tk.END, f"Created playlist for '{selected_title}' in {playlist_path}\n")
                    return

        self.message_area.insert(tk.END, f"No matching directory found for '{selected_title}'.\n")

    def iterate_through_children_and_build_playlists(self, parent_item, base_directory):
        def iterate_tree(item):
            for child in self.tree.get_children(item):
                if self.determine_item_type(child) == "title":
                    self.build_playlist_for_title(child, base_directory)
                else:
                    iterate_tree(child)

        iterate_tree(parent_item)

    def update_json_file(self, selected_item, playlist_path):
        parent_item = self.tree.parent(selected_item)
        selected_title = self.tree.item(selected_item, "text")
        parent_title = self.tree.item(parent_item, "text") if parent_item else None

        topic_name = self.get_topic_name(selected_item)

        def update_items(structure, selected_title, parent_title, playlist_path):
            for key, value in structure.items():
                if isinstance(value, dict):
                    if key == parent_title:
                        if selected_title in value:
                            structure[key][selected_title] = playlist_path  # Assign the playlist path
                            return True
                    if update_items(value, selected_title, parent_title, playlist_path):
                        return True
                elif key == selected_title and parent_title is None:
                    structure[key] = playlist_path  # Assign the playlist path
                    return True
            return False

        if update_items(self.topics[topic_name], selected_title, parent_title, playlist_path):
            self.modified_topics.add(topic_name)
            self.tree.item(selected_item, values=[playlist_path])

            # Immediately save the updated structure to the JSON file
            with open(f"{topic_name}.json", "w") as file:
                json.dump(self.topics[topic_name], file, indent=4)

        else:
            self.message_area.insert(tk.END, f"Error: Could not update playlist for '{selected_title}'.\n")

    def get_topic_name(self, item_id):
        while True:
            parent = self.tree.parent(item_id)
            if not parent:
                return self.tree.item(item_id, "text")
            item_id = parent

    def determine_item_type(self, selected_item):
        selected_title = self.tree.item(selected_item, "text")
        item_values = self.tree.item(selected_item, "values")

        # Check if the selected item is a root-level topic
        if selected_title in self.topic_names:
            return "topic"

        # If the item has a string value, it should be a title
        if item_values and isinstance(item_values[0], str):
            return "title"

        # If the item has no values or has children, it's a subtopic
        if not item_values or self.tree.get_children(selected_item):
            return "subtopic"

        # Fallback to subtopic if nothing else matches
        return "subtopic"

    def find_value_in_structure(self, structure, parent_title, title=None):
        """Navigate the structure to find the value associated with the given title under the correct parent."""
        if parent_title in structure:
            return structure[parent_title]

        for key, value in structure.items():
            if isinstance(value, dict):
                # Recursively search within nested dictionaries
                found = self.find_value_in_structure(value, parent_title, title)
                if found is not None:
                    return found

        return None

    def find_item_type(self, structure, title):
        """Search through the structure to determine the type of a given item."""

        # Check if the title matches any key in the structure
        if title in structure:
            value = structure[title]
            if isinstance(value, dict):
                return "subtopic"
            elif isinstance(value, str):
                return "title"

        # Recursively search within nested dictionaries
        for key, value in structure.items():
            if isinstance(value, dict):
                item_type = self.find_item_type(value, title)
                if item_type:
                    return item_type

        return None

    def add_item(self):
        selected_item = self.tree.selection()

        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a topic, subtopic, or title.")
            return

        selected_item = selected_item[0]
        selected_title = self.tree.item(selected_item, "text")

        # Determine the type of the selected item
        item_type = self.determine_item_type(selected_item)

        # Open a single dialog with name, type, and nesting options
        self.open_item_dialog(selected_item, selected_title, item_type)

    def open_item_dialog(self, selected_item, selected_title, item_type):
        dialog = Toplevel(self.root)
        dialog.title("Add Subtopic/Title")

        # Label and entry for the new item name
        Label(dialog, text="Enter the name of the new subtopic/title:").grid(row=0, column=0)
        new_item_name = Entry(dialog)
        new_item_name.grid(row=0, column=1)

        # Radio button to select title or subtopic
        Label(dialog, text="Select type:").grid(row=1, column=0)
        item_type_var = StringVar(value="title")
        Radiobutton(dialog, text="Title", variable=item_type_var, value="title").grid(row=1, column=1, sticky="w")
        Radiobutton(dialog, text="Subtopic", variable=item_type_var, value="subtopic").grid(row=1, column=2, sticky="w")

        # Add radio button for nesting (inside/below) - only for subtopics
        nesting_var = StringVar(value="inside")
        if item_type == "subtopic":
            Label(dialog, text="Nesting Level:").grid(row=2, column=0)
            Radiobutton(dialog, text="Inside", variable=nesting_var, value="inside").grid(row=2, column=1, sticky="w")
            Radiobutton(dialog, text="Below", variable=nesting_var, value="below").grid(row=2, column=2, sticky="w")
        else:
            # If it's a topic or title, hide the nesting level choice
            nesting_var.set("below")

        # Confirm button to submit the new item
        Button(dialog, text="Confirm",
               command=lambda: self.add_item_confirm(dialog, new_item_name.get(), item_type_var.get(),
                                                     nesting_var.get(), selected_item, selected_title, item_type)).grid(
            row=3, column=1, pady=10)

    def add_item_confirm(self, dialog, new_item_name, item_type, nesting_level, selected_item, selected_title,
                         selected_item_type):
        dialog.destroy()  # Close the dialog

        if not new_item_name:
            messagebox.showwarning("Invalid Name", "Please enter a valid name.")
            return

        # Determine the topic name from the selected item
        topic_name = self.get_topic_name(selected_item)

        # Save the current tree state before making changes
        self.save_tree_state()

        new_item = None

        # If the selected item is a title, add below (titles can't have nested structure)
        if selected_item_type == "title":
            new_item = self.tree.insert("", self.tree.index(selected_item) + 1, text=new_item_name, open=False)
            self.add_to_structure_below(topic_name, selected_title, new_item_name, item_type)
        # If it's a topic or subtopic, handle accordingly
        elif selected_item_type in {"topic", "subtopic"}:
            if nesting_level == "inside":
                new_item = self.tree.insert(selected_item, "end", text=new_item_name, open=False)
                self.add_to_structure_inside(topic_name, selected_title, new_item_name, item_type)
            elif nesting_level == "below":
                new_item = self.tree.insert("", self.tree.index(selected_item) + 1, text=new_item_name, open=False)
                self.add_to_structure_below(topic_name, selected_title, new_item_name, item_type)

        if new_item:
            # Mark the topic as modified
            self.modified_topics.add(topic_name)

            # Update the JSON file immediately
            self.update_json_file_after_edit(topic_name)

            # Rebuild the tree to ensure it's showing the latest data
            self.build_tree_structure()

            # Restore the tree state to keep it expanded as it was before
            self.restore_tree_state()

    def update_json_file_after_edit(self, topic_name):
        """Save the modified topic structure back to the corresponding JSON file."""
        with open(f"{topic_name}.json", "w") as file:
            json.dump(self.topics[topic_name], file, indent=4)

    def add_to_structure_below(self, topic_name, parent_name, new_item_name, new_item_type):
        def find_and_add_below(structure, parent_name):
            items = list(structure.items())
            for i, (key, value) in enumerate(items):
                if key == parent_name:
                    if new_item_type == "subtopic":
                        structure[new_item_name] = {}  # No need to add _type anymore
                    else:
                        structure[new_item_name] = ""  # Titles are identified by strings
                    return True
                elif isinstance(value, dict):
                    if find_and_add_below(value, parent_name):
                        return True
            return False

        if not find_and_add_below(self.topics[topic_name], parent_name):
            if new_item_type == "subtopic":
                self.topics[topic_name][new_item_name] = {}
            else:
                self.topics[topic_name][new_item_name] = ""

    def add_to_structure_inside(self, topic_name, parent_name, new_item_name, new_item_type):
        def find_and_add_inside(structure, parent_name):
            for key, value in structure.items():
                if key == parent_name and isinstance(value, dict):
                    if new_item_type == "subtopic":
                        structure[key][new_item_name] = {}  # No need for _type key
                    else:
                        structure[key][new_item_name] = ""  # Titles are identified by strings
                    return True
                elif isinstance(value, dict):
                    if find_and_add_inside(value, parent_name):
                        return True
            return False

        if not find_and_add_inside(self.topics[topic_name], parent_name):
            if new_item_type == "subtopic":
                self.topics[topic_name][new_item_name] = {}
            else:
                self.topics[topic_name][new_item_name] = ""

    def move_up(self):
        selected_item = self.tree.selection()[0]
        prev_item = self.tree.prev(selected_item)

        if prev_item:
            selected_title = self.tree.item(selected_item, "text")
            prev_title = self.tree.item(prev_item, "text")

            parent_item = self.tree.parent(selected_item)
            parent_title = self.tree.item(parent_item, "text") if parent_item else None

            if parent_title is None:
                # This is a root-level topic
                current_index = self.topic_files.index(f"{selected_title}.json")
                prev_index = self.topic_files.index(f"{prev_title}.json")
                self.topic_files[current_index], self.topic_files[prev_index] = (
                    self.topic_files[prev_index],
                    self.topic_files[current_index],
                )
                self.save_topic_files()
            else:
                topic_name = self.get_topic_name(selected_item)
                if parent_title in self.topics:
                    parent_structure = self.topics[parent_title]
                else:
                    parent_structure = self.find_value_in_structure(self.topics[topic_name], parent_title)

                if parent_structure:
                    self.swap_items_in_structure(parent_structure, selected_title, prev_title)
                    self.modified_topics.add(topic_name)
                    self.update_json_file_after_edit(topic_name)
                else:
                    print(f"Warning: Could not find structure for parent '{parent_title}'.")

            # Move the item in the tree view
            current_index = self.tree.index(selected_item)
            self.tree.move(selected_item, self.tree.parent(selected_item), current_index - 1)

    def move_down(self):
        selected_item = self.tree.selection()[0]
        next_item = self.tree.next(selected_item)

        if next_item:
            selected_title = self.tree.item(selected_item, "text")
            next_title = self.tree.item(next_item, "text")

            parent_item = self.tree.parent(selected_item)
            parent_title = self.tree.item(parent_item, "text") if parent_item else None

            if parent_title is None:
                # This is a root-level topic
                current_index = self.topic_files.index(f"{selected_title}.json")
                next_index = self.topic_files.index(f"{next_title}.json")
                self.topic_files[current_index], self.topic_files[next_index] = (
                    self.topic_files[next_index],
                    self.topic_files[current_index],
                )
                self.save_topic_files()
            else:
                topic_name = self.get_topic_name(selected_item)
                if parent_title in self.topics:
                    parent_structure = self.topics[parent_title]
                else:
                    parent_structure = self.find_value_in_structure(self.topics[topic_name], parent_title)

                if parent_structure:
                    self.swap_items_in_structure(parent_structure, selected_title, next_title)
                    self.modified_topics.add(topic_name)
                    self.update_json_file_after_edit(topic_name)
                else:
                    print(f"Warning: Could not find structure for parent '{parent_title}'.")

            # Move the item in the tree view
            current_index = self.tree.index(selected_item)
            self.tree.move(selected_item, self.tree.parent(selected_item), current_index + 1)

    def swap_items_in_structure(self, structure, item1, item2):
        items = list(structure.items())
        index1, index2 = None, None
        for i, (key, value) in enumerate(items):
            if key == item1:
                index1 = i
            elif key == item2:
                index2 = i
            if index1 is not None and index2 is not None:
                break
        if index1 is not None and index2 is not None:
            items[index1], items[index2] = items[index2], items[index1]
            structure.clear()
            structure.update(items)

    def swap_items_in_list(self, item_list, item1, item2):
        index1 = item_list.index(f"{item1}.json")
        index2 = item_list.index(f"{item2}.json")
        item_list[index1], item_list[index2] = item_list[index2], item_list[index1]

    def rename_item(self):
        selected_item = self.tree.selection()

        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a topic, subtopic, or title to rename.")
            return

        selected_item = selected_item[0]
        selected_title = self.tree.item(selected_item, "text")

        # Determine the type of the selected item
        item_type = self.determine_item_type(selected_item)

        if item_type == "topic":
            messagebox.showinfo("Rename Not Allowed", "Topic names cannot be changed.")
            return

        new_name = simpledialog.askstring("Rename Item", f"Enter a new name for '{selected_title}':")

        if new_name:
            topic_name = self.get_topic_name(selected_item)

            # Save the current tree state before making changes
            self.save_tree_state()

            # Update the in-memory structure, passing the selected_item ID to target the correct item
            self.update_structure_name(topic_name, selected_item, selected_title, new_name)

            # Update the tree item text
            self.tree.item(selected_item, text=new_name)

            # Mark the topic as modified
            self.modified_topics.add(topic_name)

            # Update the JSON file immediately
            self.update_json_file_after_edit(topic_name)

            # Rebuild the tree to ensure it's showing the latest data
            self.build_tree_structure()

            # Restore the tree state to keep it expanded as it was before
            self.restore_tree_state()

    def update_structure_name(self, topic_name, selected_item, old_name, new_name):
        def rename_item_in_structure(structure, item_id, old_name, new_name):
            for key, value in list(structure.items()):
                if key == old_name and item_id == self.tree.selection()[0]:
                    # Preserve the order by re-inserting the renamed item in the same position
                    items = list(structure.items())
                    index = items.index((key, value))  # Find the current position
                    items[index] = (new_name, value)  # Replace the old name with the new name
                    structure.clear()  # Clear the current structure
                    structure.update(items)  # Reinsert all items, maintaining the order
                    return True
                elif isinstance(value, dict):
                    # Recursively search within nested dictionaries
                    if rename_item_in_structure(value, item_id, old_name, new_name):
                        return True
            return False

        if topic_name in self.topics:
            rename_item_in_structure(self.topics[topic_name], selected_item, old_name, new_name)

    def delete_item(self):
        selected_item = self.tree.selection()[0]
        selected_title = self.tree.item(selected_item, "text")

        topic_name = self.get_topic_name(selected_item)
        self.modified_topics.add(topic_name)

        def delete_items(structure, selected_title):
            if selected_title in structure:
                del structure[selected_title]
                return True
            for key, value in structure.items():
                if isinstance(value, dict):
                    if delete_items(value, selected_title):
                        return True
            return False

        if delete_items(self.topics[topic_name], selected_title):
            self.tree.delete(selected_item)
            self.update_json_file_after_edit(topic_name)

    def add_new_topic(self):
        new_topic_name = simpledialog.askstring("New Topic", "Enter the name of the new topic:")

        if new_topic_name:
            selected_item = self.tree.selection()

            if selected_item:
                # If an item is selected, check if it's a root-level topic
                parent_item = self.tree.parent(selected_item[0])
                if parent_item == "":
                    # Add a new root-level topic below the currently selected topic
                    new_item = self.tree.insert("", self.tree.index(selected_item[0]) + 1, text=new_topic_name,
                                                open=False)
                else:
                    # The selected item is not a root-level topic, so add the new topic at the root level
                    new_item = self.tree.insert("", "end", text=new_topic_name, open=False)
            else:
                # No selection, so add the new topic at the root level as the last item
                new_item = self.tree.insert("", "end", text=new_topic_name, open=False)

            self.message_area.insert(tk.END, f"Added new topic: {new_topic_name}\n")

            # Update the in-memory structure
            self.topics[new_topic_name] = {}
            self.modified_topics.add(new_topic_name)

            # Also, update the topics_list.json file to include the new topic file
            self.topic_files.append(f"{new_topic_name}.json")
            self.save_topic_files()

            # Save the new topic structure to a new JSON file
            with open(f"{new_topic_name}.json", "w") as file:
                json.dump({}, file, indent=4)

    def delete_topic(self):
        selected_item = self.tree.selection()[0]
        selected_title = self.tree.item(selected_item, "text")

        if selected_title in self.topics:
            # Remove the topic from the in-memory structure
            del self.topics[selected_title]
            # Remove the topic from the list of topic files
            self.topic_files = [f for f in self.topic_files if not f.startswith(selected_title)]
            # Remove the topic from the modified topics set
            self.modified_topics.discard(selected_title)
            # Remove the JSON file from the filesystem
            topic_file_path = f"{selected_title}.json"
            if os.path.exists(topic_file_path):
                os.remove(topic_file_path)

            # Update the topics_list.json file to reflect the changes
            self.save_topic_files()
            # Rebuild the tree structure to reflect the changes
            self.build_tree_structure()

    def show_context_menu(self, event):
        # Show context menu
        self.context_menu.post(event.x_root, event.y_root)

    def add_youtube_link(self):
        selected_item = self.tree.selection()[0]
        selected_title = self.tree.item(selected_item, "text")

        # Prompt for YouTube link
        youtube_link = simpledialog.askstring("YouTube Link", f"Enter YouTube link for '{selected_title}':")

        if youtube_link:
            playlist_path = os.path.join(self.playlist_dir, f"{selected_title}.json")
            youtube_entry = {
                "url": youtube_link,
                "description": selected_title
            }

            with open(playlist_path, "w") as playlist_file:
                json.dump([youtube_entry], playlist_file, indent=4)

            # Update JSON file with the new playlist path
            self.update_json_file(selected_item, playlist_path)
            self.message_area.insert(tk.END, f"Added YouTube link for {selected_title}: {youtube_link}\n")

    def delete_playlist(self):
        selected_item = self.tree.selection()[0]
        selected_title = self.tree.item(selected_item, "text")
        values = self.tree.item(selected_item, "values")

        if values:
            playlist_path = values[0]
            if os.path.exists(playlist_path):
                os.remove(playlist_path)
                self.message_area.insert(tk.END, f"Deleted playlist: {playlist_path}\n")

            self.update_json_file(selected_item, "")
            self.tree.item(selected_item, values=[""])  # Clear the value in the tree

    def on_close(self):
        for topic_name in self.modified_topics:
            topic_file = f"{topic_name}.json"
            with open(topic_file, "w") as file:
                json.dump(self.topics[topic_name], file, indent=4)

        self.save_topic_files()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x800")
    app = VideoNavigatorApp(root)
    root.mainloop()
