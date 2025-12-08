from dataclasses import dataclass


@dataclass
class Player:
    """
    Docstring for Player

    :attribute name: Pretty intuitive
    :type name: str
    :attribute age: Age of the player
    :type age: int
    :attribute squad_number: Jersey number
    :type squad_number: int
    """

    name: str
    age : int
    squad_number: int = None

@dataclass
class Article:
    """
    Docstring for Article

    This dataclass is the object that represents articles.

    An Article is organized like this:
        :attribute title: Pretty intuitive
        :type title: str
        :attribute url: web address direct to the Article
        :type url: str
        :attribute summary: Contains a further explanation of the title
        :type summary: str
        :attribute date: When was the Article published
        :type date: str
    """

    title: str
    url: str
    summary: str = None
    date: str = None

    def set_date(self, date: str):
        self.date = date

    def set_summary(self, summary: str):
        self.summary = summary

