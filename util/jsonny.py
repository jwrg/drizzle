"""
Helper class for local JSON data store
"""
from json import dump, load


class Jsonny:
    """
    Class for manipulating JSON configuration data
    """

    encoding = "utf8"
    extension = "json"
    prefix = "config/"

    @staticmethod
    def get(file):
        """
        Returns a dict from a JSON file with implicit extension in base directory
        """
        try:
            with open(
                "/".join(
                    [
                        Jsonny.prefix,
                        ".".join(
                            [
                                file,
                                Jsonny.extension
                            ]
                        )
                    ]
                ), "r", encoding=Jsonny.encoding
            ) as f:
                return load(f)
        except FileNotFoundError:
            return {}

    @staticmethod
    def put(file, data, sort=False):
        """
        Persists some JSON data to disk with implicit extension in base directory
        """
        with open(
            "/".join(
                [
                    Jsonny.prefix,
                    ".".join(
                        [
                            file,
                            Jsonny.extension
                        ]
                    )
                ]
            ), "w", encoding=Jsonny.encoding
        ) as f:
            return dump(data, f, sort_keys=sort)

    def __init__(self, filename: str):
        self.filename = filename
        self.json = self.load()

    def load(self):
        return Jsonny.get(self.filename)

    def save(self, json):
        self.json = json
        return Jsonny.put(self.filename, self.json)
