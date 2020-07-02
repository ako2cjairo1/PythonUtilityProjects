import vlc
import os
import subprocess
import time
import keyboard
import concurrent.futures as task
from datetime import timedelta
from random import sample, choice
from pathlib import Path

AUDIOFILE_EXT = ["wav", "mid","mp3", "aif"]
TITLE_PADDING = 45
ARTIST_NAME_PADDING = 20

class Song:
    def __init__(self, name, track, title, artist, duration, status, song_dir):
        self.name = name
        self.track = track
        self.title = title
        self.artist = artist
        self.duration = duration
        self.status = status
        self.song_dir = song_dir 
    
    def serialize(self):
        return {
            "name": self.name,
            "track": self.track,
            "title": self.title,
            "artist": self.artist,
            "duration": self.duration,
            "status": self.status,
            "song_dir": self.song_dir
        }

class MusicPlayer:
    def __init__(self, folder_dir):
        # self.song = song
        self.folder_dir = folder_dir
        self.player = vlc.MediaPlayer()
        self.toggle_shuffle = False
        self.playlist = set()

    def get_duration(self, time_ticker=0):
        result = "--:--"
        get_length = (self.player.get_length() / 1000)
        # get duration of song in seconds minus a buffer of 10 seconds
        seconds = int("{:.0f}".format(get_length - (10 if get_length > 0 else 0))) - time_ticker

        if seconds > 0:
            # convert to timedelta(HH:mm:SS.ms) sliced to minutes and seconds
            detal_min_sec = str(timedelta(seconds=seconds))[2:]
            # extract minute value from delta time
            minutes = detal_min_sec[:2]
            # extract seconds value from delta time
            seconds = detal_min_sec[3:]
            result = ":".join([minutes, seconds])

        return result

    def play_playlist(self, current_song):
        # create a new instance of MediaPlayer using audio file
        self.player = vlc.MediaPlayer(f"{self.folder_dir}/{current_song}")
        arrow_counter = 0
        time_ticker = 0

        def _show_playlist(status):
            os.system("cls")
            print("\n")
            
            def _playing_status(state):
                status = "   Done"

                if self.player.get_state() == state.Playing:
                    left_arrows = str(('<' * arrow_counter) if arrow_counter > 0 else "").rjust(3)
                    right_arrows = str(('>' * arrow_counter) if arrow_counter > 0 else "").ljust(3)

                    status = f"{left_arrows}Playing{right_arrows}"
                else:
                    if self.player.get_state() == state.Paused:
                        status = "   Paused"

                return status     

            # playlist header
            print(f" #  {'Title'.ljust(TITLE_PADDING)}{'Artist'.ljust(ARTIST_NAME_PADDING)} Time      Status")
            print("=" * (TITLE_PADDING + ARTIST_NAME_PADDING + 25))
            
            current_song_idx = self.playlist.index(([song for song in self.playlist if current_song in song["name"]][0]))
            begin_idx = (0 if current_song_idx <= 25 else current_song_idx)
            end_idx = (25 if current_song_idx <= 25 else (current_song_idx + 25))

            alpha = begin_idx if ((len(self.playlist) - begin_idx) - end_idx) <= 25 else begin_idx - 12
            omega = end_idx if end_idx < (len(self.playlist) - 1) else len(self.playlist)

            if omega == (len(self.playlist) - 1) and len(self.playlist) > 25:
                alpha = omega - 25

            # song names list, sliced to 25 songs
            for song in self.playlist[alpha:omega]:
                track_no = song["track"].zfill(2)
                # determine the length of title, limit the size (to TITLE_PADDING value) if necessary
                title = f"{song['title'] if len(song['title']) < TITLE_PADDING else song['title'][:(TITLE_PADDING - 4)].strip() + '...'}".ljust(TITLE_PADDING)
                artist = f"{song['artist'] if len(song['artist']) < ARTIST_NAME_PADDING else song['artist'][:(ARTIST_NAME_PADDING - 3)].strip() + '...'}".ljust(ARTIST_NAME_PADDING)

                # Now Playing, check if song's status is Playing or Paused
                if song['name'] == current_song and (status.Playing or status.Paused):
                    duration = self.get_duration(time_ticker)
                    print("-" * (TITLE_PADDING + ARTIST_NAME_PADDING + 25))
                    print(f" {track_no} {title}{artist} {duration}  {_playing_status(status)}")
                    print("-" * (TITLE_PADDING + ARTIST_NAME_PADDING + 25))

                    # update the "duration" meta data if it has no (--:--) duration value
                    if song['duration'] == "--:--":
                        self.update_playlist(current_song, key="duration", value=duration)
                
                # status is Ended playing
                elif self.player.get_state == status.Ended:
                    print(f" {track_no} {title}{artist} {song['duration']}     {song['status']}")
                
                else:
                    print(f" {track_no} {title}{artist} {song['duration']}     {song['status']}")
            
            # playlist footer
            print("-" * (TITLE_PADDING + ARTIST_NAME_PADDING + 25))
            print(f" [F5] {'Shuffle' if not self.toggle_shuffle else 'Unshuffle'} \t[F9] {'Pause' if self.player.is_playing() else 'Play'} \t[F10] Next \t[ESC] Stop (navigate to menu)")
            # print("-" * (TITLE_PADDING + ARTIST_NAME_PADDING + 25))

        status = "Done"
        try:
            self.player.play()
            time.sleep(0.3)
            self.player.audio_set_volume(100)
            state = self.player.get_state()

            while self.player.is_playing() or state.Paused:
                status = "Done"

                # play or pause the song
                if keyboard.is_pressed("f9"):
                    if self.player.is_playing():
                        self.player.pause()
                    else:
                        self.player.play()
                # skip the song
                elif keyboard.is_pressed("f10"):
                    status = "Skipped"
                    break
                # toggle shuffle playlist
                elif keyboard.is_pressed("f5"):
                    status = "Shuffle"
                    break
                # stop the song
                elif keyboard.is_pressed("esc"):
                    status = "Stopped"
                    break

                # get song state every second
                state = self.player.get_state()
                # show playlist view
                _show_playlist(state)

                # run ticker while song is playing
                if self.player.is_playing():
                    time_ticker += 1
                    arrow_counter += 1
                
                # used in "<<<Playing>>>" status animation
                if arrow_counter >= 4:
                    arrow_counter = 0

                time.sleep(1)
                
                # song ended return and get the next song on the list
                if state == state.Ended:
                    break

            self.player.stop()
            return (True, status)
            
        except Exception:
            return (False, "Can't play")

    def load_playlist(self):
        playlist = []

        # checks for audio file extension names
        def _is_audiofile(filename):
            file_ext = filename.split(".")[-1]
            return file_ext.lower() in AUDIOFILE_EXT

        def _get_metadata(filename):
            # check file if audio file
            if _is_audiofile(filename):
                # create a new instance of MediaPlayer using audio file
                self.player = vlc.MediaPlayer(f"{self.folder_dir}/{filename}")
                # get details of song
                media = self.player.get_media()
                status = ""
                duration = ""

                try:
                    # get the meta data
                    media.get_mrl()
                    # parse meta data
                    media.parse()
                    # track number from meta data
                    track_no = "0" if media.get_meta(5) is None else media.get_meta(5)
                    # title from meta data
                    title = "" if media.get_meta(0) is None else media.get_meta(0)
                    # artist from meta data
                    artist = "" if media.get_meta(1) is None else media.get_meta(1)

                    # "play the song" very fast for us to get the music length
                    self.player.play()
                    # mute the sound so we don't hear anything while parsing the media data
                    self.player.audio_set_volume(0)
                    # this 
                    time.sleep(1)
                    # song length in timedelta format (mm:ss.micro seconds)
                    duration = self.get_duration()
                    self.player.stop()
                
                except Exception:
                    self.player.stop()
                    status = "Can't read"

                song = Song(filename, track_no, title, artist, duration, status, self.folder_dir)
                # append the song details to playlist
                playlist.append(song.serialize())

        # check if folder directory exist
        if os.path.isdir(self.folder_dir):
            # walk through all the files in the directory folder
            with task.ThreadPoolExecutor() as exec:
                exec.map(_get_metadata, os.listdir(self.folder_dir))

        return playlist

    def update_playlist(self, song_name, key, value):
        # update self.playlist by song name, assuming song name is unique
        for song in [song for song in self.playlist if song["name"] == song_name]:
            song.update((k, value) for k, v in song.items() if k == key)

    def music_player(self, play_shuffle=False):
        self.toggle_shuffle = play_shuffle

        if len(self.playlist) <= 0:
            print("\nChecking audio files...")
            self.playlist = self.load_playlist()

            if len(self.playlist) <= 0:
                print("**No audio files found.")
                time.sleep(3)
                return

        os.system("cls")
        print(f"\n{'Shuffling' if self.toggle_shuffle else 'Loading'} playlist...")
        time.sleep(1)

        if self.toggle_shuffle:
            self.playlist = sample(self.playlist, len(self.playlist))
            
            for _ in self.playlist:
                # get random name of song from playlist that haven't played yet.
                song = choice([song['name'] for song in self.playlist if song['status'] == ""])
                
                # play the song
                (is_done_playing, song_status) = self.play_playlist(song)
                
                # stop playing the playlist and return to menu
                if song_status == "Stopped":
                    return
                # toggle shuffle mode
                elif song_status == "Shuffle":
                    return self.music_player(play_shuffle=(not self.toggle_shuffle))

                # something went wrong while playing music
                if not is_done_playing:
                    # set the status to "*Can't play"
                    status = "*Can't play"

                # update status of the song in self.playlist (marked as "Done", "Skipped" or "Can't play")
                self.update_playlist(song, key="status", value=song_status)

        else:
            # sort songs by track number
            self.playlist = sorted(self.playlist, key=lambda x: int(x["track"]))
            
            # get song from playlist that haven't played yet.
            for song in [song for song in self.playlist if song["status"] == ""]:
                # play the song
                (is_done_playing, song_status) = self.play_playlist(song["name"])

                # stop playing the playlist and return to menu
                if song_status == "Stopped":
                    break
                # toggle shuffle mode
                elif song_status == "Shuffle":
                    return self.music_player(play_shuffle=(not self.toggle_shuffle))

                # something went wrong while playing music   
                if not is_done_playing:
                    # set the status to "*Can't play"
                    song_status = "*Can't play"

                # update status of the song in self.playlist (marked as "Done", "Skipped" or "Can't play")
                self.update_playlist(song['name'], key="status", value=song_status)  

        # reset the playlist
        self.playlist = []  
        return

                
