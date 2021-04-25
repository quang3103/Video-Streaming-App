import socket


# A TCP based echo server

echoSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


# Bind the IP address and the port number

echoSocket.bind((socket.gethostbyname(socket.gethostname()), 5008))


# Listen for incoming connections

echoSocket.listen()


# Start accepting client connections

while(True):

    (clientSocket, clientAddress) = echoSocket.accept()

    # Handle one request from client

    while(True):

        data = clientSocket.recv(1024)

        print("At Server: %s" % data)

        if(data != b''):

            # Send back what you received

            clientSocket.sendto(
                data, (socket.gethostbyname(socket.gethostname()), 5008))

            #break
