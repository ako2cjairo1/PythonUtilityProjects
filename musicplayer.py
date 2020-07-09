import vlc
import os
import sys
import subprocess
import time
import keyboard
import json
from argparse import ArgumentParser
import concurrent.futures as task
from datetime import timedelta
from random import sample, choice
from pathlib import Path
from itertools import repeat

MUSIC_DB_FILE = "Music Database.json"
AUDIOFILE_EXT = ["wav", "mid","mp3", "aif"]
TITLE_PADDING = 40
ARTIST_NAME_PADDING = 20

class Song:
    def __init__(self, name, track, title, artist, genre, duration, status, song_dir):
        self.name = name
        self.track = track
        self.title = title
        self.artist = artist
        self.duration = duration
        self.status = status
        self.song_dir = song_dir
        self.genre = genre
    
    def serialize(self):
        return {
            "name": self.name,
            "track": self.track,
            "title": self.title,
            "artist": self.artist,
            "genre": self.genre,
            "duration": self.duration,
            "status": self.status,
            "song_dir": self.song_dir
        }

class MusicPlayer:
    def __init__(self):
        self.folder_dir = ""
        self.audio_file = ""
        self.player = None
        self.volume = 70
        self.toggle_shuffle = False
        self.all_music = False
        self.random_music = False
        self.playlist = set()
        self.title = ""
        self.artist = ""
        self.genre = ""

    def get_duration(self, media=None, ticker=0):
        result = "--:--"

        microsec = media.get_duration() if media else self.player.get_length()
        get_length = (microsec / 1000)
        # get duration of song in seconds minus a buffer of 10 seconds
        seconds = int("{:.0f}".format(get_length - (10 if get_length > 0 else 0))) - ticker

        if seconds > 0:
            # convert to timedelta(HH:mm:SS.ms) sliced to minutes and seconds
            detal_min_sec = str(timedelta(seconds=seconds))[2:]
            # extract minute value from delta time
            minutes = detal_min_sec[:2]
            # extract seconds value from delta time
            seconds = detal_min_sec[3:5]
            result = ":".join([minutes, seconds])
        return result


    def load_music_from_json(self):
        song_db = []
        if os.path.isfile(MUSIC_DB_FILE):
            with open(MUSIC_DB_FILE, "r", encoding="utf-8") as fr:
                json_db = json.load(fr)
                song_db.extend(json_db)
        return song_db


    def search_song_by(self, title="", artist="", genre=""):
        def _isFound(song):

            def _is_possible_match(keyword, meta_keyword):
                keyword_list = keyword.split()
                # if keyword is more than 2 words...
                if len(keyword_list) > 2:
                    match_count = 0

                    for word in keyword_list:
                        # let's count matching words
                        if word in meta_keyword:
                            match_count += 1
                    if match_count < 3:
                        # not enough matching words
                        return False
                    else:
                        # possible match found
                        return True

            title_filter = (title.strip().lower() in song["title"].strip().lower())
            artist_filter = (artist.strip().lower() in song["artist"].strip().lower())
            genre_filter = (genre.strip().lower() in song["genre"].strip().lower())

            if title and artist and genre:
                if not title_filter:
                    title_filter = _is_possible_match(title, song["title"].strip().lower())
                if not artist_filter:
                    artist_filter = _is_possible_match(artist, song["artist"].strip().lower())
                if not genre_filter:
                    genre_filter = _is_possible_match(genre, song["genre"].strip().lower())

                if title == artist == genre:
                    return (title_filter or artist_filter or genre_filter)
                elif title and artist:
                    return (title_filter and artist_filter)
                elif artist and genre:
                    return (artist_filter and genre_filter)
                elif title and genre:
                    return (title_filter and genre_filter)
                else:
                    return (title_filter and artist_filter and genre_filter)

        songs = self.load_music_from_json()

        filtered_playlist = []
        for song in songs:
            if _isFound(song):
                filtered_playlist.append(song)
        
        if len(filtered_playlist) > 0:
            return filtered_playlist
        else:
            return None


    def load_media(self, is_playlist=True):
        playlist = []
        self.playlist_counter = 0

        def _update_music_db():
            update_master_song_db = []
            isUpdate = False

            if not os.path.isfile(MUSIC_DB_FILE):
                for item in playlist:
                    # parse the playlist and create a Song object
                    song = Song(item["name"], item["track"], item["title"], item["artist"], item["genre"], item["duration"], item["status"], item["song_dir"]).serialize()
                    # append the parsed song to update_master_song_db
                    update_master_song_db.append(song)

                # self.playlist = update_master_song_db

            else:
                new_songs = []
                master_song_db = self.load_music_from_json()

                for item in playlist:
                    # check if the item already exis in our database from json
                    if not self.isFound(master_song_db, item["name"], item["song_dir"]):
                        # parse the playlist and create a Song object
                        song = Song(item["name"], item["track"], item["title"], item["artist"], item["genre"], item["duration"], item["status"], item["song_dir"]).serialize()
                        # append the parsed song to update_master_song_db
                        new_songs.append(song)
                
                # flag that the master list is updating..
                if len(new_songs) > 0:
                    # insert the new songs to master list of songs
                    master_song_db.extend(new_songs)
                    update_master_song_db = master_song_db
                    isUpdate = True
                    # self.playlist = new_songs
                    
                else:
                    # self.playlist = playlist
                    # we don't need to update the master list
                    return

            if len(update_master_song_db) > 0:
                if isUpdate:
                    print(f" Updating music database profile...")
                else:
                    print(" Creating music database profile...")
                time.sleep(1)

                # write/re-write the update_master_song_db with the new song(s)
                with open(MUSIC_DB_FILE, "w", encoding="utf-8") as fw:
                    json.dump(update_master_song_db, fw, indent=4)

            if isUpdate:
                print(f" {len(new_songs)} music added in database.")
                time.sleep(1)
            return

        # checks for audio file extension names
        def _is_audiofile(filename):
            file_ext = filename.split(".")[-1]
            return file_ext.lower() in AUDIOFILE_EXT

        # get meta data details of music file
        def _get_metadata(filename, subdir):
            # check file if audio file
            if _is_audiofile(filename):
                file_name = f"{subdir}/{filename}" if is_playlist else filename
                status = ""
                duration = "--:--"

                try:
                    # create a new instance of MediaPlayer using audio file
                    self.player = vlc.MediaPlayer(file_name)

                    # get details of song
                    media = self.player.get_media()
                    # get the meta data
                    media.get_mrl()
                    # parse meta data
                    media.parse()
                    
                    # title from meta data
                    title = "" if media.get_meta(0) is None else media.get_meta(0)
                    # artist from meta data
                    artist = "" if media.get_meta(1) is None else media.get_meta(1)
                    # artist from meta data
                    genre = "" if media.get_meta(2) is None else media.get_meta(2)
                    # track number from meta data
                    track_no = 0 if media.get_meta(5) is None else media.get_meta(5)
                    # song length in timedelta format (mm:ss.micro seconds)
                    duration = self.get_duration(media=media)
                    
                except Exception:
                    status = "Err"

                
                # ths handles "missing header" error during media parsing
                # let's check at least one of of required meta data
                if title and (track_no or artist or genre):
                    song = Song(filename, track_no, title, artist, genre, duration, status, subdir)
                    # append the song details to playlist
                    return song.serialize()
                    # playlist.append(song.serialize())
                    # self.playlist_counter += 1
                    # os.system("cls")
                    # print("\nThis may take a while. Please wait...")
                    # print(f"Discovered music file(s): {self.playlist_counter}")
                # else:
                #     print(f"Can't Peak: {filename}")
            return None

        def _display_discovered_songs():
            self.playlist_counter += 1
            os.system("cls")
            print("\n\tThis may take a while. Please wait...")
            print(f"\tDiscovered song(s): {self.playlist_counter}")

        os.system("cls")
        print(f"\n\tChecking music database...")
        time.sleep(1)

        # get music list from json database
        playlist = self.load_music_from_json()
        
        if len(playlist) > 0:
            # all music file loader
            if self.all_music:
                pass

            # random music loader
            elif self.random_music:
                random_songs = []
                music_counter = 0
                retry_counter = 0

                while True:
                    # pick a random song from the playlist
                    random_song = choice(playlist)

                    # let's make sure we have unique song names
                    if not self.isFound(random_songs, random_song["name"], random_song["song_dir"]):
                        # build list of names and corresponding dir
                        random_songs.append(random_song)
                        music_counter += 1
                    
                    retry_counter += 1
                    # we only need 12 random song, if we can't complete 12..
                    # let's wait for the retry_counter to reach 100 tries before break loop
                    if music_counter > 12 or retry_counter >= 100:
                        break

                # let's set the random songs we created in result playlist
                playlist = random_songs

            # from the playlist, filter the "song_dir" 
            elif is_playlist and os.path.isdir(self.folder_dir):
                playlist = [songs for songs in playlist if songs["song_dir"].strip().lower() == str(self.folder_dir).strip().lower()]

            # 1 song loader, check if audio file exist
            elif os.path.isfile(self.audio_file):
                music_filename = self.audio_file.split("\\")
                song_name = music_filename[-1]
                song_dir = self.audio_file.replace("\\" + song_name,"")
                
                playlist = [song for song in playlist if song["name"].strip().lower() == song_name.strip().lower() and song["song_dir"].strip().lower() == song_dir.strip().lower()]
        
        # we didn't find the song/playlist in music database.
        # try to search them starting from user home folder (Path.home())
        if len(playlist) <= 0:
            os.system("cls")
            print("\n\tThis may take a while. Please wait...")
            time.sleep(1)
            
            # all music file loader
            if self.all_music:
                # walk through all the files in the user directory folder
                for subdir, _, music_files in os.walk(Path.home()):
                    if len([folder for folder in ["documents", "downloads", "music"] if folder in subdir.lower()]) <= 0:
                        continue

                    music_files = [music for music in music_files if _is_audiofile(music)]
                    
                    if len(music_files) > 0:
                        with task.ThreadPoolExecutor(max_workers=5) as exec:
                            for song in [song for song in exec.map(_get_metadata, music_files, repeat(subdir)) if song is not None]:
                                playlist.append(song)
                                _display_discovered_songs()
                            time.sleep(2)
            
            # random music loader
            elif self.random_music:
                all_song = []
                # walk through all the files in the user directory folder
                for subdir, _, music_files in os.walk(Path.home()):
                    # check if music_files are audio files
                    music_files = [music for music in music_files if _is_audiofile(music)]
                    if len(music_files) > 0:
                        # create an instance of Song to manage meta data info
                        songs = [Song(name, 0, "", "", "", "", "", subdir).serialize() for name in music_files]
                        
                        with task.ThreadPoolExecutor() as exec:
                            exec.map(all_song.append, songs)
                
                if len(all_song) > 0:
                    rand_music = []
                    retry_counter = 0
                    music_counter = 0
                    while True:
                        # pick a random song from the playlist
                        random_song = choice(all_song)
                    
                        # let's make sure we have unique song names
                        if not self.isFound(rand_music, random_song["name"], random_song["song_dir"]):
                            # build list of names and corresponding dir
                            rand_music.append(random_song)
                            # get the meta data of this selected song
                            _get_metadata(random_song["name"], random_song["song_dir"])
                            music_counter += 1
                        
                        retry_counter += 1
                        # we only need 12 random song, if we can't complete 12..
                        # let's wait for the retry_counter to reach 100 tries before break loop
                        if music_counter > 12 or retry_counter >= 100:
                            break
        
            # playlist loader check if folder directory exist
            elif is_playlist and os.path.isdir(self.folder_dir):
                # walk through all the files in the directory folder
                files = os.listdir(self.folder_dir)
                
                if len(files) > 0:
                    with task.ThreadPoolExecutor(max_workers=5) as exec:
                        for song in [song for song in exec.map(_get_metadata, files, repeat(self.folder_dir)) if song is not None]:
                            playlist.append(song)
                            _display_discovered_songs()
                        time.sleep(2)

            # 1 song loader, check if audio file exist   
            elif os.path.isfile(self.audio_file):
                _get_metadata(self.audio_file, self.folder_dir)
            os.system("cls")

        self.player = None
        # finally, update the music library, if there are new music to add
        _update_music_db()

        if self.title or self.artist or self.genre: 
            filtered_playlist = self.search_song_by(self.title, self.artist, self.genre)
            if filtered_playlist:
                playlist = filtered_playlist
            else:
                playlist = []

        return playlist


    def update_playlist(self, song_name, key, value):
        # update self.playlist by song name, assuming song name is unique
        for song in [song for song in self.playlist if song["name"] == song_name]:
            song.update((k, value) for k, v in song.items() if k == key)


    def isFound(self, ref_list, name, song_dir):
        for song in ref_list:
            if name.strip().lower() == song["name"].strip().lower() and song_dir.strip().lower() == song["song_dir"].strip().lower():
                return True
        return False


    def music_player(self, playlist_folder="", play_shuffle=False, play_all_music=False):
        self.folder_dir = playlist_folder
        self.toggle_shuffle = play_shuffle
        self.all_music = play_all_music

        os.system("cls")
        if len(self.playlist) <= 0:
            
            # load media and parse meta information
            self.playlist = self.load_media()
            # set the location of command prompt (music player view)
            os.system("CMDOW @ /ren \"Music Player\" /mov 445 -35 /siz 770 600")

            if len(self.playlist) <= 0:
                print("\n**No audio files found.")
                time.sleep(3)
                return

        os.system("cls")
        print(f"\n\t{'Shuffling' if self.toggle_shuffle else 'Loading'} playlist...")
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
                print(" " + "=" * (TITLE_PADDING + ARTIST_NAME_PADDING + 27))
                
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
                        duration = self.get_duration(ticker=time_ticker)
                        print(" " + "-" * (TITLE_PADDING + ARTIST_NAME_PADDING + 27))
                        print(f" {track_no} {title} {artist} {duration}  {_playing_status(status)}")
                        print(" " + "-" * (TITLE_PADDING + ARTIST_NAME_PADDING + 27))

                        # update the "duration" meta data if it has no (--:--) duration value
                        if song['duration'] == "--:--":
                            self.update_playlist(current_song, key="duration", value=duration)    
                    else:
                        print(f" {track_no} {title} {artist} {song['duration']}     {song['status']}")
                
                # playlist footer
                print(" " + "=" * (TITLE_PADDING + ARTIST_NAME_PADDING + 27))
                print(f" [F5] {'Shuffle' if not self.toggle_shuffle else 'Unshuffle'} \t[F9] {'Pause' if self.player.is_playing() else 'Play'} \t[F10] Next \t[F4] Stop (navigate to menu)")
                
                if len(self.playlist) > 25:
                    print(f" Showing {len(self.playlist[alpha:omega])} of {len(self.playlist)} songs on the playlist...")
                else:
                    print(f" {len(self.playlist)} songs on the playlist...")

            status = "Done"
            try:
                self.player.play()
                time.sleep(0.3)
                self.player.audio_set_volume(self.volume)
                state = self.player.get_state()

                while self.player.is_playing() or state.Paused:
                    status = "Done"

                    # stop the song
                    if keyboard.is_pressed("f4"):
                        status = "Stopped"
                        break
                    # toggle shuffle playlist
                    elif keyboard.is_pressed("f5"):
                        status = "Shuffle"
                        break
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
                    # volume down
                    elif keyboard.is_pressed("f12"):
                        if 0 < self.volume < 100:
                            self.volume -= 2
                    # volume up
                    elif keyboard.is_pressed("ins"):
                        if 0 < self.volume < 100:
                            self.volume += 2

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
                        status = "Err"

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
                    song_status = "Err"

                # update status of the song in self.playlist (marked as "Done", "Skipped" or "Can't play")
                self.update_playlist(song['name'], key="status", value=song_status)  

        # reset the playlist
        self.playlist = []  
        return


    def compact_music_player(self, is_playlist, playlist_folder="", music_file="", play_shuffle=False, play_all_music=False):
        self.folder_dir = playlist_folder
        self.toggle_shuffle = play_shuffle
        self.all_music = play_all_music

        os.system("cls")
        if len(self.playlist) <= 0:
            # for single music player parameter
            if not is_playlist and music_file:
                self.audio_file = music_file
            
            # load media and parse meta information
            self.playlist = self.load_media(is_playlist=is_playlist)
            # set the location of command prompt (music player view)
            os.system("CMDOW @ /ren \"Music Player\" /mov 601 -35 /siz 790 110")

            if len(self.playlist) <= 0:
                print("\n**No audio file found.")
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
                            duration = self.get_duration(ticker=time_ticker)
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
                self.player.audio_set_volume(self.volume)
                state = self.player.get_state()

                while self.player.is_playing() or state.Paused:
                    status = "Done"

                    # stop the song
                    if keyboard.is_pressed("f4"):
                        status = "Stopped"
                        break
                    # toggle shuffle playlist
                    elif keyboard.is_pressed("f5"):
                        status = "Shuffle"
                        break
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
                    # volume down
                    elif keyboard.is_pressed("f12"):
                        if 0 < self.volume < 100:
                            self.volume -= 2
                    # volume up
                    elif keyboard.is_pressed("ins"):
                        if 0 < self.volume < 100:
                            self.volume += 2
    
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
        if is_playlist or self.random_music:
            os.system("cls")
            print(f"\n\t{'Shuffling' if self.toggle_shuffle else 'Loading'} playlist...")
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
                            status = "Err"

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
                        status = "Err"

                    # update status of the song in self.playlist (marked as "Done", "Skipped" or "Can't play")
                    self.update_playlist(song["name"], key="status", value=song_status)

        # single music player
        elif not is_playlist and music_file:
            self.audio_file = music_file

            os.system("cls")
            print(f"\n\tLoading music...")
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
                status = "Err"

            # update status of the song in self.playlist (marked as "Done", "Skipped" or "Can't play")
            self.update_playlist(songname, key="status", value=song_status)

        # reset the playlist
        self.playlist = []
        return


    def play_some_music(self, is_playlist=True, playlist_folder="", music_file="", play_all_music=False, shuffle=False, compact_mode=True):
        if compact_mode:
            self.compact_music_player(is_playlist=is_playlist, playlist_folder=playlist_folder, music_file=music_file, play_shuffle=shuffle, play_all_music=play_all_music)
        else:
            self.music_player(play_shuffle=shuffle, playlist_folder=playlist_folder, play_all_music=play_all_music)
        return


         
