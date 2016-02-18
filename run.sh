#!/bin/bash
sleep 5 && \
ovs-vsctl set bridge s1 protocols=OpenFlow10,OpenFlow13 & \
mn --controller=remote,ip=127.0.0.1,port=6633 --topo=single,5 --mac
