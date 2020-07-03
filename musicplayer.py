import vlc
import os
import subprocess
import time
import keyboard
from datetime import timedelta
from random import sample, choice
from pathlib import Path

AUDIOFILE_EXT = ["wav", "mid","mp3", "aif"]
TITLE_PADDING = 40
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
    def __init__(self):
        # self.song = song
        self.folder_dir = ""
        self.audio_file = ""
        self.player = None
        self.toggle_shuffle = False
        self.all_music = False
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
            seconds = detal_min_sec[3:5]
            result = ":".join([minutes, seconds])

        return result

    def load_media(self, is_playlist=True):
        playlist = []

        def _check_files(file_count=0):
            os.system("cls")
            print(f"\nChecking audio files..." + (f"{file_count} music files found so far." if self.all_music else ""))

        # checks for audio file extension names
        def _is_audiofile(filename):
            file_ext = filename.split(".")[-1]
            return file_ext.lower() in AUDIOFILE_EXT

        def _get_metadata(filename, subdir):
            # check file if audio file
            if _is_audiofile(filename):
                file_name = f"{subdir}/{filename}" if is_playlist else filename
                status = ""
                duration = ""

                try:
                    # create a new instance of MediaPlayer using audio file
                    self.player = vlc.MediaPlayer(file_name)
                    # "play the song" very fast for us to get the music length
                    self.player.play()
                    # # mute the sound so we don't hear anything while parsing the media data
                    self.player.audio_set_volume(0)
                    time.sleep(0.1)

                    # get details of song
                    media = self.player.get_media()
                    # get the meta data
                    media.get_mrl()
                    # parse meta data
                    media.parse()
                    # track number from meta data
                    track_no = 0 if media.get_meta(5) is None else media.get_meta(5)
                    # title from meta data
                    title = "" if media.get_meta(0) is None else media.get_meta(0)
                    # artist from meta data
                    artist = "" if media.get_meta(1) is None else media.get_meta(1)
                    
                    # song length in timedelta format (mm:ss.micro seconds)
                    duration = self.get_duration()
                    
                except Exception:
                    status = "Can't read"

                self.player.stop()
                self.player = None

                # ths handles "missing header" error during media parsing
                if track_no != 0 and title and artist:
                    song = Song(filename, track_no, title, artist, duration, status, subdir)
                    # append the song details to playlist
                    playlist.append(song.serialize())


        _check_files()
        time.sleep(1)
        
        if self.all_music:
            file_counter = 1
            # walk through all the files in the user directory folder
            for subdir, _, music_files in os.walk(f"{Path.home()}\\Music"):
                for audiofile in music_files:
                    _get_metadata(audiofile, subdir)
                    _check_files(file_counter)
                    file_counter += 1
                    
        # check if folder directory exist
        elif is_playlist and os.path.isdir(self.folder_dir):
            # walk through all the files in the directory folder
            for audiofile in os.listdir(self.folder_dir):
                _get_metadata(audiofile, self.folder_dir)
            
        elif os.path.isfile(self.audio_file):
            _get_metadata(self.audio_file, self.folder_dir)

        self.player = None
        return playlist

    def update_playlist(self, song_name, key, value):
        # update self.playlist by song name, assuming song name is unique
        for song in [song for song in self.playlist if song["name"] == song_name]:
            song.update((k, value) for k, v in song.items() if k == key)

    def music_player(self, playlist_folder, play_shuffle=False, play_all_music=False):
        self.folder_dir = playlist_folder
        self.toggle_shuffle = play_shuffle
        self.all_music = play_all_music

        os.system("cls")
        if len(self.playlist) <= 0:
            # initialize player by parsing meta data of audio file(s)
            self.playlist = self.load_media()

            if len(self.playlist) <= 0:
                print("**No audio files found.")
                time.sleep(3)
                return

        os.system("cls")
        print(f"\n{'Shuffling' if self.toggle_shuffle else 'Loading'} playlist...")
        time.sleep(1)

        # Internal method: actual music player for playlist, 
        # it also show renders the table view of music list
        def _play(current_song):
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
                print(f" #    {'Title'.ljust(TITLE_PADDING)} {'Artist'.ljust(ARTIST_NAME_PADDING)} Time      Status")
                print("=" * (TITLE_PADDING + ARTIST_NAME_PADDING + 25))
                
                total = len(self.playlist)
                current_song_idx = self.playlist.index(([song for song in self.playlist if current_song in song["name"]][0]))

                song_idx = (0 if current_song_idx < 25 else current_song_idx)
                alpha = (song_idx - 12) if (song_idx - 12) >= 0 else song_idx
                omega = (alpha + 25) if (alpha + 25) <= total else total

                if total >= 25 and (omega == total):
                    alpha = (omega - 25)

                # song names list, sliced to 25 songs
                for song in self.playlist[alpha:omega]:
                    track_no = song["track"].zfill(2).ljust(4)
                    # determine the length of title, limit the size (to TITLE_PADDING value) if necessary
                    title = f"{song['title'] if len(song['title']) < TITLE_PADDING else song['title'][:(TITLE_PADDING - 4)].strip() + '...'}".ljust(TITLE_PADDING)
                    artist = f"{song['artist'] if len(song['artist']) < ARTIST_NAME_PADDING else song['artist'][:(ARTIST_NAME_PADDING - 3)].strip() + '...'}".ljust(ARTIST_NAME_PADDING)

                    # Now Playing, check if song's status is Playing or Paused
                    if song['name'] == current_song and (status.Playing or status.Paused):
                        duration = self.get_duration(time_ticker)
                        print("-" * (TITLE_PADDING + ARTIST_NAME_PADDING + 28))
                        print(f" {track_no} {title} {artist} {duration}  {_playing_status(status)}")
                        print("-" * (TITLE_PADDING + ARTIST_NAME_PADDING + 28))

                        # update the "duration" meta data if it has no (--:--) duration value
                        if song['duration'] == "--:--":
                            self.update_playlist(current_song, key="duration", value=duration)    
                    else:
                        print(f" {track_no} {title} {artist} {song['duration']}     {song['status']}")
                
                # playlist footer
                print("=" * (TITLE_PADDING + ARTIST_NAME_PADDING + 28))
                print(f" [F5] {'Shuffle' if not self.toggle_shuffle else 'Unshuffle'} \t[F9] {'Pause' if self.player.is_playing() else 'Play'} \t[F10] Next \t[F4] Stop (navigate to menu)")

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
                        # to avoid skipping multiple times at once
                        time.sleep(1) 
                        break
                    # toggle shuffle playlist
                    elif keyboard.is_pressed("f5"):
                        status = "Shuffle"
                        break
                    # stop the song
                    elif keyboard.is_pressed("f4"):
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


        # Main function of music_player
        # shuffle mode playlist iterator
        if self.toggle_shuffle:
            self.playlist = sample(self.playlist, len(self.playlist))
            
            for _ in self.playlist:
                unplayed_list = [song for song in self.playlist if song["status"] == ""]

                if len(unplayed_list) > 0:
                    # get random name of song from playlist that haven't played yet.
                    song = choice(unplayed_list)
                    self.folder_dir = song["song_dir"]
                    
                    # play the song
                    (is_done_playing, song_status) = _play(song["name"])
                    
                    # stop playing the playlist and return to menu
                    if song_status == "Stopped":
                        return
                    # toggle shuffle mode
                    elif song_status == "Shuffle":
                        # call itself with parameters to shuffle/unshuffle music list
                        return self.music_player(playlist_folder=self.folder_dir, play_shuffle=(not self.toggle_shuffle))

                    # something went wrong while playing music
                    if not is_done_playing:
                        # set the status to "*Can't play"
                        status = "*Can't play"

                    # update status of the song in self.playlist (marked as "Done", "Skipped" or "Can't play")
                    self.update_playlist(song["name"], key="status", value=song_status)

        # ordered playlist
        else:
            # sort songs by track number
            self.playlist = sorted(self.playlist, key=lambda x: int(x["track"]))
            
            # get song from playlist that haven't played yet.
            for song in [song for song in self.playlist if song["status"] == ""]:
                self.folder_dir = song["song_dir"]
                # play the song
                (is_done_playing, song_status) = _play(song["name"])

                # stop playing the playlist and return to menu
                if song_status == "Stopped":
                    break
                # toggle shuffle mode
                elif song_status == "Shuffle":
                    # call itself with parameters to shuffle/unshuffle music list
                    return self.music_player(playlist_folder=self.folder_dir, play_shuffle=(not self.toggle_shuffle))

                # something went wrong while playing music   
                if not is_done_playing:
                    # set the status to "*Can't play"
                    song_status = "*Can't play"

                # update status of the song in self.playlist (marked as "Done", "Skipped" or "Can't play")
                self.update_playlist(song['name'], key="status", value=song_status)  

        # reset the playlist
        self.playlist = []  
        return

    def compact_music_player(self, is_playlist, playlist_folder="", music_file="", play_shuffle=False):
        self.folder_dir = playlist_folder
        self.toggle_shuffle = play_shuffle

        os.system("cls")
        if len(self.playlist) <= 0:
            # for single music player parameter
            if not is_playlist and music_file:
                self.audio_file = music_file
            
            self.playlist = self.load_media(is_playlist=is_playlist)

            if len(self.playlist) <= 0:
                print("**No audio file found.")
                time.sleep(3)
                return

        # Internal method: actual music player for playlist, 
        # it also show renders the table view of music list
        def _play(music_name=""):
            # create a new instance of MediaPlayer using audio file
            self.player = vlc.MediaPlayer(self.audio_file)
            arrow_counter = 0
            time_ticker = 0.1
            scroll_ticker = 0.1

            def _show_song(status):
                os.system("cls")
        
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

                # song names list, sliced to 25 songs
                for song in self.playlist:
                    if music_name and music_name == song["name"]:
                        track_no = (song["track"] + ".").ljust(4)
                        # determine the length of title, limit the size (to TITLE_PADDING value) if necessary
                        title = f"{song['title'] if len(song['title']) < TITLE_PADDING else song['title'][:(TITLE_PADDING - 4)].strip() + '...'}".ljust(TITLE_PADDING)
                        artist = f"{song['artist'] if len(song['artist']) < ARTIST_NAME_PADDING else song['artist'][:(ARTIST_NAME_PADDING - 3)].strip() + '...'}".ljust(ARTIST_NAME_PADDING)

                        # Now Playing, check if song's status is Playing or Paused
                        if status.Playing or status.Paused:
                            duration = self.get_duration(time_ticker)
                            track_details = f" {track_no} {title}  {artist}  {duration} {_playing_status(status)}    "
                            animate_track_details = track_details[int(scroll_ticker * 10):(len(track_details) - 1) + int(scroll_ticker * 10)] + track_details[0:int(scroll_ticker * 10)]

                            print(" " + "-" * (TITLE_PADDING + ARTIST_NAME_PADDING + 33))
                            print(" " + animate_track_details)
                            print(" " + "-" * (TITLE_PADDING + ARTIST_NAME_PADDING + 33))

                            # update the "duration" meta data if it has no (--:--) duration value
                            if song['duration'] == "--:--":
                                self.update_playlist(current_song, key="duration", value=duration)
                        else:
                            print(f" {track_no} {title} {artist} {song['duration']}     {song['status']}")
                        break

            status = "Done"
            try:
                self.player.play()
                time.sleep(1)
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
                        # to avoid skipping multiple times at once
                        time.sleep(1) 
                        break
                    # toggle shuffle playlist
                    elif keyboard.is_pressed("f5"):
                        status = "Shuffle"
                        break
                    # stop the song
                    elif keyboard.is_pressed("f4"):
                        status = "Stopped"
                        break

                    # get song state every second
                    state = self.player.get_state()
                    # show playlist view
                    _show_song(state)

                    # run ticker while song is playing
                    if self.player.is_playing():
                        time_ticker += 0.17
                        scroll_ticker += 0.1
                        arrow_counter += 1

                    if scroll_ticker >= 9.5:
                        scroll_ticker = 0
                    
                    # used in "<<<Playing>>>" status animation
                    if arrow_counter >= 4:
                        arrow_counter = 0

                    time.sleep(0.1)
                    
                    # song ended return and get the next song on the list
                    if state == state.Ended:
                        break

                self.player.stop()
                return (True, status)
                
            except Exception:
                return (False, "Can't play")


        # playlist music player
        if is_playlist and self.folder_dir:
            os.system("cls")
            print(f"\n{'Shuffling' if self.toggle_shuffle else 'Loading'} playlist...")
            time.sleep(1)
            
            if self.toggle_shuffle:
                self.playlist = sample(self.playlist, len(self.playlist))
                
                for _ in self.playlist:
                    unplayed_list = [song for song in self.playlist if song["status"] == ""]

                    if len(unplayed_list) > 0:
                        # get random name of song from playlist that haven't played yet.
                        song_choice = choice(unplayed_list)
                        self.folder_dir = song_choice["song_dir"]

                        self.audio_file = f"{self.folder_dir}/{song_choice['name']}"
                        # play the song
                        (is_done_playing, song_status) = _play(song_choice["name"])
                        
                        # stop playing the playlist and return to menu
                        if song_status == "Stopped":
                            return
                        # toggle shuffle mode
                        elif song_status == "Shuffle":
                            return self.compact_music_player(playlist_folder=self.folder_dir, is_playlist=is_playlist, play_shuffle=(not self.toggle_shuffle))

                        # something went wrong while playing music
                        if not is_done_playing:
                            # set the status to "*Can't play"
                            status = "*Can't play"

                        # update status of the song in self.playlist (marked as "Done", "Skipped" or "Can't play")
                        self.update_playlist(song_choice["name"], key="status", value=song_status)
            
            else:
                # sort songs by track number (asc order)
                self.playlist = sorted(self.playlist, key=lambda x: int(x["track"]))

                # get song from playlist that haven't played yet.
                for song in [song for song in self.playlist if song["status"] == ""]:
                    self.folder_dir = song["song_dir"]
                    self.audio_file = f"{self.folder_dir}/{song['name']}"
                    
                    # play the song
                    (is_done_playing, song_status) = _play(song["name"])
                    
                    # stop playing the playlist and return to menu
                    if song_status == "Stopped":
                        return
                    # toggle shuffle mode
                    elif song_status == "Shuffle":
                        return self.compact_music_player(playlist_folder=self.folder_dir, is_playlist=is_playlist, play_shuffle=(not self.toggle_shuffle))

                    # something went wrong while playing music
                    if not is_done_playing:
                        # set the status to "*Can't play"
                        status = "*Can't play"

                    # update status of the song in self.playlist (marked as "Done", "Skipped" or "Can't play")
                    self.update_playlist(song["name"], key="status", value=song_status)

        # single music player
        elif not is_playlist and music_file:
            self.audio_file = music_file

            os.system("cls")
            print(f"\nLoading music...")
            time.sleep(1)
            
            songname = self.playlist[0]["name"]
            # play the song
            (is_done_playing, song_status) = _play(songname)
            
            # stop playing the playlist and return to menu
            if song_status == "Stopped":
                return

            # something went wrong while playing music
            if not is_done_playing:
                # set the status to "*Can't play"
                status = "*Can't play"

            # update status of the song in self.playlist (marked as "Done", "Skipped" or "Can't play")
            self.update_playlist(songname, key="status", value=song_status)

        # reset the playlist
        self.playlist = []
        return


                
