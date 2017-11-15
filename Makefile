install:
			mkdir -p /opt/pyS3-volume
			mkdir -p /etc/docker/plugins
			pip3 install bottle s3cmd
			s3cmd --configure
			cp app.py /opt/pyS3-volume
			cp dockerconfig/pyS3-volume.json /etc/docker/plugins/
			cp systemdconfig/pyS3-volume.service /etc/systemd/system/
