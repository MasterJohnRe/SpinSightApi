from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# === CONFIGURATION CONSTANTS ===
MONGO_URI = "mongodb://77.137.79.162:27017"
DB_NAME = "crazytime"
COLLECTION_NAME = "results"
DB_USERNAME = "skipper"
PASSWORD = "ibnfIMsumGqKTFqF"
CONNECTION_STRING = r'mongodb+srv://skipper:ibnfIMsumGqKTFqF@spinsightcluster.h48lboi.mongodb.net/?retryWrites=true&w=majority&appName=SpinSightCluster'


class MongoDBHandler:
    def __init__(self, uri=CONNECTION_STRING, db_name=DB_NAME, collection_name=COLLECTION_NAME):
        try:
            self.client = MongoClient(uri)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
            print("✅ Connected to MongoDB.")
        except ConnectionFailure as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise

    def insert_document(self, document):
        """
        Inserts a single document into the MongoDB collection.
        :param document: dict
        :return: insert result object
        """
        if not isinstance(document, dict):
            raise ValueError("Document must be a dictionary.")
        result = self.collection.insert_one(document)
        return result

    def query_document(self, query):
        """
        Queries documents matching the provided filter.
        :param query: dict
        :return: list of matching documents
        """
        if not isinstance(query, dict):
            raise ValueError("Query must be a dictionary.")
        results = self.collection.find(query)
        return list(results)

    def update_document(self, filter_query, update_fields):
        """
        Updates a document by applying $set with given fields.
        :param filter_query: dict - MongoDB filter
        :param update_fields: dict - fields to set
        :return: update result
        """
        if not isinstance(filter_query, dict) or not isinstance(update_fields, dict):
            raise ValueError("Both arguments must be dictionaries.")
        result = self.collection.update_one(filter_query, {"$set": update_fields})
        return result
