from setuptools import setup, find_packages

setup(
    name='my-app',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'aiohttp==3.8.4',
        'cryptography==39.0.1',
        'Flask==2.2.2',
        'Flask-Cors==3.0.10',
        'Flask-Session==0.4.0',
        'google-api-python-client==2.86.0',
        'google-auth-oauthlib==0.4.6',
        'itsdangerous==2.0.1',
        'protobuf==3.18.1',
        'pymongo==4.3.3',
        'python-dotenv==1.0.0',
    ],
    entry_points={
        'console_scripts': [
            'my-app = my_app.cli:main'
        ]
    },
)
