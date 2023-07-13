import requests
import json
import time
import math
import random
def getReq(link):
  x = requests.get(link)
  print(x.status_code)
  return x.content
import xmltodict
import geopy
import geopy.distance
import re
import zipfile
from os import path
import csv


ctb_stop = json.loads(getReq('https://raw.githubusercontent.com/hkbus/hk-bus-crawling/gh-pages/routeFareList.min.json'))
#using HK Bus Crawling@2021, https://github.com/hkbus/hk-bus-crawling as an alternative method to get ctbstoplist rather than crawling
KMB2 = json.loads(getReq("https://data.etabus.gov.hk/v1/transport/kmb/stop"))

#parse Stops
_stoplist = {}
for i in KMB2["data"]:
  _stoplist[str(i["stop"])] = {"data": i, "alt": [], "td": []}

def formatCrawlerStop(i,e):
  return {"stop":i, "name_en":e["name"]["en"], "name_tc": e["name"]["zh"], "lat":e["location"]["lat"], "long":e["location"]["lng"]}
for i in ctb_stop["stopList"]:
  if len(i)==6 and i.isnumeric():
    _stoplist[i] = {"data": formatCrawlerStop(i,ctb_stop["stopList"][i]), "alt": [], "td": []}

KMB_rt = json.loads(getReq("https://data.etabus.gov.hk/v1/transport/kmb/route/"))
CTB_rt = json.loads(getReq("https://rt.data.gov.hk/v2/transport/citybus/route/ctb"))

#PARSE ROUTES
_rtlist = {"KMB":{},"CTB":{}}

for i in KMB_rt["data"]:
  try: _rtlist["KMB"][i["route"]]
  except: _rtlist["KMB"][i["route"]] = {"co":"KMB", "route":i["route"], "var":{}, "td":{}}
  _rtlist["KMB"][i["route"]]["var"][i["bound"]+i["service_type"]] = i
for i in CTB_rt["data"]:
  _rtlist["CTB"][i["route"]] = {"co":"CTB", "route":i["route"], "var":{
    "I":{"route":i["route"], "bound":"I", "dest_tc":i["dest_tc"], "dest_en":i["dest_en"], "orig_tc":i["orig_tc"], "orig_en":i["orig_en"], "stops":[]},
    "O":{"route":i["route"], "bound":"O", "orig_tc":i["dest_tc"], "orig_en":i["dest_en"], "dest_tc":i["orig_tc"], "dest_en":i["orig_en"], "stops":[]}
  }, "td":{}}
  _rtlist["CTB"][i["route"]]["var"]["I"]["stops"] = list(map(lambda x: x["stop"],json.loads(getReq("https://rt.data.gov.hk/v2/transport/citybus/route-stop/ctb/"+i["route"]+"/inbound"))["data"]))
  _rtlist["CTB"][i["route"]]["var"]["O"]["stops"] = list(map(lambda x: x["stop"],json.loads(getReq("https://rt.data.gov.hk/v2/transport/citybus/route-stop/ctb/"+i["route"]+"/outbound"))["data"]))

KMB_rtstop = json.loads(getReq("https://data.etabus.gov.hk/v1/transport/kmb/route-stop"))
for i in KMB_rtstop["data"]:
  if not "stops" in _rtlist["KMB"][i["route"]]["var"][i["bound"]+i["service_type"]]: _rtlist["KMB"][i["route"]]["var"][i["bound"]+i["service_type"]]["stops"] = []
  _rtlist["KMB"][i["route"]]["var"][i["bound"]+i["service_type"]]["stops"].append(i["stop"])

#TDGOVHK
r = requests.get('https://static.data.gov.hk/td/pt-headway-tc/gtfs.zip')
open('gtfs.zip', 'wb').write(r.content)
zipfile.ZipFile("gtfs.zip","r").extractall("gtfs")

