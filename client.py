import socket
import threading

#login
#while True:
    #acc=input("Do you have account? (Y/N): ").lower()
    #if acc=="y" or acc=="yes":
     #   email= input("email: ")
      #  password=input("password: ")
       # break
    #elif acc=="n" or acc=="no":
     #   name=input("Your nickname: ")
      #  email= input("email: ")
#  password=input("password: ")
#       break

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
                if message[4:]=="acc":
                    #if acc=="y" or acc=="yes":
                    client.send(f"/log,duki@gmail.com,duki123".encode(encode_format))
                    #elif acc=="n" or acc=="no":
                        #client.send(f"/reg,{email},{password},{name}".encode(encode_format))
                elif message[4:]=="quit":
                    print("Successfully disconnected")
                    connected=False
                    client.close()
                    return
                elif message[4:]=="load gameplay scene":
                    print("load gameplay scene!")
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
                elif message[4:16]=="remove boxes":
                    amount=message[17:]
                    print("Remove boxes:"+str(amount))
                    client.send("/ca".encode(encode_format))
                elif message[4:17]=="show question":
                    question=message[18:]
                    print("Question: "+str(question))
                elif message[4:7]=="die":
                    amount=message[8:].split(",")
                    print(f"You lost!\nAdd coins:{amount[0]}\nDeduce points:{amount[1]}")
                elif message[4:7]=="win":
                    amount=message[8:].split(",")
                    print(f"You won!\nAdd coins:{amount[0]}\nAdd points:{amount[1]}")
            elif message[:3]=="err":
                if message[4:]=="cre":
                    print("Wrong credentials!")
                    connected=False
                    client.close()
                    return
                elif message[4:]=="exsists":
                    print("Account with this email already exsists!")
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
    while connected:
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