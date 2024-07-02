from datetime import datetime

def now():
  return datetime.today().strftime('%d-%m-%Y_%H_%M_%S')