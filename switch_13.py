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
from ryu.base import app_manager  # basic app
from ryu.controller import ofp_event  # ofp events
from ryu.controller.handler import MAIN_DISPATCHER  # handlers
from ryu.controller.handler import CONFIG_DISPATCHER  # handlers
from ryu.controller.handler import set_ev_cls

# openflow version 1.3
from ryu.ofproto import ofproto_v1_3

# packets
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import ipv6

# other stuff
import time


class Switch(app_manager.RyuApp):
    # set OF 1.3
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        """Initialize class and prepare mac_table"""

        super(Switch, self).__init__(*args, **kwargs)

        # define mac table
        self.mac_table = {}

    def add_flow(self, datapath, priority, match, actions, timeout=10, buffer_id=None):
        """Add flow to datapath"""

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        if buffer_id:
            mod = parser.OFPFlowMod(
                datapath=datapath,
                buffer_id=buffer_id,
                priority=priority,
                match=match,
                instructions=inst
            )
        else:
            mod = parser.OFPFlowMod(
                datapath=datapath,
                priority=priority,
                match=match,
                instructions=inst
            )

        # send to datapath (switch)
        datapath.send_msg(mod)

    # event definition
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def configure_switch(self, ev):
        """
        Run during datapath first connection
            run on: ofp_event.EventOFPSwitchFeatures
            when switch state is: CONFIG_DISPATCHER (establishing connection)
        """

        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions, 0)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
        Handle packet_in events
            run on: ofp_event.EventOFPPacketIn
            when switch state is: MAIN_DISPATCHER (connected to controller)
        """

        print('--- new packet_in at time {}'.format(time.time()))
        # gain data about incoming mgs/packet
        # incomming msg - packet_in datastructure
        msg = ev.msg

        # datapath - (= switch)
        datapath = msg.datapath

        # OF protocol
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # parser parsing
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        # create parsing variables
        in_port = msg.match['in_port']

        print('\tswitch: {}, port: {}'.format(datapath.id, in_port))

        # read ethernet header
        if eth is not None:
            print('\teth: src: {}, dst: {}'.format(eth.src, eth.dst))
            # set mac table enty
            self.mac_table.setdefault(datapath.id, {})
            self.mac_table[datapath.id][eth.src] = in_port

        # read ipv4 protocols
        ip4 = pkt.get_protocol(ipv4.ipv4)
        if ip4 is not None:
            print('\tipv4: src: {}, dst: {}'.format(ip4.src, ip4.dst))

        # decide on outport
        outport = None
        if eth.dst in self.mac_table[datapath.id]:
            print('\trecord exists at switch {} port {}'.format(
                datapath.id,
                self.mac_table[datapath.id][eth.dst]
                )
            )
            outport = self.mac_table[datapath.id][eth.dst]
        elif eth.dst == 'ff:ff:ff:ff:ff:ff':
            print('\tbroadcast mac')
            outport = ofproto.OFPP_FLOOD  # special variable for FLOOD target interface
        else:
            print('\tno record for {} going to flood, sorry'.format(eth.dst))
            outport = ofproto.OFPP_FLOOD

        print('\tMAC table: ' + str(self.mac_table))

        # send packet to outport
        # create actions
        if outport is not None:
            # create action
            actions = [parser.OFPActionOutput(outport)]

            # install flow for next packets
            if outport != ofproto.OFPP_FLOOD:
                print('\tgoing to install flow')
                # create match condition
                match = parser.OFPMatch(eth_dst=eth.dst)
                # flow priority
                priority = 1
                # timeout - flow is discardes after timeout secs
                timeout = 60

                self.add_flow(datapath, priority, match, actions, timeout, msg.buffer_id)

            # send packet
            print('\tsending packet to port {}'.format(outport))
            # create out object
            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=msg.buffer_id,
                in_port=in_port,
                actions=actions
            )
            # send out object
            datapath.send_msg(out)
