# imports
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls

# openflow version 1.3
from ryu.ofproto import ofproto_v1_3

# timestamp
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
        ## get data about incoming mgs
        print '--- new packet_in at %s' % datetime.now()

        # incomming msg - OFPPacketIn
        msg = ev.msg
        print msg
        
        # datapath - (= switch)
        datapath = msg.datapath
        print datapath

        # OF protocol
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        print ofp
        print ofp_parser

        ## add your code here && enjoy PST
