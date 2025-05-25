from dotenv import load_dotenv
import os,requests, xmltodict, json
load_dotenv()
token_url = os.getenv("TOKEN_URL")
token_headers = json.loads(os.getenv("TOKEN_HEADERS"))
token_data = json.loads(os.getenv("TOKEN_DATA"))

def orcid_read():
    try:
        r = requests.post(token_url, headers=token_headers, data=token_data)
        r.raise_for_status()
        access_token = r.json()["access_token"]
        # print("Obtained token:", access_token)
    except requests.exceptions.HTTPError as e:
        print("Token request failed:", e, r.text)
        raise
    
    with open('./orcid_id.txt', 'r') as f:
        for orcid_id in f.readlines():
            orcid_id = orcid_id.strip()
            public_url = f"https://pub.sandbox.orcid.org/v3.0/{orcid_id}/record"
            record_headers = {
                "Accept": "application/vnd.orcid+xml",
                "Authorization": f"Bearer {access_token}"
            }

            try:
                r = requests.get(public_url, headers=record_headers)
                r.raise_for_status()
                print(f"{orcid_id}: Record fetched successfully:")
                record_dict = xmltodict.parse(r.text)
                os.makedirs("./data", exist_ok=True)
                with open(f"data/{orcid_id}_result.json", 'w') as f:
                    f.write(json.dumps(record_dict, indent=2))
                # with open(f'{orcid_id}_result.xml', 'w') as f:
                #     f.write(r.text)
                # print(r.text)
            except requests.exceptions.HTTPError as e:
                print("Fetch failed:", e, r.text)
                raise                            
        
def traverse_file(data, path, target):
    path = path or []
    if isinstance(data, dict):
        # print(f"dict type in {path}")
        for k, v in data.items():
            new_path = path + f'["{k}"]'
            if target in k:
                yield new_path, k.split(":")[0], v
            yield from traverse_file(data=v, path=new_path, target=target)
    elif isinstance(data, list):
        # print(f"list type in {path}")
        # print(data[0])
        for i in range(len(data)):
            # print(idx, item)
            # new_path = path + f"[{idx}]"
            yield from traverse_file(data=data[i], path=path, target=target)
        # yield from traverse_file(data=data[0], path=path, target=target)

def orcid_write(dir="./data"):
    # with open("./orcid_result.csv", 'a'):
    with open("./orcid_result.csv", 'w') as wf:
        for file in os.listdir(dir):
            with open(os.path.join(dir, file), 'r') as rf:
                data = json.load(rf)
                wf.write(f"{data["record:record"]["person:person"]["person:name"]["personal-details:credit-name"]},{data["record:record"]["person:person"]["person:name"]["@path"]}\n")
                # print(f"{data["record:record"]["person:person"]["person:name"]["personal-details:credit-name"]},{data["record:record"]["person:person"]["person:name"]["@path"]}")
                # wf.write()
                
                gen = traverse_file(data["record:record"]["activities:activities-summary"], path='data["record:record"]["activities:activities-summary"]', target=("-summary"))
                   
if __name__ == '__main__':
    # orcid_read()
    orcid_write()