import sys
from enum import Enum
import copy

""" for debugging """


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def trap():
    exit(1)


""" Card locations """
Opponent = -1  # on the opponent's side of the board
InHand = 0  # on the player's side of the board
Mine = 1  # on the opponent's side of the board
OutOfPlay = 2  # for simulation use only, represented used (wasted) cards

""" Card Types """
Creature = 0
GreenItem = 1
RedItem = 2
BlueItem = 3

MAX_MANA = 12

CARDS_PER_DRAFT = 3

""" Mana curve """
ZERO = 1
ONE = 1
TWO = 6
THREE = 7
FOUR = 7
FIVE = 5
SIX = 3
SEVEN_PLUS = 2
CREATURE_NUM = 25


class Card:
    def __init__(self):
        self.id = None  # the identifier of a card
        self.idx = None
        self.cardId = None  # the identifier representing the instance of the card (there can be multiple instances of the same card in a game).
        self.location = None  # 0: in the player's hand, 1: on the player's side of the board, -1: on the opponent's side of the board
        self.cardType = None
        self.cost = None
        self.attack = None
        self.defense = None
        self.hpChange = None
        self.hpChangeEnemy = None
        self.cardDraw = None
        # self.abilities = None

        self.breakthrough = False
        self.charge = False
        self.guard = False
        self.drain = False
        self.ward = False
        self.lethal = False

        self.canAttack = False
        self.used = False

    def remove_ward(self):
        self.ward = False

    def do_attack(self, card_target):
        if self.lethal:
            card_target.receive_damage(amount=1000)
        else:
            card_target.receive_damage(amount=self.attack)

    def receive_damage(self, amount):
        if amount <= 0: return
        if self.ward:
            self.remove_ward()
            return
        self.defense -= amount
        if self.defense <= 0:
            self.location = OutOfPlay


class Player:
    def __init__(self):
        self.hp = None
        self.mana = None
        self.cardsRemaining = None
        self.rune = None
        self.draw = None

        self.cards_drawn = 0  # Represented number of cards drawn with the turn


class State:
    def __init__(self):
        self.players = [Player(), Player()]
        self.opponent_hand = None
        self.cards = []
        self.opponent_actions = None
        self.card_number_and_action_list = None

    def isInDraft(self):
        return self.players[0].mana == 0

    def update(self, turn, player_idx=0):
        """
        For simulation
        """
        my_player = copy.deepcopy(self.players[player_idx])
        opponent = copy.deepcopy(self.players[1 - player_idx])

        def apply_global_effects(card):
            my_player.cards_drawn += card.cardDraw
            my_player.mana -= card.cost
            my_player.hp += card.hpChange
            opponent.hp += card.hpChangeEnemy

        def summon():
            # Find the card summoned
            card = self.cards[action.idx]
            # Validity check
            assert card.cost <= my_player.mana, log("Attempted to summon a card without enough mana")
            assert card.cardType == Creature, log('Attempted to summon a non-creature card')
            # Play the card onto the board
            card.location = Mine if player_idx == 0 else Opponent
            card.canAttack = card.charge  # Creature can attack once it has "Charge"

            apply_global_effects(card)

        def use():
            card = self.cards[action.idx]
            assert card.cost <= my_player.mana, log("Attempted to use a card without enough mana")
            assert card.cardType != Creature, log("Attempted to use a creature card")

            apply_global_effects(card)
            card.location = OutOfPlay

            if action.idxTarget != -1:
                card_target = self.cards[action.idxTarget]

                # Keyword changes
                if card.cardType == GreenItem:
                    card_target.abilities |= card.abilities
                elif card.cardType == RedItem:
                    card_target.abilities &= ~card.abilities

                card_target.attack += card.attack

                # Damage
                # Check if the card is a damage and the target has Ward
                if card.defense > 0:
                    card_target.defence += card.defense
                else:
                    card_target.deal_damage(-card.defense)

        def attack():
            card = self.cards[action.idx]
            assert card.location == (Mine if player_idx == 0 else Opponent), log(
                "Attacking with an attacker that I do not control")
            assert card.canAttack, log("Attacking with an attacker that cannot attack")

            # Check for guards
            found_guard = False
            attacking_guard = False

            for card_ in self.cards:
                if card_.location != (Mine if Opponent else Mine): continue
                if not card_.guard: continue
                # There exits at least one guard
                found_guard = True
                if action.idxTarget == -1: log("Attempting attacking a player when there is a guard on board")
                if card_.idx == action.idxTarget:
                    attacking_guard = True

            assert not (found_guard and not attacking_guard), log(
                "Attempting attacking a creature when there is a guard on board")

            if action.idxTarget == -1:  # Hit face
                if card.attack > 0:
                    opponent.hp -= card.attack
            else:  # Hit creatures
                card_target = self.cards[action.idxTarget]

                # breakthrough
                if card.brekthrough:
                    if not card_target.ward:  # Breakthrough only when target is not Ward
                        reminder = card.attack - card_target.defense
                        if reminder >= 0: opponent.hp -= reminder

                # Drain
                if card_target.attack > 0:
                    if not card.ward and card_target.drain:
                        opponent.hp += card.attack  # Drain only if mine is not Ward

                if card.attack > 0:
                    if not card_target.ward and card.drain:
                        my_player.hp += card.attack  # Drain only if target is not Ward

                # Attack
                card.do_attack(card_target)
                card_target.do_attack(card)

        for action in turn.actions:
            if action.type == ActionType.Summon:  # Summon either a creature and an item
                summon()

            elif action.type == ActionType.Use:
                use()

            elif action.type == ActionType.Attack:
                attack()


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
        self.idx = 0
        self.idxTarget = 0

    """ helper functions """

    def pass_(self):
        self.type = ActionType.Pass

    def summon(self, idx):
        self.type = ActionType.Summon
        self.idx = idx

    def attack(self, idx, idxTarget=-1):
        self.type = ActionType.Attack
        self.idx = idx
        self.idxTarget = idxTarget

    def pick(self, idx):
        self.type = ActionType.Pick
        self.idx = idx

    def use(self, idx, idxTarget=-1):
        self.type = ActionType.Use
        self.idx = idx
        self.idxTarget = idxTarget

    def print(self, state, ending="; "):
        if self.type == ActionType.Pass:
            print("PASS")
        elif self.type == ActionType.Summon:
            card = state.cards[self.idx]
            print("SUMMON {}".format(card.id), end=ending)

        elif self.type == ActionType.Attack:
            card = state.cards[self.idx]
            card_target = state.cards[self.idxTarget]
            print("ATTACK {0} {1}".format(card.id, card_target.id), end=ending)

        elif self.type == ActionType.Pick:
            card = state.cards[self.idx]
            print("PICK {}".format(card.id), end=ending)

        elif self.type == ActionType.Use:
            card = state.cards[self.idx]
            card_target = state.cards[self.idxTarget]
            print("USE {0} {1}".format(card.id, card_target.id), end=ending)

        else:
            log("Action not found: {}".format(self.type))
            trap()


