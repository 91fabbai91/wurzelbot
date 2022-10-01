import logging
import abc
import re
from . import http_connection

class Quest(metaclass=abc.ABCMeta):
    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        self._http_connection = http_connection
        self._amount = {}
        self._reward = []
        self._logger = logging.getLogger(self.__class__.__name__)

    def get_quest(self):
        raise NotImplementedError
     


class CityQuest(Quest):
    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        super().__init__(http_connection)
    
    def get_quest(self):
        quest_data = self._http_connection.execute_command("do=CityQuest&action=getQuest")['data']['questtext']
        quest_data = quest_data.replace('.','')
        amount, self._reward = re.split(" f&uuml;r ", quest_data)
        self._reward = re.split(" und ", self._reward)
        amount = re.split("Liefere |, | und | ",amount)
        for i in range(1,len(amount),2):
                self._amount.update({amount[i+1]: int(amount[i])})
        self._logger.debug("Needed amount: {amount} and reward: {reward}".format(amount=self._amount, reward=self._reward))
        return self._amount, self._reward

    def fullfil_quest(self):
        self._http_connection.execute_command("do=CityQuest&action=getQuest")
        self._http_connection.execute_command('do=CityQuest&action=send')
        


class ParkQuest(Quest):
    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        super().__init__(http_connection)

    def get_quest(self):
        quest_data = self._http_connection.execute_command("do=park_getquest")['questData']
        self._reward = quest_data['reward']
        for product in quest_data['products']:
            self._amount.update({product['name']: product['missing']})
        self._logger.debug("Needed amount: {amount} and reward: {reward}".format(amount=self._amount, reward=self._reward))
        return self._amount, self._reward


class DecoGardenQuest(Quest):
    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        super().__init__(http_connection)

    def get_quest(self):
        quest_data = self._http_connection.execute_decogarden_command("do=clickObj&which=pond")['questData']
        self._reward = quest_data['reward']
        for product in quest_data['products']:
            self._amount.update({product['name']: product['missing']})
        self._logger.debug("Needed amount: {amount} and reward: {reward}".format(amount=self._amount, reward=self._reward))
        return self._amount, self._reward

class BeesGardenQuest(Quest):
    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        super().__init__(http_connection)

    def get_quest(self):
        quest_data = self._http_connection.execute_command("do=bees_quest_get")['questData']
        self._reward = quest_data['reward']
        for product in quest_data['products']:
            self._amount.update({product['name']: product['missing']})
        self._logger.debug("Needed amount: {amount} and reward: {reward}".format(amount=self._amount, reward=self._reward))
        return self._amount, self._reward