import socket
import time
import os
import threading
class Server:
    def __init__(self, port):
        ip = "127.0.0.1"
        bufferSize = 1024
        self.UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.UDPServerSocket.bind((ip, port))
        self.table = {}
        
    def run(self):
        bufferSize  = 102400
        while True:
            try:
                bytesAddressPair = self.UDPServerSocket.recvfrom(bufferSize)
                message = bytesAddressPair[0].decode("ascii")
                mode = message[0]
                msg = message[1:]
                address = bytesAddressPair[1]
                
                if mode == "0":
                    # register mode
                    self.handle_register(address, msg)
                    
                if mode == "2":
                    # offline chat mode for client
                    self.handle_off_line_chat(address, msg)
                elif mode == "4":
                    self.dereg(address, msg)
                elif mode == "6":
                    self.handle_channel_message(address, msg)
                
            except KeyboardInterrupt:
                os._exit(0)
            except:
                pass
            

    def wait_for_ack_from_client(self):
        try:
            self.UDPServerSocket.settimeout(0.5)
            bytesAddressPair = self.UDPServerSocket.recvfrom(102400)
            self.UDPServerSocket.settimeout(None)
            message = bytesAddressPair[0].decode("ascii")
            mode = message[0]
            # msg = message[1:]
            if mode == "7" or mode == "9":
                self.is_waiting = False
        except:
            return
        

    def handle_channel_message(self, address, msg):
        self.UDPServerSocket.sendto(str.encode("7"), address)
        sender_name = None
        changed = False
        for i in self.table:
            if i[1] == address[0] and i[2] == address[1]:
                sender_name = i[0]
        message = str.encode("8Channel_Message<{}>: {}".format(sender_name, msg))
        for i in self.table:
            if i[0] != sender_name:
                if self.table[i]:
                    # online client, direct send
                    self.UDPServerSocket.sendto(message, (i[1], i[2]))
                    self.is_waiting = True
                    self.terminate = False
                    waiting = threading.Thread(target=self.wait_for_ack_from_client)
                    waiting.start()
                    time.sleep(0.5)
                    
                    
                    waiting.join()
                    if self.is_waiting:
                        
                        print("No Ack from {}".format(i[0]))
                        
                        if not self.check_client_online(i[1], i[2]):
                            changed = True                            
                            self.table[i] = False
                            f = open("{}.txt".format(i[0]), "a")
                            t = time.time()
                            f.write(" ".join(["Channel_Message<{}>".format(sender_name),  str(t), msg]) + "\n")
                            f.close()
                else:
                    # offline client, append to file
                    f = open("{}.txt".format(i[0]), "a")
                    t = time.time()
                    f.write(" ".join(["Channel_Message<{}>".format(sender_name),  str(t), msg]) + "\n")
                    f.close()

        if changed:
            self.broadcast_table()

    def handle_off_line_chat(self, address, msg):
        content = msg.split()
        sender, receiver, message = content[0], content[1], content[2]
        # recover the message if it has space
        receiver_ip, receiver_port, receiver_status = None, None, None
        # send received ack to client
        ackBytes = str.encode("3success")
        self.UDPServerSocket.sendto(ackBytes, (address[0], address[1]))
        for i in self.table:
            if i[0] == receiver:
                receiver_ip, receiver_port, receiver_status = i[1], i[2], self.table[i]
        if receiver_ip is None:
            # should not happen because the condition is checked on client side
            print("user name not found")
            return
        if receiver_status:
            # check if the receiver is indeed online
            status = self.check_client_online(receiver_ip, receiver_port)
            if not status:
                # offline: update table and brocast table
                self.table[(receiver, receiver_ip, receiver_port)] = False
                self.broadcast_table()
                
            else:
                # send err msg to the client
                errBytes = str.encode("3online")
                self.UDPServerSocket.sendto(errBytes, (receiver_ip, receiver_port))

                # send the table to the client
                str_to_send = "1"
                for i in self.table:
                    name, client_ip, client_port = i
                    status = str(self.table[i])
                    str_to_send +=  " ".join([name, client_ip, str(client_port), status]) + ","
                bytesToSend = str.encode(str_to_send)
                self.UDPServerSocket.sendto(bytesToSend, (client_ip, client_port))
                return
        
        # offline client
        if len(content) > 3:
            for i in range(3, len(content)):
                message += " " + content[i]
        
        f = open("{}.txt".format(receiver), "a")
        t = time.time()
        f.write(" ".join([sender,  str(t),  message]) + "\n")
        f.close()
        
        
    def check_client_online(self, receiver_ip, receiver_port):
        # for _ in range(5):
        #     print("checking", flush=True)
        #     self.is_waiting = True
        #     self.UDPServerSocket.sendto(str.encode("9"), receiver_ip, receiver_port)
        #     waiting_thread = threading.Thread(target=self.wait_for_ack_from_client)
        #     waiting_thread.start()
        #     time.sleep(0.5)
        #     # waiting_thread.join()
        #     self.UDPServerSocket.settimeout(None)
        #     if not self.is_waiting:
        #         return True
        return False


    def dereg(self, address, name):
        for i in self.table:
            if i == (name, address[0], address[1]):
                self.table[i] = False
                break
        # send ack to the client of dereg
        bytesToSend = str.encode("5")
        self.UDPServerSocket.sendto(bytesToSend, (address[0], address[1]))
        self.broadcast_table()
    def broadcast_table(self):
        # mode 1 for brocast table
        str_to_send = "1"
        for i in self.table:
            name, client_ip, client_port = i
            status = str(self.table[i])
            str_to_send +=  " ".join([name, client_ip, str(client_port), status]) + ","
        bytesToSend = str.encode(str_to_send)
        for i in self.table:
            name, client_ip, client_port = i
            if self.table[i]:
                
                self.UDPServerSocket.sendto(bytesToSend, (client_ip, client_port))

    def handle_register(self, address, message):
        # True: online, False: offline
        client_ip, client_port = address
        # check duplicate active user
        for i in self.table:
            if i[0] == message and self.table[i]:
                bytesToSend = str.encode("2duplicate")
                self.UDPServerSocket.sendto(bytesToSend, (client_ip, client_port))
                return
        # send ack and brocast table
        self.table[(message, client_ip, client_port)] = True
        bytesToSend = str.encode("2[Welcome, You are registered]")
        self.UDPServerSocket.sendto(bytesToSend, (client_ip, client_port))
        

        self.broadcast_table()

        # check if any saved message by checking the corresponding file exists
        if os.path.exists("{}.txt".format(message)):
            # send the indication message first
            # mode 4 for offline message to the client
            bytesToSend = str.encode("4You have message")
            self.UDPServerSocket.sendto(bytesToSend, (client_ip, client_port))
            # extract message from file, and send to the client
            # mode 4 for offline messages
            f = open("{}.txt".format(message))
            lines = f.readlines()
            for line in lines:
                line_split = line.split()
                sender, time_stamp, offline_message = line_split[0], line_split[1], " ".join(line_split[2:])
                bytesToSend = str.encode("4{}: {} {}".format(sender, time_stamp, offline_message))
                self.UDPServerSocket.sendto(bytesToSend, (client_ip, client_port))
            f.close()
            os.remove("{}.txt".format(message))
