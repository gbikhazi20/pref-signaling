from env import Environment


# Run simulation
if __name__ == "__main__":

    NUM_PARTICIPANTS = 10
    env = Environment(num_men=NUM_PARTICIPANTS, num_women=NUM_PARTICIPANTS, max_proposals=3)
    env.simulate(n=1000, save_results=True, results_dir="results3")
