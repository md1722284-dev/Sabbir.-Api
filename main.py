import asyncio
import time
import httpx
import json
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from asgiref.sync import async_to_sync  # এটি ব্যবহার করা জরুরি
from google.protobuf import json_format
from Crypto.Cipher import AES

# আপনার প্রোজেক্টের প্রোটো ফাইলগুলো ইমপোর্ট করুন
from proto import FreeFire_pb2, main_pb2, AccountPersonalShow_pb2

app = Flask(__name__)
CORS(app)

# গ্লোবাল ভেরিয়েবল
cached_tokens = {}
SUPPORTED_REGIONS = {"IND", "BR", "US", "SAC", "NA", "SG", "RU", "ID", "TW", "VN", "TH", "ME", "PK", "CIS", "BD", "EUROPE"}
MAIN_KEY = base64.b64decode('WWcmdGMlREV1aDYlWmNeOA==')
MAIN_IV = base64.b64decode('Nm95WkRyMjJFM3ljaGpNJQ==')
RELEASEVERSION = "OB53"
USERAGENT = "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)"

# --- হেল্পার ফাংশনসমূহ ---
def pad(text: bytes) -> bytes:
    padding_length = AES.block_size - (len(text) % AES.block_size)
    return text + bytes([padding_length] * padding_length)

def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    aes = AES.new(key, AES.MODE_CBC, iv)
    return aes.encrypt(pad(plaintext))

async def get_token_info(region: str):
    # টোকেন এক্সপায়ার হয়েছে কি না চেক করে নতুন টোকেন তৈরি করার লজিক এখানে থাকবে
    # আপাতত সিম্পল রাখার জন্য ডিরেক্ট কল লজিক রাখা হলো
    pass 

async def GetAccountInformation(uid, region):
    # আপনার আগের লজিক অনুযায়ী API কল করার ফাংশন
    # নিশ্চিত করুন এখানে await httpx.AsyncClient() ব্যবহার করছেন
    pass

# --- রুটস ---
@app.route('/player-info')
def get_account_info():
    uid = request.args.get('uid')
    if not uid:
        return jsonify({"error": "Please provide UID."}), 400

    # লুপের ভেতরে async_to_sync ব্যবহার করুন
    for region in SUPPORTED_REGIONS:
        try:
            # asyncio.run() এর পরিবর্তে এটি ব্যবহার করুন
            return_data = async_to_sync(GetAccountInformation)(uid, region)
            if return_data:
                return jsonify(return_data)
        except Exception as e:
            continue

    return jsonify({"error": "UID not found"}), 404

# Vercel-এর জন্য নিচের অংশটি এভাবে রাখুন
if __name__ == '__main__':
    app.run()
