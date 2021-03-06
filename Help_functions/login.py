import csv
import os
import requests
import json
import time


def write_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f)


def define_login_details(nick="", password="", server=""):
    """Saving nicks, passwords for each server from the user, for later use."""
    file_name = '../Help_functions/login_details.csv'
    if nick and password and server:
        with open(file_name, 'a', newline='') as csvFile:
            writer = csv.writer(csvFile)
            if not os.path.isfile(file_name):
                writer.writerow(["Server", "Nick", "Password"])
            writer.writerow([server, nick, password])

    if not os.path.isfile(file_name):
        with open(file_name, 'a', newline='') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(["Server", "Nick", "Password"])
            print("I will need your nick & password for each server in order to function.")
            print("I will store this data in a local csv (excel) file, so you won't have to write it each time.")
            print(f"(You will be able to edit this file ({file_name}) manually whenever you want)")
            servers = input("Pls write all the servers you want to add (separated by a comma):\n")
            nick, password = "", ""
            for server in servers.split(","):
                server = server.strip().lower()
                if nick and password:
                    print(f"If your nick/password for {server} is the same as of the previous server, you can leave that field blank")
                new_nick = input(f"Your nick at {server} (pay attention to uppercase and lowercase letters): ")
                new_password = input(f"Your password at {server} (pay attention to uppercase and lowercase letters): ")
                if new_nick:
                    nick = new_nick
                if new_password:
                    password = new_password
                writer.writerow([server, nick, password])


def get_nick_and_pw(server):
    nick, password = "", ""
    with open('../Help_functions/login_details.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == server:
                nick, password = row[1], row[2]
                break
    if nick and password:
        return nick, password
    else:
        define_login_details()


def login(server):
    """
    Saving cookies and user agent string in a local file, and replace the cookies if they are too old.
    Usage:
    from login import login
    session = login(server)
    """
    define_login_details()
    URL = f"https://{server}.e-sim.org/"
    cookies_file_name = '../Help_functions/cookies.txt'
    if not os.path.isfile(cookies_file_name):
        write_json({}, cookies_file_name)
    with open(cookies_file_name, 'r') as file:
        data = json.load(file)
        try:
            user_agent = data["user_agent"]
        except:
            print("Go to this site - https://www.whatsmyua.info/ , copy your user-agent and paste here")
            user_agent = input(
                "It will tell e-sim that you browsing through your regular browser, so make sure there are no mistakes\n")
            data.update({"user_agent": user_agent})
            write_json(data, cookies_file_name)

    headers = {"User-Agent": user_agent, "Referer": f"{URL}index.html"}
    session = requests.session()    
    online_check = False
    if server in data:
        old_cookies = requests.utils.cookiejar_from_dict(data[server])
        session.cookies.update(old_cookies)
        online_check = session.get(URL + "storage.html", headers=headers)
        print(online_check.url)
        online_check = "notLoggedIn" in str(online_check.url)
    print(online_check)        
    if online_check or server not in data:
        nick, password = get_nick_and_pw(server)
        try:
            payload = {'login': nick, 'password': password, 'remember': True}
        except:
            define_login_details()
            payload = {'login': nick, 'password': password, 'remember': True}
        
        session.get(URL, headers=headers)
        r = session.post(URL + "login.html", headers=headers, data=payload)
        if "notLoggedIn" in str(r.url):
            print(r.url)
            print("Program stopped. Check your details and try again.")
            raise SystemExit(0)
        data.update({server: requests.utils.dict_from_cookiejar(session.cookies)})
        write_json(data, cookies_file_name)

    return session


def double_click(server, queue="", session=""):
    URL = f"https://{server}.e-sim.org/"
    if not session:
        session = login(server)

    if queue == "+":
        payload1 = {'task': "WORK", "action": "put", "submit": "Add plan"}
        payload2 = {'task': "TRAIN", "action": "put", "submit": "Add plan"}
        session.post(URL + "taskQueue.html", data=payload1)
        session.post(URL + "taskQueue.html", data=payload2)

    session.post(URL + "train/ajax?action=train")
    print("Trained successfully at", server)
    session.post(URL + "work/ajax?action=work")
    print("Worked at", server)
    time.sleep(3)  # some delay


if __name__ == "__main__":
    print(define_login_details.__doc__)
    define_login_details()
    print(login.__doc__)
    print("write the servers you want to work and train in (separated by a comma)")
    servers = input("If you want all of them, press Enter:\n")
    if servers:
        servers = set(servers.split(","))  # random order
        for server in servers:
            double_click(server.strip())
    else:
        with open('../Help_functions/login_details.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] != "Server":
                    double_click(row[0])
