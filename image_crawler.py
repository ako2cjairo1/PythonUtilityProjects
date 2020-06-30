# This is a sample implementation of BeautifulSoup python library
# finds image urls on stock.adobe.com site and download them afterwards.

from bs4 import BeautifulSoup
import requests as rq
import os
import json
import sys
import time
import concurrent.futures as tasks

FOLDER_NAME = "Downloaded Images"
WALLPAPER_DIR = f"C:/Users/Dave/Pictures/{FOLDER_NAME}"


class ImageCrawler:

    def download_image(self, image_link, counter):
        def _remove_invalid_chars_from_filename(file_name):
            invalid_symbols = {"/", "'", "?", "#"}

            # remove invalid symbols from filename
            for symbol in invalid_symbols:
                file_name = file_name.replace(symbol, " ")

            # limit the filename length to 30 chars if more than 30
            file_name = file_name[:100] if len(file_name) > 100 else file_name

            # remove leading and trailing spaces
            return file_name.strip()

        def _create_file_dir(filename):
            # combine dir folder and filename
            file_dir = f"{WALLPAPER_DIR}/{filename}"

            if not os.path.isfile(file_dir):
                return file_dir, filename

            # append "Copy of" if file already exist in download folder
            file_name = f"Copy of {filename}"

            # apply recursion until file directory name is unique
            return _create_file_dir(file_name)

        # remove invalid characters from filename
        name = _remove_invalid_chars_from_filename(image_link[0])

        # determine extension name based on src link, last section of url
        if len(image_link) == 3:
            ext_name = image_link[2]
        else:
            ext_name = image_link[1][-4:]

        # combine file name and extension
        file_name = f"{counter}. {name}{ext_name}"

        # append "Copy of" if file exist in folder
        file_dir, file_name = _create_file_dir(file_name)

        # create images in binary mode
        with open(file_dir, "wb+") as fw:
            # create images using content from image link we extracted from site
            image = rq.get(image_link[1]).content
            fw.write(image)
            print(f"{file_name.ljust(110, ' ')} DOWNLOADED")

    def download_images(self, image_links, search_keyword):
        image_count = len(image_links)

        # return to main() when no results found.
        if image_count <= 0:
            print(f"\nNo iamge(s) found for \"{search_keyword}\"")
            self.start()

        # ask download options to user
        while True:
            ask_count = input(
                f"\nFound {image_count} images of \"{search_keyword}\"\n\n   [ a - Download All ({image_count}) ]\n   [ c - Cancel ]\n\nType the number how many to download: ")
            if ask_count.lower().strip() == "c":
                self.start()
                break
            if ask_count.lower().strip() == "a":
                break
            if ask_count.isdigit() and int(ask_count) <= image_count:
                image_count = int(ask_count)
                break
            print("Invalid input. Try again.")

        # create folder of images to be downloaded
        if not os.path.isdir(f"{WALLPAPER_DIR}"):
            os.mkdir(WALLPAPER_DIR)

        start = time.perf_counter()
        msg = "This may take a while. "
        print(
            f"\n{msg if image_count > 9 else ''}Downloading {image_count} images...\n")

        try:
            with tasks.ThreadPoolExecutor() as executor:
                img_indexer = [index for index in range(1, image_count + 1)]
                # map each image link item to be downloaded concurrently
                # slice item count to the specified image_count to download
                executor.map(self.download_image,
                             image_links[:image_count], img_indexer)

            finish = time.perf_counter()
            print(f"\nFinished in {round(finish-start, 2)} seconds.")
            print(
                f"Successfully downloaded {image_count} images of \"{search_keyword}\" to \"{FOLDER_NAME}\" folder.")
        except Exception as ex:
            print(f"Somethingtry: went wrong. {str(ex)}")

    def scrape_images(self, search_keywords):
        def _parse_html(link, params=None):
            # get html of page with a search keyword of images to find
            response = rq.get(link) if params is None else rq.get(
                link, params=params)

            # using BeautifulSoup to parse the content from response
            return BeautifulSoup(response.text, "html.parser")

        def _sort_list_of_tuple(tuple_list):
            def swap(idx1, idx2):
                tuple_list[idx1], tuple_list[idx2] = tuple_list[idx2], tuple_list[idx1]

            # using insertion sort algorithm for list of tuples
            for i in range(len(tuple_list)):
                current = tuple_list[i]
                pos = i

                # continually swap until reaches the last smaller list
                while pos > 0 and tuple_list[pos - 1][0].lower() > current[0].lower():
                    swap(pos, pos - 1)
                    pos -= 1

                # swap the last smallest list
                tuple_list[pos] = current

            return tuple_list

        img_links = []

        for search_keyword in search_keywords.split(";"):
            adobe_soup = _parse_html(
                f"https://stock.adobe.com/ph/search/images?k={search_keyword}")

            # find all anchor tags that has a specific class attribute and filter only src that does not end with "gif"
            # from list of anchor tags find "src" value of images inside each anchor tag
            adobe_site1 = [(f"Adobe Stock-{anchor.img['alt']}", anchor.img["src"]) for anchor in adobe_soup.find_all("a", {
                "class": "js-search-result-thumbnail non-js-link"}) if anchor.img["src"].split(".")[-1] != "gif"]
            adobe_site2 = [(f"Adobe Stock-{img['alt']}", img["data-lazy"])
                        for img in adobe_soup.find_all("img") if img["src"].split(".")[-1] == "gif"]

            # # put the list to main list of images
            img_links.extend(adobe_site1)
            img_links.extend(adobe_site2)

            hd_soup = _parse_html(
                f"https://www.hdwallpapers.in/search.html?q={search_keyword}")

            if hd_soup is not None:
                page_size = [anchor.text for anchor in hd_soup.select(
                    "a") if "/search/page/" in anchor["href"]]

                if page_size:
                    # determine the page size of webpage to parse
                    size = page_size[len(
                        page_size) - 1] if page_size[len(page_size) - 1].isdigit() else (page_size[len(page_size) - 2] if page_size[len(page_size) - 2].isdigit() else page_size[0])

                    for page_no in range(1, int(size)):
                        hd_soup = _parse_html(
                            f"https://www.hdwallpapers.in/search/page/{page_no}?q={search_keyword}")

                        if hd_soup is not None:
                            hd_site1 = [(f"HD Wallpapers-{img['src'].split('/')[-1].split('.')[-2]}",
                                        f"https://www.hdwallpapers.in/download/{img['src'].split('/')[-1]}") for img in hd_soup.find_all("img") if ".jpg" in img["src"]]

                            img_links.extend(hd_site1)

            stocksnap_soup = _parse_html(
                f"https://stocksnap.io/search/{search_keyword}")

            # select img tags that has src starts with "https://image.shutterstock.com/image-photo"
            # from img tags found, create a list of tuples with image name and image url
            stocksnap_site1 = [(f"StockSnap.io-{img['src'].split('/')[-1].split('.')[-2]}", img["src"])
                            for img in stocksnap_soup.select('img[src^="https://image.shutterstock.com/image-photo"]')]
            stocksnap_site2 = [(f"StockSnap.io-{img['alt']}", img["src"]) for img in stocksnap_soup.find_all(
                'img') if "https://cdn.stocksnap.io/img-thumbs" in img["src"]]

            # put the list to main list of images
            img_links.extend(stocksnap_site1)
            img_links.extend(stocksnap_site2)

            params = (("query", f"{search_keyword}^"),
                    ("xp", "^"), ("per_page", "1000"))
            # parse the response using BeautifulSoup
            unsplash_soup = _parse_html(
                "https://unsplash.com/napi/search", params)
            # expected to load json type data instead of html tags
            data = json.loads(str(unsplash_soup))

            unsplash_site1 = []
            for item in data["photos"]["results"]:
                img_url = item["urls"]["full"]
                extension_name = [ext_name for ext_name in img_url.split(
                    "&") if "fm=" in ext_name]
                # append tuple of (image name, image url, image extension name)
                unsplash_site1.append(
                    (f"Unsplash-{item['id']}", img_url, extension_name[0].replace("amp;fm=", ".")))

            # put the list to main list of images
            img_links.extend(unsplash_site1)

        # sort the merged list by name (ascending order - implicit)
        return _sort_list_of_tuple(img_links)

    def start(self):
        try:
            while True:
                search_keyword = input(
                    "\n[Type \"quit\" to end] What images are you looking for (use semicolon \";\" to separate multiple keywords)? ")

                if search_keyword.lower().strip() == "quit":
                    print("\nImage scraping ended.")
                    exit()

                print("\nThis may take a while. Searching...")
                # start scraping images from sites
                image_links = self.scrape_images(search_keyword)

                # download images found on sites
                self.download_images(image_links, search_keyword)

        except KeyboardInterrupt:
            print("\n(keyboard interrupt) Image scraping ended.")

        except Exception as e:
            print(f"Exception: {e}")


if __name__ == "__main__":
    image_crawler = ImageCrawler()
    image_crawler.start()
