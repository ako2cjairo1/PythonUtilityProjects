import os
import ctypes
import random
import time
import ctypes
import keyboard
from shutil import move
from typing import List
from PIL import Image
from win32.win32api import GetSystemMetrics
import pythoncom
import pywintypes
import win32gui
from win32com.shell import shell, shellcon
user32 = ctypes.windll.user32


class Wallpaper:
    def __init__(self):
        self.DOWNLOADED_DIR = "C:\\Users\\Dave\\Pictures\\Downloaded Images\\"
        self.WALLPAPER_DIR = "C:\\Users\\Dave\\Pictures\\HD Wallpapers\\"

    def set_wallpaper(self, image_path: str, use_activedesktop: bool = True):
        def force_refresh():
            user32.UpdatePerUserSystemParameters(1)

        def enable_activedesktop():
            def find_window_handles(parent: int = None, window_class: str = None, title: str = None) -> List[int]:
                def _make_filter(class_name: str, title: str):
                    """https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumwindows"""

                    def enum_windows(handle: int, h_list: list):
                        if not (class_name or title):
                            h_list.append(handle)
                        if class_name and class_name not in win32gui.GetClassName(handle):
                            return True  # continue enumeration
                        if title and title not in win32gui.GetWindowText(handle):
                            return True  # continue enumeration
                        h_list.append(handle)
                    return enum_windows

                cb = _make_filter(window_class, title)
                try:
                    handle_list = []
                    if parent:
                        win32gui.EnumChildWindows(parent, cb, handle_list)
                    else:
                        win32gui.EnumWindows(cb, handle_list)
                    return handle_list
                except pywintypes.error:
                    return []

            """https://stackoverflow.com/a/16351170"""
            try:
                progman = find_window_handles(window_class='Progman')[0]
                cryptic_params = (0x52c, 0, 0, 0, 500, None)
                user32.SendMessageTimeoutW(progman, *cryptic_params)
            except IndexError as e:
                raise WindowsError('Cannot enable Active Desktop') from e

        if use_activedesktop:
            enable_activedesktop()
        pythoncom.CoInitialize()
        iad = pythoncom.CoCreateInstance(shell.CLSID_ActiveDesktop,
                                         None,
                                         pythoncom.CLSCTX_INPROC_SERVER,
                                         shell.IID_IActiveDesktop)
        iad.SetWallpaper(str(image_path), 0)
        iad.ApplyChanges(shellcon.AD_APPLY_ALL)
        force_refresh()

    def change_wallpaper(self):
        image_name = ""
        file_dir = ""
        not_found = True
        screen_width, screen_height = GetSystemMetrics(0), GetSystemMetrics(1)

        while not_found:
            image_name = random.choice(os.listdir(self.DOWNLOADED_DIR))
            file_dir = f"{self.DOWNLOADED_DIR}{image_name}"

            if os.path.isfile(file_dir):

                img = Image.open(file_dir)
                # check dimensions of image
                if img.size[0] >= screen_width and img.size[1] >= screen_height:
                    not_found = False

        if file_dir:
            self.set_wallpaper(file_dir)
            # ctypes.windll.user32.SystemParametersInfoW(20, 0, file_dir, 0)

        return image_name

    def swap_dirs(self):
        self.DOWNLOADED_DIR, self.WALLPAPER_DIR = self.WALLPAPER_DIR, self.DOWNLOADED_DIR

    def dynamic_change_wallpaper(self, frequency=60, clrscr=False):
        ticker = frequency

        while True:
            if ticker >=  frequency:
                try:
                    if clrscr:
                        os.system("cls")
                        print("Changing the wallpaper...")
                    
                    # set a dynamic wallpaper
                    name = self.change_wallpaper()

                    if clrscr:
                        os.system("cls")
                    
                    # show the filename of wallpaper used
                    print(f"\nWallpaper:\n{name}")
                    ticker = 0

                except Exception as ex:
                    print(str(ex))
            
            # on demand change wallpaper
            if keyboard.is_pressed("f7"):
                ticker = frequency

            # switch source folder to WALLPAPER DIR
            if keyboard.is_pressed("f3"):
                self.swap_dirs()
                ticker = frequency

            # copy the current wallpaper to wallpaper collection
            if keyboard.is_pressed("f6"):
                move(f"{self.DOWNLOADED_DIR}{name}", f"{self.WALLPAPER_DIR}{name}")
                print(f"{name}\nCopied...")
                time.sleep(2)

                # show the filename of wallpaper used
                print(f"\nWallpaper:\n{name}")

            ticker += 1
            time.sleep(1)


if __name__ == "__main__":
    wp = Wallpaper()
    wp.dynamic_change_wallpaper(60, True)
