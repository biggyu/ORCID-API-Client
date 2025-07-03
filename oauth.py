# oauth_app.py
from dotenv import load_dotenv
from flask import Flask, request, redirect
import os, requests, json
import urllib.parse

app = Flask(__name__)
load_dotenv()
# token_url = os.getenv("TOKEN_URL")
token_headers = json.loads(os.getenv("TOKEN_HEADERS"))
# token_headers = json.loads(os.getenv("TOKEN_HEADERS"))
# token_read_data = json.loads(os.getenv("TOKEN_READ_DATA"))
token_update_data = json.loads(os.getenv("TOKEN_SANDBOX_UPDATE"))

REDIRECT_URI  = "http://127.0.0.1:8000/oauth/callback"
ORCID_AUTH    = "https://sandbox.orcid.org/oauth/authorize"
ORCID_TOKEN   = "https://sandbox.orcid.org/oauth/token"

@app.route("/")
def index():
    params = {
        "client_id":     token_update_data["client_id"],
        "response_type": "code",
        # "scope":         "/authenticate",
        "scope":         token_update_data["scope"],
        "redirect_uri":  REDIRECT_URI,
        "state":         "secure_random_string",  #TODO: change to something unpredictable
    }
    url = ORCID_AUTH + "?" + urllib.parse.urlencode(params, safe="/ ")
    return redirect(url)

@app.route("/oauth/callback")
def oauth_callback():
    code  = request.args.get("code")
    state = request.args.get("state")
    if not code:
        return "Error: no code provided", 400

    # (Optional) verify state matches what you originally set

    # checking for /authenticate scope
    # data = {
    #     "client_id":     token_update_data["client_id"],
    #     "client_secret": token_update_data["client_secret"],
    #     "grant_type":    "authorization_code",
    #     "code":          code,
    #     "redirect_uri":  REDIRECT_URI,
    # }
    # headers = {
    #     "Accept":       "application/json",
    #     "Content-Type": "application/x-www-form-urlencoded",
    # }
    # resp = requests.post(ORCID_TOKEN, data=data, headers=headers)
    # resp.raise_for_status()

    # token_data = resp.json()
    # # token_data contains:
    # #   access_token, refresh_token, expires_in, scope, orcid, name, etc.

    # return (
    #     f"Hello, {token_data['name']}!<br>"
    #     f"Your ORCID iD is {token_data['orcid']}.<br>"
    #     f"Access Token: {token_data['access_token']}.<br>"
    #     f"Refresh Token: {token_data['refresh_token']}.<br>"
    #     f"Issued: {issued_at.isoformat()}.<br>"
    #     f"Expries: {expires_at.isoformat()}.<br>"
    # )

    data = {
        "client_id":     token_update_data["client_id"],
        "client_secret": token_update_data["client_secret"],
        "grant_type":    token_update_data["grant_type"],
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
    }
    # headers = {
    #     "Accept":       "application/json",
    #     "Content-Type": "application/x-www-form-urlencoded",
    # }
    resp = requests.post(ORCID_TOKEN, data=data, headers=token_headers)
    resp.raise_for_status()

    token_data = resp.json()
    access_token = token_data["access_token"]
    orcid_id     = token_data["orcid"]
    
    # print(access_token, orcid_id)
    #TODO: sandbox and public
    employment_url = f"https://api.sandbox.orcid.org/v3.0/{orcid_id}/work"
    
    headers = {
        "Content-Type":  "application/vnd.orcid+json",
        "Authorization": f"Bearer {access_token}"
    }

    #Single Work Adding
    with open("work.json", "r", encoding="utf-8") as f:
        payload = json.load(f)

    post_resp = requests.post(employment_url, headers=headers, data=json.dumps(payload))
    
    employment_url = f"https://api.sandbox.orcid.org/v3.0/{orcid_id}/works"
    
    headers = {
        "Content-Type":  "application/vnd.orcid+json",
        "Authorization": f"Bearer {access_token}"
    }

    #Multiple Works Adding
    with open("work_mult.json", "r", encoding="utf-8") as f:
        payload = json.load(f)

    post_resp = requests.post(employment_url, headers=headers, data=json.dumps(payload))
    try:
        post_resp.raise_for_status()
        return (
            "<h2>Work added!</h2>"
            f"<pre>{post_resp.text}</pre>"
        )
    except requests.exceptions.HTTPError as e:
        return (    
            "<h2>Failed to add work</h2>"
            f"<p>{e}</p><pre>{post_resp.text}</pre>"
        ), 400
    
if __name__ == "__main__":
    app.run(port=8000, debug=True)
