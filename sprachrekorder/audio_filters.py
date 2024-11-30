import math
import os
from pydub import AudioSegment, effects
import numpy as np

def apply_filter(input_file, output_file, filter_name, param1=0, param2=0, param3=0):
    """Applies the selected filter to the audio."""
    print("Loading audio from:", input_file)
    if not os.path.exists(input_file):
        print("File does not exist. Check the path or permissions.")
        return

    try:
        audio = AudioSegment.from_file(input_file)
        print("File loaded successfully.")
    except Exception as e:
        print(f"Failed to load file: {e}")
        return

    if filter_name == "Robot":
        octaves = -0.5
        mod_frequency = 50
        
        # Step 1: Lower the pitch
        new_sample_rate = int(audio.frame_rate * (2 ** octaves))
        pitched_audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_sample_rate}).set_frame_rate(audio.frame_rate)
        
        # Step 2: Apply smooth amplitude modulation
        samples = np.array(pitched_audio.get_array_of_samples(), dtype=np.float32)
        sine_wave = np.sin(2 * np.pi * mod_frequency / pitched_audio.frame_rate * np.arange(len(samples)))
        modulated_samples = samples * (0.5 + 0.5 * sine_wave)  # Mild modulation to avoid distortion

        # Prevent clipping
        max_amplitude = np.max(np.abs(modulated_samples))
        if max_amplitude > 0:
            modulated_samples = (modulated_samples / max_amplitude) * (2**15 - 1)

        modulated_samples = modulated_samples.astype(np.int16)
        audio = pitched_audio._spawn(modulated_samples.tobytes())
        audio = effects.compress_dynamic_range(audio, threshold=-20.0, ratio=4.0)

    elif filter_name == "Echo":
        delay_ms = 300
        decay_factor = -10
        echo = audio - abs(decay_factor)
        audio = audio.overlay(echo, delay_ms)
        audio = audio.fade_in(50).fade_out(150)

    elif filter_name == "High Pitch":
        octaves = 0.5
        new_sample_rate = int(audio.frame_rate * (2 ** octaves))
        audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_sample_rate}).set_frame_rate(audio.frame_rate)

    elif filter_name == "Reverb":
        initial_delay_ms = 20
        decay_factor = -5
        reflections_count = 10
        max_reflection_delay = 150
        reflections = audio
        delay_ms = initial_delay_ms
        for i in range(reflections_count):
            reflection = audio - abs(decay_factor * (i + 1))
            reflections = reflections.overlay(reflection, delay_ms)
            delay_ms = min(delay_ms + 20, max_reflection_delay)
        audio = reflections.fade_in(20).fade_out(50)

    elif filter_name == "Bass Boost":
        speed_factor = 1.2
        bass_boost_factor = 1.5
        new_frame_rate = int(audio.frame_rate / speed_factor)
        slowed_audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_frame_rate})
        slowed_audio = slowed_audio.low_pass_filter(150)
        audio = slowed_audio + bass_boost_factor

    elif filter_name == "Custom":
        # Apply custom modifications based on param1, param2, param3
        print(f"Custom Filter Params: Speed({param1}), Volume({param2}), Reverse({param3})")
        audio = audio.speedup(playback_speed=1 + param1 / 100.0)  # Adjust speed based on param1
        audio = audio + (param2 - 50)  # Adjust volume based on param2
        if param3 > 50:
            audio = audio.reverse()  # Reverse if param3 > 50

    else:
        print(f"Unknown filter: {filter_name}")
        return

    # Export the modified audio
    audio.export(output_file, format="wav")
    print(f"Filter '{filter_name}' applied and saved as {output_file}.")
