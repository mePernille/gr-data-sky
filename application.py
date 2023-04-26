import socket
import time
import argparse
import sys
from struct import *



# I integer (unsigned long) = 4bytes and H (unsigned short integer 2 bytes)
# see the struct official page for more info
header_format = '!IIHH'


def client():
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Creating a UDP socket
    serverAddr = ('127.0.0.1', 8083)
    try:
        clientSocket.connect(serverAddr)

    except ConnectionError as e:
        print(e)
        sys.exit()  

    data = b'0' * 1460 # pakken, aka bilde som skal sendes afsted
    sequence_number=1
    acknowledgment_number = 0
    window = 0 # window value should always be sent from reciever-side (from safiquls header.py)
    flags = 0 # we are not going to set any flags when we send a data packet
    packet = create_packet(sequence_number,  acknowledgment_number, flags, window, data)
    clientSocket.send(packet)      

def server():
    addr = ('127.0.0.1', 8083)
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        serverSocket.bind(addr)
    except:
        print("bind failed")
        sys.exit()

    print(f"Server is listening")

    while True:
        msg, clientAddr = serverSocket.recvfrom(1472)
        handle_client(msg, clientAddr) 
    serverSocket.close()



def create_packet(seq, ack, flags, win, data):
    header = pack(header_format, seq, ack, flags, win) 

    packet = header + data

    return packet  

def handle_client(msg, clientAddr):
    #msg = connectionSocket.recv(1472)
    #now let's look at the header
    #we already know that the header is in the first 12 bytes

    header_from_msg = msg[:12]
    print(len(header_from_msg))

    #now we get the header from the parse_header function
    #which unpacks the values based on the header_format that 
    #we specified
    seq, ack, flags, win = unpack(header_format, header_from_msg)
    print(f'seq={seq}, ack={ack}, flags={flags}, recevier-window={win}')

    #now let's parse the flag field
    syn, ack, fin = parse_flags(flags)
    print (f'syn_flag = {syn}, fin_flag={fin}, and ack_flag={ack}')

    if syn == 1:
        print("this is a syn packet")
    
    if ack == 1:
        print("this is an ack packet")
    
    if fin == 1:
        print("this is a fin packet")

    elif syn != 1 and ack != 1 and fin != 1:
        print("no flags are set")

    # Motta data fra klient
    data = msg[12:]
    print(f"Mottatt {len(data)} bytes med data")

def parse_flags(flags):
    #we only parse the first 3 fields because we're not 
    #using rst in our implementation
    syn = flags & (1 << 3)
    ack = flags & (1 << 2)
    fin = flags & (1 << 1)
    return syn, ack, fin


def main():

    parser = argparse.ArgumentParser(description="Reliable Transport Protocol", epilog="End of thelp")

    parser.add_argument('-s', '--server', action='store_true')
    parser.add_argument('-c', '--client', action='store_true')
    

    args = parser.parse_args()

    if args.server:
        server()
    
    elif args.client:
        client()
    
    else:
        print("You need to specify either -s or -c")
        sys.exit()



if __name__ == '__main__':
    main()    
