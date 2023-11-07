from pymongo import MongoClient

mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]
USERS = db["users"]
POSTS = db["posts"]
LIKES = db["likes"]

class Database:
    
    global USERS, POSTS, LIKES

    def insertUserIntoTheCollection(username, password):
        return USERS.insert_one({"username" : username, "password" : password.decode('utf-8')})

    def findUser(username):
        return USERS.find_one({"username" : username})

    def findToken(token):
        return USERS.find_one({"auth_token" : token})
        
    def addAuthToken(username, token):
        return USERS.update_one({"username" : username}, {"$set" : {"auth_token" : token}})

    