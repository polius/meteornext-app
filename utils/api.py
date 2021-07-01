import sys
import pyotp
import requests
import threading

session = requests.Session()

def check_params():
    # Check Parameter
    try:
        if len(sys.argv) == 1:
            print("- Argument is missing. Please enter the number of deployments to create.")
            sys.exit()
        n = int(sys.argv[1])
        if n < 1 or n > 20:
            print("- Argument not valid. Should be [1-20].")
            sys.exit()
        return n
    except Exception:
        print("- Argument is not an integer.")
        sys.exit()

def login():
    global session
    json = {
        "username": "polius",
        "password": "&maXxo#gJCt:XoG=TXiH3_nn:+jE=s^w6hbU:zTb}T.zc.D3Q7wQV%#}TL]RT6DU",
        # "mfa": pyotp.TOTP('LOMBQEKO32BUYTOXDOV7Z6UW2VYIPOHK').now()
    }
    r = session.post('https://meteor2.io/api/login', json=json)
    if r.status_code == 200:
        print("- Login successful.")
        session.headers['X-CSRF-TOKEN'] = session.cookies.get_dict()['csrf_access_token']

def logout():
    global session
    r = session.post('https://meteor2.io/api/logout')
    if r.status_code == 200:
        print("- Logout successful.")

def deployments(n):
    threads = []
    for i in range(n):
        print(f"- Creating deployment: {i+1}/{n}...")
        t = threading.Thread(target=deployment, args=(i,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

def deployment(i):
    json = {
        "name": f"D{i+1}",
        "release": "a2",
        "environment": 2,
        "mode": "BASIC",
        "databases": "mysql",
        "queries": "[{\"id\":1,\"query\":\"SHOW DATABASES\"}]",
        "method": "DEPLOY",
        "scheduled": None,
        "start_execution": True,
        "url": "https://meteor2.io",
    }
    r = session.post('https://meteor2.io/api/deployments', json=json)
    if r.status_code == 200:
        result = r.json()
        print(f"- {result['message']}")


n = check_params()
login()
deployments(n)
logout()
