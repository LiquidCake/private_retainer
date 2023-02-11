#!/bin/sh

sudo mkdir -p /var/prt-scrapper-data/video_preview
sudo chmod 777 -R /var/prt-scrapper-data

#env variables are not available in cron, even $USER, so we need helper file with static path
sudo echo USER=$USER > /var/prt-scrapper-data/prt-static-env

#disable web servers if installed
sudo service nginx stop
sudo service apache2 stop
sudo systemctl disable nginx
sudo systemctl disable apache2
