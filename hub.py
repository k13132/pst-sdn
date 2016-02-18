# impors
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls

# openflow version 1.3
from ryu.ofproto import ofproto_v1_3

from datetime import datetime


class Hub(app_manager.RyuApp):
    # set OF 1.3
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    # class initialization
    def __init__(self, *args, **kwargs):
        super(Hub, self).__init__(*args, **kwargs)

    # event definition 
    # run on: ofp_event.EventOFPPacketIn
    # when switch state is: MAIN_DISPATCHER (connected to controller)
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        print '--- new packet_in at time %s' % datetime.now()
        ## gain data about incoming mgs/packet
        # incomming msg - packet_in datastructure
        msg = ev.msg
        #print msg

        in_port = msg.match._fields2[0][1]
        
        # datapath - (= switch)
        datapath = msg.datapath
        #print datapath

        # OF protocol
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        #print ofp
        #print ofp_parser

        ## send packet to all interfaces (OFPPK_FLOOD constant)
        # create actions
        actions = [ofp_parser.OFPActionOutput(ofp.OFPP_FLOOD)]
        # create out object
        out = ofp_parser.OFPPacketOut(
            datapath = datapath, 
            buffer_id = msg.buffer_id, 
            in_port = in_port,
            actions = actions
        )
        # send out object
        datapath.send_msg(out)

        print '\tswitch: %s, port: %s' % (datapath.id, in_port)
        print '\tflooded to port OFPP_FLOOD'
