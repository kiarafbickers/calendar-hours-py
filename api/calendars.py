# Flask-related imports
from flask import Flask, jsonify, request
from flask_cors import CORS

# Standard library imports
from datetime import datetime
from typing import List

# Google-related imports
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# MongoDB-related imports
from bson.objectid import ObjectId

# Local imports
from mongodb import get_mongo_client

# Create Flask app instance
app = Flask("calendar_functions")
CORS(app)

# Initialize MongoDB client
mongo_client = get_mongo_client()

@app.route('/calendars', methods=['GET'])
def get_user_calendars():
    user_email = request.args.get('user_email')
    credentials = request.args.get('credentials')
    collection = request.args.get('collection')
    print("user_email:", user_email)

    try:
        print("Building the Google Cal API client...")
        # Build the Google Calendar API client
        cal_service = build('calendar', 'v3', credentials=credentials)
        print("cal_service:", cal_service)

        # Get the list of all calendars for the user
        calendars_result = cal_service.calendarList().list().execute()
        all_calendars = calendars_result.get('items', [])
        # print("all_calendars: ")
        # print(json.dumps(all_calendars, indent=4))

        # Add an initialized "disabled" flag to each calendar
        initialize_calendar_enabled_flags(user_email, all_calendars, collection)

        return all_calendars

    except HttpError as error:
        print('An error occurred: %s' % error)
        return None

def initialize_calendar_enabled_flags(user_email, all_calendars, collection):
    for calendar in all_calendars:
        if 'enabled' not in calendar or calendar['enabled'] is None:
            calendar['enabled'] = False
            print(f"Calendar '{calendar['summary']}' does not have a valid value for 'enabled' key, setting it to False.")
            save_user_calendars_to_db(user_email, all_calendars, collection)
        else:
            print(f"Calendar '{calendar['summary']}' has value {calendar['enabled']} for 'enabled' key.")
    return None

def print_calendar_enabled_state(all_calendars):
    for calendar in all_calendars:
        calendar_name = calendar['summary']
        is_enabled = calendar['enabled']
        print(f"- {'Enabled' if is_enabled else 'Disabled'} - {calendar_name}")
    return None

def save_user_calendars_to_db(user_email, all_calendars, collection):
    print("user_email:", user_email)

    try:
        # Try to find the user in the database by their email
        existing_user = collection.find_one({'email': user_email})

        # If the user exists, update their calendars
        if existing_user:
            collection.update_one(
                {'_id': existing_user['_id']},
                {'$set': {'calendars': all_calendars}}
            )
            print(f"Updated Existing User: {existing_user['name']}, Email: {existing_user['email']}")
            print("User ID:", existing_user['_id'])

        else:
            print(f"No user found with email: {user_email}")

        return None

    except Exception as e:
        print("Error:", e)
        return None

@app.route('/calendars/<calendar_id>', methods=['PUT'])
def toggle_calendar_enabled(calendar_id, user_info, all_calendars, collection):
    # Find the calendar with the matching ID
    for calendar in all_calendars:
        if calendar['id'] == calendar_id:
            # Toggle the enabled flag for the calendar
            calendar['enabled'] = not calendar['enabled']
            save_user_calendars_to_db(user_info, all_calendars, collection)
            return calendar
    # If the calendar ID was not found, return None
    return None
