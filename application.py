import socket
import time
import argparse
import sys
from struct import *
from DRTP import *
import re



# I integer (unsigned long) = 4bytes and H (unsigned short integer 2 bytes)
# see the struct official page for more info
header_format = '!IIHH'


def client(ip, port, file, reli):
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Creating a UDP socket
    serverAddr = (ip, port)
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
    clientSocket.sendto(packet, serverAddr) 


    if reli == 'stop_and_wait':
        stop_and_wait(clientSocket,serverAddr, packet) # sender pakken og clientSocket til stop and wait funktionen

    elif reli == 'GBN':
        GBN(clientSocket, serverAddr, packet)

    elif reli == 'SR':
        SR()            

    clientSocket.close() # lukker client socket, Men er det her vi vil lukke den...

def server(ip, port, reli):
    addr = (ip, port)
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

def check_ip(addres):
    try:
        ipValue = str(addres)
    except:
        raise argparse.ArgumentError('must be different format')
    #https://www.abstractapi.com/guides/python-regex-ip-address
    match = re.match(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", ipValue)
    if not match:
        print("You must enter a valid Ip address")
        sys.exit() # when IP is not valid the system will exit. 
    else:
        return ipValue
    
def check_port(valu): 
    try:
        value = int(valu) #testing the port value
    except ValueError:
        raise argparse.ArgumentTypeError('expected an interger!')
    if (value < 1024 ): 
        print('port must be above 1024')
        
    elif(value > 65535):
        print("port must be les then 65535")    
    else:
        return value 

def main():

    parser = argparse.ArgumentParser(description="Reliable Transport Protocol", epilog="End of thelp")

    parser.add_argument('-s', '--server', action='store_true')
    parser.add_argument('-c', '--client', action='store_true')
    parser.add_argument('-i', '--ip', type=check_ip, default='127.0.0.1')
    parser.add_argument('-p','--port', type=check_port, default=8083)
    parser.add_argument('-f','--file')
    parser.add_argument('-r', '--reliability', type=str, choices=['stop_and_wait','GBN','SR'])
    

    args = parser.parse_args()

    if args.server:
        server(args.ip, args.port, args.reliability)
    
    elif args.client:
        client(args.ip, args.port, args.file, args.reliability)
    
    else:
        print("You need to specify either -s or -c")
        sys.exit()



if __name__ == '__main__':
    main()    
