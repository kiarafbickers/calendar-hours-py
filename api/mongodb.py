# mongo.py
#Standard library imports
import json
from datetime import datetime

#Third-party package imports
from google.oauth2.credentials import Credentials
from pymongo import MongoClient
from bson.objectid import ObjectId

#Local imports
from secrets.db_secrets import db_connection_string, db_name
from config import app_config

def get_mongo_client():
    client = MongoClient(app_config.DATABASE_URI)
    return client

class MongoDBClient:
    def __init__(self, app):
        self.client = MongoClient(app_config.DATABASE_URI)
        self.db = self.client[app_config.DATABASE_NAME]
        self.collection = self.db['users']

    def save_or_update_user(self, google_user, credentials):
        try:
            # Extract the user's email from the google user object
            user_email = google_user['email']
            print("User Email:", user_email)

            # Format the credentials object and print it for debugging purposes
            auth_token = format_credentials(credentials)
            print("Auth Token Obtained:", json.dumps(auth_token, indent=2))

            # Try to find the user in the database by their email
            existing_user = self.collection.find_one({'email': user_email})

            # If the user exists, update their credentials
            if existing_user:

                # mongo_id = str(existing_user['_id'])

                # Update the existing user's credentials in the database
                self.collection.update_one(
                    {'_id': existing_user['_id']},  # filter parameter added to update only the matched document
                    {'$set': {

                        # Update the google user credentials (not email)
                        'google_id': google_user['id'],
                        'verified_email': google_user['verified_email'],
                        'full_name': google_user['name'],
                        'first_name': google_user['given_name'],
                        'last_name': google_user['family_name'],
                        'picture': google_user['picture'],
                        'locale': google_user['locale'],
                        'google_hd': google_user['hd'],

                        # Update the new user's google oauth credentials
                        'token': auth_token['token'],
                        'refresh_token': auth_token['refresh_token'],
                        'token_uri': auth_token['token_uri'],
                        'client_id': auth_token['client_id'],
                        'scopes': auth_token['scopes'],
                        'expiry': auth_token['expiry'],

                        # Update the timestamp for when the user was last updated
                        'updated_at': datetime.now().isoformat()
                    }}
                )

                mongo_id = str(existing_user['_id'])
                print(f"The MongoDB ObjectId for {user_email} is: {mongo_id}")
                print(f"Updated User:", existing_user['email'], existing_user['full_name'])

            else:
                print(f"No user found with email: {user_email}")

                # Insert a new user into the database
                new_user = self.collection.insert_one({

                    # Update the new user's google user credentials
                    'google_id': google_user['id'],
                    'email': google_user['email'],
                    'verified_email': google_user['verified_email'],
                    'full_name': google_user['name'],
                    'first_name': google_user['given_name'],
                    'last_name': google_user['family_name'],
                    'picture': google_user['picture'],
                    'locale': google_user['locale'],
                    'google_hd': google_user['hd'],

                    # Update the new user's google oauth credentials
                    'token': auth_token['token'],
                    'refresh_token': auth_token['refresh_token'],
                    'token_uri': auth_token['token_uri'],
                    'client_id': auth_token['client_id'],
                    'scopes': auth_token['scopes'],
                    'expiry': auth_token['expiry'],

                    # Update the timestamp for when the user was last updated and created
                    'updated_at': datetime.now().isoformat(),
                    'created_at': datetime.now().isoformat()
                })

                if new_user.acknowledged:
                    saved_user = self.collection.find_one({'_id': new_user.inserted_id})

                    mongo_id = str(existing_user['_id'])
                    print(f"The MongoDB ObjectId for {saved_user['email']} is: {mongo_id}")
                    print(f"Saved New User: {saved_user['email']}, {saved_user['name']}")
                else:
                    print("Failed to Save User to the DB.")
                    return None

            total_users = self.collection.count_documents({})
            print(f"Total Count of Users: {total_users}")

            return None

        except ConnectionError as ce:
            print(f"Error: {ce}. Could not connect to the MongoDB server.")
            return None

        except Exception as e:
            print("Error:", e)
            return None

    def connect_to_mongodb(self):
        # Connect to the MongoDB database
        client = MongoClient(app_config.DATABASE_URI)
        print(f"Client: {client}")

        db = client[app_config.DATABASE_NAME]
        print(f"Database: {db}")

        collection = db['users']
        print(f"Collection: {collection}")

        return collection

def format_credentials(credentials):
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "scopes": credentials.scopes,
        "expiry": credentials.expiry.isoformat(),
    }
