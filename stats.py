import json


class Stats:
    def __init__(self):
        self.proposals_sent = 0
        self.roses_sent = 0 # roses are attached to proposals, not sent separately
        self.proposals_sent_accepted = 0
        self.roses_sent_accepted = 0
        self.adsnr_sent = 0   # Avg. Desirability Score of agents proposed to with No Rose (ADSNR)
        self.adsnr_sent_accepted = 0  # Avg. Desirability Score of agents who accepted proposals with No Rose (ADSNR)
        self.adsr_sent = 0  # props sent with rose...
        self.adsr_sent_accepted = 0 # ...you get the idea

        self.proposals_received = 0
        self.roses_received = 0
        self.proposals_received_accepted = 0
        self.roses_received_accepted = 0
        self.adsnr_received = 0
        self.adsnr_received_accepted = 0
        self.adsr_received = 0
        self.adsr_received_accepted = 0


    # def save(self, agent, results_dir="results"):
    #     # write stats to file
    #     with open(f"{results_dir}/{agent.id}.txt", "w") as f:
    #         f.write(f"Total success rate: {self.proposals_accepted / self.proposals_sent}\n")
    #         f.write(f"No rose success rate: {self.proposals_accepted_no_rose / self.proposals_sent_no_rose}\n")
    #         f.write(f"Rose success rate: {self.proposals_accepted_w_rose / self.proposals_sent_w_rose}\n")
    #         f.write(f"Self desirability score: {agent.desirability_score}\n")
    #         f.write(f"Average desirability score of accepted proposals: {self.avg_desirability_score_accepted}\n")
    #         f.write(f"Average desirability score of sent proposals: {self.avg_desirability_score_sent}\n")
    
    def save(self, agent, results_dir="results"):
        self.agent_id = agent.id
        self.desirability_score = agent.desirability_score
        # write stats to file
        with open(f"{results_dir}/{agent.id}.json", "w") as file:
            json.dump(self.__dict__, file, indent=4)
    
    @staticmethod
    def update_avg(old_avg, n):
        if old_avg == 0:
            return n
        else:
            return (old_avg + n) / 2

    def track_sent(self, proposal):
        self.proposals_sent += 1

        if proposal.has_rose:
            self.roses_sent += 1
            self.adsr_sent = Stats.update_avg(old_avg=self.adsr_sent, n=proposal.receiver.desirability_score)
            if proposal.accepted:
                self.roses_sent_accepted += 1
                self.proposals_sent_accepted += 1
                self.adsr_sent_accepted = Stats.update_avg(old_avg=self.adsr_sent_accepted, n=proposal.receiver.desirability_score)
        else:
            self.adsnr_sent = Stats.update_avg(old_avg=self.adsnr_sent, n=proposal.receiver.desirability_score)
            if proposal.accepted:
                self.proposals_sent_accepted += 1
                self.adsnr_sent_accepted = Stats.update_avg(old_avg=self.adsnr_sent_accepted, n=proposal.receiver.desirability_score)

    
    def track_received(self, proposal):
        self.proposals_received += 1

        if proposal.has_rose:
            self.roses_received += 1
            self.adsr_received = Stats.update_avg(old_avg=self.adsr_received, n=proposal.sender.desirability_score)
            if proposal.accepted:
                self.roses_received_accepted += 1
                self.proposals_received_accepted += 1
                self.adsr_received_accepted = Stats.update_avg(old_avg=self.adsr_received_accepted, n=proposal.sender.desirability_score)
        else:
            self.adsnr_received = Stats.update_avg(old_avg=self.adsnr_received, n=proposal.sender.desirability_score)
            if proposal.accepted:
                self.proposals_received_accepted += 1
                self.adsnr_received_accepted = Stats.update_avg(old_avg=self.adsnr_received_accepted, n=proposal.sender.desirability_score)
        

