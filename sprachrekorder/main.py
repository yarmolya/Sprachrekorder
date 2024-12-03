import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, simpledialog, messagebox
import json
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from audio_filters import apply_filter
from pydub.playback import play
from pydub import AudioSegment
from playsound import playsound #switching from pydub to playsound due to access issues
from playback_visualization import AudioPlotter, get_short_path_name, toggle_recording, visualize_audio_live, save_audio_to_file
from ttkthemes import ThemedTk



class VoiceModifierApp:
    CUSTOM_FILTERS_FILE = "custom_filters.json"
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Recorder and Modifier")
        self.root.geometry("800x600")

        # Set modern theme for ttk widgets
        root = ThemedTk(theme="radiance")


        # Initialize variables
        self.audio_file = None
        self.modified_audio_file = os.path.join(os.getcwd(), "modified_audio.wav")
        self.custom_filters = self.load_custom_filters()

        # Add the close confirmation
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Create the main frames
        self.left_frame = ttk.Frame(self.root, style="Custom.TFrame", width=200, relief="ridge", padding=(10, 10))
        self.right_frame = ttk.Frame(self.root, style="Custom.TFrame", relief="ridge", padding=(10, 10))

        # Pack the frames side by side
        self.left_frame.pack(side="left", fill="y", padx=10, pady=10)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Initialize AudioPlotter and embed it in the right frame
        self.audio_plotter = AudioPlotter(parent_frame=self.right_frame, root=root)

        # Add buttons to the left frame
        self.create_widgets()


    def create_widgets(self):
        # File Selection Section
        self.select_file_button = ttk.Button(self.left_frame, text="Select Audio File", command=self.select_audio_file)
        self.select_file_button.pack(side="top", pady=10)

        # Recording Section
        record_button = ttk.Button(self.left_frame, text="Start Recording", command=lambda: toggle_recording(self.audio_plotter, record_button))
        record_button.pack(side="top", pady=10)

        # Filter Selection
        self.filter_var = tk.StringVar(self.root)
        self.filter_var.set("Select Filter")  # Default option

        
        self.filter_menu = ttk.OptionMenu(
            self.left_frame,
            self.filter_var,
            "Select Filter",
            "Robot",
            "Echo",
            "High Pitch",
            "Reverb",
            "Bass Boost",
            *self.custom_filters.keys(),
            "Custom",
            command=self.on_filter_change
        )
        self.filter_menu.pack(side="top", pady=10)
        # Custom Filter Parameters (Initially Hidden)
        self.custom_frame = ttk.Frame(self.left_frame)

        # Speed Slider
        self.slider1_label = ttk.Label(self.custom_frame, text="Speed:")
        self.slider1_label.pack(side="top")
        self.slider1 = ttk.Scale(self.custom_frame, from_=0, to=100, orient='horizontal')
        self.slider1.pack()

        # Volume Slider
        self.slider2_label = ttk.Label(self.custom_frame, text="Volume:")
        self.slider2_label.pack(side="top")
        self.slider2 = ttk.Scale(self.custom_frame, from_=0, to=100, orient='horizontal')
        self.slider2.pack()

        # Reverse Option using OptionMenu
        self.reverse_label = ttk.Label(self.custom_frame, text="Reverse:")
        self.reverse_label.pack(side="top")
        self.reverse_var = tk.StringVar(value="No")  # Default to "No"
        self.reverse_menu = ttk.OptionMenu(
            self.custom_frame, self.reverse_var, "Yes", "No"
        )
        self.reverse_menu.pack(side="top")

        # Save Custom Filter Button (Initially Hidden)
        self.save_custom_button = ttk.Button(self.left_frame, text="Save Current Custom Filter", command=self.save_current_custom_filter)
        self.delete_custom_button = ttk.Button(self.left_frame, text="Delete Selected Custom Filter", command=self.delete_selected_custom_filter)
        
        # Apply Filter Button
        self.apply_filter_button = ttk.Button(self.left_frame, text="Apply Filter", command=self.apply_filter)
        self.apply_filter_button.pack(side="top", pady=10)

        # Play Audio Button
        self.play_button = ttk.Button(self.left_frame, text="Play Modified Audio", command=self.play_audio)
        self.play_button.pack(side="top", pady=10)

        # Save Button
        self.save_button = ttk.Button(self.left_frame, text="Save Audio", command=self.save_audio)
        self.save_button.pack(side="top", pady=10)

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
        """Handle selecting an audio file and visualizing it."""
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio Files", "*.wav *.mp3 *.ogg")]
        )
        if file_path:
            self.audio_file = os.path.normpath(file_path)
            print(f"Selected file: {self.audio_file}")
            playsound(self.audio_file)
            
            # Load the audio file
        
            from scipy.io.wavfile import read as wavfile_read
            try:
                samplerate, data = wavfile_read(self.audio_file)
                if data.ndim > 1:  # If stereo, use only one channel
                    data = data[:, 0]
                
                # Check the maximum amplitude before normalization
                max_amplitude_before = np.max(np.abs(data))
                print(f"Max amplitude before normalization: {max_amplitude_before}")

                # Normalize the audio data to [-1, 1]
                data = data / np.max(np.abs(data))

                # Generate time values for the x-axis
                time_values = np.linspace(0, len(data) / samplerate, num=len(data))

                # Update the plot directly
                self.audio_plotter.ax.clear()  # Clear the previous plot
                self.audio_plotter.ax.plot(time_values, data, color='g')  # Plot the waveform
                
                # Adjust the scale of the axes
                self.audio_plotter.ax.set_xlim(0, len(data) / samplerate)  # Set x-axis to match duration
                self.audio_plotter.ax.set_ylim(-1.5, 1.5)  # Set y-axis to show full amplitude
                
                # Update the canvas
                self.audio_plotter.canvas.draw_idle()

            except Exception as e:
                print(f"Error loading audio file: {e}")

    def start_recording(self):
        visualize_audio_live(self.audio_plotter)

    def apply_filter(self):
        if not self.audio_file:
            print("Recording new audio file...")
            self.audio_plotter.stop_recording()

            print(f"Audio file saved at: {self.audio_file}")


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
            short_path = get_short_path_name(self.modified_audio_file.replace("\\", "/"))
            playsound(short_path)
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
