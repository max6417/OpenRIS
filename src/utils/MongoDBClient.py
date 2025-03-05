from pymongo import MongoClient, errors


class MongoDBClient:

    def __init__(self, url="mongodb://127.17.0.2:27017"):
        self.client = MongoClient(host=[url])["app"]

    def list_databases(self):
        return self.client.list_database_names()

    def create_collection(self, name):
        return self.client[name]

    def delete_database(self, name):
        return self.client[name].drop()

    def add_document(self, name, elem):
        return self.client[name].insert_one(elem)

    def delete_document(self, name, id):
        return self.client[name].delete_one({"_id": id})

    def get_document(self, name, req):
        return self.client[name].find_one(req)

    def get_documents(self, name, req):
        return self.client[name].find(req)

    def update_document(self, name, id, updated):
        updated = {"$set": {updated}}
        return self.client[name].update_one({"_id": id}, updated)

    def list_documents(self, name):
        return self.client[name].find()
