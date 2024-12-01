import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Thread, Event
import time
from pydub import AudioSegment
from pydub.playback import play
from scipy.io import wavfile

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
        self.data, self.samplerate = load_audio_file(file_path)
        total_samples = len(self.data)
        chunk_size = 2048  # Number of samples to process at a time

        # Create an event for synchronization between the audio playing and plotting
        plot_event = Event()

        def plot_and_play():
            audio = AudioSegment.from_file(file_path)
            total_chunks = total_samples // chunk_size

            for chunk_index in range(total_chunks + 1):
                start = chunk_index * chunk_size
                end = min((chunk_index + 1) * chunk_size, total_samples)
                
                # Update the plot with the current chunk of audio data
                self.update_plot(start, end)

                # Play the corresponding chunk of audio
                chunk = audio[start:end]
                play(chunk)

                # Wait for the audio to finish or until the next chunk
                plot_event.wait()
                plot_event.clear()

            print("Audio playback finished.")

        # Separate thread for plotting
        def plot_updater():
            while True:
                plot_event.set()
                time.sleep(chunk_size / self.samplerate)  # Wait before next chunk update

        # Start the threads for plotting and playing audio
        plot_thread = Thread(target=plot_updater)
        plot_thread.start()

        # Start the audio playback in a separate thread
        audio_thread = Thread(target=plot_and_play)
        audio_thread.start()