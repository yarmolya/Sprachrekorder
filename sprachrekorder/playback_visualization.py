import os
from tkinter import filedialog
from matplotlib.animation import FuncAnimation
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Thread, Event
import time
import queue as q
from scipy.io.wavfile import read as wavfile_read, write
from pydub import AudioSegment
from pydub.playback import play
import sounddevice as sd
from playsound import playsound
import ctypes

is_recording = False
recording_data = []  # Store recorded audio
samplerate = 44100
audio_queue = q.Queue()

# Visualization settings
device = 0  # Default input device
window = 1000  # Size of the visualization window in milliseconds
downsample = 1  # Downsample factor
channels = [1]  # List of audio channels
interval = 30  # Update interval in milliseconds
device_info = sd.query_devices(device, 'input')
samplerate = int(device_info['default_samplerate'])
length = int(window * samplerate / (1000 * downsample))


def get_short_path_name(long_path):
    """Convert a long path to its short path equivalent on Windows bc playsound is wack."""
    buffer = ctypes.create_unicode_buffer(260)  # MAX_PATH in Windows
    ctypes.windll.kernel32.GetShortPathNameW(long_path, buffer, 260)
    return buffer.value

def load_audio_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio Files", "*.wav *.mp3 *.ogg")]
        )
        if file_path:
            self.audio_file = os.path.normpath(file_path) 
            print(f"Selected file: {self.audio_file}")
            self.audio_plotter.play_audio_with_plot(file_path)
            samplerate, data = wavfile_read(file_path)
            if data.ndim > 1:  # If stereo, use only one channel
                data = data[:, 0]
                return data, samplerate
            
def save_audio_to_file():
        """Save the recorded audio data to a file and return the path."""
        global recording_data, samplerate  # Ensure these are properly defined
        
        if not recording_data:
            print("No audio data to save!")
            return None

        audio_array = np.concatenate(recording_data, axis=0)

        root = tk.Tk()
        root.withdraw()  # Hide the Tkinter GUI window
        output_path = filedialog.asksaveasfilename(defaultextension=".wav",
                                                    filetypes=[("WAV Files", "*.wav")])
        root.destroy()  # Close the Tkinter window

        if not output_path:
            print("Save operation cancelled by user.")
            return None

        try:
            write(output_path, samplerate, audio_array)  # Save the file
            print(f"Recording saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"Failed to save recording: {e}")
            return None
    
def toggle_recording(audio_plotter, button):
    """Toggle recording state and update the button text."""
    if audio_plotter.is_recording:
        audio_plotter.stop_recording()
        button.config(text="Start Recording")
    else:
        audio_plotter.start_recording()
        button.config(text="Stop Recording")


def visualize_audio_live():
    """Run the audio visualization and manage recording."""
    global is_recording
    is_recording = False

    # Settings for audio and plot
    chunk_size = 1024
    audio_buffer = np.zeros(chunk_size * 10)

class AudioPlotter:
    def __init__(self, parent_frame, root, samplerate=44100, chunk_size=1024):
        self.parent_frame = parent_frame
        self.root = root
        self.samplerate = samplerate
        self.chunk_size = chunk_size
        self.is_recording = False
        self.audio_buffer = np.zeros(self.chunk_size * 10)
        self.stream = None

        # Create the Matplotlib figure and embed it in the parent frame
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.ax.set_facecolor((0, 0, 0))  # Black background
        self.line, = self.ax.plot([], [], color='g')
        self.ax.set_ylim(-1, 1)
        self.ax.set_xlim(0, len(self.audio_buffer) / self.samplerate)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

    def audio_callback(self, indata, frames, time, status):
        """Callback to process audio data in real-time."""
        global recording_data

        if status:
            print(f"Stream status: streaming")

        # Update the audio buffer for visualization
        self.audio_buffer = np.roll(self.audio_buffer, -frames)
        self.audio_buffer[-frames:] = indata[:, 0]  # Use the first channel only

        # Append data for recording if enabled
        if self.is_recording:
            print(f"callback is called")
            recording_data.append(indata.copy())


    def update_plot(self):

        """Update the waveform plot with new audio data."""
        scale_factor = 20  # Increase this value to make the waveforms wider
        scaled_audio = self.audio_buffer * scale_factor  # Scale the amplitude of the audio data

        x = np.linspace(0, len(self.audio_buffer) / self.samplerate, len(self.audio_buffer))
        self.line.set_data(x, scaled_audio)

        # Adjust horizontal and vertical scales
        self.ax.set_xlim(0, len(self.audio_buffer) / self.samplerate)  # Time axis
        self.ax.set_ylim(-1, 1)  # Amplitude axis

        if recording_data:
            print(f"Recording data sample: {recording_data[:10]}")  # Display a few samples
            print(f"Recording data range: {np.min(recording_data)} to {np.max(recording_data)}")

        self.canvas.draw_idle()

        # Schedule the next update
        if self.is_recording:
            self.root.after(30, self.update_plot)
        

    def start_recording(self):
        """Start recording and visualization."""
        if not self.is_recording:
            self.is_recording = True
            is_recording = True
            print(is_recording)
            self.stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=1,
                callback=self.audio_callback
            )
            self.stream.start()
            print("Stream started for recording.")
            self.update_plot()
            print("Recording started.")

    def stop_recording(self):
        """Stop recording and visualization."""
        if self.is_recording:
            self.is_recording = False
            if self.stream:
                self.stream.stop()
                self.stream.close()
            save_audio_to_file()
            print("Recording stopped.")
            print(f"Recording data length: {len(recording_data)}")

