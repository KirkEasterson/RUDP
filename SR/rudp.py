import socket
import struct
import random
import datetime


class CircularQueue:  # For to make circular queue more efficient

    # Constructor
    def __init__(self, maxSize):
        self.queue = [None] * maxSize
        self.head = 0
        self.tail = 0
        self.size = 0
        self.maxSize = maxSize

    # Adding elements to the queue
    def enqueue(self, data):
        if self.is_full():
            return ('Queue full')
        self.queue[self.tail] = data
        self.tail = (self.tail + 1) % self.maxSize
        self.size += 1
        return True

    # Removing elements from the queue
    def dequeue(self):
        if self.is_empty():
            return ('Queue empty')
        data = self.queue[self.head]
        self.queue[self.head] = None
        self.head = (self.head + 1) % self.maxSize
        self.size -= 1
        return data

    # Getter
    def get_index(self, index):
        if (index > self.size):
            return ('Invalid index')
        real_index = (index + self.head) % self.maxSize
        return self.queue[real_index]

    # Setter
    def set_index(self, index, value):
        if (index > self.size):
            return ('Invalid index')
        real_index = (index + self.head) % self.maxSize
        self.queue[real_index] = value
        return True

    # Get size
    def num_elems(self):
        return self.size

    # Check if full
    def is_full(self):
        return (self.size == self.maxSize)

    # Check if empty
    def is_empty(self):
        return (self.size == 0)


def send_datagram(sock, IP, S_PORT, D_PORT, LEN, CHECKSUM, SEQ, payload, type):
    header = struct.pack('!HHHHQ', S_PORT, D_PORT, LEN, CHECKSUM, SEQ)
    sock.sendto(header+payload, (IP, D_PORT))  # Send the datagram
    print('Sending ', type, ': ', SEQ)


def send():

    IP = 'localhost'  # IP address
    S_PORT = 1000  # Source port
    D_PORT = 1001  # Destination port
    LEN = 0  # Length of datagram, initialize it to 0
    CHECKSUM = 0  # Not used, 0 is a dummy value

    header_length = 16
    payload_length = 256  # Length of payload in bytes
    window_size = 10  # Size of the window
    timeout = 3  # Time out in seconds

    head_SEQ = 0  # Head sequence number of queue
    num_iter = 0  # Number of current iteration
    last_SEQ = -1  # SEQ of last datagram, stays at -1 until iteration is known

    num_timeouts = 0  # Number of timeouts
    timeout_SEQ = []  # SEQs that have timed-out (time-outed?)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create socket
    sock.bind((IP, S_PORT))  # Bind IP address and port number

    window = CircularQueue(window_size)  # Initialize the queue
    is_ACKed = CircularQueue(window_size)  # Initialize the queue

    try:
        filename = input('Enter source file name: ')  # Get filename
        file = open(filename, 'rb')  # Open the file in binary mode
    except FileNotFoundError:
        print('File does not exist. Send aborted...')
        return

    p_loss = float(
        input('Enter probability of datagram loss from receiver to sender (value from 0 to 1, excluding 1): '))

    print('Sending...')
    while True:  # While there are unsent bytes in the file

        num_iter += 1  # Increase iteration number
        print('--------------------- ITERATION ', num_iter)

        while (not window.is_full()):  # While space in buffer
            SEQ = (head_SEQ + window.num_elems())  # Get SEQ of the datagram
            payload = file.read(payload_length)  # Get next payload
            window.enqueue(payload)  # Put data in the buffer
            is_ACKed.enqueue(False)  # Put false ACK in the buffer
            if (not payload):  # If payload is empty, file is done
                last_SEQ = SEQ  # Last SEQ is the previous SEQ
                print('Final SEQ: ', last_SEQ)
                break  # Exit loop
            print('Buffered SEQ: ', SEQ)

        # Send datagrams
        for i in range(window_size):  # For all eligible datagrams in buffer
            if (not is_ACKed.get_index(i)):
                SEQ = head_SEQ + i  # Get SEQ for current datagram
                payload = window.get_index(i)  # Get the data from the queue
                # Add size of header to length field
                LEN = len(payload) + header_length

                # Send datagram
                send_datagram(sock, IP, S_PORT, D_PORT, LEN,
                              CHECKSUM, SEQ, payload, 'SEQ')
                if (SEQ == last_SEQ):  # If at last datagram
                    break  # Stop sending

        # Receive ACKs
        print('Waiting for ACKs...')

        sock.setblocking(0)
        time_out_after = datetime.timedelta(timeout)  # Get time to stop at
        start_time = datetime.datetime.now()  # Start the timer

        while (not window.is_empty()):  # Loop for timeout

            if (datetime.datetime.now() > start_time + time_out_after):  # If time out 
                num_timeouts += 1  # Increase counter fo rnumber of timeouts
                timeout_SEQ.append(head_SEQ)  # Add SEQ to timeout list
                print('Timeout SEQ: ', head_SEQ)
                break  # Break loop to start sending again
            else:
                resp = sock.recv(64)  # Receive the ACK
                if (resp == -1) or (random.random() < p_loss):
                    continue



            # sock.settimeout(timeout)  # Set timeout
            # try:
            #     resp = sock.recv(64)  # Receive the ACK
            # except socket.timeout:
            #     num_timeouts += 1  # Increase counter fo rnumber of timeouts
            #     timeout_SEQ.append(head_SEQ)  # Add SEQ to timeout list
            #     print('Timeout SEQ: ', head_SEQ)
            #     break  # Break loop to start sending again
            # finally:
            #     sock.settimeout(None)  # Reset timeout for socket

            # if (random.random() < p_loss):  # Calculate if packet is lost
            #     continue

            bin_header = resp[:header_length]  # Isolate header
            header = struct.unpack(
                '!HHHHQ', bin_header)  # Unpack header

            ACK = header[4]  # Get the SEQ from the header
            index = (ACK - head_SEQ)  # Get index in buffers

            # If valid index in queue
            if (index >= 0) and (index < window_size) and (not is_ACKed.get_index(index)):
                print('Received ACK: ', ACK)
                is_ACKed.set_index(index, True)  # Mark SEQ as ACKed

                # While not empty and head has been ACKed
                while (not window.is_empty()) and (is_ACKed.get_index(0)):
                    window.dequeue()  # Dequeue the data
                    is_ACKed.dequeue()  # Dequeue the ACK
                    print('Debuffering SEQ: ', head_SEQ)
                    if (head_SEQ == last_SEQ):  # If last datagram
                        print('--------------------- FILE SENT')
                        print('Number of timeouts: ', num_timeouts)
                        if(num_timeouts):
                            print('Timeouts on SEQ:')
                            for seq in timeout_SEQ:
                                print(seq)
                        return
                    else:
                        head_SEQ += 1  # Move SEQ head to next number


