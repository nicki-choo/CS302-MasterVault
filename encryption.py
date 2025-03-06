from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
import base64
from pymongo import MongoClient
from bson.objectid import ObjectId


client = MongoClient('mongodb+srv://Conor:M0ng0DB1@mastervaultdb1.lf6e7.mongodb.net/')
db = client.MasterVault
userData = db["userData"]


SALT_SIZE = 16
KEY_SIZE = 32
ITERATIONS = 100000



def pad(data):
    pad_len = 16 - (len(data) % 16)
    return data + (chr(pad_len) * pad_len).encode()

def unpad(data):
    pad_len = data[-1]
    return data[:-pad_len]

def derive_key(salt, sessionID):
    findPost = userData.find_one({"_id": ObjectId(sessionID)})
    passphrase = str(findPost['DOB']) + str(findPost['_id']) + findPost['accountType']
    return PBKDF2(passphrase, salt, dkLen=KEY_SIZE, count=ITERATIONS)


def encrypt(plaintext, sessionID):
    salt = get_random_bytes(SALT_SIZE)
    key = derive_key(salt, sessionID)
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext.encode()))
    return base64.b64encode(salt + iv + ciphertext).decode('utf-8')

def decrypt(ciphertext, sessionID):
    ciphertext = base64.b64decode(ciphertext)
    salt = ciphertext[:SALT_SIZE]
    iv = ciphertext[SALT_SIZE:SALT_SIZE+16]
    encrypted_data = ciphertext[SALT_SIZE+16:]
    key = derive_key(salt, sessionID)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(encrypted_data))
    return plaintext.decode('utf-8')




