import base64

def saveBinaryAsImage(binary, path):
  with open(path, "wb") as image:
    image.write(binary)
    
def saveBase64AsImage(base64File, path):
  data_bytes = base64.b64decode(base64File)

  with open(path, "wb") as image:
    image.write(data_bytes)
    
# saveBase64AsImage("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C9A", "./aqui.jpg")
  