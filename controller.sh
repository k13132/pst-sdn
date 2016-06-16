#!/bin/bash

file="$1"

if [ "$file" == "" ]; then
	file="hub.py";
fi

if [ "$2" != "docker" ]; then
	ryu-manager "$file"
else
	docker run --rm -ti --volume $PWD:/usr/share/app/files/:ro tomkukral/ryu ryu-manager files/$file
fi
