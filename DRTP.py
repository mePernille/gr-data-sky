# DRTP
# first header from cient to server with sin flag
# server sends syn ack
# now connection are etasblish
import time
import socket
from struct import *
import sys


#	def stop_and_wait(clientSocket,serverAddr, packet): # denne må tage ind headeren
#	    while True:
#	        clientSocket.sendto(packet, serverAddr) # sender en pakke, OBS hvorfor er sendto og recvfrom hvide her?
#	
#	        data, serverAddr = clientSocket.recvfrom(2400)
#	        ack_number = 0
#	        if ack == 1 and seq == ack_number: # hvis den modtager en ack
#	            ack_number += 1 # forventer at neste pakke skal ha et nummer højere
#	            continue # fortsetter at sende pakker
#	        else:
#	            clientSocket.settimeout(0.5)# venter i 500ms, må tage imot socket også

header_format = '!IIHH'

def create_packet(seq, ack, flags, win, data):
    header = pack(header_format, seq, ack, flags, win) 

    packet = header + data

    return packet  

def parse_flags(flags):
    #we only parse the first 3 fields because we're not 
    #using rst in our implementation
    syn = flags & (1 << 3)
    ack = flags & (1 << 2)
    fin = flags & (1 << 1)
    return syn, ack, fin


def stop_and_wait(clientSocket, file, serverAddr): # denne må tage ind headeren
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

            while wait_for_ack(clientSocket, seq_number, serverAddr) == False:
                print("lost")
                clientSocket.sendto(packet,serverAddr)
                break


                

            '''
            while not wait_for_ack(clientSocket, seq_number + 1, serverAddr):
                print(f"Packet {seq_number} lost, resending")
                clientSocket.sendto(packet, serverAddr)
               ''' 

            print(f"Packet {seq_number} sent successfully")
            seq_number += 1
            ack_number += 1
            data = f.read(1460)
        
        # Send fin flag
        flags = 2 # fin flag
        fin_packet = create_packet(seq_number, ack_number, flags, window, b'')
        clientSocket.sendto(fin_packet, serverAddr)

            
def wait_for_ack(clientSocket, expected_ack, serverAddr):
    clientSocket.settimeout(0.5) # 500 ms timeout
    try:
        msg, serverAddr = clientSocket.recvfrom(1472)
        print("Recived ack")
        header = msg[:12]
        seq, ack, flags, win = unpack(header_format, header)
        _, ack_flag, _ = parse_flags(flags)
        

        if ack_flag == 4 and ack == expected_ack:
            clientSocket.settimeout(None) # reset timeout
            return True
    
    except socket.timeout:
        print("Timeout, no ACK received")
        return False
        
    return True

    

def GBN(clientSocket, serverAddr, packet):
    while True:
        for i in range(0, len(packet), 5): # sender 5 biter av pakken om gangen
            packet.sendto(packet, serverAddr) #sender det til server

        # tjekke pakke nr

def SR():
    print("hei")    