#!/bin/sh

#user crontab

crontab -l > user-mycron

echo "1 * * * * /home/$USER/prt/scr-run-scrapper-root-job.sh" >> user-mycron
echo "1 * * * * /home/$USER/prt/scr-run-scrapper-publish-videos-job.sh" >> user-mycron

crontab user-mycron
rm user-mycron
