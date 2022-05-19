import argparse

from client import Client
from server import Server

#create an ArgumentParser object
parser = argparse.ArgumentParser()
#declare arguments

parser.add_argument('-s', type = int, help='server port number')

parser.add_argument('-c', metavar='N', nargs='+',help='<name> <server-ip> <server-port> <client-port>')

args = parser.parse_args()


if args.c:
    name, server_ip, server_port, client_port = args.c
    server_port = int(server_port)
    client_port = int(client_port)
    server_ip_list = server_ip.split(".")
    if len(server_ip_list) != 4:
        print("server IP address should be 4 numbers")
    elif int(server_ip_list[0]) > 255 or int(server_ip_list[0]) < 0 or int(server_ip_list[1]) > 255 or int(server_ip_list[1]) < 0 or int(server_ip_list[2]) > 255 or int(server_ip_list[2]) < 0 or int(server_ip_list[3]) > 255 or int(server_ip_list[3]) < 0:
        print("server IP address invalid")
    elif server_port < 1024 or server_port > 65535:
        print("The server port number is out of range. Valid range [1024, 65535]")
    elif client_port < 1024 or client_port > 65535:
        print("The client port number is out of range. Valid range [1024, 65535]")
    else:
        client = Client(server_ip, server_port, client_port)
        client.run(name)
elif args.s:
    server_port = args.s
    server = Server(server_port)
    server.run()
else:
    print("wrong usage")
