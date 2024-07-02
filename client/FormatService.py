def stringToBinary(string):
  return ' '.join(format(x, 'b') for x in bytearray(string, 'utf-8'))