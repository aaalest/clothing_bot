import pymongo
from config import config
from dataclasses import dataclass, fields, field, asdict, is_dataclass, MISSING
from typing import Any


class BaseCollection:
    @dataclass
    class Template:
        def as_dict(self):
            return asdict(self)

        @staticmethod
        def as_dict_one(self):
            print(self.nest)

        def nest(self):
            nested_dict = {}
            for f in fields(self):
                # Check if the field type is another dataclass (nested)
                if is_dataclass(f.type):
                    # Recursively get its nested class dictionary
                    nested_dict[f.name] = f.type().nested_class_dict()
                elif f.default_factory:
                    # Handle default factory case where it could return a dataclass
                    try:
                        potential_class = f.default_factory()
                        if is_dataclass(potential_class):
                            nested_dict[f.name] = potential_class.nest()
                    except TypeError:
                        # If the default factory doesn't return a dataclass, ignore
                        pass
            return nested_dict

    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    def mongo(self) -> pymongo.collection.Collection:
        database = client[config.bot.database_name]
        return database[self.collection_name]

    def update_documents(self):
        for document in self.mongo().find():
            self.fill_document(document)
            self.sort_document(document)

    def recursive_fill(self, target, source) -> dict:
        for key, value in source.items():
            if isinstance(value, dict):
                target[key] = self.recursive_fill(target.get(key, {}), value)
            elif key not in target:
                target[key] = value
        return target

    def fill_document(self, document):
        update_query = {"$set": self.recursive_fill(document, self.Template().as_dict())}
        if update_query["$set"]:
            self.mongo().update_one({"_id": document["_id"]}, update_query)

    def recursive_sort(self, source, template) -> dict:
        sorted_doc = {}
        # Include keys from both the source document and the template
        all_keys = set(source.keys()).union(template.keys())

        for key in all_keys:
            if key in source:
                if key in template:
                    # If the key is also in the template and is a dictionary, sort recursively
                    if isinstance(template[key], dict) and isinstance(source[key], dict):
                        sorted_doc[key] = self.recursive_sort(source[key], template[key])
                    else:
                        # Otherwise, take the value from the source
                        sorted_doc[key] = source[key]
                else:
                    # If the key is not in the template but in the source, keep the source value
                    sorted_doc[key] = source[key]

        return sorted_doc

    def sort_document(self, document):
        sorted_document = self.recursive_sort(source=document, template=self.Template().as_dict())
        self.mongo().replace_one({"_id": document["_id"]}, sorted_document)


class Members(BaseCollection):
    def __init__(self):
        super().__init__('members')

    @dataclass
    class Template(BaseCollection.Template):
        name: str = field(default=None)
        user_id: int = field(default=None)
        language: str = field(default='en')
        generations: list = field(default_factory=list)


class Generations(BaseCollection):
    def __init__(self):
        super().__init__('generations')

    @dataclass
    class Template(BaseCollection.Template):
        user_id: int = field(default=None)
        input: 'Generations.Template.Input' = field(default_factory=lambda: Generations.Template.Input())
        output: 'Generations.Template.Output' = field(default_factory=lambda: Generations.Template.Output())
        options: 'Generations.Template.Options' = field(default_factory=lambda: Generations.Template.Options())
        generation_time: float = field(default=None)

        @dataclass
        class Options(BaseCollection.Template):
            upper: str = field(default=None)
            upper_color: str = field(default=None)
            lower: str = field(default=None)
            lower_color: str = field(default=None)
            style: str = field(default=None)

        @dataclass
        class Input(BaseCollection.Template):
            file_id: str = field(default=None)
            file_unique_id: str = field(default=None)
            file_size: int = field(default=None)
            file_path: str = field(default=None)

        @dataclass
        class Output(BaseCollection.Template):
            file_id: str = field(default=None)
            file_unique_id: str = field(default=None)
            file_size: int = field(default=None)
            file_path: str = field(default=None)


def update_collections():
    collections = [
        members,
        generations
    ]
    for collection in collections:
        collection.update_documents()


client = pymongo.MongoClient(config.bot.mongo)

members = Members()
generations = Generations()
