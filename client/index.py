import socket
from enum import Enum
import time
import ImageService
import TimeService
import FormatService
import random
import hashService

HOST = "127.0.0.1"
PORT = 1234


class TCPClient:
  
  showLog = True
  COMMANDS= Enum("commands", ['EXIT', 'CHAT', 'FILE', 'ERRO'])
  BUFFER_SIZE = 1500 * 4
  PATCH_IMAGES = './tcp/client/images'
  END_MESSAGE = b"FIM"
  SEQ_SIZE = 5
  ACK_MESSAGE = b"ACK"
  CHECKSUM_SIZE = 16
  ERROR_RATE_SEND_ACK = 0
  
  def __init__(self, host, port):
    self.host = host
    self.port = port
    self.client = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    self.client.connect((self.host, self.port))
    self.__log("Waiting for server response")
    
  def exit(self):
    self.send(self.COMMANDS.EXIT.name, "")
    self.client.close()
    
  def send(self, command, data):
    payload = self.__mount(command, data)
    self.client.send(payload)
    
    if command == self.COMMANDS.EXIT.name:
      return
    
    command, data = self.__recv()
    
    if command == self.COMMANDS.ERRO.name:
      self.__onError(data)
      return
    elif command == self.COMMANDS.CHAT.name:
      self.__onChat(data)
    elif command == self.COMMANDS.FILE.name:
      self.__onFile(data)
      
  def __onError(self, data):
    self.__log(f"ERROR: {data}")
      
  def __onChat(self, data):
    self.__log(f"SERVER: {data}")
    
  def __onFile(self, data):
    ImageService.saveBase64AsImage(data, f"{self.PATCH_IMAGES}/{TimeService.now()}.jpg")
  
  def __recv(self):
    packages = []
    hasFinished = False
    lastSeqReceived = None
    
    while hasFinished == False:
      allBytesReceived = self.client.recv(self.BUFFER_SIZE)
      
      # a variavel bytesReceived as vezes recebe 2 ou mais pacotes juntos.
      # é preciso separar esses pacotes. cada pacote tem o tamanho de BUFFER_SIZE
      
      bytesPackages = [allBytesReceived[i:i + 1500] for i in range(0, len(allBytesReceived), 1500)]
      
      for bytesReceived in bytesPackages:
        
        seqReceived, checksum, dataReceived, hasFinished = self.__extractPackage(bytesReceived)
        seqNumber = int(self.__decode(seqReceived))
        self.__log(f"\nReceived from server SEQ {seqNumber}. Tam packages: {len(packages)}")
        
        if(not self.__checksum(checksum, dataReceived)):
          self.__log(f"Checksum failed for package {seqReceived}")
          # Ignore package
          self.__log(f"Package {seqNumber} ignored")
          # send ACK to server
          self.__sendACK(lastSeqReceived)
        elif seqNumber == len(packages) + 1:
          self.__log(f"Package {seqNumber} received")
          packages.append(dataReceived)
          lastSeqReceived = seqReceived
          self.__sendACK(seqReceived)
        else:
          # Ignore package
          self.__log(f"Package {seqNumber} ignored")
          # send ACK to server
          self.__sendACK(lastSeqReceived)
          
    binaryResponse = b"".join(packages)
    # return self.__unmount(self.client.recv(self.BUFFER_SIZE))
    return self.__unmount(binaryResponse)
    
  def __sendACK(self, seqReceived):
    if random.randint(1, 100) > self.ERROR_RATE_SEND_ACK:
      ack = self.ACK_MESSAGE + seqReceived
      self.client.send(ack)
      self.__log(f"Sending ACK to server: {ack}")
    else:
      self.__log(f"[ERROR] ACK {seqReceived} lost")
      
  def __extractPackage(self, bytesReceived):
    hasFinished = bytesReceived.endswith(self.END_MESSAGE)
    seqReceived = bytesReceived[:self.SEQ_SIZE]
    checksum = bytesReceived[self.SEQ_SIZE:self.SEQ_SIZE + self.CHECKSUM_SIZE]
    dataReceived = bytesReceived[self.SEQ_SIZE + self.CHECKSUM_SIZE:-len(self.END_MESSAGE)] if hasFinished else bytesReceived[self.SEQ_SIZE + self.CHECKSUM_SIZE:]
    return (seqReceived, checksum, dataReceived, hasFinished)
  
  def __checksum(self, checksum, data):
    return checksum == hashService.hashBinary(data)
  
  def __mount(self, command, data):
    commandBytes = self.__encode(command)
    dataBytes = self.__encode(data)
    return commandBytes + dataBytes
  
  def __unmount(self, payload):
    command = payload[:4]
    data = payload[4:]
    commandDecode = self.__decode(command)
    dataDecode = self.__decode(data)
    return (commandDecode, dataDecode)
    
  def __encode(self, payload):
    return payload.encode()
  
  def __decode(self, payload):
    return payload.decode('utf-8')
    
  def __log(self, message):
    if self.showLog:
      print(message)



client = TCPClient(HOST, PORT)

while True:
  command = input("Command: (CHAT, FILE, EXIT) ")
  
  if command in client.COMMANDS.__members__:
    command = client.COMMANDS[command]
    
    if command == client.COMMANDS.EXIT:
      client.exit()
      break
    elif command == client.COMMANDS.CHAT:
      message = input("CLIENT: ")
      client.send(command.name, message)
    elif command == client.COMMANDS.FILE:
      filename = input("FILENAME: ")
      client.send(command.name, filename)
    
  else:
    print("Command not found")
    continue