import requests
import json
from datetime import datetime, timedelta
from collections import Counter
import os
import pandas as pd

json_path = "json"
json_commits_path = f"{json_path}/commits"

def load_github_data():
    api_url = "https://api.github.com/users/hugego88/repos"
    response = requests.get(api_url)
    commit_response = ""
    repos =  response.json()

    # Writing to repos.json
    with open(f"{json_path}/repos.json", "w") as f:
        json.dump(repos, f, ensure_ascii=False, indent=4)

    for repo in repos:
        repo_name = repo["name"]
        commit_url = repo["commits_url"].replace("{/sha}", "")
        commit_response = requests.get(commit_url)
        commits = commit_response.json()

        # Writing to repos.json
        with open(f"{json_commits_path}/{repo_name}.json", "w") as f:
            json.dump(commits, f, ensure_ascii=False, indent=4)


def prepare_data():
    all_commit_dates = []

    files = os.listdir(f"./{json_commits_path}")
    for file in files:
        f = open(f"./{json_commits_path}/{file}")
        commits = json.load(f)
        for commit in commits:
            commit_date_str = commit["commit"]["committer"]["date"]
            commit_date = datetime.strptime(commit_date_str, '%Y-%m-%dT%H:%M:%SZ')
            all_commit_dates.append(commit_date)
    all_commit_dates.sort()

    # create list of all days
    base = datetime.today()
    date_list = [(base - timedelta(days=x), 0) for x in range(365)]



    print(all_commit_dates)
    #dcounts = Counter(d[0] for d in all_commit_dates)
    #print(dcounts)


if __name__ == '__main__':
    # load_github_data()
    prepare_data()