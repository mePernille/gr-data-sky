# This file contains all the reliablity functions and some helper functions to make packets and handle test cases.

import time
import socket
from struct import *
import sys
import random

# The 12 byte header format
header_format = '!IIHH'

# from Safiquls header template
# A function to create a packet with header information and application data
# Arguments: seq - the sequence number of the packet
#            ack - the acknowledgement number of the packet
#            flags - the flags of the packet
#            win - the window of the packet
#            data - the data of the packet
# Returns: the packet with header and data
def create_packet(seq, ack, flags, win, data): 
    header = pack(header_format, seq, ack, flags, win) 
    packet = header + data
    return packet  

# from Safiquls header template
# A function to parse the flags from the header of a packet
# Arguments: flags - the flags of the packet
# Returns: the flag values. syn = 8, ack = 4, fin = 2
def parse_flags(flags):
    # 0 0 0 0 represents no flags
    # 1 0 0 0 syn flag set, and the decimal equivalent is 8
    # 0 1 0 0  ack flag set, and the decimal equivalent is 4
    # 0 0 1 0  fin flag set, and the decimal equivalent is 2
    syn = flags & (1 << 3)
    ack = flags & (1 << 2)
    fin = flags & (1 << 1)
    return syn, ack, fin

# Counters for test cases
ack_counter = 0
seq_counter = 0

# A function to handle test cases
# Arguments: test_case - the test case to be handled
#            clientSocket - the socket to send from
# Returns: True if the packet/ack should be dropped, False if it should be sent
def handle_test_case(test_case, clientSocket):
    # Using global variables to keep track of the counters
    global seq_counter
    global ack_counter

    # Test cases are either 'loss' or 'skip_ack'
    # If the test case is 'loss', we skip every 20th packet
    if test_case == 'loss':
        # Increment the counter for every packet
        seq_counter += 1
        if seq_counter == 20: 
            #print("skip pakke")
            return True # Return True to indicate that the packet should be dropped
        else:
            return False # Return False to indicate that the packet should be sent
    
    # If the test case is 'skip_ack', we skip every 20th ack
    elif test_case == 'skip_ack':
        # Increment the counter for every ack
        ack_counter += 1
        if ack_counter == 20: 
            #print("skip ack")
            return True # Return True to indicate that the ack should be dropped
        else:
            return False # Return False to indicate that the ack should be sent
        
# A function to send a file using stop and wait
# Arguments: clientSocket - the socket to send from
#            file - the file to be sent
#            serverAddr - the address to send to
# Returns: None
def stop_and_wait(clientSocket, file, serverAddr): 
    # start_time, elapsed_time and bytes_sent is used to calculate the bandwidth
    start_time = time.time()
    elapsed_time = 0
    bytes_sent = 0
    # opening the file in read binary mode
    with open(file, 'rb') as f:
        # reading the first 1460 bytes of the file
        data = f.read(1460)
        # setting seq, ack, window and flags before creating the packet
        seq_number = 1 
        ack_number = 0
        window = 0 # in this function the window will not be used
        flags = 0

        # while there is data to be read from the file
        while data:
            # creating the packet
            packet = create_packet(seq_number, ack_number, flags, window, data) 
            #print(f"Packet {seq_number} sent successfully")
            # sending the packet to the server
            clientSocket.sendto(packet, serverAddr)

            # calling the wait_for_Ack to check if we get an ack, then proceeding
            while wait_for_ack(clientSocket, seq_number, serverAddr) == False: 
                #print("lost")
                clientSocket.sendto(packet,serverAddr) 
                # if we don't get an ack, we resend the packet
                # Seq_number should decrease to match the seq number of the packet we are resending
                # But this is not implemented, because handle_test_case can not handle it
                # seq_number -= 1 
                break

            seq_number += 1 # while we receive an ack, the seq number increases 
            ack_number += 1 # the same applies to the ack number
            # reading the next 1460 bytes of the file
            data = f.read(1460)
        
        # Send fin flag
        flags = 2 # fin flag
        fin_packet = create_packet(seq_number, ack_number, flags, window, b'')
        clientSocket.sendto(fin_packet, serverAddr)
        # Calculating bandwidth
        end_time = time.time()
        # If the elapsed time is 0, we set it to 0.0001 to avoid division by 0
        elapsed_time = end_time - start_time
        if elapsed_time == 0:
            elapsed_time = 0.0001
        bytes_sent = seq_number * 1460
        # Calculating bandwidth in Mbit/s
        bandwidth = ((bytes_sent / 1000000) / elapsed_time) * 8
        # Printing the results
        print(f"elapsed time: {'{:.3f}'.format(elapsed_time)} seconds, bytes sent: {bytes_sent} bytes, bandwidth: {'{:.2f}'.format(bandwidth)} Mbit/s")

