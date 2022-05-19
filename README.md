Qinghang Hong qh2249

### Command to compile:
Server:
`python3 ChatApp.py -s 8000`

Client:
`python3 ChatApp.py -c bob 127.0.0.1 8000 9000`

### Project Structure:
    
   #### ChatApp.py: ####
        1. It parses and checks commandline arguments. 
        2. It checks the -c or -s flag.
        3. It checks the format of the IP address, including if length is 4, 
        and if all four numbers are [0, 255]
        4. It checks if the port number in range [0, 65535]
        5. It creates corresponding client/server object, pass in IP address, port number, and nickname to the object. And call the memeber function `run`

  #### client.py ####
    1. Create two threads. 
        1. First one is to listen to the user input and send messages.
        2. Second one is to receive messages from other clients/server
    2. To send each message, add a `mode` in front to indicate to the receiver which types of message
        For example, sending the other client "2hello" let the receiving client know that the message is chat and content is "hello"
    3. To receive message, check the ip address and port and determine if it is server. 
    And check the first char to see which type of message it is and call corresponding handler
    4. To create timeout scenarios, set flag `self.is_waiting = True` after sending a message and sleep for 0.5s. 
    On receiving the ack, unset the flag `self.is_waiting = False`. 
    After waking up, checking if the flag is changed by the receiving thread can determine if ack is received.
    5. Features implemented:
        1. register, re-register, de-register with timely ACK
        2. send and receive messages(with space, punctuations) from other clients with timely ACK if the user is active, 
        4. check if receiver offline, then send to server with timely ACK without sending to the client
        5. send and receive channel message with timely ACK
        6. receive tables from servers
        7. receive offline messages
         

    5. Some edge cases handled(not all listed):
        1. print err message when invalid commands(wrong length, typo, etc)
        2. exit when register existing names in command line. Print error when use command `reg` 
        3. print error if do anything other than reg after dereg
        4. ignore all messages if de-reg
        5. print error reg when is active
        6. Server not responding will result in exiting the program

#### 3. server.py. ####

        1. Create a thread to constantly listen to the messages from client.
        2. On receiving a message, look at the first char and call the corresponding handler.
        3. With timeout and ACK, create a new thread to receive and change the flag. 
    Sleep the main thread. After waking up, check the flag.
        4. Features implemented:
            1. register, de-register and broacast table when status changes
            2. save Off-line message in `<nickname>.txt`, 
            push them to the client when it regs back and delete the file.
            3. Forward channel message to everyone active other than the sender, save messages for offline user
            4. If no ack from supposedly active user, save the message to the file

### Not Implemented/Known bugs:

1. Confirm status to supposedly active but not responding users(Simply consider it offline)
2. Some incorrect displayed `<<<`
