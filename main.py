import sys
from enum import Enum
import copy
import random

""" for debugging """


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def trap():
    exit(1)


class Random(object):
    """
        def __init__(self, x=time):
        self.x = np.uint64(x)

    def get_random_(self):
        self.x ^= self.x << np.uint64(21)
        self.x ^= self.x >> np.uint64(35)
        self.x ^= self.x << np.uint64(4)
        return abs(np.int64(self.x).item())
    """

    @classmethod
    def get_random_int(cls, upper_bound):
        """
        Return a number between 0 and upper_bound
        """
        return random.randint(0, upper_bound)


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

MAX_CREATURES_IN_PLAY = 6

OPPONENT_FACE = -1

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


class Player:
    def __init__(self):
        self.hp = None
        self.mana = None
        self.cardsRemaining = None
        self.rune = None
        self.draw = None

        self.cards_drawn = 0  # Represented number of cards drawn with the turn

    def do_attack(self, card, card_target):
        if card.lethal:
            self.receive_damage(card_target, amount=1000)
        else:
            self.receive_damage(card_target, amount=card.attack)

    @classmethod
    def receive_damage(cls, card, amount):
        if amount <= 0: return
        if card.ward:
            card.remove_ward()
            return
        card.defense -= amount
        if card.defense <= 0:
            card.location = OutOfPlay


