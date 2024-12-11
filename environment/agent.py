import numpy as np
import random

from stats.stats import Stats


class Proposal:
    def __init__(self, sender, receiver, use_rose):
        self.sender = sender
        self.receiver = receiver
        self.has_rose = use_rose
    
    def accept(self):
        self.accepted = True
    
    def reject(self):
        self.accepted = False

class Agent:
    def __init__(self, id, gender, num_roses, num_proposals, desirability_score, num_participants=10, learning_rate=0.1, discount_factor=0.95):
        """
        Initialize an agent.
        
        :param id: Unique identifier for the agent
        :param gender: Gender of the agent ('man' or 'woman')
        :param num_roses: Number of digital roses available to the agent
        :param num_proposals: Number of proposals the agent can send
        :param desirability_score: Desirability score of the agent
        :param num_participants: Number of participants of the opposite gender in the simulation
        """
        self.id = id # format is {gender}_{i} for i <= num participants of same gender
        self.gender = gender
        self.desirability_score = desirability_score  # how attractive this agent is to others
        self.num_participants = num_participants
        self.num_roses = num_roses # number of roses the agent can send
        self.roses_sent = 0
        self.num_proposals = num_proposals # number of proposals the agent can send
        self.proposals_sent = list()
        self.proposals_received = list()
        self.stats = Stats()
        self.send_q_table = np.zeros((num_participants, 2)) # row for each agent in opposite sex, col for each action in {proposal, proposal w/ rose}
        self.receive_q_table = np.zeros((num_participants, 2)) # row for each agent in opposite sex, col for each action in {accept, reject}
        self.exploration_rate = 1.0
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.valid_receivers = [self.get_agent_id(self.__opp_gender(), i) for i in range(self.num_participants)]
    
    def __str__(self):
        return f"{self.id}, ds={self.desirability_score}"
    
    def __opp_gender(self):
        return "man" if self.gender == "woman" else "woman"
    
    def __update_proposals_sent(self, proposal):
        self.proposals_sent.append(proposal)
        
    def __update_proposals_received(self, proposal):
        self.proposals_received.append(proposal)

    def __update_valid_receivers(self, receiver_id):
        self.valid_receivers.remove(receiver_id)

    @staticmethod
    def __q_table_max_idx(q_table):
        # return the location of the max value in the q table
        return np.unravel_index(np.argmax(q_table), q_table.shape)

    @staticmethod 
    def get_agent_id(gender, id):
        if gender not in {"man", "woman"}:
            raise ValueError(f"Gender must be one of {{man, woman}}. Received: {gender}")
    
        return f"{gender}_{id}"

    def best_send_action(self):
        has_rose = self.roses_sent < self.num_roses
        valid_choices_q_table = list()
        valid_idx = list()
        # build up a subset of q table with only valid choices
        for receiver_id in self.valid_receivers:
            idx = int(receiver_id.split("_")[1])
            valid_choices_q_table.append(self.send_q_table[idx][: 2 if has_rose else 1]) 
            valid_idx.append(idx)
        
        max_idx = Agent.__q_table_max_idx(np.array(valid_choices_q_table))

        # return the receiver id and the action
        return (valid_idx[max_idx[0]], int(max_idx[1]))

    def best_receive_action(self, proposal):
        # valid_choices_q_table = list()
        # valid_idx = list()
        # build up a subset of q table with only valid choices
        sender_idx = int(proposal.sender.id.split("_")[1])
        return np.argmax(self.receive_q_table[sender_idx])

    def send(self, proposal):
        """
        Process a sent proposal.
        """
        self.__update_valid_receivers(proposal.receiver.id)
        self.__update_proposals_sent(proposal)
    
    def receive(self, proposal):
        """
        Process a received proposal.
        """
        self.__update_proposals_received(proposal)

    def choose_send_action(self):
        """
        Choose an action using epsilon-greedy strategy (with exploration and exploitation).
        
        :return: dict of format {receiver_id: str, "action": int}
        """
        if len(self.proposals_sent) >= self.num_proposals:
            # this shouldn't happen
            raise ValueError("Limit on proposals reached")

        valid_actions = [0]
        if self.roses_sent <= self.num_roses:
            valid_actions.append(1)

        action = {"receiver_id": None, "action": None}
        
        if random.random() < self.exploration_rate:
            action["action"] = random.choice(valid_actions)
            action["receiver_id"] = random.choice(self.valid_receivers)
        
        else:
            q_max = self.best_send_action()
            action["receiver_id"] = self.get_agent_id(self.__opp_gender(), q_max[0])
            action["action"] = q_max[1]

        return action

    def choose_receive_action(self, proposal):
        """
        Choose an action using epsilon-greedy strategy.
        """
        if len(self.proposals_received) == 0:
            return
        
        valid_actions = [0, 1] # 0 for reject, 1 for accept
        action = None

        if random.random() < self.exploration_rate: # could have a different exploration rate for receiving
            action = random.choice(valid_actions)
        
        else:
            action = self.best_receive_action(proposal) # this is q_max

        return action
    
    def screen_proposals_received(self):
        """
        Process received proposals and update Q-table based on rewards.
        """
        for proposal in self.proposals_received:
            action = self.choose_receive_action(proposal)
            if action == 1: 
                proposal.accept() # accept if that is the chosen action
            else:
                proposal.reject()
    
    def __sent_proposal_reward(self, proposal):
        """
        Calculate the reward for a sent proposal.
        :param proposal: proposal to evaluate
        """
        if proposal.sender != self:
            raise ValueError(f"Invalid sender. Expected {self.id}. Received {proposal.receiver.id}")
        
        d = proposal.receiver.desirability_score

        return d + (d - self.desirability_score) * 2 if proposal.accepted else - 10

    def process_matches(self, track_stats=False):
        """
        Process sent proposals and update Q-table based on rewards.
        """
        for proposal in self.proposals_sent:
            reward = self.__sent_proposal_reward(proposal)
            self.update_send_q_table(proposal, reward)
            if track_stats:
                self.stats.track_sent(proposal)
        
        for proposal in self.proposals_received:
            reward = self.received_proposal_reward(proposal)
            self.update_receive_q_table(proposal, reward)
            if track_stats:
                self.stats.track_received(proposal)

    def __get_send_q_loc(self, proposal):
        receiver_idx = int(proposal.receiver.id.split("_")[1])
        action = 1 if proposal.has_rose else 0
        return receiver_idx, action

    def __get_receive_q_loc(self, proposal):
        sender_idx = int(proposal.sender.id.split("_")[1])
        action = 1 if proposal.accepted else 0
        return sender_idx, action

    def update_send_q_table(self, proposal, reward):
        """
        Update the send Q-table using the Q-learning formula.
        """
        current_q_row, current_q_col = self.__get_send_q_loc(proposal)
        current_q = self.send_q_table[current_q_row, current_q_col]
        max_future_q = np.max(self.send_q_table)
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_future_q - current_q)
        self.send_q_table[current_q_row, current_q_col] = new_q
    
    def update_receive_q_table(self, proposal, reward):
        """
        Update the receive Q-table using the Q-learning formula.
        """
        current_q_row, current_q_col = self.__get_receive_q_loc(proposal)
        current_q = self.receive_q_table[current_q_row, current_q_col]
        max_future_q = np.max(self.receive_q_table)
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_future_q - current_q)
        self.receive_q_table[current_q_row, current_q_col] = new_q
    
    def reset(self):
        self.roses_sent = 0
        self.proposals_sent = list()
        self.proposals_received = list()
        self.valid_receivers = [self.get_agent_id(self.__opp_gender(), i) for i in range(self.num_participants)]       