#parse Rt
coopRt=[]
with open('gtfs/routes.txt') as csvfile:
  reader = csv.reader(csvfile)
  next(reader, None)
  for [id,co,rt,dst,_,_] in reader:
    if co=="KMB+CTB":
      _rtlist["KMB"][rt]["td"][id]=dst
      _rtlist["CTB"][rt]["td"][id]=dst
      if not rt in coopRt: coopRt.append(rt)
    elif co=="KMB" or co=="CTB":
      try: _rtlist[co][rt]["td"][id]=dst
      except: print(rt)
    elif co=="LWB":
      try: _rtlist["LWB"][rt]["td"][id]=dst
      except: print(rt)

#Match CTB & KMB STOPS
NOTMACHER = []
MATCHER = {}
def parseCoopRt(c,k):
  global MATCHER,NOTMACHER
  for i in c:
    for j in k:
      ix = _stoplist[i]["data"]
      jx = _stoplist[j]["data"]
      dst = geopy.distance.geodesic((ix["lat"],ix["long"]), (jx["lat"],jx["long"])).m
      if dst<100:
        if not i in MATCHER: MATCHER[i]=[]
        if not j in MATCHER: MATCHER[j]=[]
        MATCHER[i].append([j,dst])
        MATCHER[j].append([i,dst])
  for i in k:
    if not i in MATCHER: NOTMACHER.append(i)
  for i in c:
    if not i in MATCHER: NOTMACHER.append(i)

for i in coopRt:
  try: parseCoopRt(_rtlist["KMB"][i]["var"]["I1"]["stops"],_rtlist["CTB"][i]["var"]["O"]["stops"])
  except: pass
  try: parseCoopRt(_rtlist["KMB"][i]["var"]["I1"]["stops"],_rtlist["CTB"][i]["var"]["I"]["stops"])
  except: pass
  try: parseCoopRt(_rtlist["KMB"][i]["var"]["O1"]["stops"],_rtlist["CTB"][i]["var"]["O"]["stops"])
  except: pass
  try: parseCoopRt(_rtlist["KMB"][i]["var"]["O1"]["stops"],_rtlist["CTB"][i]["var"]["I"]["stops"])
  except: pass
print(NOTMACHER)

for i in MATCHER:
  min2 = min(MATCHER[i], key = lambda x:x[1])
  _stoplist[i]["alt"].append(min2[0])
  #print(_stoplist[i]["data"]["name_tc"], _stoplist[min2[0]]["data"]["name_tc"])

#PARSE KMB BBIs (annoying)
KMBBBI = {}
for i in _stoplist:
  if len(i)<7: continue
  if not "(" in _stoplist[i]["data"]["name_tc"] and not "總站" in _stoplist[i]["data"]["name_tc"]: continue
  j = re.sub(r"\d+\)", "", _stoplist[i]["data"]["name_tc"])
  for k in _stoplist:
    if len(k)<7: continue
    if j in _stoplist[k]["data"]["name_tc"]:
      if not i in KMBBBI: KMBBBI[i]=[]
      if not k in KMBBBI: KMBBBI[k]=[]
      KMBBBI[i].append(k)
      KMBBBI[k].append(i)

for i in KMBBBI:
  j = _stoplist[i]["alt"]
  _stoplist[i]["alt"] += KMBBBI[i]

#PARSE TDGOV STOPS
with open('gtfs/stops.txt') as csvfile:
  reader = csv.reader(csvfile)
  next(reader, None)
  for [id,stop_name,lat,long,_,_,_] in reader:
    for j in _stoplist:
      if _stoplist[j]["data"]["name_tc"] in stop_name and not j in _stoplist[j]["td"]:
        _stoplist[j]["td"].append(id)

#Part II GTFS

GTFS_rt = {}
#Parse GTF RtStopList
with open('gtfs/stop_times.txt') as csvfile:
  reader = csv.reader(csvfile)
  headers = next(reader, None)
  for [trip_id, _, _, stop_id, seq, _, _, _] in reader:
    [rt, bound, _, _] = trip_id.split('-')
    if rt not in GTFS_rt: GTFS_rt[rt] = {"1":{},"2":{}}
    GTFS_rt[rt][bound][int(seq)] = stop_id

