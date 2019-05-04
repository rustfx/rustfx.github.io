import sys
import inspect
import math

from state import State
import actions
import items.weapons as weapons
import items.potions as potions
import items.armor as armor
import events

__author__ = 'Stephen Conway'


class Location:
    def __init__(self, name, hotkey, linked):
        self.name = name
        self.hotkey = hotkey
        self.linked = linked
        print("{}\n{}".format(self.name, self.intro_text()))
        print()
        # Ability to automatically list a shop's wares
        # if issubclass(getattr(sys.modules[__name__], self.name.replace(" ", "")), Shop):
        #     self.print_inventory()
        self.print_actions()

    def do_action(self, action, **kwargs):
        action_method = getattr(self, action.method.__name__)
        if action_method:
            action_method(**kwargs)

    def intro_text(self):
        raise NotImplementedError()

    @staticmethod
    def change_location(location):
        cur_state = State()
        ins_state = cur_state.load_quicksave()
        player = ins_state['player']
        player.location = location
        cur_state.save_cur_state()

    def print_actions(self):
        avail_actions = self.available_actions()
        for move in avail_actions:
            print(move)

    def available_moves(self):
        moves = []
        for link in self.linked:
            refmod = getattr(sys.modules[__name__], link)
            move = actions.GoToLocation(refmod, getattr(refmod, "name"), getattr(refmod, "hotkey"))
            moves.append(move)
        return moves

    def available_actions(self):
        import player
        moves = self.available_moves()
        view_inventory_action = actions.ViewInventory(player.Player)
        equip_item_action = actions.EquipItem(player.Player)
        moves.append(view_inventory_action)
        moves.append(equip_item_action)
        return moves


class Village(Location):
    name = "Village"
    hotkey = "V"
    linked = ["Forest", "Inn", "WeaponShop", "ArmorShop", "PotionShop"]

    def __init__(self):
        super().__init__(self.name, self.hotkey, self.linked)

    def intro_text(self):
        return "There are lots of people going about there business here. You see various shops along the main road."

    def available_actions(self):
        moves = super().available_actions()
        return moves

    def print_inventory(self):
        pass


class Inn(Location):
    name = "Inn"
    hotkey = "N"
    linked = ["Village"]

    def __init__(self):
        super().__init__(self.name, self.hotkey, self.linked)

    def intro_text(self):
        return "Welcome to the SleepItOff Inn. Do you want to rest?"

    def available_actions(self):
        import player
        moves = super().available_actions()
        moves.append(actions.Rest(player.Player))
        return moves

    def print_inventory(self):
        pass


class Forest(Location):
    name = "Forest"
    hotkey = "F"
    linked = ["Village"]

    def __init__(self):
        super().__init__(self.name, self.hotkey, self.linked)

    def intro_text(self):
        return "The forest is dark and ominous. There are likely monsters hiding behind every tree."

    def available_actions(self):
        moves = super().available_actions()
        moves.append(actions.LookForTrouble(events.Event()))
        return moves

    def print_inventory(self):
        pass


