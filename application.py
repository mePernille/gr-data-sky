import socket
import time
import argparse
import sys
from struct import *
import re
from DRTP import stop_and_wait
from DRTP import GBN
from DRTP import SR
from DRTP import create_packet
from DRTP import parse_flags
from DRTP import header_format
from DRTP import handle_test_case
from DRTP import wait_for_ack
from DRTP import send_SR

# A function that runs a client 
# Arguments: ip - ip address of the server
#            port - port number of the server
#            file - file to be sent
#            reli - reliability protocol to be used
#            test_case - test case to be used
# Returns: None
def client(ip, port, file, reli, test_case):
    # Creating a UDP client socket
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    # Setting a timeout for the socket
    clientSocket.settimeout(0.5) # 500 ms timeout
    # Setting the server address
    serverAddr = (ip, port)
    # Connecting to the server
    try:
        clientSocket.connect(serverAddr)
    # If the connection fails, print the error and exit the program
    except ConnectionError as e:
        print(e)
        sys.exit()  
    
    # Sending a syn-packet to the server
    flags = 8 # 8 = syn flag
    data = b'' # no data in the syn-packet
    packet = create_packet(0, 0, flags, 0, data) # creating a syn-packet
    clientSocket.sendto(packet, serverAddr) # sending it

    # Waiting for a syn-ack packet from the server
    msg, serverAddr = clientSocket.recvfrom(1472)
    # Unpacking the header, the header is 12 bytes
    header = msg[:12] 
    seq, ack, flags, win = unpack(header_format, header)
    # Parsing the flags
    syn, ack, fin = parse_flags(flags) 
    if flags == (8 | 4): # 8 | 4 = syn and ack flag
        #print("syn-ack packet received")
        data = b'' # no data in the ack packet
        flags = 4
        # Creating an ack packet
        ackPacket = create_packet(0, 1, flags, 0, data)
        # Sending the ack packet to the server
        clientSocket.sendto(ackPacket, serverAddr) 

    # The rest of the packages are handled by the reliability protocol
    # If the reliability protocol is stop_and_wait
    if reli == 'stop_and_wait':
        stop_and_wait(clientSocket, file, serverAddr) # sending clientsocket, file and serveraddress

    # If the reliability protocol is GBN
    elif reli == 'GBN':
        GBN(clientSocket, serverAddr, file, test_case) # sending clientsocket, serveraddress, file and test_case

    # If the reliability protocol is SR
    elif reli == 'SR':
        send_SR(clientSocket, serverAddr, file, test_case) # sending clientsocket, serveraddress, file and test_case

    clientSocket.close() # closing the client socket

# A function that runs a server
# Arguments: ip - ip address of the server
#            port - port number of the server
#            reli - reliability protocol to be used
#            test_case - test case to be used
# Returns: None
def server(ip, port, reli, test_case):
    # Creating a UDP server socket
    addr = (ip, port)
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Binding the socket to the address
    try:
        serverSocket.bind(addr)
    # If the binding fails, print the error and exit the program
    except:
        print("bind failed")
        sys.exit()

    # Message to be printed when the server is running
    print(f"Server is listening")

    # Creating a file to write the received data to
    output_file = 'received_file.jpg'
    # Clearing the file if it already exists
    open(output_file, 'w').close() 
    packet_num = 0 # used to count received packets
    received_seq = set() # keep track of received sequence numbers

    # Receiving packets from the client
    while True:
        # Setting start time for the bandwidth calculation
        start_time = time.time()
        elapsed_time = 0
        bytes_sent = 0
        # Receiving a packet from the client
        msg, addr = serverSocket.recvfrom(1472)
        # Unpacking the header, the header is 12 bytes
        header_from_msg = msg[:12]
        # Unpacking the data, the data is the rest of the packet
        data = msg[12:]
        seq, ack, flags, win = unpack(header_format, header_from_msg)

        # Checking if the packet has already been received
        if seq in received_seq:
            continue
        # If the packet has not been received, add it to the set
        else:
            received_seq.add(seq)

        #parse the flag field
        synflag, ackflag, finflag = parse_flags(flags)

        # Checking if the packet is a syn packet
        if synflag == 8:
            #print("received syn")            
            sequence_number = 0
            acknowledgment_number = 1   # an ack for the last sequence
            window = 0 # window value 
            flags = 12 # we are setting the ack and syn flags
            # Creating a syn-ack packet
            synAck = create_packet(sequence_number, acknowledgment_number, flags, window, b'')
            #print ('Sending syn ack')
            serverSocket.sendto(synAck, addr) # send the packet to the client

        # Checking if the packet is an ack packet
        if ackflag == 4:
            #print("received ack")
            continue

        # Handling the rest of the packets where synflag and ackflag are both 0
        elif synflag == 0 and ackflag == 0:
            # Checking if the reliability protocol is SR
            if reli == 'SR':
                # Sending an ack for the first packet
                acknowledgment_number = seq
                window = 5
                flags = 4 # we are setting the ack flag
                # Creating an ack packet
                ack_packet = create_packet(0, acknowledgment_number, flags, window, b'')
                serverSocket.sendto(ack_packet, addr)
                #print(f"sent ack for packet {seq}")
                # Calling the SR function to handle the rest of the packets
                SR(serverSocket, data, seq, finflag, output_file, test_case)
            # Handling packages for the stop_and_wait and GBN reliability protocols
            else:  
                # Checking if the packet is the next packet in the sequence
                packet_num = len(received_seq) -1
                # Checking if the packet is the next packet in the sequence
                if seq == packet_num:
                    packet_num +=1 
                    # Writing the data to the file
                    with open(output_file, 'ab') as f:
                        f.write(data) 
                
                # Setting the acknowledgment number for the ack as the sequence number of the packet
                acknowledgment_number = seq
                window = 0
                flags = 4 # we are setting the ack flag

                # If handle_test_case returns true, we skip sending the ack
                if handle_test_case(test_case, serverSocket):
                    continue # skip sending the ack
                # Creating and sending the ack
                ack = create_packet(seq, acknowledgment_number, flags, window, b'')
                serverSocket.sendto(ack, addr)

                # Checking if the packet is the last packet
                if finflag == 2: # checking if the finflag is set.
                    #print("received fin packet")
                    break
    
