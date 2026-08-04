
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()

uri = os.getenv('MONGO')

client = MongoClient(uri, server_api=ServerApi('1'))

musicQueue_db = client['guildMusic']