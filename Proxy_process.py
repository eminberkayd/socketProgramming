import re
import pandas as pd
import socket
import time



cached_table = {"Index":[0,1,2,3,4],
                "Data (Integer)":[0,1,2,3,4],
                "Frequency":[0,0,0,0,0]} # Frequency is used to delete the oldest index later

cached_table = pd.DataFrame(cached_table,index=cached_table["Index"])


proxy_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM) # AF_INET is for IPv4, SOCK_STREAM is for TCP
print("...PROXY SERVER SOCKET SUCCESSFULLY CREATED...")

PROXY_HOST = "127.0.0.1" #localhost, loopback interface
PROXY_PORT = 6003

# This line avoids bind() exception: OSError: [Errno 48] Address already in use as you configure address reuse
proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
proxy_socket.bind((PROXY_HOST, PROXY_PORT)) # Proxy socket is bound to specified HOST and PORT
print ("Proxy Socket is bound to IP:",PROXY_HOST," PORT:",PROXY_PORT)
proxy_socket.listen(1) #backlog = 1, so this socket can only make connection with 1 client
print("Listening for connections...")
conn, clientAddress = proxy_socket.accept() # accept method blocks until the connection established
                                            # conn is the new socket which will be used to send and receive data
                                            # clientAddress is tuple which contains client ipv4, and port number 
print ('Connected by client: ', clientAddress)


proxy_2_server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

SERVER_HOST = "127.0.0.5" #localhost
SERVER_PORT = 6006 # non-privileged ports are > 1023

proxy_2_server_socket.connect((SERVER_HOST, SERVER_PORT)) # Proxy is connected to server

def find_data(indexx):
    """
    Find the corresponding Data(Integer) value to given index\n
    indexx = The index number that you want is corresponding Data column value.
    """
    return int(cached_table["Data (Integer)"].loc[cached_table["Index"]==int(indexx)].to_string(index=False))
def inc_freq(indexx):
    """
    Increase frequency content to max freq value + 1,\n
    in order to understand which row is oldest later:
    """
    cached_table["Frequency"].loc[cached_table["Index"]==int(indexx)] = cached_table["Frequency"].max()+1
    
