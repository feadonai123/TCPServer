import base64


def readImageAsBinary(path):
  with open(path, "rb") as image:
    return image.read()
  
def saveBinaryAsImage(binary, path):
  with open(path, "wb") as image:
    image.write(binary)
    
def readImageAsBase64(path):
  with open(path, "rb") as image:
    return base64.b64encode(image.read()).decode()