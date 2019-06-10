import sys
import socket
import struct

# Defaults
IP = 'localhost'
S_PORT = 1000
D_PORT = 1001
payload_length = 256
window_size = 5
filename = 'lizard.jpg'

# Prompt user for input
# S_PORT = input('Enter source port: ')
# D_PORT = input('Enter destination port: ')
# payload_length = input('Enter payload length in bytes: ')
# window_size = input('Enter window size: ')
# filename = input('Enter file name: ')

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Create socket
LEN = 0 # Length of datagram, initialize it to 0
CHECKSUM = 0 # Not used, 0 is a dummy value
SEQ = 0 # Initial sequence number

window = [None] * window_size # Initialize circular queue
num_in_window = 0 # Number of un-ACKed datagrams in the queue


try:
    with open(filename, 'rb') as file: # Open the file in binary mode
        payload = file.read(payload_length) # Get payload from file
        while payload: # While there are unsent bytes in the file
            LEN = len(payload) + 16 # Add size of header to length field
            header = struct.pack('!HHHHQ', S_PORT, D_PORT, LEN, CHECKSUM, SEQ) # Create the header struct
            sock.sendto(header + payload, (IP, D_PORT)) # Send the datagram
            SEQ += len(payload) # Move SEQ number for next datagram
            payload = file.read(payload_length) # Get next payload
finally:
    file.close() # Close the file
