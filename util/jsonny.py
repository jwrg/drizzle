"""
Helper class for local JSON data store
"""
from json import dump, load


class Jsonny:
    """
    Static class for manipulating simple utf8 JSON data
    """

    encoding = "utf8"
    extension = "json"

    @staticmethod
    def get(file):
        """
        Returns a dict from a JSON file with implicit extension in base directory
        """
        with open(
            ".".join([file, Jsonny.extension]), "r", encoding=Jsonny.encoding
        ) as f:
            return load(f)

    @staticmethod
    def put(file, data, sort=False):
        """
        Persists some JSON data to disk with implicit extension in base directory
        """
        with open(
            ".".join([file, Jsonny.extension]), "w", encoding=Jsonny.encoding
        ) as f:
            return dump(data, f, sort_keys=sort)
