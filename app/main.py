import socket
import sys


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this block to pass the first stage
    #
    dns_server_add = sys.argv[2]
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("127.0.0.1", 2053))
    
    while True:
        try:
            buf, source = udp_socket.recvfrom(1024)
            print(buf)
            cursor = 0
            id = int.from_bytes(buf[cursor: cursor + 2], byteorder="big")
            cursor += 2
            flags_and_codes = int.from_bytes(buf[cursor: cursor + 2], byteorder="big")
            cursor += 2
            question_count = int.from_bytes(buf[cursor: cursor + 2], byteorder="big")
            cursor += 8

            questions = []
            for i in range(question_count):
                question = bytes([])
                while buf[cursor] != 0:
                    if question != b'' and (buf[cursor] >> 6) & 3:
                        ptr = int.from_bytes(buf[cursor:cursor+2], byteorder="big")
                        ptr = ptr & ~(3 << 14)

                        while buf[ptr] != 0:
                            ln = buf[ptr]
                            question += buf[ptr: ptr + ln + 1]
                            ptr += ln + 1

                        question += buf[ptr: ptr + 1]
                        cursor += 2
                    else:
                        ln = buf[cursor]
                        question += buf[cursor: cursor + ln + 1]
                        cursor += ln + 1

                question += buf[cursor: cursor + 1]
                cursor += 1
                question += buf[cursor:cursor+4]
                cursor += 4
                questions.append(question)

            ans_id = id
            ans_flags_and_codes = flags_and_codes | (1 << 15)
            ans_flags_and_codes = ans_flags_and_codes | (4)
            ans_count = question_count
            ans = b""

            response = bytes()
            for question in questions:
                resolver_socket = socket.socket(socket.AF_INET, type=socket.SOCK_DGRAM)
                resolver_socket.sendto(ans_id.to_bytes(length=2, byteorder="big") + flags_and_codes.to_bytes(length=2, byteorder="big") + (1).to_bytes(length=2, byteorder="big") + b"\x00" * 6 + question, (dns_server_add.split(":")[0], int(dns_server_add.split(":")[1])))
                ans += resolver_socket.recvfrom(512)[0][12 + len(question):]
    
                # ans_name = question[:-4]
                # ans_type = (1).to_bytes(length=2, byteorder="big")
                # ans_class = (1).to_bytes(length=2, byteorder="big")
                # ans_ttl = (60).to_bytes(length=4, byteorder="big")
                # ans_length = (4).to_bytes(length=2, byteorder="big")
                # ans_data = (((8).to_bytes(length=1, byteorder="big")) 
                #     + ((8).to_bytes(length=1, byteorder="big")) 
                #     + ((8).to_bytes(length=1, byteorder="big")) 
                #     + ((8).to_bytes(length=1, byteorder="big"))
                # )

                # ans += (bytes(ans_name)
                #     + ans_type 
                #     + ans_class 
                #     + ans_ttl 
                #     + ans_length 
                #     + ans_data)

            response += (ans_id.to_bytes(length=2, byteorder="big") 
                + ans_flags_and_codes.to_bytes(length=2, byteorder="big") 
                + question_count.to_bytes(length=2, byteorder="big") 
                + ans_count.to_bytes(length=2, byteorder="big")
                + b"\x00" * 4 
            )
            for i in range(question_count):
                response += questions[i]
            response += ans

            print(response)
            udp_socket.sendto(response, source)
        except Exception as e:
            print(f"Error receiving data: {e}")
            break


if __name__ == "__main__":
    main()
