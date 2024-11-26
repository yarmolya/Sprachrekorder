from pydub import AudioSegment

def apply_filter(input_file, output_file, filter_name):
    """Applies the selected filter to the audio."""
    audio = AudioSegment.from_file(input_file)

    if filter_name == "Robot":
        # Example: Apply pitch shifting or distortion
        audio = audio.speedup(playback_speed=1.5)
    elif filter_name == "Echo":
        # Example: Add echo effect
        audio = audio + 5  # Amplify volume for echo-like effect
    elif filter_name == "High Pitch":
        # Example: Increase pitch
        audio = audio.speedup(playback_speed=1.2)

    audio.export(output_file, format="wav")
    print(f"Filter '{filter_name}' applied and saved as {output_file}.")
