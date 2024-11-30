import math
import os
from pydub import AudioSegment, effects
import numpy as np
from scipy.signal import lfilter, butter


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
        octaves=-0.5
        mod_frequency=50
        
        # Step 1: Lower the pitch
        new_sample_rate = int(audio.frame_rate * (2 ** octaves))
        pitched_audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_sample_rate}).set_frame_rate(audio.frame_rate)
        
        # Step 2: Apply smooth amplitude modulation
        samples = np.array(pitched_audio.get_array_of_samples(), dtype=np.float32)
        sine_wave = np.sin(2 * np.pi * mod_frequency / pitched_audio.frame_rate * np.arange(len(samples)))
        modulated_samples = samples * (0.5 + 0.5 * sine_wave)  # Mild modulation to avoid distortion

        # Prevent clipping by normalizing the modulated signal
        max_amplitude = np.max(np.abs(modulated_samples))
        if max_amplitude > 0:
            modulated_samples = (modulated_samples / max_amplitude) * (2**15 - 1)

        modulated_samples = modulated_samples.astype(np.int16)

        # Step 3: Re-spawn the audio with modulated samples
        audio = pitched_audio._spawn(modulated_samples.tobytes())

        # Step 4: Add compression for a smoother, more controlled sound
        audio = effects.compress_dynamic_range(audio, threshold=-20.0, ratio=4.0)
        

    elif filter_name == "Echo":
        # Overlay audio with itself to create a rich, clear echo effect
        delay_ms=300
        decay_factor=-10
        echo = audio - abs(decay_factor)  # Apply volume reduction (in dB)
    
        # Apply delay (overlay the original audio with the delayed echo)
        audio = audio.overlay(echo, delay_ms)
        
        # Optional: Add a fade-in and fade-out to the echo for smoother transition
        audio = audio.fade_in(50).fade_out(150)  

    elif filter_name == "High Pitch":
        # Pitch shift up: Adjust playback speed to higher without distortion
        octaves = 0.5  # Increase pitch by half an octave
        new_sample_rate = int(audio.frame_rate * (2 ** octaves))
        audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_sample_rate}).set_frame_rate(audio.frame_rate)

    elif filter_name == "Reverb":
        initial_delay_ms=20
        decay_factor=-5
        reflections_count=10
        max_reflection_delay=150
        reflections = audio  # Start with the original audio
    
        delay_ms = initial_delay_ms  # Initial delay for the first reflection
        
        for i in range(reflections_count):
            # Create a quieter reflection
            reflection = audio - abs(decay_factor * (i + 1))  # Decrease volume more for each reflection
            
            # Overlay the original audio with the reflection with a delay
            reflections = reflections.overlay(reflection, delay_ms)
            
            # Gradually increase the delay to simulate distant reflections
            delay_ms = min(delay_ms + 20, max_reflection_delay)  # Delay increases but does not exceed max
            
            # Optionally apply a small fade to each reflection to smooth transitions (can be adjusted)
            audio = reflections.fade_in(20).fade_out(50)  # Short fade-in and fade-out
        
        
    elif filter_name == "Bass Boost":
        speed_factor=1.2
        bass_boost_factor=1.5
        # Slow down the audio by adjusting the frame rate
        new_frame_rate = int(audio.frame_rate / speed_factor)
        slowed_audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_frame_rate})
        
        # Apply a slight bass boost: Boost the low-end frequencies
        slowed_audio = slowed_audio.low_pass_filter(150)  # Keep only the bass frequencies below 150 Hz
        
        # Amplify the entire track to boost bass perception
        audio = slowed_audio + bass_boost_factor  # Increase the volume slightly to boost bass perception



    # Export the modified audio to a new file
    audio.export(output_file, format="wav")
    print(f"Filter '{filter_name}' applied and saved as {output_file}.")
