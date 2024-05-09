#!/bin/bash

# Wait for MongoDB container to be ready
until docker exec mongo_1 mongo --eval 'db.getMongo()'; do
  echo "Waiting for MongoDB container to be ready..."
  sleep 2
done


# Define MongoDB hosts and ports
HOST1="mongo_1"
PORT1="27017"
HOST2="mongo_2"
PORT2="27017" # Assuming MongoDB is running on the default port 27017 in all containers
HOST3="mongo_3"
PORT3="27017" # Assuming MongoDB is running on the default port 27017 in all containers
REPLICA_SET_NAME="myReplicaSet"

# Initialize the replica set
init_replica_set() {
  docker exec mongo_1 mongo --eval "
    if (rs.status().ok != 1) {
      rs.initiate({
        _id: '$REPLICA_SET_NAME',
        members: [
          { _id: 0, host: '$HOST1:$PORT1' },
          { _id: 1, host: '$HOST2:$PORT2' },
          { _id: 2, host: '$HOST3:$PORT3' }
        ]
      })
    }
  "
}

# Check if MongoDB is already part of a replica set
is_in_replica_set() {
  docker exec mongo_1 mongo --eval "rs.status().ok == 1" | grep true
}

if is_in_replica_set; then
  echo "MongoDB already part of a replica set."
else
  echo "Initializing replica set..."
  init_replica_set
fi

