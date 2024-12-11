import argparse
import ast

from environment.env import Environment


def parse_dict(arg):
    try:
        # Replace single quotes if any and parse into a dictionary safely
        return ast.literal_eval(arg)
    except (ValueError, SyntaxError):
        raise argparse.ArgumentTypeError("Invalid dictionary format. Use {key1: val1, key2: val2}.")

# Run simulation
if __name__ == "__main__":
    # set up command line arguments
    parser = argparse.ArgumentParser(description="Run the simulation.")
    parser.add_argument("--num_men", type=int, default=10, help="Number of male participants. Default is 10.")
    parser.add_argument("--num_women", type=int, default=10, help="Number of women participants. Default is 10.")
    parser.add_argument("--num_episodes", type=int, default=1000, help="Number of episodes to run. Default is 1000.")
    parser.add_argument("--max_proposals", type=int, default=3, help="Maximum number of proposals each agent can send. Default is 3.")
    parser.add_argument("--rose_distribution", type=parse_dict, default="{0.8: 2, 0.2:6}", help="Distribution of roses. Default is {0.8: 2, 0.2: 6}.")
    parser.add_argument("--save_results", action="store_true", help="Raise flag to save results")
    parser.add_argument("--save_ep", type=int, default=800, help="Episode on which to start saving results. Only used if --save_results is used. Default is 800.")
    parser.add_argument("--results_dir", type=str, default="results", help="Directory to save the results to. Default is 'results'.")
    args = parser.parse_args()

    # run simulation
    env = Environment(num_men=args.num_men, num_women=args.num_women, max_proposals=3)
    env.simulate(n=args.num_episodes, save_results=args.save_results, save_ep=args.save_ep, results_dir=args.results_dir)
