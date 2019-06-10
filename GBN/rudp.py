import sys
import socket
import struct
import random


class CircularQueue:

    # Constructor
    def __init__(self, maxSize):
        self.queue = [None] * maxSize
        self.head = 0
        self.tail = 0
        self.size = 0
        self.maxSize = maxSize

    # Adding elements to the queue
    def enqueue(self, data):
        if self.size == self.maxSize:
            return ("Queue Full!")
        self.queue[self.tail] = data
        self.tail = (self.tail + 1) % self.maxSize
        self.size += 1
        return True

    # Removing elements from the queue
    def dequeue(self):
        if self.size == 0:
            return ("Queue Empty!")
        data = self.queue[self.head]
        self.head = (self.head + 1) % self.maxSize
        self.size -= 1
        return data

    # Get size
    def num_elems(self):
        return self.size

    # Check if empty
    def is_full(self):
        if (self.size == self.maxSize):
            return True
        return False


def send_datagram(sock, IP, S_PORT, D_PORT, LEN, CHECKSUM, SEQ, payload, type):
    header = struct.pack('!HHHHQ', S_PORT, D_PORT, LEN, CHECKSUM, SEQ)
    sock.sendto(header+payload, (IP, D_PORT))  # Send the datagram
    print('Sending ', type, ': ', SEQ)
    # print(payload, '\n\n')


def send():

    IP = 'localhost'  # IP address
    S_PORT = 1000  # Source port
    D_PORT = 1001  # Destination port
    payload_length = 256  # Length of payload
    window_size = 10  # Size of the window
    timeout = 3  # Time out

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create socket
    sock.bind((IP, S_PORT))  # Bind IP address and port number

    LEN = 0  # Length of datagram, initialize it to 0
    CHECKSUM = 0  # Not used, 0 is a dummy value

    head_SEQ = 0  # Head sequence number of queue
    window = CircularQueue(window_size)  # Initialize the queue
    unacked = 0  # Number of un-ACKed datagrams in the queue
    num_iter = 1  # Number of current iteration
    last_SEQ = -1  # SEQ of last datagram, stays at -1 until iteration is known
    num_timeouts = 0

    try:
        filename = input('Enter file name: ')  # Get filename
        file = open(filename, 'rb')  # Open the file in binary mode
    except FileNotFoundError:
        print("File does not exist. Send aborted...")
        return

    print("Sending...")
    while True:  # While there are unsent bytes in the file
        print('--------------------- ITERATION ', num_iter)

        # Fill the buffer
        while (not window.is_full()):
            payload = file.read(payload_length)  # Get next payload
            if (not payload):  # If payload is empty, file is done
                break
            window.enqueue(payload)  # Put data in the buffer
            SEQ = (head_SEQ + unacked)  # Get SEQ of the datagram
            unacked += 1  # Increase number of datagrams that haven't been acked
            print('Buffered SEQ: ', SEQ)

        # Send datagrams
        for i in range(unacked):  # Send unacked number of datagrams
            SEQ = head_SEQ + i  # Get SEQ for current datagram
            payload = window.dequeue()  # Get the data from the queue
            window.enqueue(payload)  # Put the data back in the queue
            LEN = len(payload) + 16  # Add size of header to length field
            send_datagram(sock, IP, S_PORT, D_PORT,
                          LEN, CHECKSUM, SEQ, payload, 'SEQ')
            if (LEN < payload_length+16):  # If less than max length, it's the last datagram
                last_SEQ = (SEQ + 1)  # Save last SEQ
                LEN = 16  # Add size of header to length field
                payload = b''
                send_datagram(sock, IP, S_PORT, D_PORT, LEN,
                              CHECKSUM, last_SEQ, payload, 'final SEQ')  # Send last datagram

        # Timer
        print('Waiting for ACKs...')
        while True:  # Loop for timeout
            sock.settimeout(timeout)
            try:
                resp = sock.recv(64)  # Receive the ACK
            except socket.timeout:
                print("TIMEOUT")
                num_timeouts += 1
                break
            finally:
                sock.settimeout(None)

            bin_header = resp[:16]  # Isolate header
            header = struct.unpack('!HHHHQ', bin_header)  # Unpack header
            if (header[4] == head_SEQ):  # If ACK  is the one we are expecting
                print('Received ACK: ', header[4])
                unacked -= 1  # Decrement number of unacked datagrams
                head_SEQ += 1  # Move SEQ head to next number
                window.dequeue()  # Remove the data from the queue
                if (head_SEQ == last_SEQ):  # If at last datagram
                    print('--------------------- FILE SENT')
                    print('Number of timeouts: ', num_timeouts)
                    return
            if (unacked == 0):  # If all datagrams were ACKed
                print('All packets ACKed')
                break

        num_iter += 1  # Increase iteration number


