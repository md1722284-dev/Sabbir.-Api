import asyncio
import time
import httpx
import json
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from cachetools import TTLCache
from typing import Tuple
from asgiref.sync import async_to_sync
from google.protobuf import json_format
from google.protobuf.message import Message
from Crypto.Cipher import AES

# Proto files import (ensure these are in your folder)
from proto import FreeFire_pb2, main_pb2, AccountPersonalShow_pb2

app = Flask(__name__)
CORS(app)
cache = TTLCache(maxsize=100, ttl=300)
cached_tokens = {}

MAIN_KEY = base64.b64decode('WWcmdGMlREV1aDYlWmNeOA==')
MAIN_IV = base64.b64decode('Nm95WkRyMjJFM3ljaGpNJQ==')
RELEASEVERSION = "OB53"
USERAGENT = "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)"
SUPPORTED_REGIONS = {"IND", "BR", "US", "SAC", "NA", "SG", "RU", "ID", "TW", "VN", "TH", "ME", "PK", "CIS", "BD", "EUROPE"}

# --- Utility Functions ---
def pad(text: bytes) -> bytes:
    padding_length = AES.block_size - (len(text) % AES.block_size)
    return text + bytes([padding_length] * padding_length)

def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    aes = AES.new(key, AES.MODE_CBC, iv)
    return aes.encrypt(pad(plaintext))

async def get_access_token(account: str):
    url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
    payload = account + "&response_type=token&client_type=2&client_secret=2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3&client_id=100067"
    headers = {'User-Agent': USERAGENT, 'Content-Type': "application/x-www-form-urlencoded"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, data=payload, headers=headers)
        data = resp.json()
        return data.get("access_token", "0"), data.get("open_id", "0")

async def create_jwt(region: str):
    # Credentials logic simplified
    if region == "IND": account = "uid=4363983977&password=ISHITA_0AFN5_BY_SPIDEERIO_GAMING_UY12H"
    else: account = "uid=4418979127&password=RIZER_K4CY1_RIZER_WNX02"
    
    token_val, open_id = await get_access_token(account)
    body = json.dumps({"open_id": open_id, "open_id_type": "4", "login_token": token_val, "orign_platform_type": "4"})
    
    proto_msg = FreeFire_pb2.LoginReq()
    json_format.ParseDict(json.loads(body), proto_msg)
    proto_bytes = proto_msg.SerializeToString()
    
    payload = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, proto_bytes)
    headers = {'User-Agent': USERAGENT, 'Content-Type': "application/octet-stream", 'ReleaseVersion': RELEASEVERSION}
    
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://loginbp.ggblueshark.com/MajorLogin", data=payload, headers=headers)
        instance = FreeFire_pb2.LoginRes()
        instance.ParseFromString(resp.content)
        msg = json.loads(json_format.MessageToJson(instance))
        
        cached_tokens[region] = {
            'token': f"Bearer {msg.get('token','0')}",
            'server_url': msg.get('serverUrl','0'),
            'expires_at': time.time() + 25000
        }

async def get_token_info(region: str):
    info = cached_tokens.get(region)
    if not info or time.time() > info['expires_at']:
        await create_jwt(region)
    return cached_tokens[region]['token'], cached_tokens[region]['server_url']

async def GetAccountInformation(uid, region):
    token, server = await get_token_info(region)
    
    # Proto setup
    req_msg = main_pb2.GetPlayerPersonalShow()
    json_format.ParseDict({'a': uid, 'b': "7"}, req_msg)
    payload = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, req_msg.SerializeToString())
    
    headers = {'User-Agent': USERAGENT, 'Authorization': token, 'Content-Type': "application/octet-stream", 'ReleaseVersion': RELEASEVERSION}
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{server}/GetPlayerPersonalShow", data=payload, headers=headers)
        res_instance = AccountPersonalShow_pb2.AccountPersonalShowInfo()
        res_instance.ParseFromString(resp.content)
        return json.loads(json_format.MessageToJson(res_instance))

# --- Flask Routes ---
@app.route('/player-info')
def get_account_info():
    uid = request.args.get('uid')
    if not uid: return jsonify({"error": "UID missing"}), 400

    # Try all regions if not cached
    for region in SUPPORTED_REGIONS:
        try:
            # Using async_to_sync for Vercel stability
            data = async_to_sync(GetAccountInformation)(uid, region)
            if data: return jsonify(data)
        except:
            continue
    return jsonify({"error": "Not found"}), 404

# Vercel needs the 'app' object
if __name__ == '__main__':
    app.run()