if __name__ == "__main__":
    while True:
        os.system("cls")
        os.system("CMDOW @ /ren \"Music Player\" /mov 625 -35 /siz 770 600")
        print("\n","=" * 40)
        print("\t[1] Play a music")
        print("\t[2] Playlist")
        print("\t[3] Playlist (compact mode)")
        print("\t[4] Search computer for music files.")
        print("\t[5] Play all music files from user directory.")
        print("\t[0] Exit")
        print("\n","=" * 40)
        option = input("\tYour input here: ").strip()
        print(" " + "-" * 40)

        if option == "1":
            audio_file = input("Put your music filename here (i.e.: C:\\Users\\Music\\Song.mp3): ")

            if os.path.isfile(audio_file):
                # set the location of command prompt
                os.system("CMDOW @ /ren \"Music Player\" /mov 601 -35 /siz 790 110")

                mp = MusicPlayer()
                mp.compact_music_player(is_playlist=False, music_file=audio_file)

        elif option == "2":
            music_dir = input("Put your playlist location here (i.e.: C:\\Users\\Music\\Playlist): ")

            if os.path.isdir(music_dir):
                mp = MusicPlayer()
                mp.music_player(playlist_folder=music_dir)

        elif option == "3":
            music_dir = input("Put your playlist location here (i.e.: C:\\Users\\Music\\Playlist): ")

            if os.path.isdir(music_dir):
                # set the location of command prompt
                os.system("CMDOW @ /ren \"Music Player\" /mov 601 -35 /siz 790 110")

                mp = MusicPlayer()
                mp.compact_music_player(is_playlist=True, playlist_folder=music_dir)

        elif option == "4":
            audio_filename = input("Put the song title or description here (i.e.: \"music\", \"music.mp3\" or \".mp3\" ): ").strip().lower()
            
            print("\nSearching for audio files...\n")
            time.sleep(2)
            extension_names = ' OR .'.join(AUDIOFILE_EXT)
            # open windows explorer and look for files using queries
            explorer = f'explorer /root,"search-ms:query=name:{audio_filename} AND type:(.{extension_names}) AND (size:medium OR large)&crumb=location:{Path.home()}&"'
            subprocess.Popen(explorer, shell=False, stdin=None,stdout=None, stderr=None, close_fds=False)
            
            print("Check the files we found in Windows Explorer folder..")
            time.sleep(10)
        
        elif option == "5":
            mp = MusicPlayer()
            mp.music_player(play_all_music=True, playlist_folder=f"{Path.home()}\\Music")

        elif option == "0":
            exit()