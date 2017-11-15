#!/usr/bin/python3

import json
import shutil
import tempfile
import logging 
import logging.handlers
from bottle import post, run, request, get

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('/mnt/programming/ionic/code/docker-volume/app.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

volume_mapping = dict()

def process_request(reqbody):
    raw_opts = reqbody.read().decode()
    opts = json.loads(raw_opts)
    return opts

@post('/Plugin.Activate')
def plugin_activate():
    logging.info("Activating S3 volume .....")
    payload = {'Implements': ['VolumeDriver']}
    return json.dumps(payload)

@post('/VolumeDriver.Create')
def volume_driver_create():
    Opts = process_request(request.body)
    vol_name = Opts.get('Name', None)    
    buck_name = Opts.get('Opts').get('bucket', None)
    err_msg = ''
    if not buck_name or not vol_name:
        err_msg = "Mandatory bucket name not passed"
        logger.error("Volume creation error mandatory params not passed Name: %s , Bucket: %s", vol_name, buck_name)
    else:
        dir_path = tempfile.mkdtemp()
        global volume_mapping
        volume_mapping[vol_name] = {buck_name: dir_path}        
        logger.debug('Created volume at %s for bucket %s', dir_path, buck_name)
        
    payload = {'Err': err_msg}
    return json.dumps(payload)

@post('/VolumeDriver.Remove')
def volume_driver_remove():
    Opts = process_request(request.body)
    vol_name = Opts.get('Name', None)
    if vol_name:
        global volume_mapping
        dir_paths = volume_mapping[vol_name]
        for path in dir_paths.values():
            shutil.rmtree(path)
            logger.debug('Removed %s volume', path)
    else:
        err_msg = 'Error volume name not passed'
        logger.error('Volume name was not passed!')

    payload = {'Err': err_msg}
    return json.dumps(payload)

@post('/VolumeDriver.Mount')
def volume_driver_mount():
    Opts = process_request(request.body)
    vol_name = Opts.get('Name', None)
    err_msg = ''
    mount_path = ''
    if vol_name:
        global volume_mapping
        mapping = volume_mapping.get(vol_name, None)        
        if not mapping:
            err_msg = 'Volume has not been mounted on the filesystem yet'
            logger.error('Volume %s does not have a mapping on the file system yet', vol_name)
        else:        
            mount_path = list(mapping.values())[0]
    else:
        logger.error("Volume name not passed")
        err_msg = 'Volume name not passed'
    
    payload = {'Err': err_msg, 'Mountpoint': mount_path}
    return json.dumps(payload)
    
@post('/VolumeDriver.Unmount')
def volume_driver_unmount():
    # for now we dont unmount until we get the explicit remove volume 
    payload = {'Err': ''}

    return json.dumps(payload)

@post('/VolumeDriver.Get')
def volume_get():
    global volume_mapping
    mappings = list(volume_mapping.values())[0]
    path = ''
    name = list(volume_mapping.keys())[0]
    if mappings:
        path = list(mappings.values())[0]

    payload = {
        'Volume': {
            'Name': name,
            'Mountpoint': path
        },
        'Err': ''
    }
    logger.info(json.dumps(payload))
    return json.dumps(payload)

@post('/VolumeDriver.List')
def volume_driver_list():
    global volume_mapping
    items = list()
    for key, mounts in volume_mapping.items():
        mounts = mounts.values()[0]
        mount_path = list(mounts.values())[0]
        items.append({"Name": key, "Mountpoint": mount_path})
    
    payload = {
        "Volumes": items,
        "Err": ''
    }

    return json.dumps(payload)


@get('/')
def index():
    return "Hello"  

run(host='127.0.0.1', port="8090", debug=True)
