#!/usr/bin/env python

from scapy.all import *
from scapy.layers.dns import DNSRR, DNS, DNSQR
from scapy_http import http
import pprint
from collections import defaultdict

pp = pprint.PrettyPrinter(indent=4)

stars = lambda n: "*" * n


try:
    interface = raw_input("[*] Enter Desired Interface: ")
except KeyboardInterrupt:
    print "[*] User Requested Shutdown..."
    print "[*] Exiting..."
    sys.exit(1)

observed = []

def sniffmgmt(p):
    #pp.pprint(pkt_to_dict(p))
    if p.haslayer(http.HTTPRequest):
        http_layer = p.getlayer(http.HTTPRequest)
        ip_layer = p.getlayer(IP)
        print '\n{0} -> HTTP {1[Method]} {1[Host]}{1[Path]}'.format(p.getlayer(Ether).src, http_layer.fields)
        if "POST" in str(p):
            print "\n".join((stars(40) + "POST PACKET" + stars(40),
                  "\n".join(p.sprintf("{Raw:%Raw.load%}").split(r"\r\n")),
                  stars(91)))
    if p.haslayer(DNS):
        if p.qdcount > 0 and isinstance(p.qd, DNSQR):
            name = p.qd.qname
            if name not in observed:
                print p.getlayer(Ether).src + " -> DNS -> " + name
                observed.append(name)

print "Detecting:"
sniff(prn=sniffmgmt)