if __name__ == "__main__":
    parser = ArgumentParser(description="Give option to search and play music.")

    # add option argument
    parser.add_argument("--option", action="store", dest="option", required=True, help="Command option for music player.")
    
    # required parm for option "music file"
    parser.add_argument("--filename", action="store", dest="filename", help="Filename of music to play.")
    
    # required parm for option "playlist"
    parser.add_argument("--dir", action="store", dest="dir_folder", help="Folder location of playlist to play.")
    
    # shuffle option
    parser.add_argument("--shuffle", action="store", dest="isShuffle", help="Shuffle the playlist. [True or False]")

    # Music player view (compact or normal)
    parser.add_argument("--mode", action="store", dest="isCompact", help="Determine the view of Music player [compact or normal].")

    # required parms for option: "play by"
    parser.add_argument("--title", action="store", dest="title", help="Title of music to search and play.")
    parser.add_argument("--artist", action="store", dest="artist", help="Artist name of music to search and play.")
    parser.add_argument("--genre", action="store", dest="genre", help="Genre of music to search and play.")
    
    
    # create an instanc of MusicPlayer 
    mp = MusicPlayer()
    # parse parameter values
    param = parser.parse_args()

    # --option parameter
    option = param.option.strip().lower()
    # --shuffle parameter
    isShuffle = True if param.isShuffle and param.isShuffle.strip().lower() == "true" else False
    # --mode parameter
    isCompact = True if param.isCompact and param.isCompact.strip().lower() == "compact" else False


    try:
        if option == "music file":
            # play sing song in compact mode
            mp.play_some_music(is_playlist=False, playlist_folder=param.dir_folder, music_file=param.filename, shuffle=isShuffle, compact_mode=isCompact)
            
        elif option == "playlist":
            # play the playlist of music
            mp.play_some_music(playlist_folder=param.dir_folder, shuffle=isShuffle, compact_mode=isCompact)
        
        elif option == "play all":
            # play all music starting from User folder directory
            mp.play_some_music(play_all_music=True, playlist_folder=Path.home(), shuffle=isShuffle, compact_mode=isCompact)
        
        elif option == "random":
            # flag the load_media() funciton to initiate random song mode
            mp.random_music = True
            # paly random suggested music
            mp.play_some_music(shuffle=isShuffle, compact_mode=isCompact)

        elif option == "play by":        
            # music title will be used for music search
            # if param.title:
            mp.title = param.title
            # music artist will be used for music search
            # if param.artist:
            mp.artist = param.artist
            # music genre will be used for music search
            # if param.genre:
            mp.genre = param.genre    
            
            # paly random suggested music
            mp.play_some_music(shuffle=isShuffle, compact_mode=isCompact)

    except KeyboardInterrupt:
        exit()