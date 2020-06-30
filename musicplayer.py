import vlc
import os
import time
import keyboard
from datetime import timedelta
from random import sample, choice



music_dir = "C:/Users/Dave/Documents/Macbook Air BACKUP/Downloads/Post Malone - Hollywood's Bleeding (2019) Mp3 (320kbps) [Hunter]/Post Malone - Hollywood's Bleeding (2019)" #"C:/Users/Dave/Documents/Macbook Air BACKUP/Downloads/Avicii - TIM (2019) Mp3 (320 kbps) [Hunter]/Avicii - TIM (2019)"

class Song:
    def __init__(self, name, duration, status, song_dir):
        self.name = name
        self.duration = duration
        self.status = status
        self.song_dir = song_dir 
    
    def serialize(self):
        return {
            'name': self.name,
            "duration": self.duration,
            "status": self.status,
            "song_dir": self.song_dir
        }

class MusicPlayer:
    def __init__(self, folder_dir):
        # self.song = song
        self.folder_dir = folder_dir
        self.player = vlc.MediaPlayer()
        self.playlist = set()

    def play_playlist(self, song):
        os.system("cls")
        print("\nLoading song...")

        # create a media player object
        self.player = vlc.MediaPlayer(f"{self.folder_dir}/{song}")
        base_padding = max([len(song_name["name"]) for song_name in self.playlist]) + 5

        def _show_playlist(status):
            os.system("cls")
            print("\n")

            print(f"{'Music Name'.ljust(base_padding)} Time      Status")
            print("=" * (base_padding + 25))
            
            for item in self.playlist:
                if item['name'] == song and (status.Playing or status.Paused):
                    playing_status = "Now Playing..." if self.player.get_state() == status.Playing else ("Paused" if self.player.get_state() == status.Paused else "Done")
                    print("-" * (base_padding + 25))
                    print(f"{item['name'].replace('.mp3','').ljust(base_padding)} {item['duration']}     {playing_status}")
                    print("-" * (base_padding + 25))
                elif self.player.get_state == status.Ended:
                    print(f"{item['name'].replace('.mp3','').ljust(base_padding)} {item['duration']}     '{item['status']}'")
                else:
                    print(f"{item['name'].replace('.mp3','').ljust(base_padding)} {item['duration']}     {item['status']}")

        status = "Done"
        try:
            self.player.play()
            time.sleep(1.5)
            state = self.player.get_state()

            while self.player.is_playing() or state.Paused:
                status = "Done"
                if keyboard.is_pressed(" "):
                    if self.player.get_state() == state.Playing:
                        self.player.pause()
                    else:
                        self.player.play()
                elif keyboard.is_pressed("n"):
                    status = "Skipped"
                    break

                state = self.player.get_state()
                time.sleep(1)
                _show_playlist(state)
                if state == state.Ended:
                    break

            time.sleep(1)
            self.player.stop()
            return True, status
            
        except Exception as ex:
            print(ex)
            return False

    def load_playlist(self):
        playlist = []

        for _, _, songs in os.walk(self.folder_dir):
            for song in songs:
                if ".mp3" in song:
                    status = ""
                    duration = ""
                    self.player = vlc.MediaPlayer(f"{self.folder_dir}/{song}")
                    
                    try:
                        self.player.play()
                        time.sleep(0.3)
                        duration = str(timedelta(seconds=int("{:.0f}".format(self.player.get_length() / 1000))))
                        self.player.stop()
                        
                    except Exception:
                        self.player.stop()
                        status = "Can't read"

                    duration = duration[2:] if duration[2:] != "00:00" else "--:--"
                    song = Song(song, duration, status, self.folder_dir)
                    playlist.append(song.serialize())
        
        return playlist

    def music_player(self, play_shuffle=False):

        print("\nPlaylist is loading...")
        self.playlist = self.load_playlist()
        
        if play_shuffle:
            self.playlist = sample(self.playlist, len(self.playlist))
            
            for _ in self.playlist:
                song = choice([name['name'] for name in self.playlist if name['status'] == ""])
                
                result, status = self.play_playlist(song)
                if not result:
                    status = "*Can't play"

                # save the last song as done playing
                for s in [item for item in self.playlist if item["name"] == song]:
                    s.update((key, status) for key, value in s.items() if key == "status")

        else:
            for song in self.playlist:
                if song['name'] not in self.done_playing:
                    if self.play_playlist(song['name']):
                        # save the last song as done playing
                        self.done_playing.append(song['name'])
            
        exit()

                
if __name__ == "__main__":
    mp = MusicPlayer(folder_dir=music_dir)
    mp.music_player(play_shuffle=True)