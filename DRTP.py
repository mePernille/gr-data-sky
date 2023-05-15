# This file contains all the reliablity functions and some helper functions to make packets and handle test cases.

import time
import socket
from struct import *
import sys
import random


header_format = '!IIHH'

# from Safiqul header templet
def create_packet(seq, ack, flags, win, data): 
    header = pack(header_format, seq, ack, flags, win) 

    packet = header + data

    return packet  
# from Safiqul header templet
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
        if seq_counter == 20: # Skipper hver 20. pakke
            #print("skip pakke")
            return True # Returnerer True for å indikere at pakken skal droppes
        else:
            return False
    elif test_case == 'skip_ack':
        ack_counter += 1
        if ack_counter == 20: # Skipper hver 20. ack
            #print("skip ack")
            return True # Returnerer True for å indikere at ack skal droppes
        else:
            return False # Returnerer False for å indikere at ack skal sendes
        

def stop_and_wait(clientSocket, file, serverAddr): # taking in the socket to send from, the file we want to send, and the server addres we are sending to
    # Sender ny pakke, men ikke med samme seq nr. Det fungerer ikke å endre
    # på grunn av test casen
    start_time = time.time()
    elapsed_time = 0
    bytes_sent = 0
    with open(file, 'rb') as f:
        #print('lager pakke')
        data = f.read(1460)
        # setting seq, ack, window and flags before creating the packet
        seq_number = 1 
        ack_number = 0
        window = 0 # in this function the window will not be used
        flags = 0

        while data:
            packet = create_packet(seq_number, ack_number, flags, window, data) # creating the packet
            #print(f"Packet {seq_number} sent successfully")
            clientSocket.sendto(packet, serverAddr) # the client sends the packet, using the  build in function sendto(), since its UDP

            # calling the wait_for_Ack to chek if we get an ack, then proceeding
            while wait_for_ack(clientSocket, seq_number, serverAddr) == False: 
                #print("lost")
                clientSocket.sendto(packet,serverAddr) # if we do not receive an ack.... ?
                #seq_number -= 1 Skulle ha vært der for å sende pakken på nytt, men det funker ikke med test casen
                break

            seq_number += 1 # while we receive an ack, the seq number increases 
            ack_number += 1 # the same applys to the ack number
            data = f.read(1460)
        
        # Send fin flag
        flags = 2 # fin flag
        fin_packet = create_packet(seq_number, ack_number, flags, window, b'')
        clientSocket.sendto(fin_packet, serverAddr)
        end_time = time.time()
        elapsed_time = end_time - start_time
        if elapsed_time == 0:
            elapsed_time = 0.0001
        bytes_sent = seq_number * 1460
        bandwidth = ((bytes_sent / 1000000) / elapsed_time) * 8
        print(f"elapsed time: {'{:.3f}'.format(elapsed_time)} seconds, bytes sent: {bytes_sent} bytes, bandwidth: {'{:.2f}'.format(bandwidth)} Mbit/s")

            
def wait_for_ack(clientSocket, expected_ack, serverAddr):
    clientSocket.settimeout(0.5) # 500 ms timeout
    try:
        msg, serverAddr = clientSocket.recvfrom(1472)
        header = msg[:12]
        seq, ack, flags, win = unpack(header_format, header)
        _, ack_flag, _ = parse_flags(flags)
        #print(f"Recived ack {ack}")
        

        if ack_flag == 4 and ack == expected_ack:
            clientSocket.settimeout(None) # reset timeout
            return True
    
    except socket.timeout:
        print("Timeout, no ACK received")
        return False
        
    return True

def GBN(clientSocket, serverAddr, file, test_case):
    # Når man kjører skip_ack så fortsetter den å sende pakker selv om den ikke får ack
    # Den hopper over ack 20 og sender så pakke 24.
    # Med test case loss så printer server skip pakke, men GBN sender fortsatt pakke 20
    start_time = time.time()
    elapsed_time = 0
    bytes_sent = 0
    global start

    with open(file, 'rb') as f:
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

            while start < number_packets:
                while seq_number < start + window+1:
                    packet = create_packet(seq_number, ack_number, flags, window, data)
                    clientSocket.sendto(packet, serverAddr)
                    #print(f"packet {seq_number} sent")
                    seq_number += 1

                if wait_for_ack(clientSocket, seq_number, serverAddr) == True:
                    start +=1
                    if seq_number == ack_number:
                        ack_number +=1
                        if handle_test_case(test_case, clientSocket):
                            seq_number += 2 # hvis vi skal skippe en pakke så øker vi seq_number med 2
                            continue
                        else:
                            seq_number += 1
                    #print(f"seq nr er : {seq_number} start nr er : {start}")    
                else:
                    print("resending")
                    seq_number = start
  

        flags = 2 # fin flag
        fin_packet = create_packet(seq_number, ack_number, flags, window, b'')
        clientSocket.sendto(fin_packet, serverAddr)
        #print("Sent fin packet")
        end_time = time.time()
        elapsed_time = end_time - start_time
        if elapsed_time == 0:
            elapsed_time = 0.0001
        bytes_sent = seq_number * 1460
        bandwidth = ((bytes_sent / 1000000) / elapsed_time) * 8
        print(f"elapsed time: {'{:.3f}'.format(elapsed_time)} seconds, bytes sent: {bytes_sent} bytes, bandwidth: {'{:.2f}'.format(bandwidth)} Mbit/s")

    clientSocket.close()    

