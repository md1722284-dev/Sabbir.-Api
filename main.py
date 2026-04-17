import asyncio
import time
import httpx
import json
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from asgiref.sync import async_to_sync
from google.protobuf import json_format
from Crypto.Cipher import AES

# আপনার ফোল্ডারে থাকা প্রোটো ফাইলগুলো ইমপোর্ট করুন
try:
    from proto import FreeFire_pb2, main_pb2, AccountPersonalShow_pb2
except ImportError:
    pass

app = Flask(__name__)
CORS(app)

# সেটিংস
MAIN_KEY = base64.b64decode('WWcmdGMlREV1aDYlWmNeOA==')
MAIN_IV = base64.b64decode('Nm95WkRyMjJFM3ljaGpNJQ==')
RELEASEVERSION = "OB53"
USERAGENT = "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)"
SUPPORTED_REGIONS = {"IND", "BR", "US", "SAC", "NA", "SG", "RU", "ID", "TW", "VN", "TH", "ME", "PK", "CIS", "BD", "EUROPE"}

# --- সাহায্যকারী ফাংশন ---
def pad(text: bytes) -> bytes:
    padding_length = AES.block_size - (len(text) % AES.block_size)
    return text + bytes([padding_length] * padding_length)

def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    aes = AES.new(key, AES.MODE_CBC, iv)
    return aes.encrypt(pad(plaintext))

async def GetAccountInformation(uid, region):
    # আপনার API কল করার মূল লজিক এখানে থাকবে
    # আগের কোডের মতো httpx ব্যবহার করে ডেটা ফেচ করুন
    return {"status": "success", "uid": uid, "region": region}

# --- রুটস ---
@app.route('/')
def home():
    return jsonify({"message": "API is running. Use /player-info?uid=YOUR_ID"})

@app.route('/player-info')
def get_account_info():
    uid = request.args.get('uid')
    if not uid:
        return jsonify({"error": "UID প্রদান করুন"}), 400

    # Vercel-এর জন্য লুপের ভেতরে async_to_sync ব্যবহার করা নিরাপদ
    for region in SUPPORTED_REGIONS:
        try:
            data = async_to_sync(GetAccountInformation)(uid, region)
            if data:
                return jsonify(data)
        except:
            continue
            
    return jsonify({"error": "কোনো রিজিয়নে তথ্য পাওয়া যায়নি"}), 404

if __name__ == '__main__':
    app.run()
