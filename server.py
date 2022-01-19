import socket
import threading
import questionsAndAnswers
import random

#-------------------Classes
class Room:
    def __init__(self,name):
        self.name=name
        self.players=[]
        self.status="open"

    def addPlayer(self,conn):
        if self.status=="closed":
            conn.send("Room is full".encode(encode_format))
            return

        self.players.append(conn)
        if len(self.players)==5:
            self.status="closed"

    def removePlayer(self,conn):
        self.players.remove(conn)
        self.status="open"
class Client:
    def __init__(self,conn,name):
        self.conn=conn
        self.name=name
        self.room=""
        self.action=-1
        self.boxes=0

    def getConn(self):
        return self.conn

#-------------------Variables
host = "" #ip adresa servera
port = 5000 #port na kome slusa server
encode_format="utf-8"
maxPlayers=5 #maksimalni broj igraca po sobi
minPlayers=0 #minimalni broj igraca po sobi

rooms=[]
clients=[]
questions=questionsAndAnswers.questions

#-------------------Functions

#rooms
def joinRoom(name,conn):
    global maxPlayers
    for room in rooms:
        if room.name==name:
            if len(room.players)==maxPlayers and room.name!="global":
                conn.send(f"inf Room \"{room.name}\" is full!".encode(encode_format))
                return
            client=getClient(conn)
            if client.room==name:
                conn.send(f"inf Already in room \"{name}\"".encode(encode_format))
                return
            if client.room!="":
                leaveRoom(client)

            room.addPlayer(client)
            client.room=name
            conn.send(f"inf Successfully joined room: \"{name}\"".encode(encode_format))
            return

    conn.send(f"inf Cloudnt find room with name \"{name}\"".encode(encode_format))
def createRoom(name,conn):
    for room in rooms:
        if room.name==name:
            conn.send("inf Room with this name already exsists!".encode(encode_format))
            return

    room= Room(name)
    room.maxPlayers=5
    rooms.append(room)
    conn.send(f"inf Room with name: \"{name}\" created!".encode(encode_format))
    joinRoom(name,conn)
def deleteRoom(room):
        rooms.remove(room)
def getRoom(roomName):
    for room in rooms:
        if room.name==roomName:
            index=rooms.index(room)
            return rooms[index]
def leaveRoom(client):
    roomName=client.room
    room=getRoom(roomName)
    room.players.remove(client)

    if len(room.players)==0:
        if roomName!="global":
            deleteRoom(room)

#client
def handleClient(conn): #tretira poruke od klijenta
    joinRoom(name="global",conn=conn)
    while True:
        try:
            message=conn.recv(1024).decode(encode_format) #primi poruku od klijenta koja je dugacka 1024 bita,ceka dok ne dodje neka poruka
            if message[0]=="/":
                command=message[:3]
                if command=="/cr": #napravi sobu
                    name=message[4:]
                    createRoom(name,conn)
                elif command=="/jr": #udji u sobu
                    name=message[4:]
                    joinRoom(name,conn)
                elif command=="/lv": #izadji iz sobe
                    joinRoom(name="global",conn=conn)
                elif command=="/qu": #izadji iz igrice (kopletno)
                    quitClient(conn)
                elif command=="/st": #pocni igru
                    startGame(conn)
                elif command=="/ca": #potvrdi izvresenu komandu
                    confirmAction(conn)
                elif command=="/an":
                    answer=message[4:]
                    setAnswer(conn,answer)
                else:
                    conn.send("inf Wrong command!".encode(encode_format))
        except:

            break
def newConnection():
    print(f"Server started on port {port}")
    while True:
        conn,address = server.accept() #ceka dok ne dodje do neke konekcije

        #pita za nick i cuva ga
        conn.send("req name".encode(encode_format))
        name=conn.recv(1024).decode(encode_format)

        client=Client(conn=conn,name=name)
        clients.append(client)

        print(f"Client {name} joined!")
        client.conn.send("inf Connected to server!".encode(encode_format))

        #pravi novi thread za klijenta kako bi mogao da opsluzi novog klijenta

        thread = threading.Thread(target=handleClient,args=(client.conn,))
        thread.start()
def getClient(conn):
    for client in clients:
        if client.getConn() == conn:
            return client
