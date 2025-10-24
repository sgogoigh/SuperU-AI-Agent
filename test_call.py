import superu
import time
import json
import os

from dotenv import load_dotenv
load_dotenv()

superu_client = superu.SuperU(os.getenv("SUPER_U_API_KEY")) #Your Api Key

phone_number = '918402854904' #Number to call

create_call = superu_client.calls.create(
            from_='912269976873', #Buy this number from dev.superu.ai
            to_=phone_number,
            assistant_id='83789bdd-ab1b-40f2-9a91-8457dbb8b7d8', #Get this id when creating the assistant
            max_duration_seconds=120
        )

print(create_call.text)