import asyncio

# Import initialize_app function from google_auth_session module
from google_auth_session import initialize_app

# Set up server
if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    app = loop.run_until_complete(initialize_app())

    print("-------- Set Up Server -------------------------")
    app.run(port=8000)
