import requests
import json
from datetime import datetime, timedelta
import os
from paho.mqtt import client as mqtt_client
import time

class Object:
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

class awtrix_github:
    json_path = "json"
    json_commits_path = f"{json_path}/commits"
    max_commits = 0
    days = ["", 0]

    def load_github_data(self):
        api_url = "https://api.github.com/users/hugego88/repos"
        response = requests.get(api_url)
        commit_response = ""
        repos =  response.json()

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
                if(commit_response.text == "[]"):
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
        self.days = [(base - timedelta(days=x), 0) for x in range(365)]

        files = os.listdir(f"./{self.json_commits_path}")
        for file in files:
            f = open(f"./{self.json_commits_path}/{file}")
            commits = json.load(f)
            for commit in commits:
                commit_date_str = commit["commit"]["committer"]["date"]
                commit_date = datetime.strptime(commit_date_str, '%Y-%m-%dT%H:%M:%SZ')
                commit_dates.append(commit_date)
        commit_dates.sort()

        for commit_date in commit_dates:
            for i, day in enumerate(self.days):
                if(day[0].date() == commit_date.date()):
                    self.days[i] = (day[0], day[1] +1 )
                    if(day[1] > self.max_commits):
                        self.max_commits = day[1]

        for i, day in enumerate(self.days):
            self.days[i] = (day[0], int(float(day[1])/float(self.max_commits)*15.0))

    def create_json(self):
        self.app_data = Object()
        self.app_data.icon = 5251
        self.app_data.duration = 100
        self.app_data.draw = [Object()]
        self.app_data.draw[0].dp = [31, 8, f"#0000FF"]
        self.app_data.draw.pop()
        j = 0
        offset = 6
        for i, day in enumerate(self.days):
            if(day[1] != 0):
                self.app_data.draw.append(Object())
                row = ((i+offset)%7)
                column = 31-int((i+offset)/7)
                #app_data.draw[j].dp = [column, row, f"#{day[1]:X}{day[1]:X}{day[1]:X}"]
                #app_data.draw[j].dp = [column, row, f"#00{day[1]:X}000"]
                if(i == 0):
                    self.app_data.draw[j].dp = [column, row, f"#0000FF"]
                else:
                    self.app_data.draw[j].dp = [column, row, f"#00FF00"]
                j += 1
                if(j > 15):
                    break

        print(self.app_data.toJSON())

    def send_mqtt_msg(self):
        topic = "awtrix_6ff9b8/notify"
        msg_count = 1
        while True:
            time.sleep(1)
            msg = f"messages: {msg_count}"
            result = self.client.publish(topic, self.app_data.toJSON())
            # result: [0, 1]
            status = result[0]
            if status == 0:
                print(f"Send `{msg}` to topic `{topic}`")
            else:
                print(f"Failed to send message to topic {topic}")
            msg_count += 1
            if msg_count > 1:
                break

    def connect_mqtt(self):
        broker = '192.168.178.200'
        port = 1883
        client_id = f'python-mqtt'
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)
        # Set Connecting Client ID
        self.client = mqtt_client.Client(client_id)
        # client.username_pw_set(username, password)
        self.client.on_connect = on_connect
        self.client.connect(broker, port)
        return self.client

if __name__ == '__main__':
    awtrix = awtrix_github()
    # awtrix.load_github_data()
    awtrix.prepare_data()
    awtrix.create_json()
    awtrix.connect_mqtt()
    awtrix.send_mqtt_msg()

    print("end")

    