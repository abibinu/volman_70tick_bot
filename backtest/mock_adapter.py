import logging
from datetime import datetime

class MockMT5Adapter:
    def __init__(self):
        self.connected = True
        self.current_tick = None
        self.positions = {}
        self.next_ticket = 1000

    def connect(self):
        self.connected = True
        return True

    def shutdown(self):
        self.connected = False

    def get_tick(self, symbol):
        return self.current_tick

    def set_tick(self, tick):
        self.current_tick = tick

    def place_market_order(self, symbol, direction, volume, sl, tp, comment=""):
        ticket = self.next_ticket
        self.next_ticket += 1
        self.positions[ticket] = {"symbol": symbol, "type": 0 if direction == "BUY" else 1, "volume": volume, "sl": sl, "tp": tp, "price": self.current_tick["ask"] if direction == "BUY" else self.current_tick["bid"]}
        return ticket

    def modify_sl(self, ticket, new_sl):
        if ticket in self.positions:
            self.positions[ticket]["sl"] = new_sl
            return True
        return False

    def position_exists(self, ticket):
        return ticket in self.positions

    def close_position(self, ticket):
        if ticket in self.positions:
            del self.positions[ticket]
            return True
        return False

    def check_sl_tp(self):
        if not self.current_tick:
            return []
        closed_tickets = []
        bid = self.current_tick["bid"]
        ask = self.current_tick["ask"]
        for ticket, pos in list(self.positions.items()):
            if pos["type"] == 0:
                if bid <= pos["sl"]: closed_tickets.append((ticket, "SL"))
                elif bid >= pos["tp"]: closed_tickets.append((ticket, "TP"))
            else:
                if ask >= pos["sl"]: closed_tickets.append((ticket, "SL"))
                elif ask <= pos["tp"]: closed_tickets.append((ticket, "TP"))
        for ticket, reason in closed_tickets:
            del self.positions[ticket]
        return closed_tickets
