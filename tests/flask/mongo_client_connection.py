from pymongo import MongoClient
from os import getenv

DATABASE_URL = f'mongodb+srv://db:db@cluster0.ixijz.mongodb.net/?retryWrites=true&w=majority'


class MongoClientConnection(object):
    @staticmethod
    def get_mongo_client():
        return MongoClient(DATABASE_URL)

    @staticmethod
    def get_database():
        return MongoClient(DATABASE_URL)[getenv("DATABASE")]


