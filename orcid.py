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
                #TODO: remaining json file not in orcid_id
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
                personal = data["record:record"]["person:person"]["person:name"]
                if "personal-details:credit-name" in personal.keys():
                    wf.write(f"{personal["personal-details:credit-name"]},{personal["@path"]}\n")
                else:
                    wf.write(f"{personal["personal-details:given-names"]} {personal["personal-details:family-name"]},{personal["@path"]}\n")
                # print(f"{data["record:record"]["person:person"]["person:name"]["personal-details:credit-name"]},{data["record:record"]["person:person"]["person:name"]["@path"]}")
                # wf.write()
                
                gen = traverse_file(data["record:record"]["activities:activities-summary"], path='data["record:record"]["activities:activities-summary"]', target=("-summary"))
                # gen = traverse_file(data["record:record"]["activities:activities-summary"], path='data["record:record"]["activities:activities-summary"]', target=("education:education-summary", "employment:employment-summary", "work:work-summary", "funding:funding-summary"))

                refining = {}
                for _, act, value in gen:
                    if act not in refining.keys():
                        refining[act] = [value]
                    else:
                        refining[act].append(value)
                    # print(data[path])
                for key in refining.keys():
                    wf.write(f'{key}\n')
                    # print(key)
                    for idx, summary in enumerate(refining[key]):
                        # print(summary.keys())
                        if any(key.endswith(":title") for key in summary.keys()):
                            wf.write(f',{idx + 1},{summary[f"{key}:title"]["common:title"]}\n')
                            # print(summary[f"{key}:title"]["common:title"])
                        else:
                            # address = summary["common:organization"]["common:address"]
                            address = '-'.join(str(v) for v in summary["common:organization"]["common:address"].values())
                            wf.write(f',{idx + 1},{summary["common:organization"]["common:name"]}: {address}\n')
                            # print(f'{summary["common:organization"]["common:name"]}: {address["common:city"]} {address["common:region"]} {address["common:country"]}')
                        
                        if any(key.endswith(":start-date") for key in summary.keys()):
                            start_date = '-'.join(str(v) for v in summary["common:start-date"].values())
                            wf.write(f',,{start_date} to ')
                            if "common:end-date" in summary.keys():
                                end_date = '-'.join(str(v) for v in summary["common:end-date"].values())
                                wf.write(f'{end_date}\n')
                            else:
                                wf.write('present\n')
                        if "common:publication-date" in summary.keys():
                            # date = summary["common:publication-date"]
                            date = '-'.join(str(v) for v in summary["common:publication-date"].values())
                            wf.write(f',,{date}\n')
                wf.write("\n")
        
    
if __name__ == '__main__':
    orcid_read()
    orcid_write()