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

Creature = 0
GreenItem = 1
RedItem = 2
BlueItem = 3

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
    Pick = "Pick",
    Use = "Use"


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

    def use(self, id, idTarget):
        self.type = ActionType.Use
        self.id = id
        self.idTarget = idTarget

    def print(self, ending="; "):
        if self.type == ActionType.Pass:
            print("PASS")
        elif self.type == ActionType.Summon:
            print("SUMMON {}".format(self.id), end=ending)
        elif self.type == ActionType.Attack:
            print("ATTACK {0} {1}".format(self.id, self.idTarget), end=ending)
        elif self.type == ActionType.Pick:
            print("PICK {}".format(self.id), end=ending)
        elif self.type == ActionType.Use:
            print("USE {0} {1}".format(self.id, self.idTarget), end=ending)
        else:
            log("Action not found: {}".format(self.type))
            trap()


class Turn:
    """ Consists all actions to do in one turn """

    def __init__(self):
        self.actions = []

    def isCardPlayed(self, id):
        for action in self.actions:
            if not (action.type == ActionType.Summon or action.type == ActionType.Use): continue
            if action.id == id:
                return True
        return False

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
                if c == 'B': card.breakthrough = True
                if c == 'C': card.charge = True
                if c == 'G': card.guard = True

            self.state.cards.append(card)

    def think(self):
        """ The Core part """
        # Draft phase

        if self.state.isInDraft():
            # log("Draft phase")
            return  # Todo: apply a pick strategy

        # Battle phase
        log("Battle phase")

        """ Battle preparation """

        my_creatures = []
        enemy_creatures = []

        def prepare():
            for card in self.state.cards:
                if card.location == Mine:
                    my_creatures.append(card)
                elif card.location == Opponent:
                    enemy_creatures.append(card)

        def think_summon():
            log("Summon phase")

            my_mana = self.state.players[0].mana
            while my_mana > 0:
                bestCard = None
                bestScore = -float('inf')
                for card in self.state.cards:
                    if card.location != InHand:
                        continue
                    if card.cost > my_mana:
                        continue
                    if card.cardType != Creature:  # summon only creatures
                        continue
                    if card.cardType == GreenItem and len(my_creatures) == 0:
                        continue
                    if card.cardType == RedItem and len(enemy_creatures) == 0:
                        continue
                    if self.bestTurn.isCardPlayed(card.id): continue

                    score = card.cost  # grade the cards scores directly based on its cost
                    if score > bestScore:
                        bestScore = score
                        bestCard = card

                if bestCard is None:
                    break
                else:
                    action = Action()
                    if bestCard.cardType == Creature:
                        action.summon(id=bestCard.id)
                    elif bestCard.cardType == GreenItem:
                        targetCard = my_creatures[0]
                        action.use(id=bestCard.id, idTarget=targetCard.id)
                    elif bestCard.cardType == RedItem:
                        targetCard = enemy_creatures[0]
                        action.use(id=bestCard.id, idTarget=targetCard.id)
                    elif bestCard.cardType == BlueItem:
                        action.use(id=bestCard.id, idTarget=-1)
                    self.bestTurn.actions.append(action)
                    my_mana = my_mana - bestCard.cost

        def think_attack():
            log("Attack phase")
            # Get all opponent's cards with Guard
            guards = []
            for card in self.state.cards:
                if card.location != Opponent: continue
                if not card.guard: continue
                guards.append(card)

            for card in self.state.cards:
                if card.location != Mine: continue
                # Attack the guards first
                action = Action()
                if len(guards) == 0:
                    action.attack(id=card.id)
                else:
                    # Attack the first guard
                    guard = guards[0]
                    # Make the Attack
                    action.attack(id=card.id, idTarget=guard.id)
                    # Calculate the guard's defense after attacking
                    guard.defense = guard.defense - card.attack
                    if guard.defense < 0:
                        guards.remove(guard)

                self.bestTurn.actions.append(action)

        self.bestTurn.clear()
        prepare()
        think_summon()
        think_attack()


if __name__ == '__main__':
    agent = Agent()
    while True:
        agent.read()
        agent.think()
        agent.print()