#Parse GTF FareRtList
GTFS_fare = {}
with open('gtfs/fare_attributes.txt') as csvfile:
  reader = csv.reader(csvfile)
  headers = next(reader, None)
  for [fare_id,price,_,_,_,_] in reader:
    [rt, bound, on, off] = fare_id.split('-')
    if rt not in GTFS_fare: GTFS_fare[rt] = {"1":{},"2":{}}
    price = '0' if price == '0.0000' else price
    if on not in GTFS_fare[rt][bound]: GTFS_fare[rt][bound][on]=[[price, int(off)]]
    else:
      ADDED = True
      for i in GTFS_fare[rt][bound][on]:
        if i[0]==price and i[1] < int(off):
          i[1] = int(off)
          ADDED = False
          break
      if ADDED: GTFS_fare[rt][bound][on].append([price, int(off)])


#Part III MATCHER
def GTFS2CO_stop(GTFS,co,rt,bound,map2={}):
  global mostbound
  co2 = list(map(lambda x: _stoplist[x]["td"],co))
  gtfs2 = list(GTFS.values())
  if len(co2)==len(gtfs2):
    for i in range(len(co2)):
      map2[co[i]] = [GTFS_fare[rt][bound][str(i+1)],i+1,i+1]
      mostbound[bound]+=1
    return

  for i in range(len(co2)):
    APPENDED2 = False
    for j in range(len(gtfs2)):
      if gtfs2[j] in co2[i]:
        if not co[i] in map2:
          try: 
            map2[co[i]] = [GTFS_fare[rt][bound][str(j+1)],j+1,i+1]
            mostbound[bound]+=1
          except: map2[co[i]] = ["-2",str(j+1),i+1]
        APPENDED2=True
        break
    if not APPENDED2 and not co[i] in map2: map2[co[i]] = ["-1",str(i+1)]


  return map2

def fixRt(list2,rt,bound):
  if not list2: return list2
  BOUND2 = "1" if mostbound["1"]>mostbound["2"] else "2"
  tmp02 = []
  lastWork = 0
  for i in list2:
    if list2[i][0]=="-1" or list2[i][0]=="-2": 
      tmp02.append(i)
    else:
      if len(tmp02) == list2[i][2]-lastWork-1:
        for j in range(len(tmp02)):
          try: list2[tmp02[j]] = [GTFS_fare[rt][BOUND2][str(lastWork+j+1)],lastWork+j+1,lastWork+j+1]
          except: pass
      elif len(tmp02)>0:
        print("*",rt,tmp02)
      lastWork=list2[i][2]
      tmp02=[]
  return list2
      

for co4 in ("CTB","KMB"):
  co5 = ("I","O") if co4=="CTB" else ("I1","O1")
  for i in _rtlist[co4]:
    for k in co5:
      lst = {}
      mostbound = {"1":0,"2":0}
      for j in _rtlist[co4][i]["td"]:
        try: lst = GTFS2CO_stop(GTFS_rt[j]["1"],_rtlist[co4][i]["var"][k]["stops"],j,"1",lst)
        except: pass
        try: lst = GTFS2CO_stop(GTFS_rt[j]["2"],_rtlist[co4][i]["var"][k]["stops"],j,"2",lst)
        except: pass
      if not "fare" in _rtlist[co4][i]:
        if co4 == "CTB": _rtlist[co4][i]["fare"] = {"I":[],"O":[]}
        else: _rtlist[co4][i]["fare"] = {"I1":[],"O1":[]}
      lst = fixRt(lst,j,"2")

      try: _rtlist[co4][i]["fare"][k] = list(map(lambda x:x[0][0],list(lst.values())))
      except: print(co4,i)

#Part IV parse out
f = open("_stoplist.txt","a")
f.write(json.dumps(_stoplist, ensure_ascii=False))

f2 = open("_rtlist.txt","a")
f2.write(json.dumps(_rtlist, ensure_ascii=False))
