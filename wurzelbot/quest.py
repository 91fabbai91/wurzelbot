import logging
import abc
import re
import http_connection

class Quest(metaclass=abc.ABCMeta):
    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        self._http_connection = http_connection
        self._amount = {}
        self._reward = []
        self._logger = logging.getLogger(self.__class__.__name__)

    def get_quest(self):
        raise NotImplementedError

    def fulfill_quest(self):
        raise NotImplementedError
     


class CityQuest(Quest):
    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        super().__init__(http_connection)
    
    def get_quest(self):
        try:
            quest_data = self._http_connection.execute_command("do=CityQuest&action=getQuest")['data']['questtext']
            quest_data = quest_data.replace('.','')
            amount, self._reward = re.split(" f&uuml;r ", quest_data)
            self._reward = re.split(" und ", self._reward)
            amount = re.split("Liefere |, | und | ",amount)
            for i in range(1,len(amount),2):
                    self._amount.update({amount[i+1]: int(amount[i])})
            self._logger.debug("Needed amount: {amount} and reward: {reward}".format(amount=self._amount, reward=self._reward))
        except:
            raise QuestError("No City available")
        return self._amount, self._reward

    def fullfil_quest(self):
        self._http_connection.execute_command("do=CityQuest&action=getQuest")
        self._http_connection.execute_command('do=CityQuest&action=send')
        


class ParkQuest(Quest):
    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        super().__init__(http_connection)

    def get_quest(self):
        try:
            quest_data = self._http_connection.execute_command("do=park_getquest")['questData']
            self._reward = quest_data['reward']
            for product in quest_data['products']:
                self._amount.update({product['name']: product['missing']})
            self._logger.debug(f"Needed amount: {self._amount} and reward: {self._reward}")
        except:
            raise QuestError("No ParkQuest available")
        return self._amount, self._reward
    
    def fulfill_quest(self):
        try:
            quest_data = self._http_connection.execute_command("do=park_getquest")
            for product in quest_data['products']:
                self._http_connection.execute_command(f"do=park_quest_entry&pid={product['pid']}&amount={product['missing']}&questnr={quest_data['questnr']}")
        except:
            raise QuestError("Not possible to finish quest")
            


class DecoGardenQuest(Quest):
    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        super().__init__(http_connection)

    def get_quest(self):
        try:
            deco_garden_objects = self._http_connection.execute_decogarden_command("do=getGarden")['objects']
            for object in deco_garden_objects:
                quest_data = self._http_connection.execute_decogarden_command(f"do=clickObj&which={object['id']}")['questData']
                self._reward.append(quest_data['reward'])
                for product in quest_data['products']:
                    if product['name'] in self._amount.keys:
                        amount = self._amount.get(product['name']) + product['missing']
                    else: 
                        amount = product['missing']
                    self._amount.update({product['name']: amount})
                self._logger.debug(f"Needed amount: {self._amount} and reward: {self._reward}")
        except:
            raise QuestError("No DecoGardenQuest available")
        return self._amount, self._reward

    def fulfill_quest(self):
        try:
            deco_garden_objects = self._http_connection.execute_decogarden_command("do=getGarden")['objects']
            for object in deco_garden_objects:
                quest_data = self._http_connection.execute_decogarden_command(f"do=clickObj&which={object['id']}")['questData']
                for product in quest_data['products']:
                    self._http_connection.execute_decogarden_command(f"sendProducts&pid={product['pid']}&which={object['id']}&questNr={quest_data['questnr']}&amount={product['missing']}")
        except:
            raise QuestError("No DecoGardenQuest available")
        
class BeesGardenQuest(Quest):
    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        super().__init__(http_connection)

    def get_quest(self):
        try:
            quest_data = self._http_connection.execute_command("do=bees_quest_get")['questData']
            self._reward = quest_data['reward']
            for product in quest_data['products']:
                self._amount.update({product['name']: product['missing']})
            self._logger.debug(f"Needed amount: {self._amount} and reward: {self._reward}")
            return self._amount, self._reward
        except:
            raise QuestError("No BeesGardenQuest available")

    def fulfill_quest(self):
        return super().fulfill_quest()

class TreeQuest(Quest):
    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        super().__init__(http_connection)

    def get_quest(self):
        try:
            quest_data = list(self._http_connection.execute_tree_gardencommand("op=listavailablequests")['quests'].values())[0]
            self._reward = re.sub('<[^<]+?>', '',quest_data['rewardtext']).replace('Belohnung:','')
            short_text = quest_data['short_text'].replace('.','')
            amount = re.split("Liefere |, | und | ",short_text)
            for i in range(1,len(amount),2):
                    self._amount.update({amount[i+1]: int(amount[i])})
            self._logger.debug(f"Needed amount: {self._amount} and reward: {self._reward}")
            return self._amount, self._reward
        except:
            raise QuestError("No TreeQuest available")
    
    def fulfill_quest(self):
        return super().fulfill_quest()
        

class QuestError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)