class Shop(Location):
    def __init__(self, name, hotkey, linked, inventory):
        self.inventory = inventory
        super().__init__(name, hotkey, linked)

    def intro_text(self):
        pass

    def available_actions(self):
        moves = super().available_actions()
        moves.append(actions.BuyItem(self))
        moves.append(actions.SellItem(self))
        return moves

    def print_inventory(self):
        if len(self.inventory) == 0:
            print("None")
        else:
            for idx, val in enumerate(self.inventory):
                print("[{}] {}".format((idx+1), val))

    def buy_item(self):
        cur_state = State()
        ins_state = cur_state.load_quicksave()
        player = ins_state['player']
        player_gold = player.gold
        cur_state.save_cur_state()

        self.print_inventory()
        print("[{}] Go Back".format(len(self.inventory)+1))
        print("------")
        print()

        item_idx = input("Which item do you want? ")
        item_keys = ["{}".format(x) for x in range(1, len(self.inventory)+2)]
        if item_idx in item_keys:
            if int(item_idx) == len(self.inventory)+1 \
                    or item_idx == 'exit' \
                    or item_idx == 'back':
                return

            if player_gold >= self.inventory[int(item_idx)-1].value:
                print("Bought: {}".format(self.inventory[int(item_idx)-1]))
                cur_state = State()
                ins_state = cur_state.load_quicksave()
                player = ins_state['player']
                player.gold -= self.inventory[int(item_idx)-1].value
                player.inventory.append(self.inventory[int(item_idx)-1])
                cur_state.save_cur_state()
            else:
                print("You can't afford that!")
            print()

    @staticmethod
    def get_party_level():
        cur_state = State()
        ins_state = cur_state.load_quicksave()
        party = ins_state['party']
        return math.floor(sum(char.level for char in party)/len(party))

    @staticmethod
    def sell_item():
        cur_state = State()
        ins_state = cur_state.load_quicksave()
        player = ins_state['player']
        player_inventory = player.inventory
        cur_state.save_cur_state()

        if len(player_inventory) == 0:
            print("Your inventory is empty!")
            return
        idx = 0
        for idx, val in enumerate(player_inventory):
            print("[{}] {}".format((idx+1), val))
        print("[{}] Go Back".format(idx+2))
        print("------")
        print()

        item_idx = input("Which item do you want to sell? ")
        print("------")
        print()
        item_keys = ["{}".format(x) for x in range(1, len(player_inventory)+2)]
        if item_idx in item_keys:
            if int(item_idx) == len(player_inventory)+1 \
                    or item_idx == 'exit' \
                    or item_idx == 'back':
                return

            print("Sold: {}".format(player_inventory[int(item_idx)-1]))
            cur_state = State()
            ins_state = cur_state.load_quicksave()
            player = ins_state['player']
            player.gold += (player_inventory[int(item_idx)-1].value * 0.7)
            player.inventory.pop(int(item_idx)-1)
            cur_state.save_cur_state()
            print()


class ArmorShop(Shop):
    name = "Armor Shop"
    hotkey = "A"
    linked = ["Village"]
    inventory = []

    def __init__(self):
        party_level = self.get_party_level()
        self.inventory = []
        for name, obj in inspect.getmembers(sys.modules['items.armor']):
            if inspect.isclass(obj) and obj != armor.Armor:
                if obj().for_sale:
                    cur_armor = getattr(armor, name)()
                    cur_armor.set_level(party_level)
                    self.inventory.append(cur_armor)
        super().__init__(self.name, self.hotkey, self.linked, self.inventory)

    def intro_text(self):
        return "Welcome to the Armor Shop. Would you like some armor?"

    def available_actions(self):
        moves = super().available_actions()
        return moves

    def print_inventory(self):
        super().print_inventory()

    def buy_item(self):
        super().buy_item()


class WeaponShop(Shop):
    name = "Weapon Shop"
    hotkey = "W"
    linked = ["Village"]
    inventory = []

    def __init__(self):
        party_level = self.get_party_level()
        self.inventory = []
        for name, obj in inspect.getmembers(sys.modules['items.weapons']):
            if inspect.isclass(obj) and obj != weapons.Weapon:
                if obj().for_sale:
                    cur_weapon = getattr(weapons, name)()
                    cur_weapon.set_level(party_level)
                    self.inventory.append(cur_weapon)
        super().__init__(self.name, self.hotkey, self.linked, self.inventory)

    def intro_text(self):
        return "Welcome to the Weapon Shop. Would you like a weapon?"

    def available_actions(self):
        moves = super().available_actions()
        return moves

    def print_inventory(self):
        super().print_inventory()

    def buy_item(self):
        super().buy_item()


class PotionShop(Shop):
    name = "Potion Shop"
    hotkey = "P"
    linked = ["Village"]
    inventory = []

    def __init__(self):
        self.inventory = []
        for name, obj in inspect.getmembers(sys.modules['items.potions']):
            if inspect.isclass(obj) and obj != potions.Potion:
                if obj().for_sale:
                    self.inventory.append(getattr(potions, name)())
        super().__init__(self.name, self.hotkey, self.linked, self.inventory)

    def intro_text(self):
        return "Welcome to the Potion Shop. Would you like a potion?"

    def available_actions(self):
        moves = super().available_actions()
        return moves

    def print_inventory(self):
        super().print_inventory()

    def buy_item(self):
        super().buy_item()
