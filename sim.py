import random
import numpy as np
from collections import defaultdict


NUM_PARTICIPANTS = 100

RESULTS_DIR = "results2"

class Proposal:
    def __init__(self, sender, receiver, use_rose):
        self.sender = sender
        self.receiver = receiver
        self.has_rose = use_rose
        self.accepted = False

class Stats:
    def __init__(self):
        self.proposals_sent = 0
        self.proposals_sent_no_rose = 0
        self.proposals_sent_w_rose = 0
        self.proposals_accepted = 0
        self.proposals_accepted_no_rose = 0
        self.proposals_accepted_w_rose = 0
        self.avg_desirability_score_accepted = 0
        self.avg_desirability_score_sent = 0

    def save(self, id, desirability_score):
        # write stats to file
        with open(f"{RESULTS_DIR}/{id}.txt", "w") as f:
            f.write(f"Total success rate: {self.proposals_accepted / self.proposals_sent}\n")
            f.write(f"No rose success rate: {self.proposals_accepted_no_rose / self.proposals_sent_no_rose}\n")
            f.write(f"Rose success rate: {self.proposals_accepted_w_rose / self.proposals_sent_w_rose}\n")
            f.write(f"Self desirability score: {desirability_score}\n")
            f.write(f"Average desirability score of accepted proposals: {self.avg_desirability_score_accepted}\n")
            f.write(f"Average desirability score of sent proposals: {self.avg_desirability_score_sent}\n")
    
    def update(self, proposal):
        self.proposals_sent += 1

        if proposal.has_rose:
            self.proposals_sent_w_rose += 1
            if proposal.accepted:
                self.proposals_accepted_w_rose += 1
        else:
            self.proposals_sent_no_rose += 1
            if proposal.accepted:
                self.proposals_accepted_no_rose += 1
        
        if proposal.accepted:
            self.proposals_accepted += 1
            self.avg_desirability_score_accepted = (self.avg_desirability_score_accepted + proposal.receiver.desirability_score) / 2

        self.avg_desirability_score_sent = (self.avg_desirability_score_sent + proposal.receiver.desirability_score) / 2


class Agent:
    def __init__(self, id, gender, num_roses, num_proposals, desirability_score):
        """
        Initialize an agent.
        
        :param agent_id: Unique identifier for the agent
        :param gender: Gender of the agent ('man' or 'woman')
        :param num_roses: Number of digital roses available to the agent
        :param desirability_score: Desirability score of the agent
        """
        self.id = id
        self.gender = gender
        self.desirability_score = desirability_score  # How attractive this agent is to others
        self.num_roses = num_roses
        self.roses_sent = 0
        self.num_proposals = num_proposals
        self.proposals_sent = []  # List of proposals sent
        self.proposals_received = []
        self.stats = Stats()
        self.send_q_table = np.zeros((NUM_PARTICIPANTS, 2)) # row for each agent in opposite sex, col for each action (proposal, proposal w/ rose)
        # self.receive_q_table = np.zeros((NUM_PARTICIPANTS, 2)) # row for each agent in opposite sex, col for each action (accept, reject)
        self.exploration_rate = 1.0
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.valid_receivers = [self._get_agent_id(i) for i in range(NUM_PARTICIPANTS)]
    
    def _opp_gender(self):
        return "woman" if self.gender == "man" else "man"
    
    def _get_agent_id(self, i):
        return f"{self._opp_gender()}_{i}"

    @staticmethod
    def q_table_max_idx(q_table):
        return np.unravel_index(np.argmax(q_table), q_table.shape)

    def q_table_valid_max(self, valid_receivers, has_rose):
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

    def choose_send_action(self, e):
        """
        Choose an action using epsilon-greedy strategy (with exploration and exploitation).
        
        :return: Action (0: proposal, 1: proposal with rose)
        """
        if len(self.proposals_sent) >= self.num_proposals:
            # this shouldn't happen
            raise ValueError("Limit on proposals reached")
        
        # valid_receivers = list()
        # for r in range(NUM_PARTICIPANTS): # assumes equal number of participants in each gender
        #     candidate_id = self._get_agent_id(r)
        #     if not any([candidate_id == p.receiver.id for p in self.proposals_sent]): # this is potentially slow could be sped up
        #         valid_receivers.append(candidate_id)

        valid_actions = [0]
        if self.roses_sent <= self.num_roses:
            valid_actions.append(1)

        action = {"receiver_id": None, "action": None}
        
        if random.random() < self.exploration_rate:
            action["action"] = random.choice(valid_actions)
            if e == 10:
                pass
                #print(f"valid_receivers: {self.valid_receivers}")
            action["receiver_id"] = random.choice(self.valid_receivers)
        
        else:
            q_max = self.q_table_valid_max(self.valid_receivers, len(valid_actions) > 1)
            action["receiver_id"] = self._get_agent_id(q_max[0])
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
        # print(f"{self.id} received {[(p.sender.id, p.has_rose) for p in self.proposals_received]}")
        # return None
        for proposal in self.proposals_received:
            score = self.score_proposal(proposal)
            # print(f"pscore: {score}, mescore: {self.desirability_score}")
            if score >= self.desirability_score:
                # print("accepted")
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