def SR(serverSocket, first_data, first_seq, finflag, output_file, test_case):
    # Skip ack printer skip ack, og den hopper over ack 21.
    # Den mottar ikke ack 21 men det kommer ingen feilmelding og den fortsetter å sende pakke 25
    # på test case loss mottar den ikke ack 21, men det kommer ingen feilmelding.
    # Server mottar alle pakker
    received_packets = {first_seq: first_data}
    fin_received = False

    while not fin_received:
        msg, addr = serverSocket.recvfrom(1472)
        header = msg[:12]
        data = msg[12:]
        seq, ack, flags, win = unpack(header_format, header)
        synflag, ackflag, finflag = parse_flags(flags)

        if finflag == 2:
            fin_received = True
            #print("Fin received")
            break

        if seq not in received_packets:
            received_packets[seq] = data
            #print(f"Packet {seq} received")
            acknowledgment_number = seq
            window = 5
            flags = 4 # we are setting the ack flag
            if handle_test_case(test_case, serverSocket):
                continue # hvis vi skal skippe en ack så går vi tilbake til starten av while løkken
            ack_packet = create_packet(0, acknowledgment_number, flags, window, b'')
            serverSocket.sendto(ack_packet, addr)
            #print(f"ACK {acknowledgment_number} sent")

            
    with open(output_file, 'ab') as f:
        for seq in sorted(received_packets.keys()):
            f.write(received_packets[seq])
        received_seq_list = sorted(received_packets.keys())
        #print("Liste over nr:", received_seq_list)
        #print("All packets received")

def send_SR(clientSocket, serverAddr, file, test_case):
    # Sender filen, men når jeg kjører skip_ack så hopper den bare over ack 21 uten å 
    # gå inn i else: resending. 
    start_time = time.time()
    elapsed_time = 0
    bytes_sent = 0
    global start

    with open(file, 'rb') as f:
        seq_number = 1
        ack_number = 0
        window = 5
        flags = 0
        unacked_packets = {}

        start = 1
        data = None

        # Initially fill the window
        while len(unacked_packets) < window:
            data = f.read(1460)
            if not data:
                break
            packet = create_packet(seq_number, ack_number, flags, window, data)
            unacked_packets[seq_number] = packet
            clientSocket.sendto(packet, serverAddr)
            #print(f"packet {seq_number} sent")
            #print("Current unacked_packets:", list(unacked_packets.keys()))
            seq_number += 1

        # Start sliding the window
        while True:
            if wait_for_ack(clientSocket, start, serverAddr):
                del unacked_packets[start]
                start += 1
                ack_number += 1

                # Read new data and send new packet after receiving an ACK
                data = f.read(1460)
                if data:
                    packet = create_packet(seq_number, ack_number, flags, window, data)
                    unacked_packets[seq_number] = packet
                    clientSocket.sendto(packet, serverAddr)
                    #print(f"packet {seq_number} sent")
                    #print("Current unacked_packets:", list(unacked_packets.keys()))
                    seq_number += 1
            else:
                print("resending")
                if start in unacked_packets:
                    packet = unacked_packets[start]
                    clientSocket.sendto(packet, serverAddr)
                    #print(f"packet {start} sent")
                    #print("Current unacked_packets:", list(unacked_packets.keys()))
                    seq_number = (start + window)

            # Break the loop when the file is fully read 
            if not data:
                break

        flags = 2  # fin flag
        fin_packet = create_packet(seq_number, ack_number, flags, window, b'')
        clientSocket.sendto(fin_packet, serverAddr)
        #print("Sent fin packet")
        end_time = time.time()
        elapsed_time = end_time - start_time
        if elapsed_time == 0:
            elapsed_time = 0.0001
        bytes_sent = seq_number * 1460
        bandwidth = ((bytes_sent / 1000000) / elapsed_time) * 8
        print(f"elapsed time: {'{:.3f}'.format(elapsed_time)} seconds, bytes sent: {bytes_sent} bytes, bandwidth: {'{:.2f}'.format(bandwidth)} Mbit/s")