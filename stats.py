
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

    def save(self, agent, results_dir="results"):
        # write stats to file
        with open(f"{results_dir}/{agent.id}.txt", "w") as f:
            f.write(f"Total success rate: {self.proposals_accepted / self.proposals_sent}\n")
            f.write(f"No rose success rate: {self.proposals_accepted_no_rose / self.proposals_sent_no_rose}\n")
            f.write(f"Rose success rate: {self.proposals_accepted_w_rose / self.proposals_sent_w_rose}\n")
            f.write(f"Self desirability score: {agent.desirability_score}\n")
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