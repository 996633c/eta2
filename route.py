import requests
import json
def getReq(link):
  x = requests.get(link)
  print(x.status_code)
  return x.text

ctb = json.loads(getReq('https://rt.data.gov.hk/v2/transport/citybus/route/ctb'))["data"]
nwfb = json.loads(getReq('https://rt.data.gov.hk/v1.1/transport/citybus-nwfb/route/nwfb'))["data"]
kmb = json.loads(getReq('https://data.etabus.gov.hk/v1/transport/kmb/route'))["data"]

r3=[]
for i in ctb:
  r3.append({"co":i["co"],"r":i["route"],"d":i["orig_tc"],"d_en":i["orig_en"],"b":"I"})
  r3.append({"co":i["co"],"r":i["route"],"d":i["dest_tc"],"d_en":i["dest_en"],"b":"O"})
for i in nwfb:
  r3.append({"co":i["co"],"r":i["route"],"d":i["orig_tc"],"d_en":i["orig_en"],"b":"I"})
  r3.append({"co":i["co"],"r":i["route"],"d":i["dest_tc"],"d_en":i["dest_en"],"b":"O"})
for i in kmb:
  r3.append({"co":"KMB","r":i["route"],"d":i["dest_tc"],"d_en":i["dest_en"],"b":i["bound"],"s":i["service_type"]})
with open('routes.json', 'w') as f2:
  f2.write(json.dumps(r3, ensure_ascii=False))
