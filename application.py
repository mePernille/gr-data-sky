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



def client(ip, port, file, reli):
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Creating a UDP socket
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
    header_from_msg = unpack(header_format, header) # pakker ut headeren
    syn, ack, fin = parse_flags(header_from_msg[2]) # tar ut flaggene
    if header_from_msg[2] == (8 | 4): # 8 | 4 = syn og ack flag
        print("syn-ack pakke mottatt")
        data = b'' # ingen data i ack pakken
        flags = 4
        ackPacket = create_packet(0, 1, flags, 0, data) # lager en ack pakke
        clientSocket.sendto(ackPacket, serverAddr) # sender ack pakken


    if reli == 'stop_and_wait':
        
        stop_and_wait(clientSocket, file, serverAddr) # sender clientsocket, filen og serveradressen til stop and wait funktionen

    elif reli == 'GBN':
        GBN(clientSocket, serverAddr, packet)

    elif reli == 'SR':
        with open(file, 'rb') as f:
            print('lager pakke')
            data = f.read(1460)
            seq_number = 1
            ack_number = 0
            window = 0
            flags = 0

            while data:
                packet = create_packet(seq_number, ack_number, flags, window, data)
                print('sender pakke')
                clientSocket.sendto(packet, serverAddr) # Bruker sendto siden vi sender filen over UDP
                print(f"Packet {seq_number} sent successfully")
                seq_number += 1
                ack_number += 1
                data = f.read(1460)       

            # Send fin flag
            flags = 2 # fin flag
            fin_packet = create_packet(seq_number, ack_number, flags, window, b'')
            clientSocket.sendto(fin_packet, serverAddr)    

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

    output_file = 'received_file.jpg'
    open(output_file, 'w').close() # sletter filen hvis den allerede eksisterer

    while True:
        msg, addr = serverSocket.recvfrom(1472)

        header_from_msg = msg[:12]
        print(len(header_from_msg))

        data = msg[12:]
        print(f"Received {len(data)} bytes of data")
        #unpack the header
        seq, ack, flags, win = unpack(header_format, header_from_msg)

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
            print (f'sending an acknowledgment packet of header size={len(synAck)}')
            serverSocket.sendto(synAck, addr) # send the packet to the client

        if ackflag == 4:
            print("received ack packet")
        
        elif synflag == 0 and ackflag == 0:
            if reli == 'SR':
                SR(serverSocket, data, seq, finflag, output_file)
            else:    
                with open(output_file, 'ab') as f:
                    f.write(data) # Skriver data til filen

                acknowledgment_number = seq
                window = 0
                flags = 4 # we are setting the ack flag

                ack = create_packet(seq, acknowledgment_number, flags, window, b'')
                print (f'sending an acknowledgment packet of header size={len(ack)}')
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