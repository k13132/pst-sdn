#!/usr/bin/env python
# -*- coding: utf-8 -*-

# mininet env:
#   mn --controller=remote,ip=192.168.1.1,port=6633 --topo=single,5 --mac
# set ovs to use OpenFlow 1.0 and 1.3
#   ovs-vsctl set bridge s1 protocols=OpenFlow10,OpenFlow13
#   ovs-vsctl list bridge s1
# dump flows
#   ovs-ofctl dump-flows s1
# dump flows in mininet
#   dpctl dump-flows

# doc:
# ryu OpenFlow Messages & Structures 
#   http://ryu.readthedocs.org/en/latest/ofproto_v1_3_ref.html
# ryu github 
#   https://github.com/osrg/ryu

# impors
from ryu.base import app_manager # basic app
from ryu.controller import ofp_event # ofp events
from ryu.controller.handler import MAIN_DISPATCHER # handlers
from ryu.controller.handler import set_ev_cls

# openflow version 1.3
from ryu.ofproto import ofproto_v1_3

# packets
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import ipv6

# timestamps
import time

class Switch(app_manager.RyuApp):
    # set OF 1.3
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    # class initialization
    def __init__(self, *args, **kwargs):
        super(Switch, self).__init__(*args, **kwargs)
        # define mac table
        self.mac_table = {}
        # insert broadcast port

    # event definition 
    # run on: ofp_event.EventOFPPacketIn
    # when switch state is: MAIN_DISPATCHER (connected to controller)
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        print '--- new packet_in at time %f' % time.time()
        ## gain data about incoming mgs/packet
        # incomming msg - packet_in datastructure
        msg = ev.msg

        # datapath - (= switch)
        datapath = msg.datapath

        # OF protocol
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        # parser parsing
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        # create parsing variables
        in_port = msg.match['in_port']

        print '\tswitch: %s, port: %s' % (datapath.id, in_port)

        # read ethernet header
        if eth != None:
            print '\teth: src: %s, dst: %s' % (eth.src, eth.dst)
            # set mac table enty
            self.mac_table.setdefault(datapath.id, {})
            self.mac_table[datapath.id][eth.src] = in_port

        # read ipv4 protocols
        ip4 = pkt.get_protocol(ipv4.ipv4)
        if ip4 != None:
            print '\tipv4: src: %s, dst: %s' % (ip4.src, ip4.dst)

        ## decide on outport
        outport = None
        if eth.dst in self.mac_table[datapath.id]:
            print '\trecord exists at switch %s port %s' % (datapath.id, self.mac_table[datapath.id][eth.dst])
            outport = self.mac_table[datapath.id][eth.dst]
        elif eth.dst == 'ff:ff:ff:ff:ff:ff':
            print '\tbroadcast mac'
            outport = ofp.OFPP_FLOOD # special variable for FLOOD target interface
        else:
            print '\tno record for ' + eth.dst + ', going to flood, sorry'
            outport = ofp.OFPP_FLOOD

        print self.mac_table


        ## send packet to outpuort
        # create actions
        if outport != None:
            # create action
            actions = [ofp_parser.OFPActionOutput(outport)]

            # install flow for next packets
            if outport != ofp.OFPP_FLOOD: 
                print '\tgoing to install flow'
                # create match condition  
                match = ofp_parser.OFPMatch(eth_dst = eth.dst)
                # define instruction for flow
                instruction = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)] 
                # flow priority
                priority = 1
                # timeout - flow is discardes after timeout secs
                timeout = 120

                # decide if buffer is valid - WHY?
                if msg.buffer_id != ofp.OFP_NO_BUFFER:
                     mod = ofp_parser.OFPFlowMod(datapath = datapath, buffer_id = msg.buffer_id, priority = priority, match = match, instructions = instruction, hard_timeout = timeout)
                else:
                     mod = ofp_parser.OFPFlowMod(datapath = datapath, priority = priority, match = match, instructions = instruction, hard_timeout = timeout)
                
                # send msg with flow to switch
                datapath.send_msg(mod)

            # send packet
            print '\tsending packet to port %s' % outport
            # create out object
            out = ofp_parser.OFPPacketOut(
                datapath = datapath, 
                buffer_id = msg.buffer_id, 
                in_port = in_port,
                actions = actions
            )
            # send out object
            datapath.send_msg(out)

