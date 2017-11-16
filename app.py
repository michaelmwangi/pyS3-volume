#!/usr/bin/python3

import os
import json
import shutil
import time
import tempfile
import logging 
import threading
import subprocess
import logging.handlers
from bottle import post, run, request, get

volume_mapping = dict()
SLEEP_S = 15

INSTALL_DIR = '/opt/pyS3-volume'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
log_path = os.path.join(INSTALL_DIR, 'app.log')
handler = logging.FileHandler(log_path)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def process_request(reqbody):
    raw_opts = reqbody.read().decode()
    opts = json.loads(raw_opts)
    return opts

def delete_dir(dir_path):
    shutil.rmtree(dir_path)
    logger.debug('Removed %s volume', dir_path)

def s3_sync():
    global volume_mapping
    
    while True:        
        time.sleep(SLEEP_S)        
        vols_maps = volume_mapping.copy()
        for vol_name, mount_dict in vols_maps.items():
            bucketname = list(mount_dict.keys())[0]
            path = list(mount_dict.values())[0] + '/' # add the trailing slash to indicate this is a dir
            try:
                logger.debug("Pushing %s to %s", path, bucketname)
                subprocess.check_call(['s3cmd', 'sync', path, '--delete-removed', 's3://{}'.format(bucketname)])
                logger.debug("Done pushing")
            except Exception as exc:
                logger.error("Error pushing files to S3 error: %s ", exc)
            

@post('/Plugin.Activate')
def plugin_activate():
    payload = {'Implements': ['VolumeDriver']}
    return json.dumps(payload)

@post('/VolumeDriver.Create')
def volume_driver_create():
    Opts = process_request(request.body)
    vol_name = Opts.get('Name', None)    
    buck_name = Opts.get('Opts').get('bucket', None)
    err_msg = ''
    if not buck_name or not vol_name:
        err_msg = "Mandatory params name not passed"
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
    err_msg = ''
    logger.debug("proceeding to remove volume %s", vol_name)
    if vol_name:
        global volume_mapping
        dir_paths = volume_mapping[vol_name]
        for path in dir_paths.values():
            delete_dir(path)
        del volume_mapping[vol_name]
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
    path = ''    
    Opts = process_request(request.body)
    vol_name = Opts.get('Name', None)
    if vol_name:
        path = list(volume_mapping[vol_name].values())[0]

    payload = {
        'Volume': {
            'Name': vol_name,
            'Mountpoint': path
        },
        'Err': ''
    }
    return json.dumps(payload)

@post('/VolumeDriver.Capabilities')
def volume_driver_capabilities():
    payload = {
        "Capabilities": {
            "Scope": "global"
        }
    }
    
    return json.dumps(payload)

@post('/VolumeDriver.List')
def volume_driver_list():
    global volume_mapping
    items = list()
    for key, mounts in volume_mapping.items():
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

s3_sync = threading.Thread(target=s3_sync)
s3_sync.start()
run(host='127.0.0.1', port="8090", server='paste')
