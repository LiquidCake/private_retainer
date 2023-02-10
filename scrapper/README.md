# about

this is a small containerized scrapper engine for loading embeddable videos lists from video hosting websites like `youtube` etc.  
it periodically scraps configured list of channels or search queries and saves all found videos to DB

app has 2 parts:
- scrapper engine: launches scrapper jobs, applies scrapping scripts to webpage and saves data to DB
- scrapper admin webapp: shows scrapped videos from DB, allows to preview them, change statuses and mark videos for any further 'publishing'

usage (e.g. for 'youtube'):
- build, start containers (either locally or on remote server) - see _build_ section below
- apply DB init scripts manually - `private_retainer/scrapper/db/init_db.sql` (DB creds are in .env file, see _build_ section below)
- copy scrapping scripts code from files at `private_retainer/scrapper/prt_scrapper/scrapper_job/db_persisted_scripts` to DB table `scrapper_data_target_parsing_code`
- create data targets (URL's) in DB table `scrapper_data_target` (see `example_targets.sql`), make sure to set `enabled = true`
- check configs in DB table `configuration`
- scrapper wil run once a day as configured in `private_retainer/scrapper/build/deployment/setup-cron-user.sh`
  - or it can be launched manually by sending HTTP request:
  - `/start-scrapper-job-root` - root job runs all enabled targets
  - `/start-scrapper-job-targets-list` per-targetId list job
  - `/start-scrapper-job-publish-videos` job exports videos that were 'approved' by admin to some place (existing job code is just a template and exports to json file `/var/prt-scrapper-data/published_videos_*.json`)

info:
- scrapping targets (URLs) are configured per-provider (DB table `provider` - like 'youtube' etc.) in DB table `scrapper_data_target`.
- scrapper script for particular type of targets (search page, channel page etc.) is applied according to particular target and is stored in DB `scrapper_data_target_parsing_code`. Script sources are stored in `private_retainer/scrapper/prt_scrapper/scrapper_job/db_persisted_scripts`
  - scrapper scripts in DB contain current scrapping code and some configs for particular page type scrapping (as global variables). They must be updated if scrapping logic or some of these configs need to be changed   
- found videos are sored in DB table `found_video`. Initially they are loaded with status 'unapproved' (or 'suppressed' if title contains bad words, configurable). After admin approves video it may later be 'published' by 'publish videos' job
- configurations are stored in DB table `configuration` (global or per-provider)
- scrapper root job per-provider parallelism is set in `configuration.scrapper_job_data_target_parallelism` - 1 is single worker process for all provider's targets, e.g. 10 is all provider's targets are distributed between 10 worker processes
- job run status (which is also a `run lock`) is stored in DB table `scrapper_job_status`
- job logs are stored in DB table `scrapper_job_log`
- scrapping job(s) are launched by `crontab` CRON triggers using corresponding HTTP endpoints of webapp (like `GET /start-scrapper-job-root`). Also job scripts may be launched manually (`python3 private_retainer/scrapper/prt_scrapper/run_job_root.py`)
- webapp uses `flask` dev webserver since it allows free process spawning (which we need for scrapper jobs launching) and its simplicity fits perfectly for admin webapp
- pre-created `provider`s are 'youtube' and 'tiktok', though for 'tiktok' there is only a basic script that can usualy scrap only 1st page (portion) of the newest channel videos, since after that website asks for captcha confirmation etc.   
- 'publishing' job (`run_job_publish_videos.py`) is just a template code that saves approved videos to file, you may want to change it so it loads videos to some particular place
- to change jobs run frequency - change `private_retainer/scrapper/build/deployment/setup-cron-user.sh` file for different CRON settings

## Add/update scrapping scripts
```
-- e.g. for provider=youtube, target_type=channel, video_type=full video - replace value of `parsing_code` column 
--   with content of script, mentioned in `script_name` column
INSERT INTO scrapper_data_target_parsing_code
(provider_id, target_type_id, video_type_id, parsing_code, vars, script_name) VALUES
	(1, 2, 1, '!!! insert contents of parser_youtube_channel.py', '{}'::text, 'parser_youtube_channel.py'),
```

## Build 
###### expected Linux with Docker
`e.g. install by same script as used to setup remote server: private_retainer/scrapper/build/deployment/env-init-ubuntu.sh`

### prepare build/run env 
```
sudo mkdir -p /var/prt-scrapper-data/video_preview
sudo chmod 777 -R /var/prt-scrapper-data
```

### .env files
###### Change contents of .env.local if needed. Add file '.env.prod' at the same folder using example (will be copied into container during build)   
`private_retainer/scrapper/.env.local`  (used for local debug when start with python directly)
`private_retainer/scrapper/.env.prod` (used for any Docker-based deployment)

### env

### build/locally launch containers  
`private_retainer/scrapper/rebuild-docker.sh`

## local python debug setup

#### install dependencies
`python3 -m pip install -r private_retainer/scrapper/prt_scrapper/requirements.txt`

#### launch scrapper DB container only
`docker-compose -f private_retainer/scrapper/build/package/docker-compose-local-unified.yml up prt-scrapper-postgres`

#### launch webapp
`cd private_retainer/scrapper/prt_scrapper`  
`python3 run_webapp.py`

#### to run job script directly (normally started via webapp endpoint)
`cd private_retainer/scrapper/prt_scrapper`  
`python3 run_job_root.py`

## etc

### symlincs (if need to recreate)
`cd private_retainer/scrapper/prt_scrapper/scrapper_webapp/static/img`  
`ln -s /var/prt-scrapper-data/video_preview video_preview`  


# deploy remotely

## server init

### upload files
```
#remotely - create app dir
mkdir ~/prt

#locally - send files
scp -P 22 \
private_retainer/scrapper/build/deployment/docker-compose-single-node.yml \
private_retainer/scrapper/build/deployment/redeploy.sh \
private_retainer/scrapper/build/deployment/restart.sh \
private_retainer/scrapper/build/deployment/setup-cron-user.sh \
private_retainer/scrapper/build/deployment/scr-run-scrapper-root-job.sh \
private_retainer/scrapper/build/deployment/scr-run-scrapper-publish-videos-job.sh \
private_retainer/scrapper/build/deployment/env-init-ubuntu.sh \
private_retainer/scrapper/build/deployment/init-single-node.sh \
private_retainer/scrapper/prt_scrapper/.env.prod \
myuser@myserver.com:/home/myuser/prt
```

### run init scripts
```
#remotely
sudo ~/prt/env-init-ubuntu.sh
sudo ~/prt/init-single-node.sh
~/prt/setup-cron-user.sh
```

## build / upload images

### build (check build section for details)
```
#locally
cd private_retainer/scrapper && ./rebuild-docker.sh prod
```

### upload to remote server

```
#locally
docker save -o /tmp/prt-scrapper-engine-latest.tar prt-scrapper-engine:latest && \
docker save -o /tmp/prt-scrapper-postgres-latest.tar prt-scrapper-postgres:latest && \
docker save -o /tmp/prt-scrapper-nginx-latest.tar prt-scrapper-nginx:latest

scp -P 22 \
/tmp/prt-scrapper-engine-latest.tar \
/tmp/prt-scrapper-postgres-latest.tar \
/tmp/prt-scrapper-nginx-latest.tar \
myuser@myserver.com:/home/myuser/prt
```

## run deployment
```
#remotely, !!! BACKUP DB data before containers re-deployment, it will be WIPED
~/prt/redeploy.sh

#to restart deployed app without losing DB data -
~/prt/restart.sh
```

