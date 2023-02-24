import requests
import json
def getReq(link):
  x = requests.get(link)
  print(x.status_code)
  return x.text

result = getReq('https://data.etabus.gov.hk/v1/transport/kmb/stop')
r2 = json.loads(result)
r2 = r2["data"]

r3={}
for i in r2:
  r3[i["stop"]] = [i["name_tc"],i["name_en"]]
with open('kmb_stop.json', 'w') as f2:
  f2.write(json.dumps(r3, ensure_ascii=False))
