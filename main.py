import sys
from enum import Enum

""" for debugging """


def log(msg):
    print(msg, file=sys.stderr, flush=True)

def trap():
    exit(1)


class Card:
    def __init__(self):
        self.id = None
        self.cardId = None
        self.location = None  # 0: in the player's hand, 1: on the player's side of the board, -1: on the opponent's side of the board
        self.cardType = None
        self.cost = None
        self.attack = None
        self.defense = None
        self.hpChange = None
        self.hpChangeEnemy = None
        self.cardDraw = None
        self.abilities = None


class Player:
    def __init__(self):
        self.hp = None
        self.mana = None
        self.cardsRemaining = None
        self.rune = None
        self.draw = None


class State:
    def __init__(self):
        self.players = [Player(), Player()]
        self.opponent_hand = None
        self.cards = []
        self.opponent_actions = None
        self.card_number_and_action_list = None

class ActionType(Enum):
    Pass = "Pass",
    Summon = "Summon",
    Attack = "Attack",
    Pick = "Pick"

class Action:
    def __init__(self):
        self.type = ActionType.Pass
        self.id = -1
        self.idTarget = -1

    """ helper functions """
    def pass_(self):
        self.type = ActionType.Pass

    def summon(self, id):
        self.type = ActionType.Summon
        self.id = id

    def attack(self, id, idTarget):
        self.type = ActionType.Attack
        self.id = id
        self.idTarget = idTarget

    def pick(self, id):
        self.type = ActionType.Pick
        self.id = id

    def print(self, endWith="; "):
        if self.type == ActionType.Pass:
            print("PASS", end="")
        elif self.type == ActionType.Summon:
            print("SUMMON {}".format(self.id), end="")
        elif self.type == ActionType.Attack:
            print("ATTACK {0} {1}".format(self.id, self.idTarget), end="")
        elif self.type == ActionType.Pick:
            print("Pick {}".format(self.id), end="")
        else:
            log("Action not found: {}".format(self.type))
            trap()

class Turn:
    """ Represents all actions to do in one turn """
    def __init__(self):
        self.actions = []

    def print(self):
        if len(self.actions) == 0:
            print("PASS")
            return

        for action in self.actions:
            if action == self.actions[-1]:
                action.print(endWith='\n')
            else:
                action.print()

class Agent:
    def __init__(self):
        self.state = State()
        self.bestTurn = Turn()  # best turn actions found

    def print(self):
        """
        print the bestTurn (best actions found)
        """
        self.bestTurn.print()

    def read(self):
        """
        Read all inputs
        :return: None
        """

        """ read players info """
        for i in range(2):
            player = self.state.players[i]
            player.hp, player.mana, player.cardsRemaining, player.rune, player.draw = [int(j) for j in input().split()]

        """ read opponent hand cards info """
        self.state.opponent_hand, self.state.opponent_actions = [int(i) for i in input().split()]

        """ read more opponent hand cards info """
        self.state.card_number_and_action_list = []
        for i in range(self.state.opponent_actions):
            card_number_and_action = input()
            self.state.card_number_and_action_list.append(card_number_and_action)

        """ read card info """
        self.state.cards = []  # clear the card list every turn
        card_count = int(input())
        # read every card
        for i in range(card_count):
            card = Card()

            inputs = input().split()
            card_number = int(inputs[0])
            instance_id = int(inputs[1])
            location = int(inputs[2])
            card_type = int(inputs[3])
            cost = int(inputs[4])
            attack = int(inputs[5])
            defense = int(inputs[6])
            abilities = inputs[7]
            my_health_change = int(inputs[8])
            opponent_health_change = int(inputs[9])
            card_draw = int(inputs[10])

            card.cardId = card_number
            card.id = instance_id
            card.location = location
            card.cardType = card_type
            card.cost = cost
            card.attack = attack
            card.defense = defense
            card.abilities = abilities
            card.hpChange = my_health_change
            card.hpChangeEnemy = opponent_health_change
            card.cardDraw = card_draw

            self.state.cards.append(card)


if __name__ == '__main__':
    agent = Agent()
    while True:
        agent.read()
        agent.print()