# A function to wait for an ack
# Arguments: clientSocket - the socket to send from
#            expected_ack - the ack we are expecting
#            serverAddr - the address to send to
# Returns: True if we get the expected ack, False if we don't
def wait_for_ack(clientSocket, expected_ack, serverAddr):
    clientSocket.settimeout(0.5) # 500 ms timeout
    try:
        # receiving the ack
        msg, serverAddr = clientSocket.recvfrom(1472)
        header = msg[:12]
        seq, ack, flags, win = unpack(header_format, header)
        _, ack_flag, _ = parse_flags(flags)
        #print(f"Recived ack {ack}")
        
        # If the ack flag is 4 and the ack is the expected ack, we return True
        if ack_flag == 4 and ack == expected_ack:
            clientSocket.settimeout(None) # reset timeout
            return True
    # If we don't get an ack, we return False
    except socket.timeout:
        print("Timeout, no ACK received")
        return False

    return True

# A function to send a file using GBN
# Arguments: clientSocket - the socket to send from
#            serverAddr - the address to send to
#            file - the file to be sent
#            test_case - the test case to be handled
# Returns: None
def GBN(clientSocket, serverAddr, file, test_case):
    # This function keeps sending packets even though it doesn't get an ack
    # It does not skip a sequence number if test case is loss
    # Start_time, elapsed_time and bytes_sent is used to calculate the bandwidth
    start_time = time.time()
    elapsed_time = 0
    bytes_sent = 0
    # global start is used to keep track of the first packet in the window
    global start

    # opening the file in read binary mode
    with open(file, 'rb') as f:
        # Setting seq, ack, window and flags before creating the packet
        seq_number = 1
        ack_number = 0
        window = 5
        flags = 0
        # unacked_packets is a list of tuples containing the seq number and the packet
        unacked_packets = []
        
        # Start is used to keep track of the first packet in the window
        start = 0
        while True:
            # Reading the next 1460 bytes of the file
            data = f.read(1460)
            # If there is no more data to be read, we break the loop
            if not data:
                break
            # Creating the packet
            packet = create_packet(seq_number, ack_number, flags, window, data)
            # Appending the packet to the list of unacked packets
            unacked_packets.append((seq_number, packet))
            # Number of packets in the list of unacked packets
            number_packets = len(unacked_packets)

            # While the number of packets in the list is less than the window size
            # and the seq number is less than (or equal to) the number of the last packet
            # we send the packet
            while start < number_packets:
                while seq_number < start + window+1:
                    packet = create_packet(seq_number, ack_number, flags, window, data)
                    clientSocket.sendto(packet, serverAddr)
                    #print(f"packet {seq_number} sent")
                    # Incrementing the seq number
                    seq_number += 1

                # If wait_for_ack returns True, we delete the packet from the list
                if wait_for_ack(clientSocket, seq_number, serverAddr) == True:
                    # Increment start to move the window
                    start +=1
                    # Check if we received the correct ack
                    if seq_number == ack_number:
                        # Increment the ack number
                        ack_number +=1
                        # If handle_test_case returns True, we skip a sequence number by adding 2
                        if handle_test_case(test_case, clientSocket):
                            seq_number += 2 
                            continue
                        # Otherwise we increment the seq number by 1
                        else:
                            seq_number += 1 
                # If we don't get an ack, we resend the packet
                else:
                    print("resending")
                    # We resend the whole window by setting the seq number to the start of the window
                    seq_number = start
  
        # Sending fin flag
        flags = 2 # fin flag
        fin_packet = create_packet(seq_number, ack_number, flags, window, b'')
        clientSocket.sendto(fin_packet, serverAddr)
        #print("Sent fin packet")
        # Calculating bandwidth
        end_time = time.time()
        # If the elapsed time is 0, we set it to 0.0001 to avoid division by 0
        elapsed_time = end_time - start_time
        if elapsed_time == 0:
            elapsed_time = 0.0001
        bytes_sent = seq_number * 1460
        # Calculating bandwidth in Mbit/s
        bandwidth = ((bytes_sent / 1000000) / elapsed_time) * 8
        # Printing the results
        print(f"elapsed time: {'{:.3f}'.format(elapsed_time)} seconds, bytes sent: {bytes_sent} bytes, bandwidth: {'{:.2f}'.format(bandwidth)} Mbit/s")
    # Closing the socket
    clientSocket.close()    

