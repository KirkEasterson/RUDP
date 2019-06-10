import java.io.DataOutputStream;
import java.net.Socket;
import java.util.Scanner;

public class Rudp {

    private String IP = "localhost";
    private int CHECKSUM = 0;
    private int payload_length = 256;
    private int window_size = 10;

    public static void main(String[] args) {

        Scanner scanner = new Scanner(System.in);
        int input;

        while (true) {
            System.out.print("What would you like to do? (1 = send, 2 = receive, 3 = exit): ");
            try {
                input = scanner.nextInt();
            } catch (Exception e) {
                System.out.println("Invalid choice. Try again");
            }

            switch (input) {
            case 1:
                send();
            case 2:
                receive();
            case 3:
                System.out.println("Goodbye");
                scanner.close();
                System.exit(0);
            default:
                System.out.println("Invalid choice. Try again");
            }
        }
    }

    public static void send() {

        int S_PORT = 1000;
        int D_PORT = 1001;
        int LEN = 0;
        int timeout = 3;

        int head_SEQ = 0;
        int num_iter = 0;
        int last_SEQ = -1;
        int num_timeouts = 0;

        // NOT SURE HOW TO DO THIS
        // Socket sock = new Socket(IP, S_PORT);
        // DataOutputStream out = null;

        CircularQueue<Byte[]> window = new CircularQueue<Byte[]>(window_size);
        CircularQueue<Boolean> is_ACKed = new CircularQueue<Boolean>(window_size);

        Scanner scanner = new Scanner(System.in);

        try {
            System.out.print("Enter source file name: ");
            String filename = scanner.nextLine();
        } catch (Exception e) {
            System.out.println("Error reading file");
        }

    }

    public static void receive() {
        int temp = 0;
    }

    public boolean send_datagram() {
        return false;
    }

}

class CircularQueue<T> {

    private T[] queue;
    private int head;
    private int tail;
    private int size;
    private int maxSize;

    public CircularQueue(int maxSize) {
        this.maxSize = maxSize;
        head = 0;
        tail = 0;
        size = 0;
        queue = (T[]) new Object[this.maxSize];
    }

    public boolean enqueue(T data) {
        if (is_full()) {
            return false;
        }
        queue[tail] = data;
        tail += ((tail + 1) % maxSize);
        size++;
        return true;
    }

    public T dequeue() {
        if (is_empty()) {
            return null;
        }
        T data = queue[head];
        queue[head] = null;
        head += ((head + 1) % maxSize);
        size--;
        return data;
    }

    public T get_index(int index) {
        if (index > size) {
            return null;
        }
        int real_index = (index + head) % maxSize;
        return queue[real_index];
    }

    public boolean set_index(int index, T data){
        if (index > size){
            return false;
        }
        int real_index = ((index+head))%maxSize);
        queue[real_index] = data;
        return true;
    }

    public int num_elems() {
        return size;
    }

    public boolean is_full() {
        return (size == maxSize);
    }

    public boolean is_empty() {
        return (size == 0);
    }
}
