# Declare a class
import asyncio
import os

from shazamio import Shazam
from unidecode import unidecode


class TagExtraction:
    def __init__(self, file_path, delay=10, num_retries=3):
        self.cover_link = None
        self.year = None
        self.title = None
        self.album = None
        self.author = None
        self.file_path = file_path
        self.delay = delay
        self.num_retries = num_retries
        self.directory = os.path.dirname(file_path)
        self.file_name, self.file_extension = os.path.splitext(file_path)

    # Run Shazam Audio Recognition and extract mp3 tags into local variables based on the result
    async def run_shazam_recognition(self, shazam: Shazam):

        error_str, out = await self.method_name(shazam)

        if out is None:
            print(f"\nFailed to recognize {self.file_path} after {self.num_retries} attempts. Error {error_str}")
            return False

        # Extract necessary information from recognition result
        track_info = out.get("track", {})
        self.title = track_info.get("title")
        if not self.title:
            print(f"Could not recognize song title of {self.file_path}.")
            return False

        self.author = track_info.get("subtitle", "Unknown Artist")
        self.album = TagExtraction.find_deepest_metadata_key(track_info, "Album") or "Unknown Album"
        self.year = TagExtraction.find_deepest_metadata_key(track_info, "Released") or "Unknown Year"

        images = track_info.get("images", {})
        self.cover_link = images.get("coverart", "")  # Default to empty if no cover art

        # Sanitize, rename, and update MP3 file
        self.title = self.sanitize_string(self.title)
        self.author = self.sanitize_string(self.author)
        self.album = self.sanitize_string(self.album)

        return True

    async def method_name(self, shazam: Shazam):
        attempt = 0
        out = None
        error_str = ""
        while attempt < self.num_retries:
            try:
                out = await shazam.recognize(self.file_path)
                if out:  # Assuming 'out' being non-empty means success
                    break
            except Exception as e:
                error_str = f"Attempt {attempt + 1} failed due to exception: {e}"
                print(error_str)
                attempt += 1
            if attempt < self.num_retries:
                await asyncio.sleep(self.delay)
        return error_str, out

    @staticmethod
    def find_deepest_metadata_key(data, search_key):
        """
        Recursively searches for the 'text' value corresponding to a given 'title' key
        in a deeply nested structure of lists and dictionaries.

        Args:
            data (dict or list): The nested data to search.
            search_key (str): The 'title' value to search for.

        Returns:
            str or None: The 'text' value corresponding to the search_key, or None if not found.
        """
        # If the current level is a dictionary, search within it
        if isinstance(data, dict):
            # Check if the dictionary contains the 'title' and 'text' keys and matches the search_key
            if data.get("title") == search_key and "text" in data:
                return data["text"]
            # Otherwise, recurse into the dictionary's values
            for value in data.values():
                result = TagExtraction.find_deepest_metadata_key(value, search_key)
                if result is not None:
                    return result

        # If the current level is a list, iterate through it and search each item
        elif isinstance(data, list):
            for item in data:
                result = TagExtraction.find_deepest_metadata_key(item, search_key)
                if result is not None:
                    return result

        # If no match is found, return None
        return None

    @staticmethod
    def sanitize_string(value):

        original_value = value
        value = unidecode(value)  # Attempt to transliterate to ASCII
        value = "".join(char for char in value if char not in '()<>:"/\\|?*')
        value = value.replace("&", "-")
        # Change uppercase words to capitalize (first letter uppercase, rest lowercase)
        value = " ".join(word.capitalize() for word in value.split())

        if not value.strip():
            print("Warning: Filename became empty after sanitization.")
        return value
