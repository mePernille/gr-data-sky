# DRTP
# first header from cient to server with sin flag
# server sends syn ack
# now connection are etasblish


# 
def stop_and_wait(clientSocket, packet): # denne må tage ind headeren
    while True:
        clientSocket.send(packet) # sender en pakke

        data = clientSocket.recv(2400)
        ack_number = 0
        if ack == 1 and seq == ack_number: # hvis den modtager en ack
            ack_number += 1 # forventer at neste pakke skal ha et nummer højere
            continue # fortsetter at sende pakker
        else:
            clientSocket.settimeout(0.5)# venter i 500ms, må tage imot socket også


    

def GBN():
    while True:
        for i in range(0, len(packet), 5): # sender 5 biter av pakken om gangen
            packet.sendto(serverIP, serverPort) #sender det til server

        # tjekke pakke nr

def SR():
    print("hei")    
        