import os
import random
import time
import pygame
import logging
import mutagen
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QFileDialog, QLabel, QSlider, QComboBox, QGroupBox, QGridLayout, QLineEdit, QMessageBox
from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtGui import QFont


class AudioPlayerWidget(QWidget):
    @staticmethod
    def format_time(ms):
        seconds = int(ms / 1000)
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes:02}:{seconds:02}"

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.audio_files = []
        self.current_index = -1
        self.is_paused = False
        self.is_repeat_on = False
        self.is_shuffled = False
        self.original_playlist = []

        # New time tracking variables
        self.song_start_system_time = 0
        self.paused_position_ms = 0

        # Initialize pygame mixer
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.init()
        pygame.mixer.init(frequency=44100)

        self.SONG_END = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.SONG_END)

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.check_music_status)
        self.timer.start()

        self.init_ui()
        self.load_last_folder()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # Stylesheet for Font Awesome buttons
        fa_button_style_main = "QPushButton { font-family: \"Font Awesome 6 Free\"; font-size: 18px; padding: 0px; margin: 0px; border: none; }"
        fa_button_style_volume = "QPushButton { font-family: \"Font Awesome 6 Free\"; font-size: 16px; padding: 0px; margin: 0px; border: none; }"

        # Left side (empty, as select_folder_button is moved)
        left_layout = QVBoxLayout()

        main_layout.addLayout(left_layout)

        # Right side (Playlist, Search, and Controls)
        right_layout = QVBoxLayout()
        
        # Folder selection button moved to right_layout and styled with Font Awesome
        self.select_folder_button = QPushButton("\uf07b") # Folder Open icon
        self.select_folder_button.setStyleSheet(fa_button_style_main) # Use the same style as main controls
        self.select_folder_button.setFixedSize(36, 36)
        self.select_folder_button.clicked.connect(self.select_folder)
        
        # Create a horizontal layout for the folder button and search bar
        top_controls_layout = QHBoxLayout()
        top_controls_layout.addWidget(self.select_folder_button)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Buscar por nombre de canción...")
        self.search_bar.textChanged.connect(self.filter_playlist)
        top_controls_layout.addWidget(self.search_bar)
        
        right_layout.addLayout(top_controls_layout) # Add the new layout to right_layout

        # Playlist
        self.playlist_widget = QListWidget()
        self.playlist_widget.itemDoubleClicked.connect(self.play_selected)
        right_layout.addWidget(self.playlist_widget)

        # Currently playing label
        self.current_track_label = QLabel("Ninguna canción seleccionada")
        self.current_track_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.current_track_label)

        # Progress Slider
        progress_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.sliderReleased.connect(self.set_song_position)
        self.total_time_label = QLabel("00:00")

        progress_layout.addWidget(self.current_time_label)
        progress_layout.addWidget(self.progress_slider)
        progress_layout.addWidget(self.total_time_label)
        right_layout.addLayout(progress_layout)

        # Controls
        controls_layout = QHBoxLayout()

        self.prev_button = QPushButton("\uf048") # Previous icon
        self.prev_button.setStyleSheet(fa_button_style_main)
        self.prev_button.setFixedSize(36, 36)
        self.prev_button.clicked.connect(self.play_previous)
        
        self.play_pause_button = QPushButton("\uf04b") # Play icon (initial state)
        self.play_pause_button.setStyleSheet(fa_button_style_main)
        self.play_pause_button.setFixedSize(36, 36)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        
        self.next_button = QPushButton("\uf051") # Next icon
        self.next_button.setStyleSheet(fa_button_style_main)
        self.next_button.setFixedSize(36, 36)
        self.next_button.clicked.connect(self.play_next)

        self.shuffle_button = QPushButton("\uf074") # Shuffle icon
        self.shuffle_button.setCheckable(True)
        self.shuffle_button.setStyleSheet(fa_button_style_main)
        self.shuffle_button.setFixedSize(36, 36)
        self.shuffle_button.clicked.connect(self.toggle_shuffle)

        self.repeat_button = QPushButton("\uf01e") # Repeat icon
        self.repeat_button.setCheckable(True)
        self.repeat_button.setStyleSheet(fa_button_style_main)
        self.repeat_button.setFixedSize(36, 36)
        self.repeat_button.clicked.connect(self.toggle_repeat)

        self.volume_down_button = QPushButton("\uf027") # Volume Down icon
        self.volume_down_button.setStyleSheet(fa_button_style_volume)
        self.volume_down_button.setFixedSize(32, 32)
        self.volume_down_button.clicked.connect(self.decrease_volume)

        self.volume_up_button = QPushButton("\uf028") # Volume Up icon
        self.volume_up_button.setStyleSheet(fa_button_style_volume)
        self.volume_up_button.setFixedSize(32, 32)
        self.volume_up_button.clicked.connect(self.increase_volume)

        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.play_pause_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addWidget(self.shuffle_button)
        controls_layout.addWidget(self.repeat_button)
        controls_layout.addWidget(self.volume_down_button)
        controls_layout.addWidget(self.volume_up_button)
        right_layout.addLayout(controls_layout)

        main_layout.addLayout(right_layout)



    def load_last_folder(self):
        last_folder = self.settings_manager.get_setting('last_music_folder')
        if last_folder and os.path.isdir(last_folder):
            self.load_folder_content(last_folder, autoplay=False)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Música")
        if folder_path:
            self.load_folder_content(folder_path, autoplay=True)
            self.settings_manager.set_setting('last_music_folder', folder_path)

    def load_folder_content(self, folder_path, autoplay=False):
        self.audio_files = []
        for root, _, filenames in os.walk(folder_path):
            for filename in filenames:
                if filename.endswith(('.mp3', '.wav', '.ogg', '.flac')):
                    full_path = os.path.join(root, filename)
                    try:
                        audio = mutagen.File(full_path, easy=True)
                        if audio:
                            title = audio.get('title', [os.path.basename(full_path)])[0].strip()
                            artist = audio.get('artist', ['Desconocido'])[0].strip()
                            album = audio.get('album', ['Desconocido'])[0].strip()
                        else:
                            raise mutagen.MutagenError("Could not load metadata")
                    except Exception:
                        title = os.path.basename(full_path)
                        artist = 'Desconocido'
                        album = 'Desconocido'
                    
                    self.audio_files.append({
                        'path': full_path,
                        'title': title,
                        'artist': artist,
                        'album': album
                    })
        
        self.original_playlist = list(self.audio_files)
        self.is_shuffled = False
        self.shuffle_button.setChecked(False)

        self.update_playlist_widget()

        if self.audio_files and autoplay:
            self.current_index = 0
            self.play_track()

    def filter_playlist(self, text):
        search_text = text.lower()

        filtered_list = [track for track in self.original_playlist if search_text in track['title'].lower()]

        # Store the currently playing track, if any
        current_playing_track = None
        if self.current_index != -1 and self.current_index < len(self.audio_files):
            current_playing_track = self.audio_files[self.current_index]

        self.audio_files = filtered_list
        self.update_playlist_widget()

        # After filtering, check if the previously playing track is still in the list
        if current_playing_track:
            try:
                new_index = self.audio_files.index(current_playing_track)
                self.current_index = new_index
                self.playlist_widget.setCurrentRow(self.current_index)
            except ValueError:
                # Current playing track is no longer in the filtered list
                pygame.mixer.music.stop()
                self.current_index = -1
                self.play_pause_button.setText("Play")
                self.current_track_label.setText("Ninguna canción seleccionada")
                self.progress_slider.setValue(0)
                self.current_time_label.setText("00:00")
        else:
            # If no song was playing, or if the list is now empty, reset current_index
            self.current_index = -1

    def update_playlist_widget(self):
        self.playlist_widget.clear()
        if not self.audio_files:
            self.current_time_label.setText("00:00")
            self.total_time_label.setText("00:00")
            self.progress_slider.setValue(0)
            self.progress_slider.setMaximum(0)
            self.current_track_label.setText("Ninguna canción seleccionada")
            self.current_index = -1
            pygame.mixer.music.stop()
            return

        for track in self.audio_files:
            self.playlist_widget.addItem(track['title'])
        if self.current_index != -1 and self.current_index < self.playlist_widget.count():
            self.playlist_widget.setCurrentRow(self.current_index)

    def play_track(self, start_pos_sec=0):
        logging.debug("Entering play_track")
        if 0 <= self.current_index < len(self.audio_files):
            track_path = self.audio_files[self.current_index]['path']
            logging.debug(f"track_path: {track_path}")

            try:
                logging.debug("Loading sound into pygame mixer directly")
                pygame.mixer.music.load(track_path)
                logging.debug("Sound loaded successfully")

                logging.debug(f"Playing sound from position: {start_pos_sec}")
                pygame.mixer.music.play(start=start_pos_sec)
                logging.debug("Sound playing")

                self.is_paused = False
                self.play_pause_button.setText("\uf04c") # Pause icon
                self.playlist_widget.setCurrentRow(self.current_index)
                self.current_track_label.setText(self.audio_files[self.current_index]['title'])

                # Reset time tracking
                self.paused_position_ms = start_pos_sec * 1000
                self.song_start_system_time = time.monotonic()

                # Update slider and time labels
                try:
                    audio_info = mutagen.File(track_path)
                    if audio_info:
                        song_length_ms = int(audio_info.info.length * 1000)
                        self.progress_slider.setMaximum(song_length_ms)
                        self.total_time_label.setText(self.format_time(song_length_ms))
                    else:
                        raise mutagen.MutagenError("Could not load audio info")
                except Exception as e:
                    logging.error(f"Could not get song length: {e}")
                    self.progress_slider.setMaximum(0)
                    self.total_time_label.setText("00:00")

            except Exception as e:
                logging.error(f"General error in play_track: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Error al reproducir la canción: {e}")

    def get_current_song_position_ms(self):
        if not pygame.mixer.music.get_busy() or self.is_paused:
            return self.paused_position_ms
        else:
            elapsed_seconds = time.monotonic() - self.song_start_system_time
            return self.paused_position_ms + (elapsed_seconds * 1000)

    def check_music_status(self):
        # Check for song end event
        for event in pygame.event.get():
            if event.type == self.SONG_END:
                self.handle_song_end()
        
        # Update UI if a song is playing
        if pygame.mixer.music.get_busy() and not self.is_paused:
            if not self.progress_slider.isSliderDown():
                current_pos_ms = self.get_current_song_position_ms()
                self.progress_slider.setValue(int(current_pos_ms))
                self.current_time_label.setText(self.format_time(current_pos_ms))

    def set_song_position(self):
        if self.current_index == -1:
            return

        position_ms = self.progress_slider.value()
        self.play_track(start_pos_sec=position_ms / 1000.0)

        if self.is_paused:
            pygame.mixer.music.pause()

    def play_selected(self, item):
        self.current_index = self.playlist_widget.row(item)
        self.play_track()

    def toggle_play_pause(self):
        if self.current_index == -1:
            return

        if self.is_paused:
            # Resuming
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.play_pause_button.setText("\uf04c") # Pause icon
            # Resync the start time
            self.song_start_system_time = time.monotonic()
        else:
            # Pausing
            pygame.mixer.music.pause()
            self.is_paused = True
            self.play_pause_button.setText("\uf04b") # Play icon
            # Record position when pausing
            self.paused_position_ms = self.get_current_song_position_ms()

    def play_next(self):
        if not self.audio_files:
            return
        self.current_index = (self.current_index + 1) % len(self.audio_files)
        self.play_track()

    def play_previous(self):
        if not self.audio_files:
            return
        self.current_index = (self.current_index - 1) % len(self.audio_files)
        self.play_track()

    def handle_song_end(self):
        if self.is_repeat_on:
            self.play_track()
        else:
            self.play_next()

    def toggle_repeat(self):
        self.is_repeat_on = self.repeat_button.isChecked()

    def toggle_shuffle(self):
        self.is_shuffled = self.shuffle_button.isChecked()

        if self.is_shuffled:
            if not self.original_playlist:
                self.original_playlist = list(self.audio_files)
            
            if self.current_index != -1:
                current_song = self.audio_files[self.current_index]
                self.audio_files.remove(current_song)
                random.shuffle(self.audio_files)
                self.audio_files.insert(0, current_song)
                self.current_index = 0
            else:
                random.shuffle(self.audio_files)
        else:
            if self.original_playlist:
                if self.current_index != -1:
                    current_song = self.audio_files[self.current_index]
                    self.audio_files = list(self.original_playlist)
                    if current_song in self.audio_files:
                        self.current_index = self.audio_files.index(current_song)
                else:
                    self.audio_files = list(self.original_playlist)
                self.original_playlist = []

        self.update_playlist_widget()

    def increase_volume(self):
        current_volume = pygame.mixer.music.get_volume()
        pygame.mixer.music.set_volume(min(current_volume + 0.1, 1.0))

    def decrease_volume(self):
        current_volume = pygame.mixer.music.get_volume()
        pygame.mixer.music.set_volume(max(current_volume - 0.1, 0.0))