#! /bin/bash

# Check for  mysql container
if [[ $(docker ps -a | grep esprr-mysql) ]];
then
    if [ $( docker container inspect -f '{{.State.Status}}' esprr-mysql ) != "running" ];
    then
        echo "starting mysql"
        docker start esprr-mysql
    else
        echo "mysql already running"
    fi
else 
    docker run --detach -p 3306:3306 --name esprr-mysql -e MYSQL_ROOT_PASSWORD=testpassword -d mysql:8.0.21
fi

# check for redis
if [[ $(docker ps -a | grep esprr-redis) ]];
then
    # if the container exists and is not running, start it.
    if [ $( docker container inspect -f '{{.State.Status}}' esprr-redis ) != "running" ];
    then
        echo "starting redis"
        docker start esprr-redis
    else
        echo "redis already running"
    fi
else
  # start a new redis container and publish the redis ports
  docker run --detach -p 6379:6379 --name esprr-redis -d redis redis-server
fi

# Export the environment variable required by dbmate to run migrations with "dbmate up"
export DATABASE_URL="mysql://root:testpassword@127.0.0.1:3306/esprr_data"
