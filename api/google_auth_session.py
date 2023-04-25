# Flask-related imports
from flask import Flask, current_app, session, request, jsonify, redirect
from flask_session import Session
from flask_session.__init__ import Session
from flask.sessions import SecureCookieSessionInterface
from flask_cors import CORS, cross_origin

# Standard library imports
import json

# Security and Crypto imports
from cryptography.fernet import Fernet
from itsdangerous import URLSafeTimedSerializer

# aiohttp related imports
import asyncio
import aiohttp
from aiohttp import web

# Google API related imports
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google_auth_oauthlib.flow import InstalledAppFlow

# Local imports
from mongodb import MongoDBClient

client_secrets_file = 'secrets/client_secrets.json'
with open(client_secrets_file) as f:
    secrets = json.load(f)['installed']

# Get from app setup in Google
client_id = secrets['client_id']
project_id = secrets['project_id']
auth_uri = secrets['auth_uri']
token_uri = secrets['token_uri']
auth_provider_x509_cert_url = secrets['auth_provider_x509_cert_url']
client_secret = secrets['client_secret']
redirect_uri = secrets['redirect_uris']

print(f"app with secrets_file:  {client_secrets_file}")
print(f"app with client_id:     client_id")
print(f"app with project_id:    {project_id}")
print(f"app with auth_uri:      {auth_uri}")
print(f"app with token_uri:     {token_uri}")
print(f"app with auth_cert_url: {auth_provider_x509_cert_url}")
print(f"app with client_secret: client_secret")
print(f"app with redirect_uri:  {redirect_uri}")

scopes = ['openid',
          'https://www.googleapis.com/auth/userinfo.email',
          'https://www.googleapis.com/auth/userinfo.profile',
          'https://www.googleapis.com/auth/calendar.readonly',
          'https://www.googleapis.com/auth/calendar']

# Helper function to read json file
def read_json(file_path, key):
    with open(file_path, "r") as f:
        data = json.load(f)
    return data[key]

print("-------- Global Set Up App and Session ---------")
# Create Flask app instance
app = Flask("__google_auth_session__")
print(f"app with Flask:     {app}")

print("-------- Encrypt Session Cookie ----------------")

cookie_key = read_json("secrets/cookie_secrets.json", "cookie_key")
print(f"cookie_key:         {cookie_key}")

app.secret_key = cookie_key
print(f"app.secret_key:     {app.secret_key}")

# Set up a timed serializer for encryption and signing
serializer = URLSafeTimedSerializer(app.secret_key)

class EncryptedCookieSessionInterface(SecureCookieSessionInterface):
    def get_signing_serializer(self, app):
        return serializer

app.session_interface = EncryptedCookieSessionInterface()
print(f"app with cookie:    {app}")

# Initialize the Flask session interface
Session(app)

print("-------- Set Up Cross-Origin Resource Sharing --")
CORS(app)
print(f"app with CORS:      {app}")

@app.after_request
def add_cors_headers(response):
    print("after_request executing!")
    response.headers['Access-Control-Allow-Origin'] = '*'
    if request.method == 'OPTIONS':
        response.headers['Access-Control-Allow-Methods'] = 'DELETE, GET, POST, PUT'
        headers = request.headers.get('Access-Control-Request-Headers')
        if headers:
            response.headers['Access-Control-Allow-Headers'] = headers
    return response
app.after_request(add_cors_headers)

# Initialize endpoint
@app.route('/initialize_app', methods=['GET'])
async def initialize_app():
    # from google_auth_session import login, auth, logout
    # from calendars import initialize_calendar_enabled_flags, get_user_calendars, save_user_calendars_to_db, toggle_calendar_enabled

    print("-------- Init DB -------------------------------")
    # Initialize MongoDB client
    mongo_client = MongoDBClient()
    app.config['mongo_client'] = mongo_client

    print("-------- Return App ----------------------------")

    return app

