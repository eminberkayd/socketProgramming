#Client program
import socket
import time
import re
HOST = '127.0.0.1'
PORT = 6003
#Create a sockets
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #AF_INET is for IPV4, SOCK_STREAM is for TCP
client_socket.connect((HOST,PORT)) 

while True:
    print("COMMAND FORMAT:\n\nOP=XXX;IND=Ind1,Ind2,..;DATA=Dat1,Dat2,...;\n\n OP = {GET, PUT, CLR, ADD}")
    message = input("Enter the command to be sent: ")
    #Control the message first:
    

    #You can only send byte-like objects through the socket
    client_socket.sendall(bytes(message,'utf-8'))
    time.sleep(0.5)

    #Response data is a byte object with utf-8 encoding
    Response_data=client_socket.recv(1024)
    #Decode the response into a string
    Response_data = Response_data.decode('utf-8')
    print("Decoded Response is:")
    print(Response_data)
