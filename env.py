import numpy as np
import os
import random

from agent import Agent, Proposal


class Environment:
    def __init__(self, num_men, num_women, max_proposals):
        """
        Initialize the environment.
        
        :param num_men: Number of male agents
        :param num_women: Number of female agents
        """
        self.num_men = num_men
        self.men = [
            Agent(id=f"man_{i}", gender="man", num_roses=self.assign_roses(), num_proposals=max_proposals, desirability_score=np.random.normal(50, 15))
            for i in range(num_men)
        ]
        self.num_women = num_women
        self.women = [
            Agent(id=f"woman_{i}", gender="woman", num_roses=self.assign_roses(), num_proposals=max_proposals, desirability_score=np.random.normal(50, 15))
            for i in range(num_women)
        ]
        self.all_agents = {agent.id: agent for agent in self.men + self.women}
        self.max_proposals = max_proposals  # Maximum proposals that can be sent
        self.proposals = list()  # Proposals sent during the proposal stage

    def reset(self):
        """
        Reset proposals and agents for the next episode.
        Agents' Q-tables and stats are not reset, obviously!
        """
        self.proposals = list()
        for agent in self.men + self.women:
            agent.reset()
        

    @staticmethod
    def assign_roses(d={0.8: 2, 0.2: 6}):
        """
        Assign roses to an agent. Default is 80% get 2 roses, 20% get 6 roses.
        Can be changed to any distribution.
        """
        # ensure keys of dictionary sum to 1
        if sum(d.keys()) != 1:
            raise ValueError("Keys of dictionary must sum to 1")
        
        ranges = dict() # ranges will map tuples of ranges to the number of roses they correspond to
        prev = 0
        for key in d:
            ranges[(prev, prev + key)] = d[key]
            prev += key
        
        rand = random.random()
        for (lo, hi) in ranges:
            if lo <= rand and rand < hi:
                return ranges[(lo, hi)]

    def proposal_stage(self):
        """
        Proposal stage where agents send proposals.
        """
        for sender in self.men + self.women:
            for _ in range(self.max_proposals): # currently all proposals are always used up. Could add a Q table for learning how many proposals to send?
                action = sender.choose_send_action()
                if action["receiver_id"]:
                    receiver = self.all_agents[action["receiver_id"]]
                    proposal = Proposal(sender, receiver, use_rose=action["action"] == 1)
                    self.proposals.append(proposal)

                    sender.send_proposal(proposal)
                    receiver.receive(proposal)

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
    

    def simulate(self, n=3, save_results=False, results_dir="results"):
        """
        Run the full simulation.
        """
        for episode in range(n):  # Simulate for 1000 episodes
            print(f"Episode {episode+1}")
            self.proposal_stage()
            self.response_stage()
            # Decay exploration rate
            for agent in self.men + self.women:
                agent.exploration_rate = max(0.01, agent.exploration_rate * 0.995)  # Gradually reduce exploration
            
            self.reset()
        
        if save_results:
            # make directory if it doesn't exist
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)
            for agent in self.men + self.women:
                # write contents of q table to file
                np.savetxt(f"{results_dir}/{agent.id}_q.csv", agent.send_q_table, delimiter=",")
                agent.stats.save(agent, results_dir=results_dir)