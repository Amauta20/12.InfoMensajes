
import pygame
import sys
import time

def play_audio(file_path):
    try:
        pygame.init()
        pygame.mixer.init()
        print(f"Pygame initialized successfully.")
        print(f"Loading audio file: {file_path}")
        pygame.mixer.music.load(file_path)
        print("Audio file loaded successfully.")
        print("Playing audio...")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            print(f"Playback time: {pygame.mixer.music.get_pos() / 1000:.2f} seconds")
            time.sleep(1)
        print("Playback finished.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_audio.py <path_to_audio_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    play_audio(file_path)
