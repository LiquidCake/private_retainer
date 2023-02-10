#!/bin/sh

sudo docker-compose -f ./docker-compose-single-node.yml stop
sudo docker-compose -f ./docker-compose-single-node.yml start
