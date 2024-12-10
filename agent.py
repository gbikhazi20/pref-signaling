import numpy as np
import random

from stats import Stats


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
        self.send_q_table = np.zeros((num_participants, 2)) # row for each agent in opposite sex, col for each action (proposal, proposal w/ rose)
        self.receive_q_table = np.zeros((num_participants, 2)) # row for each agent in opposite sex, col for each action (accept, reject)
        self.exploration_rate = 1.0
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.valid_receivers = [self.get_agent_id(self.__opp_gender(), i) for i in range(self.num_participants)]
    
    def __opp_gender(self):
        return "man" if self.gender == "woman" else "woman"

    @staticmethod
    def q_table_max_idx(q_table):
        return np.unravel_index(np.argmax(q_table), q_table.shape)

    @staticmethod 
    def get_agent_id(gender, id):
        if gender not in {"man", "woman"}:
            raise ValueError(f"Gender must be one of {{man, woman}}. Received: {gender}")
    
        return f"{gender}_{id}"

    def reset(self):
        self.roses_sent = 0
        self.proposals_sent = list()
        self.proposals_received = list()
        self.valid_receivers = [self.get_agent_id(self.__opp_gender(), i) for i in range(self.num_participants)]

    # returns 
    def q_table_valid_max(self, valid_receivers):
        has_rose = self.roses_sent < self.num_roses
        valid_choices_q_table = list()
        valid_idx = list()
        for receiver_id in valid_receivers:
            idx = int(receiver_id.split("_")[1])
            valid_choices_q_table.append(self.send_q_table[idx][: 2 if has_rose else 1]) 
            valid_idx.append(idx)
        
        max_idx = Agent.q_table_max_idx(np.array(valid_choices_q_table))
        return (valid_idx[max_idx[0]], int(max_idx[1]))
    
    def update_proposals_sent(self, proposal):
        self.proposals_sent.append(proposal)
    
    def update_proposals_received(self, proposal):
        self.proposals_received.append(proposal)

    def update_valid_receivers(self, receiver_id):
        self.valid_receivers.remove(receiver_id)

    def choose_send_action(self):
        """
        Choose an action using epsilon-greedy strategy (with exploration and exploitation).
        
        :return: Action (0: proposal, 1: proposal with rose)
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
            q_max = self.q_table_valid_max(self.valid_receivers)
            action["receiver_id"] = self.get_agent_id(self.__opp_gender(), q_max[0])
            action["action"] = q_max[1]

        return action
    
    def score_proposal(self, proposal):
        d = proposal.sender.desirability_score
        r = 2 if proposal.has_rose else 0

        return d + r

    def process_proposals_received(self):
        """
        Process received proposals and update Q-table based on rewards.
        """
        for proposal in self.proposals_received:
            score = self.score_proposal(proposal)
            if score >= self.desirability_score:
                proposal.accepted = True
    
    def proposal_reward(self, proposal):
        d = proposal.receiver.desirability_score

        return d + (d - self.desirability_score) if proposal.accepted else - 5

    def process_proposals_sent(self):
        """
        Process sent proposals and update Q-table based on rewards.
        """
        for proposal in self.proposals_sent:
            self.stats.update(proposal)
            reward = self.proposal_reward(proposal)
            self.update_q_table(proposal, reward)

    def get_q_loc(self, proposal):
        receiver_idx = int(proposal.receiver.id.split("_")[1])
        action = 1 if proposal.has_rose else 0
        return receiver_idx, action

    def update_q_table(self, proposal, reward):
        """
        Update the Q-table using the Q-learning formula.
        """
        current_q_row, current_q_col = self.get_q_loc(proposal)
        current_q = self.send_q_table[current_q_row, current_q_col]
        max_future_q = np.max(self.send_q_table)
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_future_q - current_q)
        self.send_q_table[current_q_row, current_q_col] = new_q


class Man(Agent):
    def __init__(self, id, num_roses, num_proposals, desirability_score, num_participants):
        super().__init__(id, num_roses, num_proposals, desirability_score, num_participants)


class Woman(Agent):
    def __init__(self, id, num_roses, num_proposals, desirability_score, num_participants):
        super().__init__(id, num_roses, num_proposals, desirability_score, num_participants)

    