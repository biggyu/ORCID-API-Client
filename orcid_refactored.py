from dotenv import load_dotenv
import os,requests, xmltodict, json
load_dotenv()
token_url = os.getenv("TOKEN_URL")
token_headers = json.loads(os.getenv("TOKEN_HEADERS"))
token_read_data = json.loads(os.getenv("TOKEN_READ_DATA"))

def traverse_file(data, target):
    # path = path or []
    if isinstance(data, dict):
        # print(f"dict type in {path}")
        for k, v in data.items():
            # new_path = path + f'["{k}"]'
            if target in k:
                yield v
            yield from traverse_file(data=v, target=target)
    elif isinstance(data, list):
        # print(f"list type in {path}")
        # print(data[0])
        for i in range(len(data)):
            # print(idx, item)
            # new_path = path + f"[{idx}]"
            yield from traverse_file(data=data[i], target=target)
        # yield from traverse_file(data=data[0], path=path, target=target)

def orcid2json(is_public=True):
    try:
        r = requests.post(token_url, headers=token_headers, data=token_read_data)
        r.raise_for_status()
        access_token = r.json()["access_token"]
        # print("Obtained token:", access_token)
    except requests.exceptions.HTTPError as e:
        print("Token request failed:", e, r.text)
        raise
    
    with open('./orcid_read_id.txt', 'r') as f:
        for orcid_id in f.readlines():
            orcid_id = orcid_id.strip()
            public_url = f"https://pub.{"" if is_public else "sandbox."}orcid.org/v3.0/{orcid_id}/personal-details"
            record_headers = {
                "Accept": "application/vnd.orcid+xml",
                "Authorization": f"Bearer {access_token}"
            }
            try:
                r = requests.get(public_url, headers=record_headers)
                r.raise_for_status()
                personal_dict = xmltodict.parse(r.text)["personal-details:personal-details"]["personal-details:name"]
                # print(personal_dict)
            except requests.exceptions.HTTPError as e:
                print("Fetch failed:", e, r.text)
                raise
            
            public_url = f"https://pub.{"" if is_public else "sandbox."}orcid.org/v3.0/{orcid_id}/works"
            record_headers = {
                "Accept": "application/vnd.orcid+xml",
                "Authorization": f"Bearer {access_token}"
            }
            try:
                r = requests.get(public_url, headers=record_headers)
                r.raise_for_status()
                record_dict = xmltodict.parse(r.text)
                os.makedirs("./data", exist_ok=True)
                codes = []
                for i, code in enumerate(traverse_file(record_dict, target=("@put-code"))):
                    if i % 100 == 0:
                        codes.append(code)
                    else:
                        codes[len(codes) - 1] += f",{code}"
                # codes = ",".join(traverse_file(record_dict, target=("@put-code")))
                # print(codes)
                orcid_detail = {}
                for idx, code in enumerate(codes):
                    work_url = f"https://pub.{"" if is_public else "sandbox."}orcid.org/v3.0/{orcid_id}/works/{code}"
                    record_headers = {
                        "Accept": "application/vnd.orcid+xml",
                        "Authorization": f"Bearer {access_token}"
                    }
                    try:
                        r = requests.get(work_url, headers=record_headers)
                        r.raise_for_status()
                        work_dict = xmltodict.parse(r.text)
                        if "personal-details:credit-name" in personal_dict.keys():
                            orcid_detail['name'] = personal_dict["personal-details:credit-name"]
                        else:
                            if "personal-details:given-names" in personal_dict.keys():
                                orcid_detail['name'] = personal_dict["personal-details:given-names"]
                            if "personal-details:family-name" in personal_dict.keys():
                                orcid_detail['name'] += " " + personal_dict["personal-details:family-name"]
                                # orcid_detail['name'] = personal_dict["personal-details:given-names"] + " " + personal_dict["personal-details:family-name"]
                        orcid_detail['ID'] = orcid_id
                        if idx == 0:
                            orcid_detail['works'] = work_dict["bulk:bulk"]["work:work"]
                        else:
                            orcid_detail['works'] += work_dict["bulk:bulk"]["work:work"]
                            
                    except requests.exceptions.HTTPError as e:
                        print("Fetch failed:", e, r.text)
                        raise
                    
                with open(f"./data/{orcid_id}.json", 'w') as f:
                    f.write(json.dumps(orcid_detail, indent=2))
                        
                print(f"{orcid_id}: Record fetched successfully:")
            except requests.exceptions.HTTPError as e:
                print("Fetch failed:", e, r.text)
                raise                            

def json2csv(dir="./data"):
    with open("./orcid_result.csv", 'w', encoding="utf-8-sig") as wf:
        for file in os.listdir(dir):
            rf = open(os.path.join(dir, file), 'r')
            data = json.load(rf)
            wf.write(f"{data['name']},{data['ID']}\n")
            for idx, work in enumerate(data['works']):
                wf.write(f",{idx + 1},")
                # if work["work:type"] == "book":
                #     if "\"" in work["work:title"]["common:title"]:
                #         title_info = work["work:title"]["common:title"].split("\"")
                #         wf.write(f'{title_info[1]}\n')
                #         wf.write(f',{",".join(title_info[2].split(",")[:-1])}\n')
                #     else:
                #         wf.write(f"{work["work:title"]["common:title"]}\n")
                # else:
                #     wf.write(f'{work["work:title"]["common:title"]}\n,')
                #     # print(work["work:contributors"]["work:contributor"])
                #     if work["work:contributors"] is not None:
                #         if type(work["work:contributors"]["work:contributor"]) is list:
                #             for contributor in work["work:contributors"]["work:contributor"]:
                #                 wf.write(f',{contributor["work:credit-name"]}')
                #         else:
                #             wf.write(f',{work["work:contributors"]["work:contributor"]["work:credit-name"]}')
                #     else:
                #         wf.write("\n")
                wf.write(f'{work["work:title"]["common:title"]}\n,')
                if work["work:contributors"] is not None:
                    if type(work["work:contributors"]["work:contributor"]) is list:
                        for contributor in work["work:contributors"]["work:contributor"]:
                            wf.write(f',{contributor["work:credit-name"]}')
                    else:
                        wf.write(f',{work["work:contributors"]["work:contributor"]["work:credit-name"]}')
                    wf.write("\n")
                else:
                    wf.write("\n")
                # wf.write(f',,{work['work:journal-title'] if 'work:journal-title' in work.keys() else {work["work:type"]}}\n')
                if "work:journal-title" in work.keys():
                    wf.write(f",,{work['work:journal-title']}\n")
                else:
                    wf.write(f",,{work['work:type']}\n")
                    
                if "common:publication-date" in work.keys():
                    wf.write(f',,{"-".join(date for date in work["common:publication-date"].values())}\n')
                    # print(work["common:publication-date"])
        
    
if __name__ == '__main__':
    orcid2json()
    json2csv()