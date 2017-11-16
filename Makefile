install:
			mkdir -p /opt/pyS3-volume
			mkdir -p /etc/docker/plugins
			pip3 install bottle s3cmd paste
			s3cmd --configure
			cp ~/.s3cfg /root/
			cp app.py /opt/pyS3-volume
			cp dockerconfig/pyS3-volume.json /etc/docker/plugins/
			cp systemdconfig/pyS3-volume.service /etc/systemd/system/
			chmod u+x /opt/pyS3-volume/app.py
			#"*** Done installing: run systemctl start pyS3-volume to start the daemon ***"

