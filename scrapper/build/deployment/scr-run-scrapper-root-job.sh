#!/bin/bash -l
source /var/prt-scrapper-data/prt-static-env
source /home/$USER/prt/.env
curl 127.0.0.1:10339/start-scrapper-job-root -u ${HTTP_BASIC_AUTH_USERNAME}:${HTTP_BASIC_AUTH_PASSWORD}
