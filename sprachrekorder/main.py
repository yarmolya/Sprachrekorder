import os
import tkinter as tk
from tkinter import filedialog
from audio_filters import apply_filter  # Custom utility functions
from visualization import visualize_audio_live  # Optional visualization functions
from visualization import save_audio_autom_to_file


class VoiceModifierApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Recorder and Modifier")

        # Initialize variables
        self.audio_file = None
        self.modified_audio_file = None
        self.modified_audio_file = "modified_audio.wav"

        # GUI Layout
        self.create_widgets()

    def create_widgets(self):
        # File Selection Section
        self.select_file_button = tk.Button(self.root, text="Select Audio File", command=self.select_audio_file)
        self.select_file_button.pack(pady=10)

        # Recording Section
        self.record_button = tk.Button(self.root, text="Start Recording", command=self.start_recording)
        self.record_button.pack(pady=10)

        # Filter Selection
        self.filter_label = tk.Label(self.root, text="Select Filter:")
        self.filter_label.pack()
        self.filter_var = tk.StringVar(self.root)
        self.filter_var.set("None")  # Default option
        self.filter_menu = tk.OptionMenu(self.root, self.filter_var, "None", "Robot", "Echo", "High Pitch", "Reverb", "Bass Boost")
        self.filter_menu.pack(pady=10)

        # Apply Filter Button
        self.apply_filter_button = tk.Button(self.root, text="Apply Filter", command=self.apply_filter)
        self.apply_filter_button.pack(pady=10)

        # Play Audio Button
        self.play_button = tk.Button(self.root, text="Play Modified Audio", command=self.play_audio)
        self.play_button.pack(pady=10)

        # Save Button
        self.save_button = tk.Button(self.root, text="Save Audio", command=self.save_audio)
        self.save_button.pack(pady=10)

    def select_audio_file(self):
        """Allows the user to select an existing audio file."""
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio Files", "*.wav *.mp3 *.ogg")]

        )
        if file_path:
            self.audio_file = file_path
            print(f"Selected file: {self.audio_file}")

    def start_recording(self):
        visualize_audio_live()

    def apply_filter(self):    
        if not self.audio_file:  # Ensure audio file path exists
            print("Recording new audio file...")
            self.audio_file = save_audio_autom_to_file()  # Save and retrieve new recording

        if not self.audio_file:  # Check if the recording was successful
            print("Recording failed or was cancelled.")
            return

        selected_filter = self.filter_var.get()  # Retrieve selected filter
        if not selected_filter or selected_filter == "None":
            print("No filter selected.")
            return

        temp_recording = self.audio_file  # Keep track of original recording
        self.modified_audio_file = "modified_audio.wav"

        print(f"Applying '{selected_filter}' filter...")
        apply_filter(self.audio_file, self.modified_audio_file, selected_filter)

        # Optionally delete the original recording to prevent duplication
        if temp_recording and temp_recording != "modified_audio.wav":
            print(f"Deleting temporary file: {temp_recording}")
            try:
                os.remove(temp_recording)
            except OSError as e:
                print(f"Error deleting file: {e}")

        
    def play_audio(self):
        """Plays the modified audio file."""
        if not self.modified_audio_file:
            print("No modified audio to play. Apply a filter first.")
            return
        from pydub.playback import play
        from pydub import AudioSegment

        audio = AudioSegment.from_file(self.modified_audio_file)
        print("Playing modified audio...")
        play(audio)

    def save_audio(self):
        """Saves the modified audio to a user-selected location."""
        if not self.modified_audio_file:
            print("No modified audio to save. Apply a filter first.")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".wav",
                                                 filetypes=[("WAV files", "*.wav")],
                                                 title="Save Modified Audio As")
        if save_path:
            from shutil import copyfile
            copyfile(self.modified_audio_file, save_path)
            print(f"Modified audio saved at {save_path}.")


# Entry Point
if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceModifierApp(root)
    root.mainloop()
