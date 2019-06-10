import socket
import struct

IP = 'localhost'
S_PORT = 1001
LEN = 0
CHECKSUM = 0
SEQ = 0

filename = 'out.jpg' # Dummy filename. The file extension has to be known and changed before any other file type is sent
file = open(filename, 'wb') # Open the file in binary mode

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Create the socket
sock.bind((IP, S_PORT)) # Bind IP address and port number

while True: # Main loop
    datagram = sock.recv(1024) # Receive the datagram
    bin_header = datagram[:16] # Get 16 bits for the header
    header = struct.unpack('!HHHHQ', bin_header) # Unpack the header
    payload = datagram[16:] # Isolate the payload
    result = bytearray(payload) # Convert payload to a bytearray
    file.write(result) # Write the payload to the file
