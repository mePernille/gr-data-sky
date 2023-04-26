import socket
import time
import argparse
import sys
from header import *


# SAFR  - sending an ack flag = 4
# S - sin (8)
# A - ack (4)
# F - flag (2)
# R - resive window(1)

def client():
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Creating a UDP socket
    serverAddr = ('127.0.0.1', 8083)
    try:
        clientSocket.connect(serverAddr)

    except ConnectionError as e:
        print(e)
        sys.exit()    

def server():
    Addr = ('127.0.0.1', 8083)
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        serverSocket.bind(Addr)
    except:
        print("bind failed")
        sys.exit()

    serverSocket.listen()
    print(f"Server is listening")

    while True:
        connectionSocket, addr = serverSocket.accept()
        handle_client(connectionSocket, addr)    
    serverSocket.close()

def handle_client(connectionSocket, addr):
    msg = connectionSocket.recv(1472)
    #now let's look at the header
    #we already know that the header is in the first 12 bytes

    header_from_msg = msg[:12]
    print(len(header_from_msg))

    #now we get the header from the parse_header function
    #which unpacks the values based on the header_format that 
    #we specified
    seq, ack, flags, win = parse_header (header_from_msg)
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

    else:
        print("no flags are set")





    #let's extract the data_from_msg that holds
    #the application data of 1460 bytes
    data_from_msg = msg[12:]
    print (len(data_from_msg))




def main():

    parser = argparse.ArgumentParser(description="Reliable Transport Protocol", epilog="End of thelp")

    parser.add_argument('-s', '--server', action='store_true')
    parser.add_argument('-c', '--client', action='store_true')
    

    args = parser.parse_args()

    if args.server and args.client:
        print("you must either run the server or the client")
        sys.exit()

    if args.server:
        server(args.server)



if __name__ == '__main__':
    main()    
