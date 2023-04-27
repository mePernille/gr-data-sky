# DRTP
# first header from cient to server with sin flag
# server sends syn ack
# now connection are etasblish


# 
def stop_wait(packet, header): # denne må tage ind headeren
    while True:
        packet.send() # sender en pakke
        if data.resv() == "ACK": # hvis den modtager en ack
            continue # fortsetter at sende pakker
        else:
            socket.settimeout(0.5)# venter i 500ms, må tage imot socket også


    

def GBN():
    while True:
        for i in range(0, len(packet), 5): # sender 5 biter av pakken om gangen
            packet.sendto(serverIP, serverPort) #sender det til server

        # tjekke pakke nr

def SR():
    print("hei")    
        