class Environment:
    def __init__(self, num_men, num_women, max_proposals):
        """
        Initialize the environment.
        
        :param num_men: Number of male agents
        :param num_women: Number of female agents
        """
        self.men = [
            Agent(id=f"man_{i}", gender="man", num_roses=self.assign_roses(), num_proposals=max_proposals, desirability_score=np.random.normal(50, 15))
            for i in range(num_men)
        ]
        self.women = [
            Agent(id=f"woman_{i}", gender="woman", num_roses=self.assign_roses(), num_proposals=max_proposals, desirability_score=np.random.normal(50, 15))
            for i in range(num_women)
        ]
        self.all_agents = {agent.id: agent for agent in self.men + self.women}
        self.max_proposals = max_proposals  # Maximum proposals that can be sent
        self.proposals = list()  # Proposals sent during the proposal stage

    def reset(self):
        """
        Reset proposals and roses for the next episode.
        """
        self.proposals = list()
        for agent in self.men + self.women:
            agent.proposals_sent = []
            agent.proposals_received = []
            agent.roses_sent = 0
            agent.valid_receivers = [agent._get_agent_id(i) for i in range(NUM_PARTICIPANTS)]

    @staticmethod
    def assign_roses():
        """
        Assign roses to an agent (80% get 2 roses, 20% get 8 roses).
        """
        return 1 if random.random() < 0.8 else 2
        # return 2 if random.random() < 0.8 else 8

    def proposal_stage(self, e):
        """
        Proposal stage where agents send proposals.
        """
        for sender in self.men + self.women:
            for _ in range(self.max_proposals): # currently all proposals are always used up
                action = sender.choose_send_action(e)
                if action["receiver_id"]:
                    sender.update_valid_receivers(action["receiver_id"])
                    receiver = self.all_agents[action["receiver_id"]]
                    proposal = Proposal(sender, receiver, action["action"] == 1)
                    self.proposals.append(proposal)
                    sender.update_proposals_sent(proposal)
                    receiver.update_proposals_received(proposal)

                else:
                    print("----WARNING: No valid receiver found*************************************")
            
            # print(f"{sender.id} sent {[(p.receiver.id, p.has_rose) for p in sender.proposals_sent]}")
            
    def response_stage(self):
        """
        Response stage where agents receive and evaluate proposals.
        """
        for agent in self.men + self.women:
            agent.process_proposals_received()
        
        for agent in self.men + self.women:
            agent.process_proposals_sent()
    

    def simulate(self, n=3, save_results=False):
        """
        Run the full simulation.
        """
        for episode in range(n):  # Simulate for 1000 episodes
            print(f"Episode {episode+1}")
            # print("=== Proposal Stage ===")
            self.proposal_stage(episode)
            # print("\n=== Response Stage ===")
            self.response_stage()
            # Decay exploration rate
            for agent in self.men + self.women:
                agent.exploration_rate = max(0.01, agent.exploration_rate * 0.995)  # Gradually reduce exploration
            
            self.reset()
        
        if save_results:
            for agent in self.men + self.women:
                # write contents of q table to file
                np.savetxt(f"{RESULTS_DIR}/{agent.id}_q.csv", agent.send_q_table, delimiter=",")
                agent.stats.save(agent.id, agent.desirability_score)


# Run simulation
if __name__ == "__main__":
    # Example: 10 men and 10 women
    NUM_PARTICIPANTS = 10
    env = Environment(num_men=NUM_PARTICIPANTS, num_women=NUM_PARTICIPANTS, max_proposals=3)
    env.simulate(n=10000, save_results=True)
