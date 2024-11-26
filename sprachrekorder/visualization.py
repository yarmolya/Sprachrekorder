import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd
from matplotlib.animation import FuncAnimation
from scipy.io.wavfile import write
import threading
import queue as q
import tkinter as tk
from tkinter import filedialog

# Global variables for audio recording and visualization
is_recording = False
recording_data = []
audio_queue = q.Queue()  # Queue for audio data
freq = 44100  # Sampling frequency

# Visualization settings
device = 0  # Default input device
window = 1000  # Size of the visualization window in milliseconds
downsample = 1  # Downsample factor
channels = [1]  # List of audio channels
interval = 30  # Update interval in milliseconds
device_info = sd.query_devices(device, 'input')
samplerate = int(device_info['default_samplerate'])
length = int(window * samplerate / (1000 * downsample))

# Plot data for visualization
plotdata = np.zeros((length, len(channels)))

# Create the plot for visualization
fig, ax = plt.subplots(figsize=(8, 4))
ax.set_title("Live Audio Waveform")
lines = ax.plot(plotdata, color=(0, 1, 0.29))  # Green waveform
ax.set_facecolor((0, 0, 0))  # Black background
ax.set_yticks([0])
ax.yaxis.grid(True)


def audio_callback(indata, frames, time, status):
    """Callback to handle audio input."""
    global is_recording, recording_data

    if status:
        print(status)

    # Push data to the queue for visualization
    audio_queue.put(indata[::downsample, [0]])

    # Store data for recording if enabled
    if is_recording:
        recording_data.append(indata.copy())


def update_plot(frame):
    """Update the waveform plot with new audio data."""
    global plotdata

    while True:
        try:
            data = audio_queue.get_nowait()
        except q.Empty:
            break

        shift = len(data)
        plotdata = np.roll(plotdata, -shift, axis=0)
        plotdata[-shift:, :] = data

    for column, line in enumerate(lines):
        line.set_ydata(plotdata[:, column])
    return lines


def save_audio_to_file():
    """Save the recorded audio data to a file."""
    global recording_data

    if not recording_data:
        print("No audio data to save!")
        return

    # Combine the recorded audio chunks
    audio_array = np.concatenate(recording_data, axis=0)

    # Ask the user for the save location
    root = tk.Tk()
    root.withdraw()
    output_path = filedialog.asksaveasfilename(defaultextension=".wav",
                                               filetypes=[("WAV Files", "*.wav")])

    if output_path:
        write(output_path, freq, audio_array)
        print(f"Recording saved to {output_path}")
    else:
        print("Save operation cancelled.")


def start_recording():
    """Start recording audio."""
    global is_recording, recording_data
    is_recording = True
    recording_data = []  # Clear previous recording data
    print("Recording started...")


def stop_recording():
    """Stop recording audio."""
    global is_recording
    is_recording = False
    print("Recording stopped.")
    save_audio_to_file()  # Save the recorded audio to a file


def visualize_audio_live():
    """Run the audio visualization and manage recording."""
    global is_recording

    def toggle_recording(event):
        """Toggle recording on or off with a button click."""
        if is_recording:
            stop_recording()
            record_button.label.set_text("Start Recording")  # Update button text
        else:
            start_recording()
            record_button.label.set_text("Stop Recording")  # Update button text

    ani = FuncAnimation(fig, update_plot, interval=interval, blit=True)

    # Add a button to start/stop recording
    from matplotlib.widgets import Button
    ax_button = plt.axes([0.8, 0.02, 0.1, 0.05])
    record_button = Button(ax_button, "Start Recording")  # Create the button first
    record_button.on_clicked(toggle_recording)

    # Start the audio stream and visualization
    with sd.InputStream(device=device, channels=max(channels), samplerate=samplerate, callback=audio_callback):
        plt.show()


if __name__ == "__main__":
    visualize_audio_live()