class Man(Agent):
    def __init__(self, id, num_roses, num_proposals, desirability_score, num_participants):
        super().__init__(f"man_{id}", "man", num_roses, num_proposals, desirability_score, num_participants)

    
    def received_proposal_reward(self, proposal):
        """
        Calculate the reward for a received proposal.
        :param proposal: proposal to evaluate
        """
        if proposal.receiver != self:
            raise ValueError(f"Invalid receiver. Expected {self.id}. Received {proposal.receiver.id}")

        # assumes people are increasingly selective as they are more desirable.
        # this function is a bit arbitrary and could be changed, but it felt intuitive:
        # an agent with desirability 40 will be open to another agent that is ~12 desirability points less than them
        # an agent with desirability 90 will be open to another agent that is ~2 desirability points less than them
        # openness = 2 * np.log2(102 - self.desirability_score)
        openness = 4 + (100 - self.desirability_score) / 10
        
        rose_boost = 0
        if proposal.has_rose:
            rose_boost = openness / 2

        if proposal.accepted:
            if proposal.sender.desirability_score < self.desirability_score - (openness + rose_boost):
                return -50
            else:
                return 50 + (proposal.sender.desirability_score - self.desirability_score) + rose_boost
        
        else:
            if proposal.sender.desirability_score < self.desirability_score - (openness + rose_boost):
                return 10
            else:
                return -30

class Woman(Agent):
    def __init__(self, id, num_roses, num_proposals, desirability_score, num_participants):
        super().__init__(f"woman_{id}", "woman", num_roses, num_proposals, desirability_score, num_participants)
    
    def received_proposal_reward(self, proposal):
        """
        Calculate the reward for a received proposal.
        :param proposal: proposal to evaluate
        """
        if proposal.receiver != self:
            raise ValueError(f"Invalid receiver. Expected {self.id}. Received {proposal.receiver.id}")

        # assumes people are increasingly selective as they are more desirable.
        # this function is a bit arbitrary and could be changed, but it felt intuitive:
        # an agent with desirability 40 will be open to another agent that is ~12 desirability points less than them
        # an agent with desirability 90 will be open to another agent that is ~2 desirability points less than them
        # openness = 2 * np.log2(102 - self.desirability_score)
        openness = 4 + (100 - self.desirability_score) / 10
        
        rose_boost = 0
        if proposal.has_rose:
            rose_boost = openness / 2

        if proposal.accepted:
            if proposal.sender.desirability_score < self.desirability_score - (openness + rose_boost):
                return -10
            else:
                return 50 + (proposal.sender.desirability_score - self.desirability_score) + rose_boost
        
        else:
            if proposal.sender.desirability_score < self.desirability_score - (openness + rose_boost):
                return 10
            else:
                return -10

    