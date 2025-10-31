import os
import random
import time
import pygame
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen import MutagenError
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QFileDialog, QLabel, QSlider, QComboBox
from PyQt6.QtCore import QUrl, Qt, QTimer

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

        self.SONG_END = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.SONG_END)

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.check_music_status)
        self.timer.start()

        self.init_ui()
        self.load_last_folder()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Folder selection
        self.select_folder_button = QPushButton("Seleccionar Carpeta")
        self.select_folder_button.clicked.connect(self.select_folder)
        layout.addWidget(self.select_folder_button)

        # Filters
        filters_layout = QHBoxLayout()
        self.artist_combo = QComboBox()
        self.artist_combo.addItem("Todos los Artistas")
        self.artist_combo.currentIndexChanged.connect(self.filter_playlist)
        filters_layout.addWidget(self.artist_combo)

        self.album_combo = QComboBox()
        self.album_combo.addItem("Todos los Álbumes")
        self.album_combo.currentIndexChanged.connect(self.filter_playlist)
        filters_layout.addWidget(self.album_combo)
        layout.addLayout(filters_layout)

        # Playlist
        self.playlist_widget = QListWidget()
        self.playlist_widget.itemDoubleClicked.connect(self.play_selected)
        layout.addWidget(self.playlist_widget)

        # Currently playing label
        self.current_track_label = QLabel("Ninguna canción seleccionada")
        self.current_track_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.current_track_label)

        # Progress Slider
        progress_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.sliderReleased.connect(self.set_song_position)
        self.total_time_label = QLabel("00:00")

        progress_layout.addWidget(self.current_time_label)
        progress_layout.addWidget(self.progress_slider)
        progress_layout.addWidget(self.total_time_label)
        layout.addLayout(progress_layout)

        # Controls
        controls_layout = QHBoxLayout()
        self.prev_button = QPushButton("Anterior")
        self.prev_button.clicked.connect(self.play_previous)
        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.next_button = QPushButton("Siguiente")
        self.next_button.clicked.connect(self.play_next)

        self.shuffle_button = QPushButton("Aleatorio")
        self.shuffle_button.setCheckable(True)
        self.shuffle_button.clicked.connect(self.toggle_shuffle)

        self.repeat_button = QPushButton("Repetir")
        self.repeat_button.setCheckable(True)
        self.repeat_button.clicked.connect(self.toggle_repeat)

        self.volume_down_button = QPushButton("Vol-")
        self.volume_down_button.clicked.connect(self.decrease_volume)

        self.volume_up_button = QPushButton("Vol+")
        self.volume_up_button.clicked.connect(self.increase_volume)

        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.play_pause_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addWidget(self.shuffle_button)
        controls_layout.addWidget(self.repeat_button)
        controls_layout.addWidget(self.volume_down_button)
        controls_layout.addWidget(self.volume_up_button)
        layout.addLayout(controls_layout)

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
                if filename.endswith(('.mp3')):
                    full_path = os.path.join(root, filename)
                    try:
                        audio = EasyID3(full_path)
                        title = audio.get('title', [os.path.basename(full_path)])[0].strip()
                        artist = audio.get('artist', ['Desconocido'])[0].strip()
                        album = audio.get('album', ['Desconocido'])[0].strip()
                    except Exception:
                        title = os.path.basename(full_path)
                        artist = 'Desconocido'
                        album = 'Desconocido'
                    
                    print(f"Loaded: {title}, Artist: {artist}, Album: {album}") # Debug print
                    self.audio_files.append({
                        'path': full_path,
                        'title': title,
                        'artist': artist,
                        'album': album
                    })
        
        self.original_playlist = list(self.audio_files)
        self.is_shuffled = False
        self.shuffle_button.setChecked(False)

        self.populate_filters()
        self.update_playlist_widget()

        if self.audio_files and autoplay:
            self.current_index = 0
            self.play_track()

    def populate_filters(self):
        artists = {"Todos los Artistas"} | {track['artist'] for track in self.original_playlist}
        albums = {"Todos los Álbumes"} | {track['album'] for track in self.original_playlist}

        self.artist_combo.blockSignals(True)
        self.album_combo.blockSignals(True)

        self.artist_combo.clear()
        self.artist_combo.addItems(sorted(list(artists)))
        self.album_combo.clear()
        self.album_combo.addItems(sorted(list(albums)))

        self.artist_combo.blockSignals(False)
        self.album_combo.blockSignals(False)

    def filter_playlist(self):
        selected_artist = self.artist_combo.currentText()
        selected_album = self.album_combo.currentText()

        filtered_list = list(self.original_playlist)

        if selected_artist != "Todos los Artistas":
            filtered_list = [track for track in filtered_list if track['artist'] == selected_artist]

        if selected_album != "Todos los Álbumes":
            filtered_list = [track for track in filtered_list if track['album'] == selected_album]

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

    def play_track(self):
        if 0 <= self.current_index < len(self.audio_files):
            track_path = self.audio_files[self.current_index]['path']
            pygame.mixer.music.load(track_path)
            pygame.mixer.music.play()
            
            self.is_paused = False
            self.play_pause_button.setText("Pausa")
            self.playlist_widget.setCurrentRow(self.current_index)
            self.current_track_label.setText(self.audio_files[self.current_index]['title'])

            # Reset time tracking
            self.paused_position_ms = 0
            self.song_start_system_time = time.time()

            # Update slider and time labels
            try:
                track_info = MP3(track_path)
                song_length_ms = int(track_info.info.length * 1000)
                self.progress_slider.setMaximum(song_length_ms)
                self.total_time_label.setText(self.format_time(song_length_ms))
            except Exception as e:
                print(f"Could not get song length: {e}")
                self.progress_slider.setMaximum(0)
                self.total_time_label.setText("00:00")

    def get_current_song_position_ms(self):
        if not pygame.mixer.music.get_busy() or self.is_paused:
            return self.paused_position_ms
        else:
            elapsed_seconds = time.time() - self.song_start_system_time
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
        seconds = position_ms / 1000.0
        
        pygame.mixer.music.play(start=seconds)
        
        # Update time tracking state
        self.paused_position_ms = position_ms
        self.song_start_system_time = time.time()

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
            self.play_pause_button.setText("Pausa")
            # Resync the start time
            self.song_start_system_time = time.time()
        else:
            # Pausing
            pygame.mixer.music.pause()
            self.is_paused = True
            self.play_pause_button.setText("Play")
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