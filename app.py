from flask import Flask, jsonify
from flask import request
import requests
import os

app = Flask(__name__)

#Load form environment variable
Tenant_ID = os.getenv('PowerBI_Tenant_ID')
Client_ID = os.getenv('PowerBI_Client_ID')
Secret_KEY = os.getenv('PowerBI_Sec_Key')

Dataset_ID = "cf408c86-d219-404e-9d68-796c3831f2a1"
Table_NAME = "LMS_Policy"
Group_ID = "62984487-2b72-4f6a-9a48-0cd851deeb3f"

Authority_URL = f"https://login.microsoftonline.com/{Tenant_ID}/oauth2/v2.0/token"
Power_BI_SCOPE = "https://analysis.windows.net/powerbi/api/.default"
Power_BI_API = Power_BI_API = f"https://api.powerbi.com/v1.0/myorg/groups/{Group_ID}/datasets/{Dataset_ID}/tables/{Table_NAME}/rows"

def get_access_token():
# Fetch OAuth2 token from AD using client credentials
    print("[DEBUG] Authority_URL:", Authority_URL)
    print("[DEBUG] Client_ID:", Client_ID)
    print("[DEBUG] Tenant_ID:", Tenant_ID)
    print("[DEBUG] Scope:", Power_BI_SCOPE)
    print("[DEBUG] Secret_Key:", Secret_KEY)
    # Do not print Secret_KEY for security
    data= {
        "client_id": Client_ID,
        "client_secret": Secret_KEY,
        "scope": Power_BI_SCOPE,
        "grant_type": "client_credentials",
    }
    print("[DEBUG] Token request payload (except secret):", {k: v for k, v in data.items() if k != 'client_secret'})
    response = requests.post(Authority_URL, data=data)
    if response.status_code != 200:
        print("[DEBUG] Token request failed:", response.status_code, response.text)
    response.raise_for_status()
    return response.json()["access_token"]

@app.route("/get-data", methods=["GET"])
def get_data():
# Exposes Power BI data as JSON to your app
    policy_no = request.args.get('policy_no')
    if not policy_no:
        return jsonify({"error": "Missing required query parameter: policy_no"}), 400

    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(Power_BI_API, headers=headers)
    if response.status_code == 200:
        data = response.json().get("value", [])
    else:
        return jsonify({"error": f"Failed to fetch data from Power BI API. Status code: {response.status_code}", "details": response.text}), response.status_code

# Find client code for a given policy
    Client_Code = None
    for row in data:
        if row.get("POL_POLICY_NO") == policy_no:
            Client_Code = row.get("CLNT_CODE")
            break

    if not Client_Code:
        return jsonify({"error": f"policy {policy_no} not found"})

# Fetch all policies for the client
    Client_policies = [
        {
            "POL_POLICY_NO": row.get("POL_POLICY_NO"),
            "CLNT_CODE": row.get("CLNT_CODE"),
            "ASSURED_NAME": row.get("ASSURED_NAME"),
            "LAPSED_STATUS": row.get("Lapsed_Status"),
            "PREMIUM": row.get("PREMIUM"),
            "POL_PMT_DIFF_NEW": row.get("NO OF MISSED PREMIUM"),
        }
        for row in data
        if row.get("CLNT_CODE") == Client_Code
    ]

    return jsonify(Client_policies)
    
if __name__ == "__main__":
    app.run(port=5000, debug=True)