# A function that checks if the ip address is valid
# Arguments: address - ip address to be checked
# Returns: ipValue - the ip address if it is valid
#          sys.exit() - if the ip address is not valid
def check_ip(address):
    # Checking if the ip address is valid
    try:
        ipValue = str(address)
    # If the ip address is not valid, print the error and exit the program
    except:
        raise argparse.ArgumentError(None, 'must be different format')
    #https://www.abstractapi.com/guides/python-regex-ip-address
    match = re.match(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", ipValue)
    if not match:
        print("You must enter a valid Ip address")
        sys.exit() # when IP is not valid the system will exit. 
    # If the ip address is valid, return it
    else:
        return ipValue

# A function that checks if the port number is valid
# Arguments: valu - port number to be checked
# Returns: value - the port number if it is valid
#          sys.exit() - if the port number is not valid
def check_port(valu): 
    # Checking if the port number is valid
    try:
        value = int(valu) 
    # If the port number is not valid, print the error and exit the program
    except ValueError:
        raise argparse.ArgumentTypeError('expected an interger!')
    if (value < 1024 ): 
        print('port must be above 1024')
        
    elif(value > 65535):
        print("port must be less then 65535")    
    # If the port number is valid, return it
    else:
        return value 
# A main function that runs the program
# Arguments: None
# Returns: None
def main():
    # Creating an argument parser
    parser = argparse.ArgumentParser(description="Reliable Transport Protocol", epilog="End of thelp")
    # Adding arguments to the parser
    parser.add_argument('-s', '--server', action='store_true')
    parser.add_argument('-c', '--client', action='store_true')
    parser.add_argument('-i', '--ip', type=check_ip, default='127.0.0.1')
    parser.add_argument('-p','--port', type=check_port, default=8083)
    parser.add_argument('-f','--file')
    parser.add_argument('-r', '--reliability', type=str, choices=['stop_and_wait','GBN','SR'])
    parser.add_argument('-t', '--test_case', type=str, choices=['loss', 'skip_ack'])
    
    # Parsing the arguments
    args = parser.parse_args()

    # Checking the user inputs
    # If the user entered -s, run the server    
    if args.server:
        serverSocket = server(args.ip, args.port, args.reliability, args.test_case)
        # If the user entered a test case, call handle_test_case
        if args.test_case:
            handle_test_case(args.test_case, serverSocket)
    # If the user entered -c, run the client
    elif args.client:
        clientSocket = client(args.ip, args.port, args.file, args.reliability, args.test_case)
        # If the user entered a test case, call handle_test_case
        if args.test_case:
            handle_test_case(args.test_case, clientSocket)
    # If the user did not enter -s or -c, print an error and exit the program
    else:
        ("You need to specify either -s or -c")
        sys.exit()

# Calling the main function
if __name__ == '__main__':
    main()    