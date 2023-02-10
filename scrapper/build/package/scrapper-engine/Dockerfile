FROM python:3.10-slim-bullseye

SHELL ["/bin/bash", "-c"]

RUN apt-get clean \
    && apt-get -y update

RUN apt-get -y install firefox-esr


ADD prt_scrapper/scrapper_common /app/scrapper_common
ADD prt_scrapper/scrapper_webapp /app/scrapper_webapp
ADD prt_scrapper/scrapper_job /app/scrapper_job

COPY prt_scrapper/.env.prod /app/.env
COPY prt_scrapper/requirements.txt /app/requirements.txt
COPY prt_scrapper/run_webapp.py /app
COPY prt_scrapper/run_job_root.py /app/run_job_root.py
COPY prt_scrapper/run_job_targets_list.py /app/run_job_targets_list.py
COPY prt_scrapper/run_job_publish_videos.py /app/run_job_publish_videos.py

COPY build/package/scrapper-engine/start_webapp.sh /app

RUN chmod +x /app/start_webapp.sh
RUN chmod +x /app/scrapper_job/service/webdriver/geckodriver

RUN groupadd prt-usr
RUN useradd -rm -d /home/prt-usr -s /bin/bash -g prt-usr -u 1001 prt-usr

RUN chown -R prt-usr:prt-usr /app

WORKDIR /app

USER prt-usr

RUN source /app/.env

RUN pip3 install -r /app/requirements.txt --no-cache-dir --user

CMD ["./start_webapp.sh"]