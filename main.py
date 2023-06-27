import requests
import json
from datetime import datetime, timedelta
import os
from paho.mqtt import client as mqtt_client
import time


class Object:
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True)


class awtrix_github:
    json_path = "json"
    json_commits_path = f"{json_path}/commits"
    max_commits = 0
    days = ["", 0]

    def load_github_data(self):
        api_url = "https://api.github.com/users/hugego88/repos"
        response = requests.get(api_url)
        commit_response = ""
        repos = response.json()

        # Writing to repos.json
        with open(f"{self.json_path}/repos.json", "w") as f:
            json.dump(repos, f, ensure_ascii=False, indent=4)

        for repo in repos:
            repo_name = repo["name"]
            commit_url = repo["commits_url"].replace("{/sha}", "")
            page = 1
            commit_url = commit_url + "?page="
            while True:
                commit_response = requests.get(f"{commit_url}{page}")
                if (commit_response.text == "[]"):
                    break
                commits = commit_response.json()

                # Writing to repos.json
                with open(f"{self.json_commits_path}/{repo_name}{page}.json", "w") as f:
                    json.dump(commits, f, ensure_ascii=False, indent=4)
                page += 1

    def prepare_data(self):
        commit_dates = []
        # create list of all days
        base = datetime.today()
        self.days = [(base - timedelta(days=x), 0) for x in range(180)]

        files = os.listdir(f"./{self.json_commits_path}")
        for file in files:
            f = open(f"./{self.json_commits_path}/{file}")
            commits = json.load(f)
            for commit in commits:
                commit_date_str = commit["commit"]["committer"]["date"]
                commit_date = datetime.strptime(
                    commit_date_str, '%Y-%m-%dT%H:%M:%SZ')
                commit_dates.append(commit_date)
        commit_dates.sort()

        for commit_date in commit_dates:
            for i, day in enumerate(self.days):
                if (day[0].date() == commit_date.date()):
                    self.days[i] = (day[0], day[1] + 1)
                    if (day[1] > self.max_commits):
                        self.max_commits = day[1]

        for i, day in enumerate(self.days):
            if (day[1] != 0):
                self.days[i] = (day[0], int(
                    float(day[1])/float(self.max_commits)*100.0+140))

    def create_json(self):
        self.app_data = Object()
        self.app_data.icon = 5251
        self.app_data.duration = 10
        self.app_data.draw = [Object()]
        self.app_data.draw[0].dp = [31, 8, f"#FFFFFF"]
        self.app_data.draw.pop()
        j = 0
        offset = (7-(datetime.today()).weekday()+5) % 7
        for i, day in enumerate(self.days):
            if (i == 0):
                self.app_data.draw.append(Object())
                row = 7-((i+offset) % 7)
                column = 31-int((i+offset)/7)
                self.app_data.draw[j].dp = [column, row, f"#FFFFFF"]
                j += 1
                continue
            if (day[1] != 0):
                self.app_data.draw.append(Object())
                row = 7-((i+offset) % 7)
                column = 31-int((i+offset)/7)
                self.app_data.draw[j].dp = [column, row, f"#00{day[1]:02X}00"]
                j += 1

    def send_mqtt_msg(self, topic):
        result = self.client.publish(topic, self.app_data.toJSON())
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Send msg to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")

    def connect_mqtt(self):
        broker = '192.168.178.200'
        port = 1883
        client_id = f'python-mqtt'
        self.client = mqtt_client.Client(client_id)
        self.client.connect(broker, port)
        return self.client

    def create_folders(self):
        if not (os.path.exists(f"./{self.json_path}")):
            os.makedirs(f"./{self.json_path}")
        if not (os.path.exists(f"./{self.json_commits_path}")):
            os.makedirs(f"./{self.json_commits_path}")


if __name__ == '__main__':
    awtrix = awtrix_github()
    awtrix.create_folders()
    if (os.path.exists(f"./{awtrix.json_path}/repos.json")):
        mod_file_time_str = os.path.getmtime(
            f"./{awtrix.json_path}/repos.json")
        t_obj = datetime.fromtimestamp(mod_file_time_str)
        if (t_obj.date() != datetime.today().date()):
            awtrix.load_github_data()
    else:
        awtrix.load_github_data()
    awtrix.prepare_data()
    awtrix.create_json()
    awtrix.connect_mqtt()
    awtrix.send_mqtt_msg("awtrix_6ff9b8/custom/github")
    awtrix.send_mqtt_msg("awtrix_6ff9b8/notify")

    print("end")
