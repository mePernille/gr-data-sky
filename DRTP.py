# DRTP
# first header from cient to server with sin flag
# server sends syn ack
# now connection are etasblish
import time
import socket
from struct import *
import sys
import random

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

ack_counter = 0
seq_counter = 0

def handle_test_case(test_case, clientSocket):
    global seq_counter
    global ack_counter
    if test_case == 'loss':
        seq_counter += 1
        if seq_counter == 20: # Skipper hver 14. pakke
            seq_counter = 0
            return True # Returnerer True for å indikere at pakken skal droppes
        else:
            return False
    elif test_case == 'skip_ack':
        ack_counter += 1
        if ack_counter == 20: # Skipper hver 14. ack
            ack_counter = 0
            return True # Returnerer True for å indikere at ack skal droppes
        else:
            return False # Returnerer False for å indikere at ack skal sendes

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
  

def GBN(clientSocket, serverAddr, file):
    global start

    with open(file, 'rb') as f:
        print('Creating packets')
        seq_number = 1
        ack_number = 0
        window = 5
        flags = 0
        unacked_packets = []
        

        start = 0
        while True:
            data = f.read(1460)
            if not data:
                break
            packet = create_packet(seq_number, ack_number, flags, window, data)
            unacked_packets.append((seq_number, packet))
            
            number_packets = len(unacked_packets)
            print(start + window)

            while start < number_packets:
                while seq_number < start + window+1:
                    packet = create_packet(seq_number, ack_number, flags, window, data)

                    clientSocket.sendto(packet, serverAddr)
                    print(f"packet {seq_number} sent")
                    seq_number += 1

                if wait_for_ack(clientSocket, seq_number, serverAddr) == True:
                    start +=1
                    if seq_number == ack_number:
                        ack_number +=1
                        seq_number += 1
                    print(f"seq nr: {seq_number} start nr : {start}")    
                else:
                    print("resending")
                    seq_number = start
  

        flags = 2 # fin flag
        fin_packet = create_packet(seq_number, ack_number, flags, window, b'')
        clientSocket.sendto(fin_packet, serverAddr)
        print("Sent fin packet")

    clientSocket.close()    

def SR(serverSocket, first_data, first_seq, finflag, output_file):
    received_packets = {first_seq: first_data}
    #expected_seq = 1
    fin_received = False

    while not fin_received:
        msg, addr = serverSocket.recvfrom(1472)
        header = msg[:12]
        data = msg[12:]
        seq, ack, flags, win = unpack(header_format, header)
        synflag, ackflag, finflag = parse_flags(flags)

        if finflag == 2:
            fin_received = True
            print("Fin received")
            break

        if seq not in received_packets:
            received_packets[seq] = data
            print(f"Packet {seq} received")
            acknowledgment_number = seq
            window = 5
            flags = 4 # we are setting the ack flag
            ack_packet = create_packet(0, acknowledgment_number, flags, window, b'')
            serverSocket.sendto(ack_packet, addr)

        #if seq == expected_seq:
        #    while expected_seq in received_packets:
        #        expected_seq += 1
            
    with open(output_file, 'ab') as f:
        for seq in sorted(received_packets.keys()):
            f.write(received_packets[seq])
        received_seq_list = sorted(received_packets.keys())
        print("Liste over nr:", received_seq_list)
        print("All packets received")