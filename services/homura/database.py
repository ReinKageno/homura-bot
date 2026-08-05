
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pyauxy import hpril

load_dotenv()

uri = os.getenv('MONGO')

client = MongoClient(uri, server_api=ServerApi('1'))

hpril('Successfully connected to server database.')

musicQueue_db = client['guildMusic']