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
                elif message[4:]=="quit":
                    print("Successfully disconnected")
                    connected=False
                    client.close()
                    return
                elif message[4:]=="Load gameplay scene":
                    print("Load gameplay scene!")
                    #UCITAJ SCENU
                    client.send("/ca".encode(encode_format))
                elif message[4:18]=="spawn players:":
                    playersNames=message[19:]
                    print("Spawn players:"+str(playersNames))
                    client.send("/ca".encode(encode_format))
                elif message[4:13]=="add boxes":
                    amount=message[14:]
                    print("Add boxes:"+str(amount))
                    client.send("/ca".encode(encode_format))
                elif message[4:17]=="add boxes":
                    question=message[18:]
                    print("Question:"+str(question))
                elif message[4:16]=="remove boxes":
                    amount=message[17:]
                    print("Remove boxes:"+str(amount))
                    client.send("/ca".encode(encode_format))
                elif message[4:17]=="show question":
                    question=message[18:]
                    print("Question: "+str(question))
                elif message[4:]=="die":
                    print("You lost!\nAdd coins:60")
                elif message[4:7]=="win":
                    amount=message[8:]
                    print("You won!\nAdd coins:"+amount)
            elif message[:3]=="err":
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