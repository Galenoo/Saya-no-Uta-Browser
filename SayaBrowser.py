import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from PIL import Image, ImageTk
import io
import os
import random
from pathlib import Path
import threading
from urllib.parse import urlparse
import json
from rich import print_json


class DanbooruViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("✦ Danbooru Saya Viewer ✦")
        self.root.geometry("900x700")

        # Configure dark theme colors
        self.bg_color = "#1a1a2e"
        self.fg_color = "#eee"
        self.accent_color = "#16213e"
        self.button_color = "#0f3460"
        self.button_hover = "#62CBBF"
        self.disabled_color = "#2d2d44"

        self.root.configure(bg=self.bg_color)

        # API credentials - User needs to fill these
        self.username = "username"  # Replace with your username
        self.api_key = "api_key"  # Replace with your API key

        # State variables
        self.current_image_url = None
        self.current_image_data = None
        self.posts_cache = []
        self.current_post = None
        self.full_res_window = None

        # Create GUI
        self.setup_gui()

        # Create Downloads folder if it doesn't exist
        self.downloads_path = Path.cwd() / "Downloads"
        self.downloads_path.mkdir(exist_ok=True)

    def setup_gui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title
        title_label = tk.Label(
            main_frame,
            text="◈ Saya no Uta Gallery ◈",
            font=("Segoe UI", 18, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
        )
        title_label.pack(pady=(0, 10))

        # Subtitle
        subtitle_label = tk.Label(
            main_frame,
            text="Browse random Saya from Danbooru",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg="#aaa",
        )
        subtitle_label.pack(pady=(0, 20))

        # Button frame
        button_frame = tk.Frame(main_frame, bg=self.bg_color)
        button_frame.pack(pady=(0, 20))

        # Random button
        self.random_btn = tk.Button(
            button_frame,
            text="▶ Get Random Saya",
            font=("Segoe UI", 11, "bold"),
            bg=self.button_color,
            fg=self.fg_color,
            activebackground=self.button_hover,
            activeforeground=self.fg_color,
            padx=20,
            pady=10,
            bd=0,
            cursor="heart",
            command=self.get_random_image,
        )
        self.random_btn.pack(side=tk.LEFT, padx=5)

        # Download button
        self.download_btn = tk.Button(
            button_frame,
            text="⬇ Download Image",
            font=("Segoe UI", 11, "bold"),
            bg=self.disabled_color,
            fg="#888",
            padx=20,
            pady=10,
            bd=0,
            state=tk.DISABLED,
            command=self.download_image,
        )
        self.download_btn.pack(side=tk.LEFT, padx=5)

        # Image container frame with border
        image_container = tk.Frame(
            main_frame, bg=self.accent_color, relief=tk.FLAT, bd=2
        )
        image_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Image display label
        self.image_label = tk.Label(
            image_container,
            bg=self.accent_color,
            text="♦ No image loaded ♦\n\nClick 'Get Random Picture' to start",
            font=("Segoe UI", 12),
            fg="#666",
        )
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.image_label.bind("<Double-Button-1>", self.show_full_resolution)

        # Status bar with text wrapping
        self.status_label = tk.Label(
            main_frame,
            text="Ready",
            font=("Segoe UI", 9),
            bg=self.bg_color,
            fg="#888",
            anchor=tk.W,
            wraplength=880,  # Allow text wrapping for long tag lists
            justify=tk.LEFT,
        )
        self.status_label.pack(fill=tk.X)

        # Info label
        info_label = tk.Label(
            main_frame,
            text="♦ Double-click image to view full resolution ♦",
            font=("Segoe UI", 8),
            bg=self.bg_color,
            fg="#666",
        )
        info_label.pack()

        # Bind hover effects
        self.random_btn.bind(
            "<Enter>", lambda e: self.on_button_hover(self.random_btn, True)
        )
        self.random_btn.bind(
            "<Leave>", lambda e: self.on_button_hover(self.random_btn, False)
        )

    def on_button_hover(self, button, entering):
        if button["state"] != tk.DISABLED:
            if entering:
                button.configure(bg=self.button_hover)
            else:
                button.configure(bg=self.button_color)

    def get_random_image(self):
        # Check credentials
        if self.username == "YOUR_USERNAME" or self.api_key == "YOUR_API_KEY":
            messagebox.showerror(
                "Configuration Error",
                "Please set your Danbooru username and API key in the code.\n\n"
                "Edit the following lines:\n"
                "self.username = 'YOUR_USERNAME'\n"
                "self.api_key = 'YOUR_API_KEY'",
            )
            return

        self.status_label.config(text="Fetching image...")
        self.random_btn.config(state=tk.DISABLED)

        # Run in thread to avoid blocking GUI
        thread = threading.Thread(target=self.fetch_image_thread)
        thread.daemon = True
        thread.start()

    def fetch_image_thread(self):
        try:
            # If cache is empty, fetch new posts
            if not self.posts_cache:
                url = "https://danbooru.donmai.us/posts.json"
                params = {
                    "tags": "saya_no_uta",
                    "limit": 1000,  # Get multiple posts to cache
                    "random": "true",
                }
                auth = (self.username, self.api_key)

                response = requests.get(url, params=params, auth=auth, timeout=10)
                response.raise_for_status()
                posts = response.json()
                # Filter posts that have file_url
                self.posts_cache = [p for p in posts if p.get("file_url")]

                if not self.posts_cache:
                    self.root.after(
                        0,
                        lambda: self.show_error(
                            "No images found with the specified tag."
                        ),
                    )
                    return

            # Get random post from cache
            self.current_post = random.choice(self.posts_cache)
            image_url = self.current_post["file_url"]

            json_str = json.dumps(self.current_post)
            print_json(json_str)
            print(
                f"{'\033[35m'}************************************************************************************************************"
            )

            # Download image
            image_response = requests.get(image_url, timeout=15)
            image_response.raise_for_status()

            self.current_image_data = image_response.content
            self.current_image_url = image_url

            # Display image
            self.root.after(0, self.display_image)

        except requests.exceptions.RequestException as e:
            self.root.after(0, lambda e=e: self.show_error(f"Network error: {str(e)}"))
        except Exception as e:
            self.root.after(0, lambda e=e: self.show_error(f"Error: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.random_btn.config(state=tk.NORMAL))

    def format_file_size(self, size_bytes):
        """Convert bytes to KB or MB with appropriate formatting"""
        size_kb = size_bytes / 1024

        if size_kb >= 1000:
            # Convert to MB
            size_mb = size_kb / 1024
            if size_mb < 10:
                return f"{size_mb:.1f} MB"
            else:
                return f"{size_mb:.0f} MB"
        else:
            # Keep as KB
            if size_kb < 10:
                return f"{size_kb:.1f} KB"
            else:
                return f"{size_kb:.0f} KB"

    def format_tags(self, tag_string, max_length=100):
        """Format tags for display, truncating if too long"""
        if not tag_string:
            return "No tags"

        # Split tags and clean them
        tags = [tag.strip() for tag in tag_string.split() if tag.strip()]

        if not tags:
            return "No tags"

        # Join tags with commas
        formatted_tags = ", ".join(tags)

        # Truncate if too long
        if len(formatted_tags) > max_length:
            formatted_tags = formatted_tags[: max_length - 3] + "..."

        return formatted_tags

    def display_image(self):
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(self.current_image_data))

            # Calculate scaling to fit in window
            max_width = self.image_label.winfo_width() - 10
            max_height = self.image_label.winfo_height() - 10

            if max_width <= 1 or max_height <= 1:
                max_width = 860
                max_height = 450

            # Calculate aspect ratio
            img_width, img_height = image.size
            aspect = img_width / img_height

            if img_width > max_width or img_height > max_height:
                if aspect > max_width / max_height:
                    new_width = max_width
                    new_height = int(max_width / aspect)
                else:
                    new_height = max_height
                    new_width = int(max_height * aspect)

                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)

            # Update label
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo  # Keep reference

            # Enable download button
            self.download_btn.config(
                state=tk.NORMAL, bg=self.button_color, fg=self.fg_color, cursor="hand2"
            )
            self.download_btn.bind(
                "<Enter>", lambda e: self.on_button_hover(self.download_btn, True)
            )
            self.download_btn.bind(
                "<Leave>", lambda e: self.on_button_hover(self.download_btn, False)
            )

            # Prepare status information
            post_id = self.current_post.get("id", "Unknown")
            dimensions = f"{img_width}×{img_height}"

            # Get file size in KB
            file_size_bytes = len(self.current_image_data)
            file_size_formatted = self.format_file_size(file_size_bytes)

            # Get and format tags
            tag_string = self.current_post.get(
                "tag_string_general", ""
            ) or self.current_post.get("tag_string", "")
            formatted_tags = self.format_tags(tag_string, max_length=150)

            # Update status with all information
            status_text = f"Image loaded • ID: {post_id} • Size: {dimensions} ({file_size_formatted})\nTags: {formatted_tags}"
            self.status_label.config(text=status_text)

        except Exception as e:
            self.show_error(f"Failed to display image: {str(e)}")

    def show_full_resolution(self, event=None):
        if not self.current_image_data:
            return

        try:
            # Create new window for full resolution
            if self.full_res_window and self.full_res_window.winfo_exists():
                self.full_res_window.destroy()

            self.full_res_window = tk.Toplevel(self.root)
            self.full_res_window.title("Full Resolution View")
            self.full_res_window.configure(bg=self.bg_color)

            # Get screen dimensions
            screen_width = self.full_res_window.winfo_screenwidth()
            screen_height = self.full_res_window.winfo_screenheight()

            # Open original image
            image = Image.open(io.BytesIO(self.current_image_data))
            img_width, img_height = image.size

            # Scale if larger than screen
            max_width = int(screen_width * 0.9)
            max_height = int(screen_height * 0.9)

            if img_width > max_width or img_height > max_height:
                aspect = img_width / img_height
                if aspect > max_width / max_height:
                    new_width = max_width
                    new_height = int(max_width / aspect)
                else:
                    new_height = max_height
                    new_width = int(max_height * aspect)

                window_width = new_width
                window_height = new_height
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                window_width = img_width
                window_height = img_height

            # Center window
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            self.full_res_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            # Display image
            photo = ImageTk.PhotoImage(image)
            label = tk.Label(self.full_res_window, image=photo, bg=self.bg_color)
            label.image = photo  # Keep reference
            label.pack()

            # Close on click
            label.bind("<Button-1>", lambda e: self.full_res_window.destroy())

        except Exception as e:
            self.show_error(f"Failed to show full resolution: {str(e)}")

    def download_image(self):
        if not self.current_image_data or not self.current_image_url:
            return

        try:
            # Get filename from URL
            parsed_url = urlparse(self.current_image_url)
            filename = os.path.basename(parsed_url.path)

            if not filename:
                filename = (
                    f"danbooru_image_{self.current_post.get('id', 'unknown')}.jpg"
                )

            # Save to Downloads folder
            filepath = self.downloads_path / filename

            # Check if file exists
            if filepath.exists():
                response = messagebox.askyesno(
                    "File Exists",
                    f"'{filename}' already exists.\nDo you want to overwrite it?",
                )
                if not response:
                    return

            # Save file
            with open(filepath, "wb") as f:
                f.write(self.current_image_data)

            self.status_label.config(text=f"Downloaded: {filename}")
            messagebox.showinfo("Download Complete", f"Image saved to:\n{filepath}")

        except Exception as e:
            self.show_error(f"Failed to download: {str(e)}")

    def show_error(self, message):
        self.status_label.config(text=f"Error: {message}")
        messagebox.showerror("Error", message)


def main():
    root = tk.Tk()
    app = DanbooruViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
