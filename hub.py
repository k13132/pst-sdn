# impors
from ryu.base import app_manager  # basic app
from ryu.controller import ofp_event  # ofp events
from ryu.controller.handler import MAIN_DISPATCHER  # handlers
from ryu.controller.handler import CONFIG_DISPATCHER  # handlers
from ryu.controller.handler import set_ev_cls

# openflow version 1.3
from ryu.ofproto import ofproto_v1_3

# other stuff
import time


class Hub(app_manager.RyuApp):
    # set OF 1.3
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        """Initialize class"""

        super(Hub, self).__init__(*args, **kwargs)

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

        outport = ofproto.OFPP_FLOOD  # special variable for FLOOD target interface

        actions = [parser.OFPActionOutput(outport)]

        # send packet
        print('\tflooding packet to all interfaces')
        # create out object
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions
        )
        # send out object
        datapath.send_msg(out)
