import requests
import json
from datetime import datetime, timedelta
import os

json_path = "json"
json_commits_path = f"{json_path}/commits"
# create list of all days
base = datetime.today()
days = [(base - timedelta(days=x), 0) for x in range(365)]
max_commits = 0

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
        page = 1
        commit_url = commit_url + "?page="
        while True:
            commit_response = requests.get(f"{commit_url}{page}")
            if(commit_response.text == "[]"):
                break
            commits = commit_response.json()

            # Writing to repos.json
            with open(f"{json_commits_path}/{repo_name}{page}.json", "w") as f:
                json.dump(commits, f, ensure_ascii=False, indent=4)
            page += 1


def prepare_data():
    commit_dates = []

    files = os.listdir(f"./{json_commits_path}")
    for file in files:
        f = open(f"./{json_commits_path}/{file}")
        commits = json.load(f)
        for commit in commits:
            commit_date_str = commit["commit"]["committer"]["date"]
            commit_date = datetime.strptime(commit_date_str, '%Y-%m-%dT%H:%M:%SZ')
            commit_dates.append(commit_date)
    commit_dates.sort()

    max_commits = 0
    for commit_date in commit_dates:
        for i, day in enumerate(days):
            if(day[0].date() == commit_date.date()):
                days[i] = (day[0], day[1] +1 )
                if(day[1] > max_commits):
                    max_commits = day[1]
                    if(max_commits == 16):
                        print(max_commits)
    print("end")

if __name__ == '__main__':
    # load_github_data()
    prepare_data()
    print("end")

    