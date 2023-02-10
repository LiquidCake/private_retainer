#!/bin/sh

sudo mkdir -p /var/prt-scrapper-data/video_preview

sudo chmod 777 -R /var/prt-scrapper-data

#disable web servers if installed
sudo service nginx stop
sudo service apache2 stop
sudo systemctl disable nginx
sudo systemctl disable apache2