while True:
    try:
        request_from_client = conn.recv(1024)
    except OSError:
        print (clientAddress, 'disconnected')
        proxy_socket.listen(1)
        conn, clientAddress = proxy_socket.accept()
        print('Connected by client: ', clientAddress)
        time.sleep(0.5)

    else:    
        #Decode the request into a string
        request_from_client = request_from_client.decode('utf-8')
        print("The request that come from client:",request_from_client)
        req_list = re.split(';|=', request_from_client)
        if req_list[1]=="GET": #OP=GET
            idxs = req_list[3].split(",")
            data = []
            req_idx = [] # The index numbers whose data will be requested since they are not in proxy.
            for i in idxs:
                if int(i) in cached_table["Index"]: # If the index number is present in proxy
                    inc_freq(int(i))
                    #Append the data to data list:
                    print("Appending data",find_data(i))
                    data.append(find_data(i))
                else: # If the index number is not present in proxy
                    print("The index that will be req from server:",i)
                    req_idx.append(i)
            #Drop the oldest rows as much new rows:
            for j in range(len(req_idx)):
                if cached_table.shape[0]==5: 
                    min_freq_idx = cached_table["Frequency"].idxmin()
                    cached_table.drop(min_freq_idx,inplace=True)
            if (len(req_idx)!=0):
                indices_str = ""
                for k in req_idx:
                    indices_str += k
                    indices_str += ","
                indices_str = indices_str[:-1] # In order to eliminate last comma
                req_to_server = f"OP=GET;IND={indices_str};"
                print("The request to the server from proxy:",req_to_server)
                proxy_2_server_socket.sendall(bytes(req_to_server,'utf-8'))
                time.sleep(1)
                resp_from_server = proxy_2_server_socket.recv(1024).decode('utf-8')#Response will be in the format of:
                                                                                # DATA=num1,num2;
                data_vals_from_server = resp_from_server.split("=")[1].split(",") 
                data.extend(data_vals_from_server)
            data_response_to_client = ""
            for l in data:
                data_response_to_client+=str(l)
                data_response_to_client+=","
            data_response_to_client = ("DATA="+data_response_to_client[:-1]+";")
            print("Response to client:",data_response_to_client)
            conn.sendall(bytes(data_response_to_client,"utf-8"))

            #Put newly acquired rows to proxy table:
            for i in range(len(req_idx)):
                new_data_dict = {"Index":req_idx[i],
                                 "Data (Integer)":data_vals_from_server[i],
                                 "Frequency":cached_table["Frequency"].max()+1} #Increase the freq of newly added row also

            print(cached_table)
        elif req_list[1]=="PUT":#OP=PUT
            #Send the PUT request to server directly
            print("PUT REQUEST FROM CLIENT IS SENT TO THE SERVER:\n",request_from_client)
            proxy_2_server_socket.sendall(bytes(request_from_client,'utf-8'))
            

            idxs = req_list[3].split(",")
            data = req_list[5].split(",")
            
            for i in range(len(idxs)):

                if int(idxs[i]) in cached_table["Index"]:
                    inc_freq(idxs[i])
                    cached_table["Data (Integer)"].loc[cached_table["Index"]==int(idxs[i])] = data[i]
                else:
                    if(cached_table.shape[0]==5):
                        min_freq_idx = cached_table["Frequency"].idxmin()
                        #drop the oldest row to put new row:
                        cached_table.drop(min_freq_idx,inplace=True)
                    if(cached_table.shape[0]==0):
                        new_data_dict = {"Index":int(idxs[i]),
                                        "Data (Integer)":int(data[i]),
                                        "Frequency": 1} #Increase the freq of newly added row also
                    else:
                        new_data_dict = {"Index":int(idxs[i]),
                                        "Data (Integer)":int(data[i]),
                                        "Frequency": cached_table["Frequency"].max()+1} #Increase the freq of newly added row also
                    cached_table.append(new_data_dict,ignore_index=True)
            
            print("Response to client:","PUT command is executed!")
            data_response_to_client = "PUT command is executed!"
            conn.sendall(bytes(data_response_to_client,"utf-8"))

            print(cached_table)
                   
        elif req_list[1]=="CLR":#OP=CLR
            cached_table.drop(cached_table.index,inplace=True) #Clear all rows
            print("All the values in proxy server is cleared!")
            #Sent the CLR request directly from client to server
            proxy_2_server_socket.sendall(bytes(request_from_client,'utf-8'))
            response2client = "All the values in the server is cleared(made zero)"
            # Send Response message to client

            conn.sendall(bytes(response2client,"utf-8"))  
            print(cached_table)

        elif req_list[1]=="ADD":#OP=ADD
            """
            It is very close to GET method, it will just
            simply add the data values it get.
            """
            idxs = req_list[3].split(",")
            data = []
            req_idx = [] # The index numbers whose data will be requested since they are not in proxy.
            for i in idxs:
                if int(i) in cached_table["Index"]: # If the index number is present in proxy
                    inc_freq(int(i))
                    #Append the data to data list:
                    print("Appending data",find_data(i))
                    data.append(find_data(i))
                else: # If the index number is not present in proxy
                    print("The index that will be req from server:",i)
                    req_idx.append(i)
            #Drop the oldest rows as much new rows:
            for j in range(len(req_idx)):
                if cached_table.shape[0]==5: 
                    min_freq_idx = cached_table["Frequency"].idxmin()
                    cached_table.drop(min_freq_idx,inplace=True)
            if (len(req_idx)!=0):
                indices_str = ""
                for k in req_idx:
                    indices_str += k
                    indices_str += ","
                indices_str = indices_str[:-1] # In order to eliminate last comma
                req_to_server = f"OP=GET;IND={indices_str};"
                print("The request to the server from proxy:",req_to_server)
                proxy_2_server_socket.sendall(bytes(req_to_server,'utf-8'))
                time.sleep(1)
                resp_from_server = proxy_2_server_socket.recv(1024).decode('utf-8')#Response will be in the format of:
                                                                                # DATA=num1,num2;
                data_vals_from_server = resp_from_server.split("=")[1].split(",") 
                data.extend(data_vals_from_server)
            data_response_to_client = f"The sum value is: {sum(data)}"
            print("Response to the client:",data_response_to_client)
            conn.sendall(bytes(data_response_to_client,"utf-8"))

            #Put newly acquired rows to proxy table:
            for i in range(len(req_idx)):
                new_data_dict = {"Index":req_idx[i],
                                 "Data (Integer)":data_vals_from_server[i],
                                 "Frequency":cached_table["Frequency"].max()+1} #Increase the freq of newly added row also

            print(cached_table)
                    

            

        
        



