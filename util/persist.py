"""
    Collection class for persisting json configuration
"""
from collections.abc import MutableMapping
from typing import Any

from flask import current_app

from util.jsonny import Jsonny


class PersistentMapping(MutableMapping):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.prefix = "test/" if current_app.testing else "config/"
        self.jsonny = Jsonny(self.filename, self.prefix)
        self.collection = self.to_obj(self.jsonny.json)

    def __getitem__(self, key: str):
        return self.collection[key]

    def __setitem__(self, key: str, value: Any):
        self.collection[key] = value
        return self.save()

    def __delitem__(self, key: str):
        del self.collection[key]
        return self.save()

    def __len__(self):
        return len(self.collection.keys())

    def __iter__(self):
        return iter(self.collection)

    def keys(self):
        return self.collection.keys()

    def load(self):
        del self.jsonny
        del self.collection
        self.jsonny = Jsonny(self.filename)
        self.collection = self.to_obj(self.jsonny.json)

    def save(self):
        return self.jsonny.save(self.to_json(self.collection))

    def to_json(self, collection: dict[str, Any]) -> dict[str, str]:
        return collection

    __to_json = to_json

    def to_obj(self, collection: dict[str, str]) -> dict[str, Any]:
        return collection

    __to_obj = to_obj