class State:
    def __init__(self):
        self.players = [Player(), Player()]
        self.opponent_hand = None
        self.cards = []
        self.opponent_actions = None
        self.card_number_and_action_list = None

        self.my_creatures_idxs = []
        self.opponent_creatures_idxs = []

    def isInDraft(self):
        return self.players[0].mana == 0

    def generateActions(self, player_idx=0):
        """
        Generate a list of legal actions
        """

        def debug_creatures_idxs():
            """
            For debugging only
            """
            log("My Creatures:")
            for idx in my_creatures_idxs:
                log(self.cards[idx].id)

            log("------")
            log("Opponent Creatures:")
            for idx in opponent_creatures_idxs:
                log(self.cards[idx].id)

        my_player = copy.deepcopy(self.players[0])
        my_creatures_idxs = copy.deepcopy(self.my_creatures_idxs)
        opponent_creatures_idxs = copy.deepcopy(self.opponent_creatures_idxs)
        actions = []

        # debug_creatures_idxs()

        for card in self.cards:
            # Playing the cards in my hand
            if card.location == InHand:
                if card.cost > my_player.mana: continue

                if card.cardType == Creature:  # Check if can summon
                    if len(my_creatures_idxs) >= MAX_CREATURES_IN_PLAY: continue
                    action = Action()
                    action.summon(card.idx)
                    # Update
                    # my_creatures_idxs.append(card.idx)
                    # my_player.mana -= card.cost
                    actions.append(action)

                else:
                    # Blue item
                    if card.cardType == BlueItem:
                        action = Action()
                        action.use(idx=card.idx, idxTarget=OPPONENT_FACE)

                        # my_player.mana -= card.cost
                        actions.append(action)

                    elif card.cardType == RedItem:
                        # Red item
                        for creature_idx in opponent_creatures_idxs:
                            # Red target opponent creature only
                            if self.cards[creature_idx].location == Mine or self.cards[
                                creature_idx].location == InHand: continue
                            action = Action()
                            action.use(idx=card.idx, idxTarget=creature_idx)
                            # my_player.mana -= card.cost
                            actions.append(action)
                    else:
                        # Green item
                        for creature_idx in my_creatures_idxs:
                            # Green target my creature only
                            if self.cards[creature_idx].location == Opponent or self.cards[
                                creature_idx].location == InHand: continue
                            action = Action()
                            action.use(idx=card.idx, idxTarget=creature_idx)
                            # my_player.mana -= card.cost
                            actions.append(action)

            # Playing the cards on the board
            elif card.location == Mine and card.canAttack:

                # Find attacking target
                found_guard = False
                for creature_idx in opponent_creatures_idxs:
                    creature = self.cards[creature_idx]
                    if creature.location == Mine: continue
                    if creature.guard:
                        # Attack any of guards
                        found_guard = True
                        action = Action()
                        action.attack(idx=card.idx, idxTarget=creature_idx)
                        actions.append(action)
                        card.canAttack = False

                if not found_guard:

                    # Attack any of opponent creatures
                    for creature_idx in opponent_creatures_idxs:
                        # creature = self.cards[creature_idx]
                        if self.cards[creature_idx].location == Mine: continue
                        action = Action()
                        action.attack(idx=card.idx, idxTarget=creature_idx)
                        actions.append(action)
                        card.canAttack = False

                    # Attack the player
                    action = Action()
                    action.attack(idx=card.idx)
                    actions.append(action)
                    card.canAttack = False

        return actions

    @classmethod
    def apply_global_effects(cls, player, opponent, card):
        player.cards_drawn += card.cardDraw
        player.mana -= card.cost
        player.hp += card.hpChange
        opponent.hp += card.hpChangeEnemy

    def summon(self, my_player, opponent, player_idx, action):
        if len(self.my_creatures_idxs) >= MAX_CREATURES_IN_PLAY: return
        # Find the card summoned
        card = self.cards[action.idx]
        # Validity check
        assert card.cost <= my_player.mana, log("Attempted to summon a card without enough mana")
        assert card.cardType == Creature, log('Attempted to summon a non-creature card')
        # Play the card onto the board
        card.location = Mine
        card.canAttack = card.charge  # Creature can attack once it has "Charge"
        my_player.mana -= self.cards[action.idx].cost
        self.my_creatures_idxs.append(card.idx)
        self.apply_global_effects(card=card, player=my_player, opponent=opponent)

    def attack(self, my_player, opponent, action, player_idx):
        card = self.cards[action.idx]
        assert card.location == Mine, log(
            "Attacking with an attacker that I do not control")
        # assert card.canAttack, log("Attacking with an attacker that cannot attack")
        if not card.canAttack: return
        # Check for guards
        found_guard = False
        attacking_guard = False

        for idxTarget in self.opponent_creatures_idxs:
            creature = self.cards[idxTarget]
            if creature.location == Mine: continue
            if creature.guard:
                if action.idxTarget == OPPONENT_FACE: log("Attempting attacking a player when there is a guard on board")

        assert not (found_guard and not attacking_guard), log("Attempting attacking a creature when there is a guard on board")

        if action.idxTarget == OPPONENT_FACE:  # Hit face
            if card.attack > 0:
                opponent.hp -= card.attack
        else:  # Hit creatures
            card_target = self.cards[action.idxTarget]

            # breakthrough
            if card.breakthrough:
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
            my_player.do_attack(card=card, card_target=card_target)
            opponent.do_attack(card=card_target, card_target=card)

            if card.location == OutOfPlay: self.my_creatures_idxs.remove(card.idx)
            if card_target.location == OutOfPlay: self.opponent_creatures_idxs.remove(card_target.idx)

    def use(self, my_player, opponent, action):
        card = self.cards[action.idx]
        assert card.cost <= my_player.mana, log("Attempted to use a card without enough mana")
        assert card.cardType != Creature, log("Attempted to use a creature card")

        self.apply_global_effects(player=my_player, opponent=opponent, card=card)
        card.location = OutOfPlay
        my_player.mana -= self.cards[action.idx].cost
        if action.idxTarget != OPPONENT_FACE:
            card_target = self.cards[action.idxTarget]

            # Keyword changes
            if card.cardType == GreenItem:
                card_target.breakthrough = card.breakthrough
                card_target.drain = card.drain
                card_target.ward = card.ward
                card_target.guard = card.guard
                card_target.lethal = card.lethal
                card_target.charge = card.charge

            elif card.cardType == RedItem:
                if card.breakthrough: card_target.breakthrough = False
                if card.ward: card_target.breakthrough = False
                if card.guard: card_target.guard = False
                if card.lethal: card_target.lethal = False
                if card.charge: card_target.charge = False
                if card.drain: card_target.drain = False

            card_target.attack += card.attack

            # Damage
            # Check if the card is a damage and the target has Ward
            if card.defense > 0:
                card_target.defense += card.defense
            else:
                opponent.receive_damage(card=card_target, amount=-card.defense)
                if card_target.location == OutOfPlay: self.opponent_creatures_idxs.remove(card_target.idx)

    def update_action(self, action, player_idx=0):
        """
        For simulation one action
        """
        my_player = self.players[0]
        opponent = self.players[1]

        if action.type == ActionType.Summon:  # Summon either a creature and an item
            self.summon(my_player=my_player, player_idx=player_idx, action=action, opponent=opponent)

        elif action.type == ActionType.Use:
            self.use(my_player=my_player, opponent=opponent, action=action)

        elif action.type == ActionType.Attack:
            self.attack(my_player=my_player, opponent=opponent, action=action, player_idx=player_idx)

    def update(self, turn, player_idx=0):
        """
        For simulation one turn
        """
        my_player = copy.deepcopy(self.players[player_idx])
        opponent = copy.deepcopy(self.players[1 - player_idx])

        for action in turn.actions:
            if action.type == ActionType.Summon:  # Summon either a creature and an item
                self.summon(my_player=my_player, player_idx=player_idx, action=action, opponent=opponent)

            elif action.type == ActionType.Use:
                self.use(my_player=my_player, opponent=opponent, action=action)

            elif action.type == ActionType.Attack:
                self.attack(my_player=my_player, opponent=opponent, action=action, player_idx=player_idx)


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

    def attack(self, idx, idxTarget=OPPONENT_FACE):
        self.type = ActionType.Attack
        self.idx = idx
        self.idxTarget = idxTarget

    def pick(self, idx):
        self.type = ActionType.Pick
        self.idx = idx

    def use(self, idx, idxTarget=OPPONENT_FACE):
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
            if self.idxTarget == OPPONENT_FACE:
                print("ATTACK {0} {1}".format(card.id, OPPONENT_FACE), end=ending)
            else:
                card_target = state.cards[self.idxTarget]
                print("ATTACK {0} {1}".format(card.id, card_target.id), end=ending)

        elif self.type == ActionType.Pick:
            card = state.cards[self.idx]
            print("PICK {}".format(card.id), end=ending)

        elif self.type == ActionType.Use:
            card = state.cards[self.idx]
            if self.idxTarget == OPPONENT_FACE:
                print("USE {0} {1}".format(card.id, OPPONENT_FACE), end=ending)
            else:
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

        self.rnd = Random()

    def reset(self):
        self.my_creatures.clear()
        self.enemy_creatures.clear()
        self.enemy_guards.clear()
        self.enemy_non_guards.clear()

    def getRandomAction(self, state, player_idx=0):
        actions = state.generateActions(player_idx)
        if len(actions) == 0: return None
        action_idx = self.rnd.get_random_int(upper_bound=len(actions) - 1)
        action = actions[action_idx]
        return action

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

        self.state.my_creatures_idxs.clear()
        self.state.opponent_creatures_idxs.clear()

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

            if card.cardType == Creature and card.location == Mine:
                self.state.my_creatures_idxs.append(card.idx)
            elif card.cardType == Creature and card.location == Opponent:
                self.state.opponent_creatures_idxs.append(card.idx)

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

    def random_think(self):

        self.bestTurn.clear()

        if self.state.isInDraft():
            pass
        else:
            new_state = copy.deepcopy(self.state)
            while True:
                action = self.getRandomAction(new_state)
                if action is None:
                    return
                # When have legal action
                # log("{} {} {}".format(action.type, self.state.cards[action.idx].id, action.idxTarget))
                self.bestTurn.actions.append(action)
                new_state.update_action(action=action, player_idx=0)


if __name__ == '__main__':
    agent = Agent()
    while True:
        agent.read()
        agent.random_think()
        agent.print()
