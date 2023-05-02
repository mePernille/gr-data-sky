# DRTP
# first header from cient to server with sin flag
# server sends syn ack
# now connection are etasblish
import time


# 
def stop_and_wait(clientSocket,serverAddr, packet): # denne må tage ind headeren
    while True:

        clientSocket.sendto(packet, serverAddr) # sender en pakke, OBS hvorfor er sendto og recvfrom hvide her?

        data, serverAddr = clientSocket.recvfrom(2400)
        ack_number = 0
        if ack == 1 and seq == ack_number: # hvis den modtager en ack
            ack_number += 1 # forventer at neste pakke skal ha et nummer højere
            continue # fortsetter at sende pakker
        else:
            clientSocket.settimeout(0.5)# venter i 500ms, må tage imot socket også


    

def GBN(clientSocket, serverAddr, packet):
    while True:
        for i in range(0, len(packet), 5): # sender 5 biter av pakken om gangen
            packet.sendto(packet, serverAddr) #sender det til server

        # tjekke pakke nr

def SR():
    print("hei")    
        