import os
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Thread, Event
import time
from pydub import AudioSegment
from pydub.playback import play
from scipy.io import wavfile
from playsound import playsound
import ctypes

def get_short_path_name(long_path):
    """Convert a long path to its short path equivalent on Windows bc playsound is wack."""
    buffer = ctypes.create_unicode_buffer(260)  # MAX_PATH in Windows
    ctypes.windll.kernel32.GetShortPathNameW(long_path, buffer, 260)
    return buffer.value

def load_audio_file(file_path):
    """Load audio file data and return data and samplerate."""
    samplerate, data = wavfile.read(file_path)
    if data.ndim > 1:  # If stereo, use only one channel
        data = data[:, 0]
    return data, samplerate

class AudioPlotter:
    def __init__(self, root):
        self.root = root
        self.data = None
        self.samplerate = None
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.line, = self.ax.plot([], [], color='g')
        self.ax.set_facecolor((0, 0, 0))

        # Create canvas and pack it to the tkinter window
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(pady=20)
        self.canvas.draw()

    def update_plot(self, start_index, end_index):
        """Update the plot with new data."""
        if self.data is not None:
            time_array = np.linspace(start_index / self.samplerate, end_index / self.samplerate, end_index - start_index)
            self.line.set_data(time_array, self.data[start_index:end_index])
            self.ax.set_xlim(start_index / self.samplerate, end_index / self.samplerate)
            self.canvas.draw()

    def play_audio_with_plot(self, file_path):
        """Load and play the audio while updating the plot."""
        # Normalize the file path to ensure compatibility with Windows
        file_path = os.path.normpath(file_path)
        file_path = file_path.replace("\\", "/")
        file_path = get_short_path_name(file_path)

        # Load the audio file data for plotting
        self.data, self.samplerate = load_audio_file(file_path)
        total_samples = len(self.data)
        chunk_size = 2048  # Number of samples to process at a time

        # Create an event for synchronization between audio playback and plotting
        plot_event = Event()

        # Function to handle plotting and synchronization
        def plot_and_play():
            # Load the audio data for visualization
            total_chunks = total_samples // chunk_size

            for chunk_index in range(total_chunks + 1):
                start = chunk_index * chunk_size
                end = min((chunk_index + 1) * chunk_size, total_samples)

                # Update the plot with the current chunk of audio data
                self.update_plot(start, end)

                # Simulate delay for synchronization
                time.sleep(chunk_size / self.samplerate)

            print("Plotting finished.")

        # Function to handle audio playback
        def play_audio():
            try:
                print(f"Playing audio from: {file_path}")
                playsound(file_path)  # Play the full audio file
            except Exception as e:
                print(f"Error playing audio: {e}")

        # Start plotting in a separate thread
        plot_thread = Thread(target=plot_and_play, daemon=True)
        plot_thread.start()

        # Start audio playback in another thread
        audio_thread = Thread(target=play_audio, daemon=True)
        audio_thread.start()

        print("Audio playback and plotting finished.")
