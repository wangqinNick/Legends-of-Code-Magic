import sys
from enum import Enum

""" for debugging """


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def trap():
    exit(1)


Opponent = -1  # on the opponent's side of the board
InHand = 0  # on the player's side of the board
Mine = 1  # on the opponent's side of the board

Breakthrough = 'B'
Charge = 'C'
Guard = 'G'

class Card:
    def __init__(self):
        self.id = None  # the identifier of a card
        self.cardId = None  # the identifier representing the instance of the card (there can be multiple instances of the same card in a game).
        self.location = None  # 0: in the player's hand, 1: on the player's side of the board, -1: on the opponent's side of the board
        self.cardType = None
        self.cost = None
        self.attack = None
        self.defense = None
        self.hpChange = None
        self.hpChangeEnemy = None
        self.cardDraw = None
        self.abilities = None
        self.breakthrough = False
        self.charge = False
        self.guard = False


'''
class CardLocation(Enum):
    Opponent = -1,  # on the opponent's side of the board
    InHand = 0,  # on the player's side of the board
    Mine = 1  # on the opponent's side of the board
'''


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

    def isInDraft(self):
        return self.players[0].mana == 0


class ActionType(Enum):
    """ Consists all available action types"""
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

    def attack(self, id, idTarget=-1):
        self.type = ActionType.Attack
        self.id = id
        self.idTarget = idTarget

    def pick(self, id):
        self.type = ActionType.Pick
        self.id = id

    def print(self, ending="; "):
        if self.type == ActionType.Pass:
            print("PASS")
        elif self.type == ActionType.Summon:
            print("SUMMON {}".format(self.id), end=ending)
        elif self.type == ActionType.Attack:
            print("ATTACK {0} {1}".format(self.id, self.idTarget), end=ending)
        elif self.type == ActionType.Pick:
            print("Pick {}".format(self.id), end=ending)
        else:
            log("Action not found: {}".format(self.type))
            trap()


class Turn:
    """ Consists all actions to do in one turn """

    def __init__(self):
        self.actions = []

    def clear(self):
        self.actions.clear()

    def print(self):
        if len(self.actions) == 0:
            print("PASS")
            return

        for i in range(len(self.actions)):
            if i == len(self.actions) - 1:
                self.actions[i].print(ending='\n')
            else:
                self.actions[i].print()


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

        """ read cards info """
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
            abilities = inputs[
                7]  # the abilities of a card. Each letter representing an ability (B for Breakthrough, C for Charge and G for Guard)
            # log("Abilities: {}".format(abilities))
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

            # abilities: 'BCG---'
            for c in abilities:
                if c == Breakthrough: card.breakthrough = True
                if c == Charge: card.charge = True
                if c == Guard: card.charge = True

            self.state.cards.append(card)

    def think(self):
        """ The Core part """
        self.bestTurn.clear()  # clear the bestTurn

        # Draft phase

        if self.state.isInDraft():
            # log("Draft phase")
            return  # Todo: apply a pick strategy

        # Battle phase
        # log("Battle phase")
        # strategy:
        # Summon: summon the largest possible one
        # Attack: only attack the enemy
        def think_summon():
            """
            Summon strategy: iterate through the cards in hand and summon the largest possible one
            """
            bestCard = None
            bestScore = -float('inf')

            my_mana = self.state.players[0].mana
            # log("Mana: {}".format(my_mana))
            for card in self.state.cards:
                # log("card id: {0}, cost: {1}, location: {2}".format(card.id, card.cost, card.location))
                if card.location != InHand:
                    continue
                if card.cost > my_mana:
                    continue
                score = card.cost  # grade the cards scores directly based on its cost
                if score > bestScore:
                    bestScore = score
                    bestCard = card

            if bestCard is not None:  # if have a card to play
                # log("Found Best Card id: {}".format(bestCard.id))
                action = Action()
                action.summon(id=bestCard.id)
                self.bestTurn.actions.append(action)

        def think_attack():
            for card in self.state.cards:
                if card.location != Mine: continue
                action = Action()
                action.attack(id=card.id)
                self.bestTurn.actions.append(action)

        think_summon()
        think_attack()


if __name__ == '__main__':
    agent = Agent()
    while True:
        agent.read()
        agent.think()
        agent.print()
