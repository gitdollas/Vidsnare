import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import threading
import subprocess
import queue
import os
import json
import shutil  # For checking ffmpeg presence
import platform # For opening folder cross-platform

# --- Configuration ---
CONFIG_FILE = "vidsnare_config.json"
DEFAULT_DOWNLOAD_FOLDER_NAME = "VidSnareDownloads" # Folder name in user's home directory
# If yt-dlp is not in PATH, set the full path here:
YT_DLP_COMMAND = "yt-dlp" # Assumes yt-dlp is in PATH

# --- Main Application Class ---
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VidSnare - yt-dlp Downloader")
        self.geometry("650x600") # Slightly wider for open folder button

        # --- Internal State ---
        self.current_process = None
        self.cancel_requested = threading.Event()
        self.ui_queue = queue.Queue()
        self.settings = {}
        self.ffmpeg_available = False
        self.default_download_dir = self.setup_default_download_dir() # Setup/get default dir path

        # --- Load Settings & Check Dependencies ---
        self.load_settings() # Now uses self.default_download_dir if no setting saved
        self.check_ffmpeg()

        # --- Create Widgets ---
        self.create_widgets()

        # --- Start UI Queue Polling ---
        self.after(100, self.process_ui_queue)

        # --- Handle Window Closing ---
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_default_download_dir(self):
        """Creates and returns the path to the default download directory."""
        home_dir = os.path.expanduser("~") # Get user's home directory
        download_dir = os.path.join(home_dir, DEFAULT_DOWNLOAD_FOLDER_NAME)
        try:
            # Create the directory if it doesn't exist
            os.makedirs(download_dir, exist_ok=True)
            return download_dir
        except OSError as e:
            print(f"[Error] Could not create default download directory '{download_dir}': {e}")
            # Fallback to current working directory if creation fails
            return os.getcwd()

    def check_ffmpeg(self):
        """Checks if ffmpeg executable is found in PATH."""
        self.ffmpeg_available = shutil.which("ffmpeg") is not None
        if not self.ffmpeg_available:
            print("[Warning] ffmpeg not found in PATH. Audio extraction/conversion might fail.")

    def load_settings(self):
        """Loads settings from the JSON config file."""
        try:
            with open(CONFIG_FILE, 'r') as f:
                self.settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.settings = {} # Start fresh if file missing or invalid
            print(f"[Info] Config file '{CONFIG_FILE}' not found or invalid. Using defaults.")
        # Output directory defaults to the dedicated folder if not found in settings
        if "output_directory" not in self.settings:
             self.settings["output_directory"] = self.default_download_dir


    def save_settings(self):
        """Saves current settings to the JSON config file."""
        self.settings["output_directory"] = self.output_path_var.get()
        self.settings["last_format"] = self.format_var.get()
        self.settings["download_playlist"] = self.playlist_var.get()
        self.settings["number_playlist"] = self.numbering_var.get()

        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            print(f"[Error] Could not save settings to '{CONFIG_FILE}': {e}")

    def on_closing(self):
        """Handles window close event, saves settings."""
        if self.current_process:
             self.cancel_download()
        self.save_settings()
        self.destroy()

    def create_widgets(self):
        """Creates and lays out all the UI widgets."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1) # Adjusted row for output expansion

        # --- URL Input ---
        row_idx = 0
        self.url_frame = ctk.CTkFrame(self)
        self.url_frame.grid(row=row_idx, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.url_frame.grid_columnconfigure(1, weight=1)

        self.url_label = ctk.CTkLabel(self.url_frame, text="Video URL:")
        self.url_label.grid(row=0, column=0, padx=5, pady=5)

        self.url_entry = ctk.CTkEntry(self.url_frame, placeholder_text="Enter video URL here")
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.paste_button = ctk.CTkButton(self.url_frame, text="Paste", width=60, command=self.paste_from_clipboard)
        self.paste_button.grid(row=0, column=2, padx=5, pady=5)

        # --- Format Selection ---
        row_idx += 1
        self.format_frame = ctk.CTkFrame(self)
        self.format_frame.grid(row=row_idx, column=0, padx=10, pady=5, sticky="ew")
        #...(rest of format selection widgets unchanged)...
        self.format_label = ctk.CTkLabel(self.format_frame, text="Format:")
        self.format_label.pack(side=tk.LEFT, padx=(5, 15), pady=5)
        self.format_var = tk.StringVar(value=self.settings.get("last_format", "best_video_audio"))
        self.radio_video_audio = ctk.CTkRadioButton(self.format_frame, text="Video+Audio (Best)", variable=self.format_var, value="best_video_audio")
        self.radio_video_audio.pack(side=tk.LEFT, padx=5, pady=5)
        self.radio_audio_only = ctk.CTkRadioButton(self.format_frame, text="Audio Only (mp3)", variable=self.format_var, value="audio_mp3")
        self.radio_audio_only.pack(side=tk.LEFT, padx=5, pady=5)
        if not self.ffmpeg_available:
            self.radio_audio_only.configure(state="disabled")
            self.ffmpeg_warning_label = ctk.CTkLabel(self.format_frame, text="(ffmpeg needed)", text_color="gray")
            self.ffmpeg_warning_label.pack(side=tk.LEFT, padx=(0, 5), pady=5)

        # --- Playlist Options ---
        row_idx += 1
        self.playlist_frame = ctk.CTkFrame(self)
        self.playlist_frame.grid(row=row_idx, column=0, padx=10, pady=5, sticky="ew")
        #...(rest of playlist widgets unchanged)...
        self.playlist_label = ctk.CTkLabel(self.playlist_frame, text="Playlist:")
        self.playlist_label.pack(side=tk.LEFT, padx=(5, 15), pady=5)
        self.playlist_var = tk.BooleanVar(value=self.settings.get("download_playlist", True))
        self.playlist_checkbox = ctk.CTkCheckBox(self.playlist_frame, text="Download Full Playlist", variable=self.playlist_var, onvalue=True, offvalue=False)
        self.playlist_checkbox.pack(side=tk.LEFT, padx=5, pady=5)
        self.numbering_var = tk.BooleanVar(value=self.settings.get("number_playlist", False))
        self.numbering_checkbox = ctk.CTkCheckBox(self.playlist_frame, text="Number Items", variable=self.numbering_var, onvalue=True, offvalue=False)
        self.numbering_checkbox.pack(side=tk.LEFT, padx=5, pady=5)

        # --- Output Directory ---
        row_idx += 1
        self.output_frame = ctk.CTkFrame(self)
        self.output_frame.grid(row=row_idx, column=0, padx=10, pady=5, sticky="ew")
        self.output_frame.grid_columnconfigure(1, weight=1) # Entry expands

        self.output_label = ctk.CTkLabel(self.output_frame, text="Save To:")
        self.output_label.grid(row=0, column=0, padx=5, pady=5)

        # Use saved path or the app's default directory
        saved_output_dir = self.settings.get("output_directory", self.default_download_dir)
        self.output_path_var = tk.StringVar(value=saved_output_dir)

        self.output_entry = ctk.CTkEntry(self.output_frame, textvariable=self.output_path_var)
        self.output_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.browse_button = ctk.CTkButton(self.output_frame, text="Browse...", width=90, command=self.browse_directory)
        self.browse_button.grid(row=0, column=2, padx=(5,0), pady=5) # Adjusted padding

        # --- NEW: Open Folder Button ---
        self.open_folder_button = ctk.CTkButton(self.output_frame, text="Open", width=60, command=self.open_output_folder)
        self.open_folder_button.grid(row=0, column=3, padx=(5,5), pady=5) # Added to the right

        # --- Action Buttons ---
        row_idx += 1
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.grid(row=row_idx, column=0, padx=10, pady=5)
        #...(rest of action buttons unchanged)...
        self.download_button = ctk.CTkButton(self.button_frame, text="Download", command=self.start_download_thread)
        self.download_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button = ctk.CTkButton(self.button_frame, text="Cancel", command=self.cancel_download, state="disabled")
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # --- Progress Display ---
        row_idx += 1
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.grid(row=row_idx, column=0, padx=10, pady=(0, 5), sticky="ew")
        self.progress_frame.grid_columnconfigure(0, weight=1)
        #...(rest of progress widgets unchanged)...
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Status: Idle")
        self.progress_label.grid(row=0, column=0, padx=5, sticky="w")
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="ew")

        # --- Output Text Area ---
        row_idx += 1
        self.output_text = ctk.CTkTextbox(self, height=150)
        self.output_text.grid(row=row_idx, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.output_text.configure(state="disabled")

    def paste_from_clipboard(self):
        """Gets text from clipboard and inserts it into the URL entry."""
        try:
            clipboard_content = self.clipboard_get()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, clipboard_content)
        except tk.TclError:
            self.update_status("Clipboard is empty or does not contain text.", error=True)

    def browse_directory(self):
        """Opens a dialog to select the output directory."""
        dir_path = filedialog.askdirectory(initialdir=self.output_path_var.get(), title="Select Download Folder")
        if dir_path:
            self.output_path_var.set(dir_path)

    def open_output_folder(self):
        """Opens the currently selected output directory in the system file explorer."""
        folder_path = self.output_path_var.get()
        if not os.path.isdir(folder_path):
            self.update_status(f"Error: Directory not found: {folder_path}", error=True)
            return

        try:
            current_os = platform.system()
            if current_os == "Windows":
                os.startfile(folder_path) # Preferred way on Windows
            elif current_os == "Darwin": # macOS
                subprocess.run(["open", folder_path], check=True)
            else: # Linux and other Unix-like
                subprocess.run(["xdg-open", folder_path], check=True)
            self.update_status("Opened output folder.") # Feedback
        except FileNotFoundError:
            # Handle case where 'open' or 'xdg-open' might not be available
            self.update_status(f"Error: Could not find command to open folder on this OS.", error=True)
        except subprocess.CalledProcessError as e:
            # Handle errors from the subprocess command itself
             self.update_status(f"Error opening folder: {e}", error=True)
        except Exception as e:
            # Catch any other unexpected errors
             self.update_status(f"An unexpected error occurred opening the folder: {e}", error=True)


    def start_download_thread(self):
        """Validates input and starts the download in a separate thread."""
        video_url = self.url_entry.get().strip()
        output_dir = self.output_path_var.get()
        selected_format = self.format_var.get()
        download_playlist = self.playlist_var.get()
        number_items = self.numbering_var.get()

        if not video_url:
            self.update_status("Please enter a video URL.", error=True)
            return

        # --- Ensure Output Directory Exists ---
        try:
            # Attempt to create if it doesn't exist (e.g., user typed a new path)
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            self.update_status(f"Invalid output directory: {e}", error=True)
            return

        # --- Update UI State ---
        self.update_status("Starting...")
        self.download_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.progress_bar.set(0)
        self.clear_output()
        self.append_output(f"URL: {video_url}")
        self.append_output(f"Format: {selected_format}")
        self.append_output(f"Playlist Mode: {'Full Playlist' if download_playlist else 'Single Video'}")
        if download_playlist:
             self.append_output(f"Numbering: {'Enabled' if number_items else 'Disabled'}")
        self.append_output(f"Saving to: {output_dir}")
        self.append_output("-" * 20)

        self.cancel_requested.clear()

        download_thread = threading.Thread(
            target=self.run_yt_dlp,
            args=(video_url, output_dir, selected_format, download_playlist, number_items),
            daemon=True
        )
        download_thread.start()

    def cancel_download(self):
        """Requests cancellation of the current download."""
        # ...(cancel_download logic unchanged)...
        if self.current_process and self.current_process.poll() is None:
            self.update_status("Cancelling...")
            self.cancel_button.configure(state="disabled")
            self.cancel_requested.set()
            try:
                self.current_process.terminate()
                self.queue_ui_update(self.append_output, "[Info] Cancellation requested. Terminating process...")
            except ProcessLookupError:
                self.queue_ui_update(self.append_output, "[Warning] Process already finished before termination.")
            except Exception as e:
                self.queue_ui_update(self.append_output, f"[Error] Could not terminate process: {e}")
        else:
             print("[Debug] No active process to cancel or process already finished.")
             self.cancel_button.configure(state="disabled")

    def run_yt_dlp(self, url, output_dir, format_option, download_playlist, number_items):
        """Runs the yt-dlp command in a subprocess and handles output."""
        # ...(run_yt_dlp logic mostly unchanged, using the passed args)...
        try:
            command = [YT_DLP_COMMAND]
            # --- Add Format Options ---
            if format_option == "best_video_audio":
                command.extend(['-f', 'bv*+ba/b'])
            elif format_option == "audio_mp3":
                if not self.ffmpeg_available:
                     raise RuntimeError("Audio extraction selected, but ffmpeg is not available.")
                command.extend(['-x', '--audio-format', 'mp3', '-f', 'ba'])
            # --- Handle Playlist Options ---
            if not download_playlist:
                command.extend(['--no-playlist'])
                output_template_str = '%(title)s [%(id)s].%(ext)s'
            else:
                if number_items:
                    output_template_str = '%(playlist_index)s - %(title)s [%(id)s].%(ext)s'
                else:
                    output_template_str = '%(title)s [%(id)s].%(ext)s'
            # --- Add Output Path ---
            output_template = os.path.join(output_dir, output_template_str)
            command.extend(['-o', output_template])
            # --- Add Progress & Other Flags ---
            command.extend(['--progress', '--newline', '--no-colors', '--no-continue', '--ignore-errors', url])

            self.queue_ui_update(self.append_output, f"Executing: {' '.join(command)}")
            # --- Execute ---
            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            self.current_process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace',
                bufsize=1, creationflags=creation_flags
            )
            # ...(Rest of output reading, parsing, and finishing logic unchanged)...
            last_percent = 0.0
            download_started = False
            current_item_str = ""
            while True:
                if self.cancel_requested.is_set():
                    self.queue_ui_update(self.update_status, "Download Cancelled.")
                    break
                line = self.current_process.stdout.readline()
                if not line and self.current_process.poll() is not None: break
                if line:
                    line = line.strip()
                    self.queue_ui_update(self.append_output, line)
                    if download_playlist and line.startswith('[download] Downloading item '):
                         parts = line.split()
                         try:
                              item_index = parts.index('item') + 1
                              current_item_str = f" (Item {parts[item_index]})"
                         except (ValueError, IndexError): current_item_str = " (Playlist)"
                    if '[download]' in line and '%' in line:
                        status_prefix = "Downloading" + current_item_str
                        if not download_started:
                            self.queue_ui_update(self.update_status, status_prefix + "...")
                            download_started = True
                        try:
                            parts = line.split()
                            for part in parts:
                                if part.endswith('%'):
                                    percent_str = part.strip('%'); percent = float(percent_str) / 100.0
                                    self.queue_ui_update(self.update_progress, percent)
                                    last_percent = percent; break
                        except ValueError: pass
                    elif '[ExtractAudio]' in line or '[Merger]' in line:
                         self.queue_ui_update(self.update_status, "Processing" + current_item_str + "...")
                         download_started = True
            if not self.cancel_requested.is_set():
                self.current_process.wait(); return_code = self.current_process.returncode; self.current_process = None
                final_status = "Playlist download " if download_playlist else "Download "
                if return_code == 0:
                    self.queue_ui_update(self.update_progress, 1.0); self.queue_ui_update(self.update_status, final_status + "finished successfully!")
                else:
                    self.queue_ui_update(self.update_progress, last_percent); self.queue_ui_update(self.update_status, f"{final_status}failed (Code: {return_code})", error=True)
                    self.queue_ui_update(self.append_output, f"Error Code: {return_code}. Check output above.")
            else: self.current_process = None

        except FileNotFoundError: # ...(Error handling mostly unchanged)...
             self.queue_ui_update(self.update_status, f"Error: '{YT_DLP_COMMAND}' not found.", error=True)
             self.queue_ui_update(self.append_output, f"Failed command: {' '.join(command if 'command' in locals() else ['yt-dlp', '...'])}")
        except RuntimeError as e:
             self.queue_ui_update(self.update_status, f"Error: {e}", error=True); self.queue_ui_update(self.append_output, f"Runtime Error: {e}")
        except Exception as e:
            error_msg = f"An unexpected error occurred: {e}"; status_msg = "An unexpected error occurred."; print(f"[Error] {error_msg}")
            if self.cancel_requested.is_set(): status_msg = "Cancelled during error."
            self.queue_ui_update(self.update_status, status_msg, error=True); self.queue_ui_update(self.append_output, f"Exception Type: {type(e).__name__}"); self.queue_ui_update(self.append_output, f"Exception Details: {str(e)}")
        finally: # ...(Cleanup unchanged)...
            self.current_process = None; self.cancel_requested.clear()
            self.queue_ui_update(lambda: self.download_button.configure(state="normal")); self.queue_ui_update(lambda: self.cancel_button.configure(state="disabled"))


    # --- Thread-Safe UI Update Methods (Unchanged) ---
    def queue_ui_update(self, func, *args): self.ui_queue.put((func, args))
    def process_ui_queue(self):
        try:
            while True:
                func, args = self.ui_queue.get_nowait()
                try: func(*args)
                except Exception as e: print(f"[UI Error] Failed executing {func.__name__}: {e}")
        except queue.Empty: pass
        finally: self.after(100, self.process_ui_queue)
    def update_status(self, message, error=False): color = "red" if error else "white"; self.progress_label.configure(text=f"Status: {message}", text_color=color)
    def update_progress(self, value): clamped_value = max(0.0, min(1.0, value)); self.progress_bar.set(clamped_value)
    def append_output(self, text): self.output_text.configure(state="normal"); self.output_text.insert(tk.END, text + "\n"); self.output_text.see(tk.END); self.output_text.configure(state="disabled")
    def clear_output(self): self.output_text.configure(state="normal"); self.output_text.delete("1.0", tk.END); self.output_text.configure(state="disabled")

# --- Main Execution ---
if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    app = App()
    app.mainloop()