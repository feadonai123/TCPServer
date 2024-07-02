import socket
import _thread
from enum import Enum
import ImageService
import time 
import random
import hashService

PORT = 1234
HOST = "127.0.0.1"

class TCPServer:
  
  threadCount = 0
  showLog = True
  COMMANDS = Enum("commands", ['EXIT', 'CHAT', 'FILE', 'ERRO'])
  BUFFER_SIZE = 1500
  SEQ_SIZE = 5
  CHECKSUM_SIZE = 16
  PATCH_IMAGES = './tcp/server/images'
  ACK_MESSAGE = b"ACK"
  WINDOWN_SIZE = 4
  END_MESSAGE = b"FIM"
  TIMEOUT = .05
  TIME_BETWEEN_PACKAGES = 0
  ERROR_RATE_CHECKSUM = 0
  
  
  def __init__(self, showLog=True):
    self.server = socket.socket(family=socket.AF_INET,type=socket.SOCK_STREAM)
    self.lock = _thread.allocate_lock()
    self.showLog = showLog
    
  def listen(self, host, port):
    self.host = host
    self.port = port
    self.server.bind((self.host, self.port))
    self.server.listen()
    self.__log(f"Socket is listening at {HOST}:{PORT}")
    
    self.__loop()
    
  def __loop(self):
    while True:
      session, address = self.server.accept()
      _thread.start_new_thread(self.__thread, (session, address))
      self.threadCount += 1
      self.__log("Thread Number: " + str(self.threadCount))
      
  def __thread(self, session, address):
    (ip, port) = address
    
    self.__log(f"\nConnection from {ip}:{port} is established")

    while True:
      command, data = self.__receive(session)
      
      if command == self.COMMANDS.EXIT.name:
        break
      elif command == self.COMMANDS.CHAT.name:
        self.__onChat(session, data)
      elif command == self.COMMANDS.FILE.name:
        self.__onFile(session, data)
      else:
        self.__onNotFound(session)
            
    self.__log(f"\nConnection from {ip}:{port} is closed")
    self.lock.acquire()
    self.threadCount -= 1
    self.lock.release()
    
    session.close()
    _thread.exit()    
    
  def __onFile(self, session, data):
    image = ImageService.readImageAsBase64(f"{self.PATCH_IMAGES}/{data}")
    self.__send(session, self.COMMANDS.FILE.name, image)
    
  def __onChat(self, session, data):
    self.__log(f"CLIENT: {data}")
    message = input("SERVER: ")
    self.__send(session, self.COMMANDS.CHAT.name, message)
    
  def __onNotFound(self, session):
    message = "Command not found"
    self.__send(session, self.COMMANDS.ERRO.name, message)
    
  def __receive(self, session):
    return self.__unmount(session.recv(self.BUFFER_SIZE))
    
  def __send(self, session, command, data):
    message = self.__mount(command, data)
    dataSize = self.BUFFER_SIZE - self.SEQ_SIZE - self.CHECKSUM_SIZE
    packages = [message[i:i + dataSize] for i in range(0, len(message), dataSize)]
    
    i = 0
    while i < len(packages):
      self.__log(f"\nSending packages {i + 1} to {min(i + self.WINDOWN_SIZE, len(packages))} to client")
      j = i
      while j < i + self.WINDOWN_SIZE and j < len(packages):
        package = packages[j]
        seq = j + 1
        package = self.__makePackage(seq, package)
        self.__log(f"Sending package {seq} to client")
        session.send(package)
        j += 1
        
      self.__log(f"Waiting for ACKs {i + 1} to {min(i + self.WINDOWN_SIZE, len(packages))} from client...")
      
      seqACKSReceived = []
      self.server.settimeout(self.TIMEOUT)
      for _ in range(self.WINDOWN_SIZE):
        if _ + i >= len(packages):
          break
        try:
          allBytesReceived = session.recv(self.BUFFER_SIZE)
          bytesPackages = [allBytesReceived[i:i + 8] for i in range(0, len(allBytesReceived), 8)]
          
          for bytesReceived in bytesPackages:
            if(bytesReceived.startswith(self.ACK_MESSAGE)):
              self.__log(f"Received ACK {self.__decode(bytesReceived[len(self.ACK_MESSAGE):])} from client")
              
              seqReceived = int(self.__decode(bytesReceived[len(self.ACK_MESSAGE):]))
              self.__log(f"Received ACK {seqReceived} from client")
              seqACKSReceived.append(seqReceived)
              
          if len(seqACKSReceived) >= self.WINDOWN_SIZE:
            break
        except socket.timeout:
          self.__log(f"Timeout for ACK")
        except Exception as e:
          self.__log(f"Error: {e}")
          
      self.server.settimeout(None)
      
      seqACKSReceived.sort()
      greater = seqACKSReceived[-1] if len(seqACKSReceived) > 0 else i
        
      self.__log(f"ACKs received in sequence: {seqACKSReceived} - {greater}")
      
      if i < len(packages) - 1:
        time.sleep(self.TIME_BETWEEN_PACKAGES)
      
      i = min(greater, len(packages))   
      
  def __mount(self, command, data):
    commandBytes = self.__encode(command)
    dataBytes = self.__encode(data)
    
    return commandBytes + dataBytes + self.END_MESSAGE
  
  def __unmount(self, payload):
    payloadDecode = self.__decode(payload)
    command = payloadDecode[0:4]
    data = payloadDecode[4:]
    return (command, data)
  
  def __encode(self, payload):
    if type(payload) == bytes:
      return payload
    return str.encode(payload)
  
  def __decode(self, payload):
    return payload.decode('utf-8')
  
  def __log(self, message):
    if self.showLog:
      print(message)
      
  def __calcChecksum(self, data):
    if random.randint(1, 100) > self.ERROR_RATE_CHECKSUM:
      checksum = hashService.hashBinary(data)
    else:
      checksum = hashService.hashBinary(data + b"1")
      self.__log(f"[ERROR] Checksum error for package")
    return checksum
  
  def __makePackage(self, seq, payload):
    seq = self.__encode(str(seq).zfill(self.SEQ_SIZE))
    if payload.endswith(self.END_MESSAGE):
      checksum = self.__calcChecksum(payload[:-len(self.END_MESSAGE)])
    else:
      checksum = self.__calcChecksum(payload)
      
    return seq + checksum + payload
    


server = TCPServer(showLog=True)
server.listen(HOST, PORT)