import socket
import threading

nickname= input("Choose your nickname: ")

host = "localhost" #ip adresa servera
port = 5000 #port na kome slusa server
encode_format="utf-8"

client= socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.connect((host,port))


def receive():
    global connected
    while True:
        try:
            #primi poruku od servera
            message=client.recv(1024).decode(encode_format)
            if message[:3] =="req":
                if message[4:]=="name":
                    client.send(nickname.encode(encode_format))
                if message[4:]=="quit":
                    print("Successfully disconnected")
                    connected=False
                    client.close()
                    return
                if message[4:]=="Load gameplay scene":
                    print("Load gameplay scene!")
                    #UCITAJ SCENU
                    client.send("/ca".encode(encode_format))
                if message[4:18]=="spawn players:":
                    playersNames=message[19:]
                    players=playersNames.split(',')
                    for name in players:
                        print("spawn player:"+name)
                    client.send("/ca".encode(encode_format))
            elif message[:3]=="err":
                if message[4:]=="nameTaken":
                    print("This name is taken!")
                    connected=False
                    client.close()
                    return
                else:
                    print(message[4:])
            elif message != "":
                print(message)
        except:
            #Doslo je do greske zatvori konekciju
            print("An error occured!")
            client.close()
            break


def write(): # salje poruku serveru
    global connected
    while True:
        message=input()
        if connected:
            client.send(message.encode(encode_format))
        else:
            break


connected=True
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread=threading.Thread(target=write)
write_thread.start()