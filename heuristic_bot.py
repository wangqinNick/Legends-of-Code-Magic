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

MAX_MANA = 12

LOW = 3
MEDIUM = 6

ZERO = 1
ONE = 1
TWO = 5
THREE = 6
FOUR = 7
FIVE = 5
SIX = 4
SEVEN_PLUS = 3

CARDS_PER_DRAFT = 3


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
        self.used = False


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

    def newAction(self):
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


class ManaCurve:
    def __init__(self):
        self.curve = None
        self.creature_count = None

    def compute_curve(self, cards):
        self.curve = [0 for _ in range(MAX_MANA + 1)]
        self.creature_count = 0
        for card in cards:
            self.curve[card.cost] += 1
            if card.cardType == Creature:
                self.creature_count += 1

    def evaluate_score(self):
        """
        Calculate the total score of the drafted cards depending on its mana cost
        """
        seven_plus = 0
        for i in range(7, MAX_MANA+1):
            seven_plus += self.curve[i]

        return abs(self.curve[0] - ZERO) + abs(self.curve[1] - ONE) + abs(self.curve[2] - TWO) + abs(self.curve[3] - THREE) + abs(self.curve[4] - FOUR) + abs(self.curve[5] - FIVE) + abs(self.curve[6] - SIX) + abs(seven_plus - SEVEN_PLUS) + 6 * abs(self.creature_count - 27)

    def print(self):
        log(self.curve)


class Agent:
    def __init__(self):
        self.state = State()
        self.bestTurn = Turn()  # best turn actions found
        self.drafted_cards = []
        self.my_creatures = []
        self.enemy_creatures = []
        self.enemy_guards = []
        self.enemy_non_guards = []

    def reset(self):
        self.my_creatures.clear()
        self.enemy_creatures.clear()
        self.enemy_guards.clear()
        self.enemy_non_guards.clear()

    def attack(self, id, idTarget=None):
        action = Action()
        if idTarget is None:
            action.attack(id=id)
        else:
            action.attack(id=id, idTarget=idTarget)
        self.bestTurn.actions.append(action)

    def print(self):
        """
        print the bestTurn (best actions found)
        """
        self.bestTurn.print()

    def findBestPair(self):
        bestPairs = []
        if len(self.enemy_guards) != 0: return bestPairs  # if guard-enemy exists
        for enemy in self.enemy_non_guards:
            if enemy.used: continue  # if enemy card already in plan
            for my_card in self.my_creatures:
                if my_card.used: continue  # if my card already in plan
                if my_card.attack >= enemy.defense and my_card.defense > enemy.attack:
                    bestPairs.append((my_card, enemy))
                    my_card.used = True
                    enemy.used = True
                    break
        return bestPairs

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
        self.state.cards.clear()  # clear the card list every turn
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

        def draft():
            curve = ManaCurve()
            # compute the scores for the three choices
            bestScore = float('inf')
            bestPick = None
            for i in range(CARDS_PER_DRAFT):
                card = self.state.cards[i]
                curve.compute_curve(self.drafted_cards)
                curve.curve[card.cost] += 1
                if card.cardType == Creature: curve.creature_count += 1

                score = curve.evaluate_score()
                curve.curve[card.cost] -= 1
                if card.cardType == Creature: curve.creature_count -= 1

                if score < bestScore:
                    bestScore = score
                    bestPick = i

            action = Action()
            action.pick(id=bestPick)
            self.bestTurn.actions.append(action)
            self.drafted_cards.append(self.state.cards[bestPick])
            curve.print()

        def prepare():
            """
            Classify all cards
            """
            self.reset()

            for card in self.state.cards:
                if card.location == Mine:
                    self.my_creatures.append(card)
                elif card.location == Opponent:
                    self.enemy_creatures.append(card)
                    if card.guard:
                        self.enemy_guards.append(card)
                    else:
                        self.enemy_non_guards.append(card)

        def think_summon():
            my_mana = self.state.players[0].mana
            while my_mana > 0:
                bestCard = None
                bestScore = -float('inf')
                for card in self.state.cards:
                    if card.location != InHand: continue
                    if card.cost > my_mana: continue
                    # if card.cardType != Creature: continue
                    if card.cardType == GreenItem and len(self.my_creatures) == 0: continue
                    if card.cardType == RedItem and len(self.enemy_creatures) == 0: continue
                    if self.bestTurn.isCardPlayed(card.id): continue
                    score = card.cost  # grade the cards scores directly based on its cost
                    if score > bestScore:
                        bestScore = score
                        bestCard = card

                if bestCard is None:
                    break
                else:
                    action = Action()
                    if bestCard.cardType == Creature:  # Summon a creature
                        action.summon(id=bestCard.id)
                        if not bestCard.charge:
                            bestCard.used = True
                        self.my_creatures.append(bestCard)

                    elif bestCard.cardType == GreenItem:  # Use a green item
                        if len(self.my_creatures) == 0: continue
                        targetCard = self.my_creatures[0]
                        action.use(id=bestCard.id, idTarget=targetCard.id)

                    elif bestCard.cardType == RedItem:  # Use a red item
                        if len(self.enemy_creatures) == 0: continue
                        targetCard = self.enemy_creatures[0]
                        action.use(id=bestCard.id, idTarget=targetCard.id)

                    elif bestCard.cardType == BlueItem:  # Use a blue item
                        action.use(id=bestCard.id, idTarget=-1)

                    my_mana = my_mana - bestCard.cost
                    self.bestTurn.actions.append(action)

        def think_attack():
            def hitFace():
                for card in self.state.cards:
                    if card.location != Mine: continue
                    if card.used: continue
                    if len(self.enemy_guards) == 0:
                        self.attack(id=card.id)  # hit face
                        card.used = True

            def trade():
                bestPairs = self.findBestPair()
                if len(bestPairs) != 0:
                    for (my_card, enemy_card) in bestPairs:
                        self.attack(my_card.id, enemy_card.id)

            def attackGuard():
                for card in self.state.cards:
                    if len(self.enemy_guards) == 0: break
                    if card.location != Mine: continue
                    if card.used: continue
                    guard = self.enemy_guards[0]
                    self.attack(id=card.id, idTarget=guard.id)
                    card.used = True
                    guard.defense = guard.defense - card.attack
                    if guard.defense <= 0:
                        self.enemy_guards.remove(guard)

            def can_win():
                total_attack = 0
                for mine in self.my_creatures:
                    if mine.used: continue
                    total_attack += mine.attack
                return total_attack >= self.state.players[1].hp

            attackGuard()
            if can_win():
                hitFace()
            else:
                trade()
                hitFace()

        self.bestTurn.clear()
        if self.state.isInDraft():
            draft()
        else:
            prepare()
            think_summon()
            think_attack()


if __name__ == '__main__':
    agent = Agent()
    while True:
        agent.read()
        agent.think()
        agent.print()
