# This is a sample implementation of BeautifulSoup python library
# finds image urls on stock.adobe.com site and download them afterwards.

from bs4 import *
import requests as rq
import os
import json
import sys

FOLDER_NAME = "downloaded images"

def create_file_dir(filename):
    # combine dir folder and filename
    file_dir = f"{FOLDER_NAME}/{filename}"

    if not os.path.isfile(file_dir):
        return file_dir, filename

    # append "Copy of" if file already exist in download folder
    file_name = f"Copy of {filename}"
    # apply recursion until file directory name is unique
    return create_file_dir(file_name)

def remove_invalid_chars_from_filename(file_name):
    invalid_symbols = {"/", "'", "?", "#"}
    
    # remove invalid symbols from filename
    for symbol in invalid_symbols:
        file_name = file_name.replace(symbol, " ")
    
    return file_name

def scrape_images(search_keyword):
    # get html of page with a search keyword of images to find
    response = rq.get(f"https://stock.adobe.com/ph/search/images?k={search_keyword}")

    # using BeautifulSoup to parse the content from response
    soup = BeautifulSoup(response.text, "html.parser")

    # find all anchor tags that has a specific class name
    anchor_tags = soup.find_all("a", attrs={"class": "js-search-result-thumbnail non-js-link"})

    img_links = []
    # from list of anchor tags find "src" value of images inside each anchor tag
    for i, anchor in enumerate(anchor_tags):
        if ".jpg" in anchor.img["src"]:
            img_links.append((anchor.img["alt"], anchor.img["src"]))
    
    print("")
    image_count = len(img_links)
    while True:
        ask_count = input(f"Found {len(img_links)} images of \"{search_keyword}\".\n(Type \"a\" - Download All, \"c\" - Cancel)\nType the number how many to download: ")
        if ask_count.lower().strip() =="c":
            main()
            break
        if ask_count.lower().strip() == "a":
            break
        if ask_count.isdigit() and int(ask_count) <= image_count:
            image_count = int(ask_count)
            break
        print("Invalid input. Try again.")


    # create folder of images to be downloaded
    if not os.path.isdir(f"./{FOLDER_NAME}"):
        os.mkdir(FOLDER_NAME)


    print(f"\nDownloading {image_count} images...\n")
    for i, image_link in enumerate(img_links):
        # limit the search count to the specified image count param
        if i+1 > image_count: break

        # get image name from alt tag, and limit the filename length to 30 chars
        name_from_link = image_link[0][:29] if len(image_link[0]) > 30 else image_link[0]

        # remove invalid characters from filename
        name = remove_invalid_chars_from_filename(name_from_link)
        
        # determine extension name based on src link, last section of url
        ext_name = image_link[1][-4:]
        
        # combine file name and extension
        file_name = f"{i+1}. {name}{ext_name}"
        
        # append "Copy of" if file exist in folder
        file_dir, file_name = create_file_dir(file_name)

        # create images in binary mode
        with open(file_dir, "wb+") as f:
            # create images using content from image link we extracted from site
            image = rq.get(image_link[1]).content
            f.write(image)
            print(f"{file_name}")

    print(f"\nSuccessfully downloaded {image_count} images to \"{FOLDER_NAME}\" folder.\n")


def main():
    try:
        while True:
            search_keyword = input("\n(Type \"quit\" to end). What images are you looking for?: ")

            if search_keyword.lower().strip() == "quit":
                print("Image scraping ended.")
                exit()
            scrape_images(search_keyword)

    except KeyboardInterrupt:
        print("\n(keyboard interrupt) Image scraping ended.")
    except Exception as e:
        print(f"Exception: {e}")


if __name__ == "__main__":
    main()