if __name__ == "__main__":
    while True:
        os.system("cls")
        print("\n","=" * 40)
        print("\t[1] Play songs")
        print("\t[2] Playlist of songs (shuffled)")
        print("\t[3] Search computer for audio files.")
        print("\t[0] Exit")
        print("\n","=" * 40)
        option = input("\tYour input here: ").strip()
        print(" ","-" * 40)

        if option == "1" or option == "2":
            music_dir = input("Put your playlist location here (i.e.: C:\\Users\\Music\\Playlist): ")

            if os.path.isdir(music_dir):
                mp = MusicPlayer(folder_dir=music_dir)
                mp.music_player()

        elif option == "3":
            audio_filename = input("Put the song title or description here (i.e.: \"music\", \"music.mp3\" or \".mp3\" ): ").strip().lower()
            
            print("\nSearching for audio files...\n")
            time.sleep(2)
            extension_names = ' OR .'.join(AUDIOFILE_EXT)
            # open windows explorer and look for files using queries
            explorer = f'explorer /root,"search-ms:query=name:{audio_filename} AND type:(.{extension_names}) AND (size:medium OR large)&crumb=location:{Path.home()}&"'
            subprocess.Popen(explorer, shell=False, stdin=None,stdout=None, stderr=None, close_fds=False)
            
            print("Check the files we found in Windows Explorer folder..")
            time.sleep(10)

        elif option == "0":
            exit()