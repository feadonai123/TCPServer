import hashlib

def hashBinary(binary):
  return hashlib.md5(binary).digest()