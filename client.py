import socket
import threading
import time
import os
from datetime import datetime
class Client:
    def __init__(self, server_ip, server_port, client_port):
        ip = "127.0.0.1"
        self.UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.UDPClientSocket.bind((ip, client_port))
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_port = client_port
        self.table = {}
        self.bufferSize = 1024
        self.isreg = False
        self.is_waiting = False        
        self.resend_time = 5
    def run(self, name):
        try:
            self.register(name)
            input_thread = threading.Thread(target=self.input_prompt)
            # input_thread.daemon = True
            recv_thread = threading.Thread(target=self.receive)
            recv_thread.daemon = True
            input_thread.start()
            recv_thread.start()
            input_thread.join()
            recv_thread.join()
        except KeyboardInterrupt:
            os._exit(0)

    def input_prompt(self):
        while True:
            command = input(">>> ").split()
            if len(command) == 0:
                continue
            action = command[0]
            if self.isreg:
                if action == "send":
                    if len(command) < 3:
                        print(">>> Usage: send <receiver_name> message")
                    else:
                        name, message = command[1], command[2]
                        for i in range(3, len(command)):
                            message += " " + command[i]
                        self.send_to_client(name, message)
                elif action == "dereg":
                    if len(command) != 2:
                        print(">>> Usage: dereg <user_name>")
                    else:
                        self.dereg(command[1])
                elif action == "reg":
                    print(">>> You are already registered!")
                elif action == "send_all":
                    if len(command) < 2:
                        print(">>> Usage: dereg <user_name>")
                    else:
                        message = " ".join(command[1:])                    
                        self.send_channel_message(message)
                else:
                    print(">>> Command not recognized. Retry!")
            else:
                if action == "reg":
                    if len(command) < 2:
                        print(">>> Usage: reg [nickname]", flush=True)
                    else:
                        self.register_back(command[1])
                else:
                    print("You are offline. Register first\n", end="", flush=True)
            
            # time.sleep(0.1)
    def send_to_client(self, name, message): 
        client_ip, client_port = None, None
        for i in self.table:
            if i[0] == name:
                client_ip, client_port = i[1], i[2]
                break
        if client_ip is None:
            print("The client {} is not found".format(name))
        else:
            if self.table[(name, client_ip, client_port)]:                    
                msg = "2" + self.name + ": " + message
                bytesToSend = str.encode(msg)
                self.UDPClientSocket.sendto(bytesToSend, (client_ip, client_port))
                # self.receive_ack_from_client((client_ip, client_port))
                self.is_waiting = True                    
                time.sleep(0.5)
                received_by_server = False
                if self.is_waiting:
                    # print("here")
                    print(">>> [No ACK from {}, message sent to server.]".format(name))
                    for _ in range(5):
                        message = "2" + self.name + " " + name + " " + message
                        bytesToSend = str.encode(message)
                        self.UDPClientSocket.sendto(bytesToSend, (self.server_ip, self.server_port))
                        self.is_waiting = True 
                        # Because server has to check if the other client is indeed offline
                        # by sending 5 messages to the other clients
                        time.sleep(0.5)
                        if not self.is_waiting:
                            received_by_server = True
                            break
                    if not received_by_server:
                        print("[Server not responding]")
                        # os._exit(0)
            else:
                # send to server
                received_by_server = False
                for _ in range(5):
                        # send message to server 5 times, until success
                        message = "2" + self.name + " " + name + " " + message
                        bytesToSend = str.encode(message)
                        self.UDPClientSocket.sendto(bytesToSend, (self.server_ip, self.server_port))
                        self.is_waiting = True 
                        time.sleep(0.5)
                        if not self.is_waiting: 
                            received_by_server = True                         
                            break
                if not received_by_server:
                    print(">>> [Server not responding]\n>>> ")
                    # os._exit(0)
                    

    def receive(self):
        while True:  
                 
            bufferSize = 102400
            msgFromOthers, address = self.UDPClientSocket.recvfrom(bufferSize)
            
            msgFromOthers = msgFromOthers.decode("ascii")
            mode, msg = msgFromOthers[0], msgFromOthers[1:]                
            if address == (self.server_ip, self.server_port):
                # msg from server   
                if mode == "1" and self.isreg:
                    # update mode
                    self.update(msg)
                if mode == "2" and self.isreg:
                    # handle the response of server after re-reg
                    self.is_waiting = False
                    self.handle_reg_ack_from_server(msg)
                if mode == "3" and self.isreg:
                    # handle the ack for sending offline chat for other client
                    self.is_waiting = False
                    self.handle_offline_chat_ack_from_server(msg)
                if mode == "4" and self.isreg:
                    # handle receiving saved messages by the server
                    self.handle_receive_offline_message(msg)
                if mode == "5" and self.isreg:
                    # received de-reg ack from server
                    self.is_waiting = False
                    self.receive_dereg_ack()
                if mode == "6" and self.isreg:
                    self.send_ack_to_server()
                if mode == "7" and self.isreg:
                    self.is_waiting = False
                    self.receive_channel_message_ack_from_server()
                if mode == "8" and self.isreg:
                    self.receive_channel_message(msg)
                if mode == "9" and self.isreg:
                    self.receive_dummy(msg)
            else:
                if mode == "2" and self.isreg:
                # online chat mode, single person
                    self.is_waiting = False
                    self.receive_message_from_client(address, msg)
                elif mode == "3" and self.isreg:
                    #  ack for online chat mode, single person
                    self.is_waiting = False
                    self.receive_ack_from_client(address)
    def receive_dummy(self, msg):
        self.UDPClientSocket.sendto(str.encode("9"), (self.server_ip, self.server_port))


    def receive_channel_message(self, msg):
        print("{}\n>>> ".format(msg), end="", flush=True)
        self.UDPClientSocket.sendto(str.encode("7"), (self.server_ip, self.server_port))  
        
             
    def receive_dereg_ack(self):
        print(">>> [You are offline. Bye.]\n", end="",  flush=True)
        
        
    def send_ack_to_server(self):
        # self.  
        self.UDPClientSocket.sendto(str.encode("6"), (self.server_ip, self.server_port))
        
        
    def  receive_ack_from_client(self, address):        
        
        client_ip, client_port = address[0], address[1]
        for i in self.table:
            if i[1] == client_ip and i[2] == client_port:
                client_name = i[0]
                break
        print(">>> [Message received by {}.]".format(client_name),flush=True)
        

    def send_ack(self, ip, port):
        bytesToSend = str.encode("3")
        # print("sending ack to {}:{}".format(ip, port))    
        self.UDPClientSocket.sendto(bytesToSend, (ip, port))


    def handle_receive_offline_message(self, msg):
        # print(msg)
        l = msg.split(" ")
        timestamp = l[1]
        try:
            datetime_ = datetime.fromtimestamp(float(timestamp))
            print(l[0], "<{}>".format(datetime_), " ".join(l[2:]), "\n>>> ", sep=" ", end="", flush=True)
        except ValueError:
            print(msg, ">>> ", sep="\n", end="", flush=True)

    def receive_message_from_client(self, address, msg):
        print(msg, ">>> ", sep="\n", end="", flush=True)
        self.send_ack(address[0], address[1])
    
    
    def dereg(self, name):
        if name == self.name:
            # mode 4 for dereg
            bytesToSend = str.encode("4{}".format(name))
            received_by_server = False
            for _ in range(5):
                # set waiting flag, True: unreceived, False: received
                self.is_waiting = True
                self.UDPClientSocket.sendto(bytesToSend, (self.server_ip, self.server_port))
                # sleep for 0.5 sec
                time.sleep(0.5)
                # After waking up, if the flag is changed, it means the ack is received
                if not self.is_waiting:
                    received_by_server = True
                    break
            if not received_by_server:
                print(">>> [Server not responding]")
                print(">>> [Exiting]")
                os._exit(0)
            self.isreg = False
            # print(self.isreg)
        else:
            print("nickname not correct. Retry!\n",end="", flush=True)
    def send_channel_message(self, msg):
        for _ in range(5):
            self.UDPClientSocket.sendto(str.encode("6" + msg), (self.server_ip, self.server_port))
            self.is_waiting = True
            time.sleep(0.5)
            received_by_server = False
            if not self.is_waiting:
                received_by_server = True
                break
        if not received_by_server:
            print(">>> [Server not responding]")
            # print(">>> [Exiting]")
            # os._exit(0)
    
    
    def receive_channel_message_ack_from_server(self):
        print(">>> [Message received by server]\n", end="",  flush=True)

    def handle_offline_chat_ack_from_server(self, msg):
        if msg == "online":
            print("The client is online and failed to send the message. Resend the message\n>>> ", end="")
        elif msg == "success":
            print("[Messages received by the server and saved]\n", end="")
        
    def update(self, msg):
        # print(msgFromServer)
        clients = msg.split(",")
        self.table = {}
        for i in clients:
            # parse the table, and override the table, update status one by one
            if i == "":
                continue
            client_name, client_ip, client_port, client_status = i.split()
            client_port = int(client_port)
            if client_status == 'True':
                client_status = True
            else:
                client_status = False
            
            self.table[(client_name, client_ip, client_port)] = client_status
        # print(msg)
        print("[Client table updated]\n>>> ", end="", flush=True)
        # print(">>> ", end="", flush=True)
        

    def register(self, name):
        
        self.name = name
        msgFromClient = "0" + self.name
        bytesToSend = str.encode(msgFromClient)
        bufferSize = 102400
        # send 0name to server, 0: register mode, name: the nickname trying to register for
        self.UDPClientSocket.sendto(bytesToSend, (self.server_ip, self.server_port))
        
        msgFromServer = self.UDPClientSocket.recvfrom(bufferSize)[0].decode("ascii")
        if msgFromServer == "2duplicate":
            # if duplicate name, exit the program
            print("[client {} exists. Exiting]".format(name))
            exit()
        # on success, print the ack message from server and set the status to true
        msg = ">>> {}\n".format(msgFromServer[1:])
        self.isreg = True
        print(msg, end="", flush=True)

    def register_back(self, name):
        self.name = name
        msgFromClient = "0" + self.name
        bytesToSend = str.encode(msgFromClient)
        self.isreg = True
        received_by_server = False
        for _ in range(5):
            # send message to the server 5 times until success
            self.is_waiting = True
            self.UDPClientSocket.sendto(bytesToSend, (self.server_ip, self.server_port))
            time.sleep(0.5)
            if not self.is_waiting:
                received_by_server = True
                break
        
        if not received_by_server:
            print("Server not responding\nExiting")
            os._exit(0)

        
    def handle_reg_ack_from_server(self, msg):
        
        if msg == "duplicate":
            print("Username active. Retry\n>>> ", end="", flush=True)
            self.isreg = False
            return
        # normal case: print welcome message, change the reg status 
        msg = ">>> {}\n".format(msg)        
        print(msg, end="", flush=True)