class Turn:
    """ Consists all actions to do in one turn """

    def __init__(self):
        self.actions = []

    def newAction(self):
        self.actions = []

    def isCardPlayed(self, idx):
        for action in self.actions:
            if not (action.type == ActionType.Summon or action.type == ActionType.Use): continue
            if action.idx == idx:
                return True
        return False

    def clear(self):
        self.actions.clear()

    def print(self, state):
        if len(self.actions) == 0:
            print("PASS")
            return

        for i in range(len(self.actions)):
            if i == len(self.actions) - 1:
                self.actions[i].print(state, ending='\n')
            else:
                self.actions[i].print(state)


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
        for i in range(7, MAX_MANA + 1):
            seven_plus += self.curve[i]

        return abs(self.curve[0] - ZERO) + abs(self.curve[1] - ONE) + abs(self.curve[2] - TWO) + abs(
            self.curve[3] - THREE) + abs(self.curve[4] - FOUR) + abs(self.curve[5] - FIVE) + abs(
            self.curve[6] - SIX) + abs(seven_plus - SEVEN_PLUS) + 10 * abs(self.creature_count - CREATURE_NUM)

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
            action.attack(idx=id)
        else:
            action.attack(idx=id, idxTarget=idTarget)
        self.bestTurn.actions.append(action)

    def print(self):
        """
        print the bestTurn (best actions found)
        """
        self.bestTurn.print(self.state)

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
            card.idx = i
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
            card.hpChange = my_health_change
            card.hpChangeEnemy = opponent_health_change
            card.cardDraw = card_draw

            # abilities: 'BCG---'
            for c in abilities:
                if c == 'B': card.breakthrough = True
                if c == 'C': card.charge = True
                if c == 'G': card.guard = True
                if c == 'D': card.drain = True
                if c == 'W': card.ward = True
                if c == 'L': card.lethal = True

            card.canAttack = False if card.location == InHand else True

            self.state.cards.append(card)

    def advanced_think(self):

        def evaluate_state(state_):
            return 0

        state = copy.deepcopy(self.state)
        best_score = -float('inf')
        best_turn = []
        for _ in range(10):
            # Generate a random turn
            random_turn = Turn()

            # Make a copy of the state -> new_state
            new_state = copy.deepcopy(state)

            # Use that turn to update the new_state
            new_state.update(random_turn, player_idx=0)

            # Evaluate the new_state
            score = evaluate_state(new_state)

            # If the score is better, keep that run
            if score > best_score:
                best_score = score
                best_turn = random_turn
        self.bestTurn = best_turn


if __name__ == '__main__':
    agent = Agent()
    while True:
        agent.read()
        agent.advanced_think()
        agent.print()
