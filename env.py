import numpy as np
import os
import random
from tqdm import tqdm

from agent import Man, Woman, Proposal


class Environment:
    def __init__(self, num_men, num_women, max_proposals, rose_distribution={0.8: 2, 0.2: 6}):
        """
        Initialize the environment.
        
        :param num_men: Number of male agents
        :param num_women: Number of female agents
        """
        self.num_men = num_men
        self.men = [
            Man(id=i, num_roses=self.assign_roses(d=rose_distribution), num_proposals=max_proposals, desirability_score=np.random.normal(50, 15),
                num_participants=num_women)
            for i in range(num_men)
        ]
        self.num_women = num_women
        self.women = [
            Woman(id=i, num_roses=self.assign_roses(d=rose_distribution), num_proposals=max_proposals, desirability_score=np.random.normal(50, 15),
                  num_participants=num_men)
            for i in range(num_women)
        ]
        self.all_agents = {agent.id: agent for agent in self.men + self.women}
        self.max_proposals = max_proposals  # Maximum proposals that can be sent
        self.proposals = list()  # Proposals sent during the proposal stage
        self.rose_distribution = rose_distribution
        self.tracking = False # whether or not to track stats

    def reset(self):
        """
        Reset proposals and agents for the next episode.
        Agents' Q-tables and stats are not reset, obviously
        """
        self.proposals = list()
        for agent in self.men + self.women:
            agent.reset()
            agent.num_roses = self.assign_roses(self.rose_distribution)
        

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
        Agents send proposals.
        """
        for sender in self.men + self.women:
            for _ in range(self.max_proposals): # currently all proposals are always used up. Could add a Q table for learning how many proposals to send?
                action = sender.choose_send_action()
                if action["receiver_id"]:
                    receiver = self.all_agents[action["receiver_id"]]
                    proposal = Proposal(sender, receiver, use_rose=action["action"] == 1)

                    self.proposals.append(proposal)
                    sender.send(proposal)
                    receiver.receive(proposal)

                else:
                    print("----WARNING: No valid receiver found*************************************")
            
            # print(f"{sender.id} sent {[(p.receiver.id, p.has_rose) for p in sender.proposals_sent]}")
            
    def response_stage(self):
        """
        Agents receive and evaluate proposals.
        """
        for agent in self.men + self.women:
            agent.screen_proposals_received()
        
        for agent in self.men + self.women:
            agent.process_matches(track_stats=self.tracking)
    

    def simulate(self, n=10, save_results=False, save_ep=8, results_dir="results"):
        """
        Run the full simulation.
        :param n: Number of episodes to run
        :param save_results: Whether to save results to a file
        :param save_ep: Save results after this episode if saving results
        :param results_dir: Directory to save results
        """

        for episode in tqdm(range(n)):  # Simulate for n episodes
            # print(f"Episode {episode+1}")
            if episode >= save_ep and save_results:
                self.tracking = True

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