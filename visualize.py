import argparse
import os
import json
import matplotlib.pyplot as plt
import numpy as np

RESULTS_DIR = "results"

def load_data(results_dir):
    data = []
    for file_name in os.listdir(results_dir):
        if file_name.endswith(".json"):
            with open(os.path.join(results_dir, file_name), 'r') as f:
                data.append(json.load(f))
    return data

def analyze_rose_effect(data):
    proposals_with_rose = []
    proposals_without_rose = []

    for agent in data:
        roses_sent = agent['roses_sent']
        proposals_sent = agent['proposals_sent']
        roses_accepted = agent['roses_sent_accepted']
        proposals_accepted = agent['proposals_sent_accepted']

        if roses_sent > 0:
            proposals_with_rose.append(roses_accepted / roses_sent)
        if proposals_sent - roses_sent > 0:
            proposals_without_rose.append((proposals_accepted - roses_accepted) / (proposals_sent - roses_sent))

    return proposals_with_rose, proposals_without_rose

def analyze_desirability_effect(data):
    desirability = []
    acceptance_rate_sent = []
    acceptance_rate_received = []

    for agent in data:
        total_proposals_sent = agent['proposals_sent']
        total_proposals_accepted = agent['proposals_sent_accepted']

        total_proposals_received = agent['proposals_received']
        total_proposals_received_accepted = agent['proposals_received_accepted']

        desirability.append(agent['desirability_score'])

        if total_proposals_sent > 0:
            acceptance_rate_sent.append(total_proposals_accepted / total_proposals_sent)

        if total_proposals_received > 0:
            acceptance_rate_received.append(total_proposals_received_accepted / total_proposals_received)
    
    if len(desirability) != len(acceptance_rate_sent) or len(desirability) != len(acceptance_rate_received):
        raise ValueError("Data mismatch. Please check the data for consistency.")

    return desirability, acceptance_rate_sent, acceptance_rate_received

def visualize_rose_effect(proposals_with_rose, proposals_without_rose, save_to="visualizations"):
    labels = ['With Rose', 'Without Rose']
    means = [
        np.mean(proposals_with_rose) if proposals_with_rose else 0,
        np.mean(proposals_without_rose) if proposals_without_rose else 0
    ]
    
    rose_color = "#d10026"
    green_color = "#00752d"
    plt.bar(labels, means, color=[rose_color, green_color])
    plt.ylabel('Acceptance Rate')
    plt.title('Effect of Sending Roses on Acceptance Rates')
    
    for i, mean in enumerate(means):
        plt.text(i, mean + 0.01, f"{mean:.2f}", ha='center', va='bottom')

    max_mean = max(means)
    plt.ylim(0, max_mean + 0.1 * max_mean)
    plt.savefig(f"{save_to}/rose_effect.png")
    plt.close()

def visualize_desirability_effect(desirability, acceptance_rate_sent, acceptance_rate_received, save_to="visualizations"):
    plt.scatter(desirability, acceptance_rate_sent, alpha=0.5, label="Sent")
    plt.scatter(desirability, acceptance_rate_received, alpha=0.5, label="Received")
    plt.xlabel('Agent Desirability Score')
    plt.ylabel('Acceptance Rate')
    plt.title('Effect of Desirability on Proposal Outcomes')
    plt.legend()
    plt.savefig(f"{save_to}/desirability_effect.png")
    plt.close()


def go(results_dir="results", save_to="visualizations"):
    # Load data
    data = load_data(results_dir)

    # Analyze and visualize rose effect
    proposals_with_rose, proposals_without_rose = analyze_rose_effect(data)
    visualize_rose_effect(proposals_with_rose, proposals_without_rose, save_to=save_to)

    # Analyze and visualize desirability effect
    desirability, acceptance_rate_sent, acceptance_rate_received = analyze_desirability_effect(data)
    visualize_desirability_effect(desirability, acceptance_rate_sent, acceptance_rate_received, save_to=save_to)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create visualizations.")
    parser.add_argument("--results_dir", type=str, default="results", help="Directory containing results to parse")
    parser.add_argument("--save_to", type=str, default="visualizations", help="Directory to save visualizations")

    args = parser.parse_args()

    # check if results directory exists
    if not os.path.exists(args.results_dir):
        raise FileNotFoundError(f"Directory {args.results_dir} not found.")

    # create visualizations folder if it doesn't exist
    if not os.path.exists(args.save_to):
        os.makedirs(args.save_to)

    go(results_dir=args.results_dir, save_to=args.save_to)
