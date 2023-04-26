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
    serverAddr = (serverip, port)
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
    





def main():

    parser = argparse.ArgumentParser(description="Reliable Transport Protocol", epilog="End of thelp")

    
    if args.server and args.client:
        print("you must either run the server or the client")
        sys.exit()



if __name__ == '__main__':
    main()    
