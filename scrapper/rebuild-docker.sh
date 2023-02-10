#!/bin/sh

#app version
major_version=1
minor_version=1
build_num=0 #dynamic

#stop docker
echo "=== Stopping scrapper containers"
docker-compose -f build/package/docker-compose-local-unified.yml stop

#remove all docker images
docker rmi -f `docker images --format="{{.Repository}}:{{.Tag}}" | grep -e prt-scrapper-postgres -e prt-scrapper-engine -e prt-scrapper-nginx`
#docker rmi -f `docker images --format="{{.Repository}}:{{.Tag}}"`


#      Build app

# Increment next build number

build_num_file="./build/build_num"

if [ -e $build_num_file ]; then
  echo "File $build_num_file already exists!"

  while IFS= read -r line;
  do
    build_num=$line
  done < $build_num_file

else
  echo >> $build_num_file
  echo "Created file $build_num_file"
fi

echo ""
echo ""

build_num=$(($build_num + 1))
echo "build num: $build_num"

#write to file
echo $build_num > $build_num_file

export BUILD_VERSION="$major_version.$minor_version.$build_num"
echo "env BUILD_VERSION: $BUILD_VERSION"

# build env
if [ "$1" = "prod" ]; then
  export BUILD_ENV="prod"
else
  export BUILD_ENV="dev"
fi

echo "env BUILD_ENV: " $BUILD_ENV


# Build postgres
echo ""
echo "=== Building prt-scrapper-postgres"

#build postgres docker image
docker build -t prt-scrapper-postgres --build-arg build_ver=$BUILD_VERSION --file build/package/scrapper-postgres/Dockerfile build/package/scrapper-postgres/
docker tag prt-scrapper-postgres prt-scrapper-postgres:$BUILD_VERSION


# Build engine
echo ""
echo "=== Building prt-scrapper-engine"

#build scrapper engine docker image
docker build -t prt-scrapper-engine --build-arg build_ver=$BUILD_VERSION --file build/package/scrapper-engine/Dockerfile .
docker tag prt-scrapper-engine prt-scrapper-engine:$BUILD_VERSION


# Build nginx
echo ""
echo "=== Building nginx"

#build nginx docker image
docker build -t prt-scrapper-nginx --build-arg build_ver=$BUILD_VERSION -f build/package/nginx/Dockerfile .
docker tag prt-scrapper-nginx prt-scrapper-nginx:$BUILD_VERSION


# Run containers
echo ""
echo "=== Starting scrapper containers"
docker-compose -f build/package/docker-compose-local-unified.yml up #--remove-orphans --force-recreate

echo ""