def receive():

    IP = 'localhost'  # IP address
    S_PORT = 1001  # Source port
    D_PORT = 1000  # Destination port
    LEN = 16  # Length of the header
    CHECKSUM = 0  # Checksum, dummy value
    exp_SEQ = 0  # Expected SEQ number
    timeout = 60  # Timeout on receiver side
    num_recvd = 0  # Number of datagrams received
    num_iter = 1  # Number of iterations
    last_SEQ = -1  # SEQ of last datagram

    window_size = 10  # Size of the window
    window = CircularQueue(window_size)  # Initialize the queue

    filename = input('Enter output file name: ')  # Get file name
    file = open(filename, 'wb')  # Open the file in binary mode

    p_loss = float(
        input('Enter probability of datagram loss (value from 0 to 1): '))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create socket
    sock.bind((IP, S_PORT))  # Bind IP address and port number
    print("Waiting...")

    done = False
    while (not done):  # Main loop
        print('--------------------- ITERATION ', num_iter)
        num_recvd = window.num_elems()  # Number of datagrams received for this iteration
        for i in range(window_size - num_recvd):  # To only fill the size of the buffer

            sock.settimeout(timeout)  # Set timeout
            try:
                datagram = sock.recv(1024)  # Receive the datagram
            except socket.timeout:
                print("Receiver timed out. File transfer being aborted.")
                # RECEIVER SHOULD BE NOTIFIED
                return
            finally:
                sock.settimeout(None)  # Stop the timeout

            if (random.random() < p_loss):
                i -= 1
                continue

            bin_header = datagram[:16]  # Get 16 bits for the header
            header = struct.unpack('!HHHHQ', bin_header)  # Unpack header
            SEQ = header[4]  # Get sequence number
            LEN = header[2]
            print('Received SEQ: ', SEQ)
            if (SEQ == exp_SEQ):  # If datagram we want is received
                num_recvd += 1  # Increase number of received datagrams
                exp_SEQ += 1  # Move to next SEQ

                if (LEN == 16):  # If last datagram
                    last_SEQ = SEQ
                    break

                # Send ACK
                payload = b''
                send_datagram(sock, IP, S_PORT, D_PORT,
                              LEN, CHECKSUM, SEQ, payload, 'ACK')

                payload = datagram[16:]  # Isolate the payload
                window.enqueue(payload)  # Add data to the buffer

        print('Number of datagrams received: ', num_recvd)
        for i in range(num_recvd):  # Write only number of datagrams received
            SEQ = (exp_SEQ - num_recvd + i)  # Get SEQ of the datagram3
            if (SEQ == last_SEQ):
                print('Final SEQ: ', SEQ)
                print('--------------------- FILE RECEIVED ')
                return
            print("Writing SEQ: ", SEQ)
            payload = window.dequeue()  # Get the data from the buffer
            # print(payload, '\n\n')
            file.write(payload)  # Write the data to the file

        num_iter += 1  # Move to next iteration


def main():
    while True:
        choice = input(
            "What would you like to do? (1 = send, 2 = receive, 3 = exit): ")
        if (choice == '1'):  # Send a file
            send()
        elif (choice == '2'):  # Receive a file
            receive()
        elif (choice == '3'):  # Exit
            print("Goodbye")
            exit(0)
        else:
            print("Invalid choice. Try again\n")  # Invalid choice


if __name__ == "__main__":
    main()
