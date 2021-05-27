#! /usr/bin/env python3
import sys,os
import requests, json
from traceback import format_exc
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API = 'https://www.googleapis.com/geolocation/v1/geolocate'
GOOGLE_API_KEY = os.getenv('GOOGLEMAP_API_KEY', "test")

PARTICLE_CLOUD = "https://api.particle.io"
PARTICLE_CLOUD_EVENT = PARTICLE_CLOUD+"/v1/devices/events"
PARTICLE_DEVICE = PARTICLE_CLOUD+"/v1/devices/"
PARTICLE_ACCESS_TOKEN = os.getenv('PARTICLE_ACCESS_TOKEN', "test")
PARTICLE_EVENT_NAME = "deviceLocator"

def getLocation(cell_tower_info):
    # print(f"Getting Location: {cell_tower_info}")
    x = requests.post(GOOGLE_API, params={"key":GOOGLE_API_KEY}, json = cell_tower_info)
    return x.json()

def get_device(macid):
    # print(f"Getting details {macid}")
    x = requests.get(PARTICLE_DEVICE+macid, params= { "access_token": PARTICLE_ACCESS_TOKEN })
    return x.json()

def convert_from_particle_format(particle_format):
    data = {}
    _is_p_format = False
    try:
        if 'c' in particle_format:
            if 'a' in particle_format['c']:
                _is_p_format = True
    except Exception as e:
        print(format_exc())
    # print(f"Format : { 'Particle' if _is_p_format == True else 'Simple' } ")

    if _is_p_format == True:
        cell_towers = []
        for towers in particle_format['c']['a']:
            cell_towers.append({  
                "cellId": towers['i'], 
                "locationAreaCode": towers['l'],
                "mobileCountryCode": towers['c'],   
                "mobileNetworkCode": towers['n']
             })
        data.update({ "cellTowers":cell_towers })
    else:
        data = particle_format
    return data

if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        data = convert_from_particle_format(data)
        getLocation(data)
    else:
        particle_cloud = None
        if len(PARTICLE_ACCESS_TOKEN) > 1:
            url = f"{PARTICLE_CLOUD_EVENT}"
            if len(PARTICLE_EVENT_NAME) > 1:
                url = f"{PARTICLE_CLOUD_EVENT}/{PARTICLE_EVENT_NAME}"
            print(f"Listeing on {url}")
            r = requests.get(url, params= { "access_token": PARTICLE_ACCESS_TOKEN } ,stream=True)
            for chunk in r.iter_content(chunk_size=1024):
                _event = chunk.decode('utf8').replace("'", '"')
                _event = _event.split("\n")
                if len(_event[0].split(": ")) > 1:
                    event_name = _event[0].split(": ")[1]
                    event_data = _event[1].split(": ")[1]
                    event_data = json.loads(event_data)
                    try:
                        cell_tower_data = json.loads(event_data['data'])
                        cell_tower_data = convert_from_particle_format(cell_tower_data)
                        location = getLocation(cell_tower_data)
                        device = get_device(event_data['coreid'])
                        print(f"Name :{device['name']} {location['location']['lat']},{location['location']['lng']} Location: {location}")
                        # print(f"{event_name}: {(event_data)}")
                    except Exception as e:
                        # print(e)
                        print(format_exc())
                        # print(f"{event_name}: {(event_data)}")

    
    
            
        