# DRTP
# first header from cient to server with sin flag
# server sends syn ack
# now connection are etasblish
import time

from application import *

<<<<<<< HEAD

def stop_and_wait(clientSocket, file, clientAddr): # denne må tage ind headeren
    with open(file, 'rb') as f:
        print('lager pakke')
        data = f.read(1460)
        seq_number = 1
=======
# 
def stop_and_wait(clientSocket,serverAddr, packet): # denne må tage ind headeren
    while True:

        clientSocket.sendto(packet, serverAddr) # sender en pakke, OBS hvorfor er sendto og recvfrom hvide her?

        data, serverAddr = clientSocket.recvfrom(2400)
>>>>>>> bb3167647c7f2f5811de1084560703ff4cde8955
        ack_number = 0
        window = 0 # window value should always be sent from reciever-side (from safiquls header.py)
        flags = 0 # we are not going to set any flags when we send a data packet

        while data:
            packet = create_packet(seq_number, ack_number, flags, window, data)
            print('sender pakke')
            clientSocket.send(packet)

            while not wait_for_ack(clientSocket, seq_number + 1, clientAddr):
                print(f"Packet {seq_number} lost, resending")
                clientSocket.send(packet)
                
            print(f"Packet {seq_number} sent successfully")
            seq_number += 1
            ack_number += 1
            data = f.read(1460)
        
        # Send fin flag
        flags = 2 # fin flag
        fin_packet = create_packet(seq_number, ack_number, flags, window, b'')
        clientSocket.send(fin_packet)
            
def wait_for_ack(clientSocket, expected_ack, clientAddr):
    clientSocket.settimeout(0.5) # 500 ms timeout
    try:
        msg, _ = clientSocket.recvfrom(1472)
        header = msg[:12]
        seq, ack, flags, win = unpack(header_format, header)
        _, ack_flag, _ = parse_flags(flags)

        if ack_flag == 4 and ack == expected_ack:
            clientSocket.settimeout(None) # reset timeout
            return True
    
    except socket.timeout:
        print("Timeout, no ACK received")
        return False
        
    return False

    

def GBN(clientSocket, serverAddr, packet):
    while True:
        for i in range(0, len(packet), 5): # sender 5 biter av pakken om gangen
            packet.sendto(packet, serverAddr) #sender det til server

        # tjekke pakke nr

def SR():
    print("hei")    
        