# A function to receive a file using SR
# Arguments: serverSocket - the socket to receive from
#            first_data - the first data packet is received in the server function
#            first_seq - the sequence number of the first data packet
#            finflag - the fin flag
#            output_file - the file to write to
#            test_case - the test case to be handled
# Returns: None
def SR(serverSocket, first_data, first_seq, finflag, output_file, test_case):
    # Stores the first received packet in a dictionary
    received_packets = {first_seq: first_data}
    # Setting the fin received flag to False
    fin_received = False

    # While we haven't received the fin flag
    while not fin_received:
        # Receiving the next packet
        msg, addr = serverSocket.recvfrom(1472)
        header = msg[:12]
        data = msg[12:]
        # Unpacking the header
        seq, ack, flags, win = unpack(header_format, header)
        # Parsing the flags
        synflag, ackflag, finflag = parse_flags(flags)

        # If the fin flag is set, we set the fin received flag to True and break the loop
        if finflag == 2:
            fin_received = True
            #print("Fin received")
            break

        # If the seq number is not in the dictionary, we add it to the dictionary
        if seq not in received_packets:
            received_packets[seq] = data
            #print(f"Packet {seq} received")
            # Set the ack number to the seq number
            acknowledgment_number = seq
            window = 5
            flags = 4 # we are setting the ack flag
            # If handle_test_case returns True, we skip the ack
            if handle_test_case(test_case, serverSocket):
                continue # We skip the rest of the loop
            # Otherwise we send the ack
            ack_packet = create_packet(0, acknowledgment_number, flags, window, b'')
            serverSocket.sendto(ack_packet, addr)
            #print(f"ACK {acknowledgment_number} sent")

    # Sorting the dictionary by the seq number and writing the packets to the output file
    with open(output_file, 'ab') as f:
        for seq in sorted(received_packets.keys()):
            f.write(received_packets[seq])
        received_seq_list = sorted(received_packets.keys())
        #print("Liste over nr:", received_seq_list)

# A function to send a file using SR
# Arguments: clientSocket - the socket to send from
#            serverAddr - the address to send to
#            file - the file to be sent
#            test_case - the test case to be handled
# Returns: None
def send_SR(clientSocket, serverAddr, file, test_case):
    # When skip_ack is used, the server does not receive the ack for packet 21.
    # But it does not resend packet 21, it just continues to send packet 25.
    # On test case loss, the server does not receive the ack for packet 21.
    # But it does not resend packet 21, it just continues to send packet 25. Never enters the else: print("resending") part.
    # Start_time, elapsed_time and bytes_sent is used to calculate the bandwidth
    start_time = time.time()
    elapsed_time = 0
    bytes_sent = 0
    # global start is used to keep track of the first packet in the window
    global start

    # opening the file in read binary mode
    with open(file, 'rb') as f:
        # Setting seq, ack, window and flags before creating the packet
        seq_number = 1
        ack_number = 0
        window = 5
        flags = 0
        # unacked_packets is a list of the unaclnowledged packets
        unacked_packets = {}
        start = 1
        data = None

        # Initially fill the window
        while len(unacked_packets) < window:
            data = f.read(1460)
            # Break the loop when the file is fully read
            if not data:
                break
            # Create the packet
            packet = create_packet(seq_number, ack_number, flags, window, data)
            # Add the packet to the list of unacked packets
            unacked_packets[seq_number] = packet
            clientSocket.sendto(packet, serverAddr)
            #print(f"packet {seq_number} sent")
            #print("Current unacked_packets:", list(unacked_packets.keys()))
            # Increment the seq number
            seq_number += 1

        # Start sliding the window
        while True:
            # If the window is full, we wait for an ack
            if wait_for_ack(clientSocket, start, serverAddr):
                # If we get an ack, we delete the packet from the list of unacked packets and increment start and ack number
                del unacked_packets[start]
                start += 1
                ack_number += 1

                # Read new data and send new packet after receiving an ACK
                data = f.read(1460)
                if data:
                    # Create the packet
                    packet = create_packet(seq_number, ack_number, flags, window, data)
                    # Add the packet to the list of unacked packets
                    unacked_packets[seq_number] = packet
                    clientSocket.sendto(packet, serverAddr)
                    #print(f"packet {seq_number} sent")
                    #print("Current unacked_packets:", list(unacked_packets.keys()))
                    # Increment the seq number
                    seq_number += 1
            
            # If we don't get an ack, we resend the packet
            else:
                print("resending")
                # Check if the packet is in the list of unacked packets
                if start in unacked_packets:
                    # If it is, we resend the packet that is first in the window
                    packet = unacked_packets[start]
                    clientSocket.sendto(packet, serverAddr)
                    #print(f"packet {start} sent")
                    #print("Current unacked_packets:", list(unacked_packets.keys()))
                    # Then we increment the seq number so the next packet is next after the window
                    seq_number = (start + window)

            # Break the loop when the file is fully read 
            if not data:
                break

        # Sending fin flag
        flags = 2  # fin flag
        fin_packet = create_packet(seq_number, ack_number, flags, window, b'')
        clientSocket.sendto(fin_packet, serverAddr)
        #print("Sent fin packet")
        # Calculating bandwidth
        end_time = time.time()
        # If the elapsed time is 0, we set it to 0.0001 to avoid division by 0
        elapsed_time = end_time - start_time
        if elapsed_time == 0:
            elapsed_time = 0.0001
        bytes_sent = seq_number * 1460
        # Calculating bandwidth in Mbit/s
        bandwidth = ((bytes_sent / 1000000) / elapsed_time) * 8
        # Printing the results
        print(f"elapsed time: {'{:.3f}'.format(elapsed_time)} seconds, bytes sent: {bytes_sent} bytes, bandwidth: {'{:.2f}'.format(bandwidth)} Mbit/s")