#!/bin/sh
mv .env.prod .env

sudo docker load -i ./prt-scrapper-engine-latest.tar && \
	sudo docker load -i ./prt-scrapper-postgres-latest.tar && \
	sudo docker load -i ./prt-scrapper-nginx-latest.tar

sudo docker-compose -f ./docker-compose-single-node.yml down

echo y | sudo docker image prune

sudo docker-compose -f ./docker-compose-single-node.yml up
