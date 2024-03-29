import requests
import json
import time
import random
from datetime import date

def getReq(link):
  x = requests.get(link)
  print(x.status_code)
  return x.content

CTB_rt = json.loads(getReq("https://rt.data.gov.hk/v2/transport/citybus/route/ctb"))["data"]

CTB_rt2 = list(map(lambda x: x["route"], CTB_rt))

CHG = {"date":str(date.today())}

FareProperty={
   "L2":"次程免費",
   "FR":"減收",
   "FF":"減收",
   "RF":"減收",
   "TF":"兩程優惠車資合共",
   "L1":"回贈首程車費" 
}
def mapCTBData(data,tf):
  if len(data)!=0 and data["adult"]: return data["adult"]
  if len(tf)!=0 and tf["adult"]: return tf["adult"]
  return "";


def mapData(data,bound):
  k = list(filter(lambda x: x["bound"]==bound and x["legType"]=="1",data))
  s = []
  if(len(k)==0): return [];
  for i in range(len(k)):
    for j in range(len(k[i]["ir"])):
      x = k[i]["ir"][j]
      s.append({
      "co": x["secondProvider"].strip(),
      "route": x["route"].strip(),
      "direction":x["direction"],
      "stopName":x["stopName"], 
      #"discount":x["discount"],
      "dInfo":FareProperty[x["discount"]]+mapCTBData(x["discountAmount"],x["totalFare"]),
      "timeLimit": x["timeLimit"],
      "remark": x["remark"]
      })
  return [k[0]["direction"],s]

  
for rt in CTB_rt2:
  k=json.loads(getReq("https://www.citybus.com.hk/concessionApi/public/bbi/api/v1/route/tc/"+rt))
  try: data = list(k.values())
  except: continue
  CHG["CTB_"+rt+"_O"] = mapData(data,"F")
  CHG["CTB_"+rt+"_I"] = mapData(data,"B")
  
  time.sleep(3*random.random())

f1 = json.loads(getReq("https://www.kmb.hk/storage/BBI_routeF1.js"))
f2 = json.loads(getReq("https://www.kmb.hk/storage/BBI_routeB1.js"))

def kmbDetailHandler(d):
  if d=="":return "";
  if not "data-title" in d: return "";
  return d.split("data-title='")[1].split("'")[0]+"\n"

KMBTimeLimit = {
"":"150",
"^":"30",
"#":"60",
"*":"90",
"@":"120"
}

for NS in [(f1,"O"),(f2,"I")]:
  for rt in NS[0]:
    if NS[0][rt]["Records"]=="": pass
    k = list(map(lambda y: {
        #"co": "",
        "route": y["sec_routeno"],
        "direction":y["sec_dest"],
        "stopName":y["xchange"] if y["xchange"]!="任何能接駁第二程路線的巴士站" else "", 
        #"discount":"",
        "dInfo":y["discount_max"],
        #"timeLimit2": y["validity"],
        "timeLimit": KMBTimeLimit[y["validity"]],
        "remark": kmbDetailHandler(y["detail"]) + y["spec_remark_chi"]                           
    },NS[0][rt]["Records"]))
    CHG["KMB_"+rt+"_"+NS[1]] = [NS[0][rt]["bus_arr"][0]["dest"],k]

with open('CHG.json', 'w') as f2:
  f2.write(json.dumps(CHG, ensure_ascii=False))
