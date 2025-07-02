from scapy.all import *
import struct

controller_ip = "10.10.25.102"
node_ip = "10.10.25.119"
divbus_ports = [1201, 1202, 1203, 1204]

noToSegmentHex = {
    0x3f: 0, 0x6: 1, 0x5b: 2, 0x4f: 3, 0x66: 4, 0x6d: 5,  0x7d: 6, 0x07: 7, 0x7f: 8, 0x6f: 9
}


reg_address = [96, 97, 98, 99]

r = rdpcap("chall.pcap")
n = len(r)
x = ""
flag = ""
meters_display_registers = {}
for i in range(n):
    pkt = r[i]
    if Raw in pkt and pkt.haslayer(TCP) and (pkt[IP].src in controller_ip or pkt[IP].dst in node_ip):
        # and (pkt[TCP].sport in divbus_ports or pkt[TCP].dport in divbus_ports):
        payload = pkt[TCP].load

        #print(payload)
        ma = struct.unpack_from('<B', payload, 0)[0]
        nb = struct.unpack_from('<B', payload, 1)[0]
        fc = struct.unpack_from('<B', payload, 2)[0]
        ra = struct.unpack_from('<H', payload, 3)[0]
        #print(fc)
        if fc == 6 and ra in reg_address:
            data = struct.unpack_from('<H', payload, 5)[0]
            if data in noToSegmentHex:
                # add the strs of these 2 outputs convert to int then char
                d = str(noToSegmentHex[data])
                x += d
                if len(x) == 3:
                    if not ma in meters_display_registers:
                        meters_display_registers[ma] = {}
                    if not ra in meters_display_registers[ma]:
                        meters_display_registers[ma][ra] = []
                        
                    c0 = chr(int(x))
                    meters_display_registers[ma][ra] += [c0]
                    x = ""


for k, v in meters_display_registers.items():
    print(f'Meter Address: {k}')
    for k0, v0 in v.items():
        print(f'Register Address: {k0}')
        print(''.join(v0))