# Auth endpoint
@app.route('/auth', methods=['GET'])
async def auth():

    app = current_app
    print(f"app /auth: {app}")

    mongo_client = current_app.config['mongo_client']
    collection = mongo_client.connect_to_mongodb()

    print("-------- OAuth Values Returned in /auth --------")
    # Create a flow instance using the client config and scopes
    flow = Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=scopes,
        redirect_uri='http://localhost:8000/auth'
    )
    print(f"Flow: {flow}")

    # Get the authorization code from the request
    code = request.args.get('code', None)
    print(f"Code: {code}")

    # If there is no authorization code, return an error
    if not code:
        return web.HTTPBadRequest(text="Authorization code not found")

    # Otherwise, exchange the authorization code for credentials
    flow.fetch_token(code=code)
    credentials = flow.credentials
    print(f"Credentials obtained: {credentials}")

    # Get the user's information from the Google API
    service = build('oauth2', 'v2', credentials=credentials)
    google_user = service.userinfo().get().execute()
    print("-------- Get Google User -----------------------")
    print("Google User Obtained:", json.dumps(google_user, indent=2))

    print("-------- Connect to MongoDB --------------------")
    collection = mongo_client.connect_to_mongodb()

    print("-------- Save/Upate User in MongoDB ------------")
    mongo_client.save_or_update_user(google_user, credentials)

    print("-------- Persist the Session Data in /auth -----")
    session['google_user'] = google_user
    session['credentials'] = credentials.to_json()

    # Redirect the user to the dashboard
    url = 'http://localhost:3001/dashboard'

    # Return the response with headers and auth url
    headers = {'Content-Type': 'application/json'}
    response_data = {'url': url}
    return response_data, 200, headers

@app.route("/sign-up", methods=['GET'])
async def sign_up():

    print("-------- Connecting to OAuth at /sign_up -------")

    app = current_app
    print(f"app /sign-up: {app}")

    # Create a flow instance using the client config and scopes
    flow = Flow.from_client_secrets_file(
        'secrets/client_secrets.json',
        scopes=scopes,
        redirect_uri='http://localhost:8000/auth'
    )
    print(f"Flow: {flow}")

    # Generate the authorization URL and store the flow in the session
    auth_url, _ = flow.authorization_url()
    print(f"Auth URL: {auth_url}")

    # Return the response with headers and auth url
    # headers = {'Content-Type': 'application/json'}
    # response_data = {'auth_url': auth_url, 'state': state}
    # return response_data, 200, headers

    # response_data = {'auth_url': auth_url, 'redirected': True}
    # headers = {'Access-Control-Allow-Origin': '*',
    #         'Content-Type': 'application/json'}
    # return jsonify(response_data), 200, headers
    return redirect(auth_url, code=302)

# Dashboard endpoint
# @app.route('/dashboard', methods=['GET'])
# async def dashboard(request: web.Request):
#     session = await aiohttp_session.get_session(request)
#     if not session.get('credentials'):
#         # If the user is not authenticated, redirect to login
#         return web.HTTPFound('/login')
#
#     # User is authenticated, load dashboard
#     return web.Response(text='Welcome to the dashboard!')

@app.route("/login", methods=['GET'])
async def login(request):
    app = current_app
    print(f"app /login: {app}")

    collection = mongo_client.connect_to_mongodb()

    # Get the session from the request
    # session = await get_session(request)

    # Check if the required keys are present in the session
    if 'google_user' in session and 'credentials' in session:
        print("-------- User is Already Logged In -------------")
        # Get the user's information from the session
        google_user = session['google_user']
        credentials = Credentials.from_authorized_user_info(info=json.loads(session['credentials']))

        # Redirect the user to the dashboard
        return web.HTTPFound('/dashboard')
    else:
        print("-------- Connecting to OAuth at /login ---------")
        # Create a flow instance using the client config and scopes
        flow = Flow.from_client_secrets_file(
            client_secrets_file=client_secrets_file,
            scopes=scopes,
            redirect_uri='http://localhost:8000/auth'
        )
        print(f"Flow: {flow}")

        # Generate the authorization URL and store the flow in the session
        auth_url, _ = flow.authorization_url()
        print(f"Auth URL: {auth_url}")

        # Redirect to the authorization URL
        return web.HTTPFound(auth_url)

# Logout endpoint
@app.route('/logout', methods=['GET'])
async def logout(request):

    print("-------- Logging Out, Goodbye! -----------------")
    # Remove the user and credentials from the session
    session = await get_session(request)
    session.clear()
    return web.HTTPFound('/')

# Helper function to convert the credentials object to a dictionary
def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

@app.route('/oauth_callback')
def oauth_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    if state != session.pop('state', None):
        return 'Invalid state parameter', 400
    flow = Flow.from_client_config(
        client_config={
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uris': redirect_uri,
            'scope': scopes,
        },
        scopes=['openid', 'email', 'profile'],
    )
    flow.fetch_token(code=code)
    # store the credentials in the session or database
    credentials = flow.credentials
    session['credentials'] = credentials.to_json()
    return redirect('/dashboard')

# # Session index count endpoint
# @app.route('/', methods=['GET'])
# async def index(request):
#     session = await get_session(request)
#     count = session.get('count', 0) + 1
#     session['count'] = count
#     return web.Response(text=f"Visited {count} times.")