def quitClient(conn):
    client=getClient(conn)
    clients.remove(client)
    conn.send("req quit".encode(encode_format))
    conn.close()


#game
def handleGame(room):
    def broadCast(mess):
        for player in room.players:
            player.conn.send(str(mess).encode(encode_format))
    def addBoxes(amount):
        count=0
        message="req add boxes:"
        for x in amount:
            message+=str(amount[count])+","
            room.players[count].boxes+=int(amount[count])
            count+=1
        message=message[:-1]
        broadCast(message)
    def waitForPlayers():
        #ceka da igrac izvrsi
        wait=True
        while wait:
            wait=False
            for player in room.players:
                if player.action!=1:
                    wait=True
                    break
        for player in room.players:
            player.action=-1
    def resetAnswers():
        for player in room.players:
            player.answer="-1"
    def checkAnswers(question):
        addBoxes=[]
        for player in room.players:
            foundAnswer=False
            for answer in question[2:]:
                if player.answer==answer:
                    addBoxes.append(len(answer))
                    foundAnswer=True
                    break
            if foundAnswer==False:
                addBoxes.append(0)
        return addBoxes
    def removeBoxes(_amount):
        amount=[]
        for player in room.players:
            amount.append(_amount)
        count=0
        message="req remove boxes:"
        for x in amount:
            message+=str(amount[count])+","
            room.players[count].boxes-=int(amount[count])
            count+=1

        message=message[:-1]
        broadCast(message)
    def checkIfSomeoneDied():
        for player in room.players:
            if player.boxes<0:
                player.conn.send("req die".encode(encode_format))
                joinRoom("global",player.conn)
    def rewardPlayers():
        for player in room.players:
            player.conn.send(f"req win:{player.boxes*3+100}".encode(encode_format))



    #ucitaj gameplay scenu
    broadCast("req Load gameplay scene")
    waitForPlayers()

    #imena igraca
    playersNames=""
    for player in room.players:
        playersNames+=str(player.name)+","
        player.boxes=0
    playersNames=playersNames[:-1]

    #spawnuj igrace sa imenima
    broadCast("req spawn players: "+str(playersNames))
    waitForPlayers()

    #daj svim igracima po 3 kutije
    startingBoxes=[]
    for player in room.players:
        startingBoxes.append(3)
    addBoxes(startingBoxes) #dodaje pocetne kutije
    waitForPlayers()

    round=1
    while True:


        resetAnswers()

        question=random.choice(questions)
        broadCast("req show question:"+question[1])

        waitForPlayers()#ceka dok igraci odgovore na pitanje

        boxes=checkAnswers(question)

        addBoxes(boxes)

        waitForPlayers()

        removeBoxes(round+2)

        waitForPlayers()

        checkIfSomeoneDied()

        round+=1

        if round==5:
            break

        if len(room.players)<=1:
            break

    rewardPlayers()

    #close game
    for player in room.players:
        joinRoom("global",player.conn)
def startGame(conn):
    global minPlayers
    client=getClient(conn)
    room=getRoom(client.room)
    if room.name=="global": #ne radi
        conn.send(f"err Cant start game from \"{room.name}\" room!".encode(encode_format))
        return
    else:
        if len(room.players)>=minPlayers:
            thread_handleGame=threading.Thread(target=handleGame,args=(room,))
            thread_handleGame.start()
        else:
            client.conn.send(f"inf Cant start game,need minimum of {minPlayers}. players!".encode(encode_format))
def setAnswer(conn,answer):
    client=getClient(conn)
    if client.room!="global:":
        client.answer=answer+"".lower()
        confirmAction(conn)
    else:
        client.conn.send("err Cant use this command now!".encode(encode_format))
def confirmAction(conn):
    client=getClient(conn)
    if client.room!="global":
        client.action=1

    else:
        client.conn.send("err Cant use this command now!".encode(encode_format))



#-------------------StartsServer

server= socket.socket(socket.AF_INET,socket.SOCK_STREAM) #ozncava da cemo da radimo sa ipv4 adresama i da cemo koristiti TCP
server.bind((host,port)) #binduje server
server.listen() #pokrece

globalRoom=Room("global")
globalRoom.maxPlayers=-1
rooms.append(globalRoom)


thread_handleConnections=threading.Thread(target=newConnection) #slusa za nove konekcije
thread_handleConnections.start()

