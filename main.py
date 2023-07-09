import requests
import json
from datetime import datetime, timedelta
import os
from paho.mqtt import client as mqtt_client
import numpy as np


class Object:
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True)


class awtrix_github:
    json_path = "json"
    json_commits_path = f"{json_path}/commits"
    repo_file_name = "repos.json"
    max_commits = 0
    days = ["", 0]
    matrix_width = 24
    matrix_height = 7
    pixel_amount = matrix_height * matrix_width
    user = "hugego88"
    api_url = f"https://api.github.com/users/{user}/repos"
    broker_adr = "192.168.178.200"
    ulanzi_name = "awtrix_6ff9b8"

    def load_github_data(self):
        response = requests.get(self.api_url)
        commit_response = ""
        repos = response.json()

        with open(f"{self.json_path}/{self.repo_file_name}", "w") as f:
            json.dump(repos, f, ensure_ascii=False, indent=4)

        for repo in repos:
            repo_name = repo["name"]
            commit_url = repo["commits_url"].replace("{/sha}", "")
            page = 1
            commit_url = commit_url + "?page="
            while True:
                if (page > 10):
                    break
                commit_response = requests.get(f"{commit_url}{page}")
                if (commit_response.text == "[]"):
                    break

                commits = commit_response.json()

                with open(f"{self.json_commits_path}/{repo_name}{page}.json", "w") as f:
                    json.dump(commits, f, ensure_ascii=False, indent=4)
                page += 1

    def prepare_data(self):
        commit_dates = []
        base = datetime.today()
        self.days = [(base - timedelta(days=x), 0)
                     for x in range(self.pixel_amount)]

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
                        self.max_commits = self.days[i][1]

        for i, day in enumerate(self.days):
            if (day[1] != 0):
                self.days[i] = (day[0], int(
                    float(day[1])/float(self.max_commits)*27.0+37)-1)

    def create_json(self):
        self.app_data = Object()
        self.app_data.icon = 5251
        self.app_data.duration = 10
        self.app_data.draw = [Object()]
        bitmap = []
        j = 0
        offset = (7-(datetime.today()).weekday()+5) % 7
        for x in range(offset):
            bitmap.append(000000)
        for i, day in enumerate(self.days):
            if (i == 0):
                bitmap.append(int("1111111111111111", 2))
                continue
            if (day[i != 0]):
                bitmap.append(
                    int("{0:05b}".format(int(day[1]/4)) + "{0:b}".format(day[1]) + "{0:05b}".format(int(day[1]/4)), 2))
                j += 1
            else:
                bitmap.append(000000)

        if (offset != 0):
            bitmap = bitmap[:-offset]
        np_array = np.array(bitmap)
        np_matrix = np_array.reshape(self.matrix_width, self.matrix_height)
        np_matrix = np.rot90(np_matrix)
        np_matrix = np.fliplr(np_matrix)
        bitmap = np_matrix.flatten().tolist()

        self.app_data.draw[0].db = [
            8, 1, self.matrix_width, self.matrix_height, bitmap]
        print(self.app_data.toJSON())

    def send_mqtt_msg(self, topic):
        result = self.client.publish(topic, self.app_data.toJSON())
        status = result[0]
        if status == 0:
            print(f"Send msg to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")

    def connect_mqtt(self):
        broker = self.broker_adr
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
    awtrix.connect_mqtt()
    awtrix.create_folders()
    if (os.path.exists(f"./{awtrix.json_path}/{awtrix.repo_file_name}")):
        mod_file_time_str = os.path.getmtime(
            f"./{awtrix.json_path}/{awtrix.repo_file_name}")
        t_obj = datetime.fromtimestamp(mod_file_time_str)
        if (t_obj.date() != datetime.today().date()):
            awtrix.load_github_data()
    else:
        awtrix.load_github_data()
    awtrix.prepare_data()
    awtrix.create_json()
    awtrix.send_mqtt_msg(f"{awtrix.ulanzi_name}/custom/github")
    awtrix.send_mqtt_msg(f"{awtrix.ulanzi_name}/notify")

    print("end")
