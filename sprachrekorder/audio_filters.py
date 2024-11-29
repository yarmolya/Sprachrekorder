import os
from pydub import AudioSegment, effects
import numpy as np
from scipy.signal import lfilter, butter
from visualization import save_audio_to_file


def apply_filter(input_file, output_file, filter_name):
    """Applies the selected filter to the audio."""
    print("Loading audio from:", input_file)
    if os.path.exists(input_file):
        print("File exists. Proceeding with loading...")
    else:
        print("File does not exist. Check path or permissions.")

    try:
        audio = AudioSegment.from_file(input_file)
        print("File loaded successfully.")
    except Exception as e:
        print(f"Failed to load file: {e}")

    if filter_name == "Robot":
        # Apply a low-pass filter to smooth out harsh sounds (optional, can adjust cutoff)
        audio = effects.low_pass_filter(audio, cutoff=1000)

        # Modulate the audio to create a robotic effect
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)

        # Generate a sine wave (modulation) at 50Hz (or a different frequency for stronger effect)
        mod_frequency = 50  # Hz, adjust for more/less robot effect
        sine_wave = np.sin(2 * np.pi * mod_frequency / audio.frame_rate * np.arange(len(samples)))

        # Apply modulation: element-wise multiplication (mild distortion)
        modulated_samples = samples * sine_wave

        # Prevent clipping by scaling back the values and applying soft clipping if necessary
        modulated_samples = np.clip(modulated_samples, -2**15, 2**15-1)

        # Convert the samples back to 16-bit format
        modulated_samples = modulated_samples.astype(np.int16)

        # Create the modulated AudioSegment from the new samples
        audio = audio._spawn(modulated_samples.tobytes()).set_frame_rate(audio.frame_rate)

    elif filter_name == "Echo":
        # Overlay audio with itself to create a rich, clear echo effect
        delay_ms = 300  # Delay in ms
        echo = audio - 10  # Reduce volume of echo
        audio = audio.overlay(echo, delay=delay_ms)

    elif filter_name == "High Pitch":
        # Pitch shift up: Adjust playback speed to higher without distortion
        octaves = 0.5  # Increase pitch by half an octave
        new_sample_rate = int(audio.frame_rate * (2 ** octaves))
        audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_sample_rate}).set_frame_rate(audio.frame_rate)

    elif filter_name == "Reverb":
        # Add reverb using feedback-style overlay
        delay_ms = 100
        reflections = audio - 5  # Slightly softer reflections
        for _ in range(3):  # Simulate multiple reflections
            reflections = reflections.overlay(audio, delay=delay_ms)
            delay_ms += 50  # Increment delay each time
        audio = reflections

    elif filter_name == "Bass Boost":
        # Boost low frequencies using a low-shelf filter
        def bass_boost(audio, gain_db=10, cutoff=100):
            samples = np.array(audio.get_array_of_samples())
            b, a = butter(1, cutoff / (audio.frame_rate / 2), btype="low")
            boosted = lfilter(b, a, samples) * (10 ** (gain_db / 20))
            return audio._spawn(boosted.astype(np.int16).tobytes())

        audio = bass_boost(audio)

    # Export the modified audio to a new file
    audio.export(output_file, format="wav")
    print(f"Filter '{filter_name}' applied and saved as {output_file}.")
