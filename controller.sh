#!/bin/bash

file="$1"

if [ "$file" == "" ]; then
	file="hub.py";
fi

if [ "$2" != "docker" ]; then
	cmd="ryu-manager \"$file\""
else
	cmd="docker run --rm -ti --volume $PWD:/usr/share/app/files/:ro tomkukral/ryu ryu-manager files/$file"
fi

echo "$cmd"
$cmd
