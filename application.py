import socket
import time
import argparse
import sys
from struct import *
import re
from DRTP import stop_and_wait
from DRTP import GBN
from DRTP import SR # havde problemer med at den ikke fandt funktionerne i DRTP filen hvis de blev importert
from DRTP import create_packet
from DRTP import parse_flags
from DRTP import header_format
from DRTP import handle_test_case
from DRTP import wait_for_ack
from DRTP import send_SR


def client(ip, port, file, reli, test_case):
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Creating a UDP socket
    clientSocket.settimeout(0.5) # 500 ms timeout
    serverAddr = (ip, port)
    try:
        clientSocket.connect(serverAddr)

    except ConnectionError as e:
        print(e)
        sys.exit()  
    
    flags = 8 # 8 = syn flag
    data = b'' # ingen data i syn pakken
    packet = create_packet(0, 0, flags, 0, data) # lager en syn pakke
    clientSocket.sendto(packet, serverAddr) # sender syn pakken

    msg, serverAddr = clientSocket.recvfrom(1472) # venter på syn ack pakken
    header = msg[:12] # tar ut headeren
    seq, ack, flags, win = unpack(header_format, header)
    syn, ack, fin = parse_flags(flags) # tar ut flaggene
    if flags == (8 | 4): # 8 | 4 = syn og ack flag
        print("syn-ack pakke mottatt")
        data = b'' # ingen data i ack pakken
        flags = 4
        ackPacket = create_packet(0, 1, flags, 0, data) # lager en ack pakke
        clientSocket.sendto(ackPacket, serverAddr) # sender ack pakken

    if reli == 'stop_and_wait':
        stop_and_wait(clientSocket, file, serverAddr) # sender clientsocket, filen og serveradressen til stop and wait funktionen

    elif reli == 'GBN':
        GBN(clientSocket, serverAddr, file, test_case)

    elif reli == 'SR':
        send_SR(clientSocket, serverAddr, file, test_case)

    clientSocket.close() # lukker client socket, Men er det her vi vil lukke den...

def server(ip, port, reli, test_case):
    addr = (ip, port)
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
     
    try:
        serverSocket.bind(addr)
    except:
        print("bind failed")
        sys.exit()

    print(f"Server is listening")


    output_file = 'received_file.jpg'
    open(output_file, 'w').close() # sletter filen hvis den allerede eksisterer

    packet_num = 0 # used to count received packets

    received_seq = set() # keep track of received sequence numbers

    while True:
        start_time = time.time()
        elapsed_time = 0
        bytes_sent = 0
        msg, addr = serverSocket.recvfrom(1472)
        header_from_msg = msg[:12]
        data = msg[12:]
        #print(f"Received {len(data)} bytes of data")
        #unpack the header
        seq, ack, flags, win = unpack(header_format, header_from_msg)

        if seq in received_seq:
            continue
        else:
            received_seq.add(seq)

        #parse the flag field
        synflag, ackflag, finflag = parse_flags(flags)

        if synflag == 8:
            print("received syn packet")
            #an acknowledgment packet from the receiver should have no data
            #only the header with acknowledgment number, ack_flag=1, win=6400
            
            sequence_number = 0
            acknowledgment_number = 1   #an ack for the last sequence
            window = 0 # window value should always be sent from the receiver-side

            flags = 12 # we are setting the ack and syn flags

            synAck = create_packet(sequence_number, acknowledgment_number, flags, window, b'')
            print ('Sending syn ack')
            serverSocket.sendto(synAck, addr) # send the packet to the client

        if ackflag == 4:
            print("received ack")
        
        elif synflag == 0 and ackflag == 0:
            if reli == 'SR':
                # Sender ack for første pakke
                acknowledgment_number = seq
                window = 5
                flags = 4 # we are setting the ack flag
                ack_packet = create_packet(0, acknowledgment_number, flags, window, b'')
                serverSocket.sendto(ack_packet, addr)
                print(f"sent ack for packet {seq}")
                SR(serverSocket, data, seq, finflag, output_file, test_case)
            else:  
                packet_num = len(received_seq) -1
                #print(f"seq number is : {seq} and packet number is {packet_num}")
                if seq == packet_num:
                    packet_num +=1 
                    with open(output_file, 'ab') as f:
                        f.write(data) # Skriver data til filen
                        #print(f"skriver {seq} til filen")
                       

                acknowledgment_number = seq
                window = 0
                flags = 4 # we are setting the ack flag

                if handle_test_case(test_case, serverSocket):
                    continue # hvis vi skal skippe en pakke så går vi tilbake til starten av while løkken
                ack = create_packet(seq, acknowledgment_number, flags, window, b'')
                #print ('sending ack')
                serverSocket.sendto(ack, addr) # send the packet to the client
                
                if finflag == 2:
                    print("received fin packet")
                    break
    

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
    parser.add_argument('-t', '--test_case', type=str, choices=['loss', 'skip_ack'])
    

    args = parser.parse_args()

    server_reli = None
    
    if args.server:
        server_reli = args.reliability
        serverSocket = server(args.ip, args.port, args.reliability, args.test_case)
        if args.test_case:
            handle_test_case(args.test_case, serverSocket)
    
    elif args.client:
        client_reli = args.reliability
        clientSocket = client(args.ip, args.port, args.file, args.reliability, args.test_case)
        if args.test_case:
            handle_test_case(args.test_case, clientSocket)
    
    else:
        ("You need to specify either -s or -c")
        sys.exit()

if __name__ == '__main__':
    main()    