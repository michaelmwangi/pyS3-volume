# pyS3-volume

This is a python port of the s3-volume-docker-plugin [https://github.com/chooban/s3-docker-volume-plugin] with some differences.

Basically this plugin creates a temporary directory on the host. The directory contents are in turn synchronised to an S3 bucket specified during volume creation.

This plugin makes use of **s3cmd** to sync with S3 and **bottle**, **cherrypy** as the web framework and web server respectively. The server binds by default to localhost and on port 8090. The defaults are trivial to change on the code base.

We also make use of systemd services according to the service file under systemdconfig directory.


# Requirements

1. Python 3
2. Pip3

# Installation

- git clone [repo-url]
- cd pyS3-volume
- sudo make install

# Usage

1. Create a docker volume

### docker volume create --driver=pyS3-volume --name s3vol --opts bucket=<bucketname> 
2. Attach docker volume to container
### docker run --rm -ti -v s3vol:/S3 ubuntu bash
This will create a volume named **s3vol** and any file added to the directory **S3** will be mirrored at the specified **bucketname**
