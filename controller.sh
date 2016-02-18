#!/bin/bash

file="$1"

if [ "$file" == "" ]; then
	file="hub.py";
fi

ryu-manager "$file"
