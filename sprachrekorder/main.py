import os
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import json
from audio_filters import apply_filter
from visualization import visualize_audio_live, save_audio_to_file
from pydub.playback import play
from pydub import AudioSegment
from playsound import playsound #switching from pydub to playsound due to access issues


class VoiceModifierApp:
    CUSTOM_FILTERS_FILE = "custom_filters.json"

    def __init__(self, root):
        self.root = root
        self.root.title("Voice Recorder and Modifier")

        # Initialize variables
        self.audio_file = None
        self.modified_audio_file = os.path.join(os.getcwd(), "modified_audio.wav")
        self.custom_filters = self.load_custom_filters()

        # GUI Layout
        self.create_widgets()

        # Add the close confirmation
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

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

        self.filter_menu = tk.OptionMenu(
            self.root,
            self.filter_var,
            "None",
            "Robot",
            "Echo",
            "High Pitch",
            "Reverb",
            "Bass Boost",
            *self.custom_filters.keys(),
            "Custom",
            command=self.on_filter_change
        )
        self.filter_menu.pack(pady=10)

        # Custom Filter Parameters (Initially Hidden)
        self.custom_frame = tk.Frame(self.root)

        # Speed Slider
        self.slider1_label = tk.Label(self.custom_frame, text="Speed:")
        self.slider1_label.pack()
        self.slider1 = tk.Scale(self.custom_frame, from_=0, to=100, orient='horizontal')
        self.slider1.pack()

        # Volume Slider
        self.slider2_label = tk.Label(self.custom_frame, text="Volume:")
        self.slider2_label.pack()
        self.slider2 = tk.Scale(self.custom_frame, from_=0, to=100, orient='horizontal')
        self.slider2.pack()

        # Reverse Option using OptionMenu
        self.reverse_label = tk.Label(self.custom_frame, text="Reverse:")
        self.reverse_label.pack()
        self.reverse_var = tk.StringVar(value="No")  # Default to "No"
        self.reverse_menu = tk.OptionMenu(
            self.custom_frame, self.reverse_var, "Yes", "No"
        )
        self.reverse_menu.pack()

        # Save Custom Filter Button (Initially Hidden)
        self.save_custom_button = tk.Button(self.root, text="Save Current Custom Filter", command=self.save_current_custom_filter)
        self.delete_custom_button = tk.Button(self.root, text="Delete Selected Custom Filter", command=self.delete_selected_custom_filter)
        
        # Apply Filter Button
        self.apply_filter_button = tk.Button(self.root, text="Apply Filter", command=self.apply_filter)
        self.apply_filter_button.pack(pady=10)

        # Play Audio Button
        self.play_button = tk.Button(self.root, text="Play Modified Audio", command=self.play_audio)
        self.play_button.pack(pady=10)

        # Save Button
        self.save_button = tk.Button(self.root, text="Save Audio", command=self.save_audio)
        self.save_button.pack(pady=10)

    def on_filter_change(self, selected_filter):
        """Show or hide custom filter settings based on the selected filter."""
        if selected_filter == "Custom" or selected_filter in self.custom_filters:
            self.custom_frame.pack(pady=10)
            self.save_custom_button.pack(pady=10)
            self.delete_custom_button.pack(pady=10)  # Show delete button
            if selected_filter in self.custom_filters:
                # Load parameters of the selected custom filter
                params = self.custom_filters[selected_filter]
                self.slider1.set(params[0])
                self.slider2.set(params[1])
                self.reverse_var.set(params[2])
        else:
            # Hide custom filter controls if not applicable
            self.custom_frame.pack_forget()
            self.save_custom_button.pack_forget()
            self.delete_custom_button.pack_forget()

    def select_audio_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio Files", "*.wav *.mp3 *.ogg")]
        )
        if file_path:
            """handling inconsistencies between mac and windows os"""
            self.audio_file = os.path.normpath(file_path) 
            print(f"Selected file: {self.audio_file}")

    def start_recording(self):
        visualize_audio_live()
    
    def apply_filter(self):
        if not self.audio_file:
            print("Recording new audio file...")
            self.audio_file = save_audio_to_file()

        if not self.audio_file:
            print("Recording failed or was cancelled.")
            return

        selected_filter = self.filter_var.get()

        if selected_filter == "Custom" or selected_filter in self.custom_filters:
            param1 = self.slider1.get()
            param2 = self.slider2.get()
            reverse = 1 if self.reverse_var.get() == "Yes" else 0  # Use the dropdown value
            print(f"Applying custom filter with parameters: {param1}, {param2}, {reverse}")
            apply_filter(self.audio_file, self.modified_audio_file, "Custom", param1, param2, reverse)
        elif selected_filter != "None":
            print(f"Applying '{selected_filter}' filter...")
            apply_filter(self.audio_file, self.modified_audio_file, selected_filter)
        else:
            print("No filter selected.")

    def save_current_custom_filter(self):
        """Save the current custom filter with a user-defined name."""
        filter_name = simpledialog.askstring("Save Custom Filter", "Enter a name for your custom filter:")
        if not filter_name:
            print("Custom filter save canceled.")
            return

        if filter_name in self.custom_filters:
            messagebox.showerror("Error", "A custom filter with this name already exists.")
            return

        params = [self.slider1.get(), self.slider2.get(), self.reverse_var.get()]
        self.custom_filters[filter_name] = params
        self.save_custom_filters()
        self.update_filter_menu()
        print(f"Custom filter '{filter_name}' saved.")

    def update_filter_menu(self):
        """Update the filter selection dropdown to include new custom filters."""
        menu = self.filter_menu["menu"]
        menu.delete(0, "end")

        # Default filters
        filters = ["None", "Robot", "Echo", "High Pitch", "Reverb", "Bass Boost"]
        for filter_name in filters + list(self.custom_filters.keys()) + ["Custom"]:
            menu.add_command(label=filter_name, command=lambda f=filter_name: self.filter_var.set(f))

    def load_custom_filters(self):
        """Load saved custom filters from a JSON file."""
        if os.path.exists(self.CUSTOM_FILTERS_FILE):
            with open(self.CUSTOM_FILTERS_FILE, "r") as file:
                return json.load(file)
        return {}

    def save_custom_filters(self):
        """Save custom filters to a JSON file."""
        with open(self.CUSTOM_FILTERS_FILE, "w") as file:
            json.dump(self.custom_filters, file)

    def play_audio(self):
        if not self.modified_audio_file:
            print("No modified audio to play.")
            return

        try:
            self.modified_audio_file = self.modified_audio_file.replace("\\", "/")
            playsound(self.modified_audio_file)
            print("Playing modified audio...")
        except Exception as e:
            print(f"An error occurred while trying to play the audio: {e}")


    def save_audio(self):
        if not self.modified_audio_file:
            print("No modified audio to save.")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".wav",
                                                 filetypes=[("WAV files", "*.wav")],
                                                 title="Save Modified Audio As")
        if save_path:
            from shutil import copyfile
            copyfile(self.modified_audio_file, save_path)
            print(f"Modified audio saved at {save_path}.")
            
    def delete_selected_custom_filter(self):
        """Delete the currently selected custom filter."""
        selected_filter = self.filter_var.get()

        if selected_filter in self.custom_filters:
            confirm = messagebox.askyesno(
                "Confirm Deletion",
                f"Are you sure you want to delete the custom filter '{selected_filter}'?"
            )
            if confirm:
                del self.custom_filters[selected_filter]
                self.save_custom_filters()  # Save updated filters
                self.update_filter_menu()  # Refresh menu
                self.filter_var.set("None")  # Reset to 'None'
                self.custom_frame.pack_forget()  # Hide sliders and buttons
                self.save_custom_button.pack_forget()
                self.delete_custom_button.pack_forget()
                print(f"Custom filter '{selected_filter}' deleted.")
        else:
            messagebox.showinfo("Info", "Cannot delete default filters or 'None'.")

    def on_close(self):
        """Confirmation dialog before closing the app."""
        confirm = messagebox.askyesno(
            "Exit",
            "Are you sure you want to close the application?"
        )
        if confirm:
            self.root.destroy()  # Close the application
        else:
            print("Close action cancelled.")

# Entry Point
if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceModifierApp(root)
    root.mainloop()
