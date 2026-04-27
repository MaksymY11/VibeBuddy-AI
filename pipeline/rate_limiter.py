class RateLimiter:
    def __init__(self, max_flows=5, max_turns=4):
        self.flow_count = 0
        self.turn_count = 0
        self.max_flows = max_flows
        self.max_turns = max_turns

    def can_start_flow(self):
        return self.flow_count < self.max_flows
    
    def can_send_message(self):
        return self.turn_count < self.max_turns
    
    def start_flow(self):
        self.flow_count += 1
        self.turn_count = 0
    
    def add_turn(self):
        self.turn_count += 1