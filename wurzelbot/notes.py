import http_connection
import logging

class Notes(object):
    def __init__(self, httpConnection: http_connection.HTTPConnection):
        self.__httpConnection = httpConnection
        self.__logger = logging.getLogger(self.__class__.__name__)

    def get_notes(self):
      return self.__httpConnection.get_notes()

    def get_min_stock(self, plant_name = None):
      note = self.get_notes()
      note = note.replace('\r\n', '\n')
      lines = note.split('\n')

      is_plant_given = not plant_name is None
      for line in lines:
        if line.strip() == '':
          continue

        if not is_plant_given and line.startswith('minStock:'):
          return self.__extract_amount(line, 'minStock:')
        
        if is_plant_given and line.startswith(f'minStock({plant_name}):'):
          return self.__extract_amount(line, f'minStock({plant_name}):')

      # Return default 0 if not found in note
      return 0

    def __extract_amount(self, line, prefix):
      min_stock_str = line.replace(prefix, '').strip()
      min_stock_int = 0
      try:
        min_stock_int = int(min_stock_str)
      except:
        self.__logger.error(f'Error: "{prefix}" must be an int')
      return min_stock_int