def receive():

    IP = 'localhost'  # IP address
    S_PORT = 1001  # Source port
    D_PORT = 1000  # Destination port
    LEN = 16  # Length of the header
    CHECKSUM = 0  # Checksum, dummy value
    head_SEQ = 0  # Expected SEQ number

    recv_timeout = 60  # Timeout on receiver side
    last_SEQ = -1  # SEQ of last datagram
    header_length = 16

    window_size = 10  # Size of the window
    window = CircularQueue(window_size)  # Initialize the data buffer
    is_ACKed = CircularQueue(window_size)  # Initialize the ACK queue

    filename = input('Enter output file name: ')  # Get file name
    file = open(filename, 'wb')  # Open the file in binary mode

    p_loss = float(
        input('Enter probability of datagram loss from sender to receiver (value from 0 to 1): '))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create socket
    sock.bind((IP, S_PORT))  # Bind IP address and port number
    print('Waiting...')

    while True:  # Main loop

        # Fill buffers with default values
        while(not is_ACKed.is_full()):  # While there is space in the buffer
            is_ACKed.enqueue(False)
            window.enqueue('')

        sock.settimeout(recv_timeout)  # Set timeout
        try:
            datagram = sock.recv(1024)  # Receive the datagram
        except socket.timeout:
            print('Receiver timed out. File transfer being aborted.')
            # RECEIVER SHOULD BE NOTIFIED
            return
        finally:
            sock.settimeout(None)  # Stop the timeout

        # Calculate if packet is lost
        if (random.random() < p_loss):
            continue

        bin_header = datagram[:header_length]  # Get 16 bits for the header
        header = struct.unpack('!HHHHQ', bin_header)  # Unpack header
        SEQ = header[4]  # Get sequence number

        print('Received SEQ: ', SEQ)
        # Send ACK
        payload = b''  # Dummy payload for ACK
        send_datagram(sock, IP, S_PORT, D_PORT, LEN,
                      CHECKSUM, SEQ, payload, 'ACK')

        index = (SEQ - head_SEQ)  # Get expected index of datagram in buffer
        if (index >= 0) and (index < window_size) and (not is_ACKed.get_index(index)):
            payload = datagram[header_length:]  # Get payload
            is_ACKed.set_index(index, True)  # Mark SEQ as ACKed
            window.set_index(index, payload)  # Add data to buffer

            LEN = header[2]  # Get length
            # print(last_SEQ)
            if (LEN == header_length):  # If last datagram
                last_SEQ = SEQ

        # Write to file and slide window
        while(is_ACKed.get_index(0)):
            print('Writing SEQ: ', head_SEQ)
            payload = window.dequeue()  # Get the data from the buffer
            file.write(payload)  # Write the data to the file
            is_ACKed.dequeue()
            if (head_SEQ == last_SEQ):  # If last datagram
                print('Final SEQ: ', SEQ)
                print('--------------------- FILE RECEIVED ')
                return
            else:
                head_SEQ += 1


def main():
    while True:
        choice = input(
            'What would you like to do? (1 = send, 2 = receive, 3 = exit): ')
        if (choice == '1'):  # Send a file
            send()
        elif (choice == '2'):  # Receive a file
            receive()
        elif (choice == '3'):  # Exit
            print('Goodbye')
            exit(0)
        else:
            print('Invalid choice. Try again\n')  # Invalid choice


if __name__ == '__main__':
    main()
