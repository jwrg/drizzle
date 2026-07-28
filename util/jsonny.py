"""
Helper class for local JSON data store
"""
from json import dump, load


class Jsonny:
    """
    Class for manipulating JSON configuration data
    """

    def __init__(
        self,
        filename: str,
        prefix: str,
        extension: str = "json",
        encoding: str = "utf8"
    ):
        self.filename = filename
        self.prefix = prefix
        self.extension = extension
        self.encoding = encoding
        self.json = self.load()

    def get(self, filename):
        """
        Returns a dict from a JSON file with explicit
        path and extension relative to base directory
        """
        try:
            with open(
                "/".join(
                    [
                        self.prefix,
                        ".".join(
                            [
                                filename,
                                self.extension
                            ]
                        )
                    ]
                ), "r", encoding=self.encoding
            ) as f:
                return load(f)
        except FileNotFoundError:
            return {}

    def put(self, filename, data, sort=False):
        """
        Persists some JSON data to disk with explicit
        path and extension relative to base directory
        """
        with open(
            "/".join(
                [
                    self.prefix,
                    ".".join(
                        [
                            filename,
                            self.extension
                        ]
                    )
                ]
            ), "w", encoding=self.encoding
        ) as f:
            return dump(data, f, sort_keys=sort)

    def load(self):
        return self.get(self.filename)

    def save(self, json):
        self.json = json
        return self.put(self.filename, self.json)
