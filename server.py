import socket
import threading

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

#-------------------Functions
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
                    answer=message[:4]
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

        validName=True
        for client in clients:
            if(client.name==name):
                conn.send("err nameTaken".encode(encode_format))
                conn.close()
                validName=False
        if validName:
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
def getRoom(roomName):
    for room in rooms:
        if room.name==roomName:
            index=rooms.index(room)
            return rooms[index]
def quitClient(conn):
    client=getClient(conn)
    clients.remove(client)
    conn.send("req quit".encode(encode_format))
    conn.close()
def leaveRoom(client):
    roomName=client.room
    room=getRoom(roomName)
    room.players.remove(client)

    if len(room.players)==0:
        if roomName!="global":
            deleteRoom(room)
    else:
        client.conn.send(f"inf Left room \"{roomName}\"!".encode(encode_format))
        return
def handleGame(room):
    def broadCast(mess):
        for player in room.players:
            player.conn.send(str(mess).encode(encode_format))


    #ucitaj gameplay scenu
    broadCast("req Load gameplay scene")

    loadedComplited=True
    while loadedComplited:
        for player in room.players:
            if player.action!=1:
                loadedComplited=False

    #spawnuj igrace
    playersNames=""
    for player in room.players:
        playersNames+=player.name+","
        player.action=-1

    playersNames=playersNames[:-1]

    broadCast("req spawn players: "+str(playersNames))
    loadedComplited=True
    while loadedComplited:
        for player in room.players:
            if player.action!=1:
                loadedComplited=False

    #pocni gameplay
    


def deleteRoom(room):
    rooms.remove(room)
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
    client.answer=answer+"".lower()
def confirmAction(conn):
    client=getClient(conn)
    client.action=1


#-------------------StartsServer
server= socket.socket(socket.AF_INET,socket.SOCK_STREAM) #ozncava da cemo da radimo sa ipv4 adresama i da cemo koristiti TCP
server.bind((host,port)) #binduje server
server.listen() #pokrece

globalRoom=Room("global")
globalRoom.maxPlayers=-1
rooms.append(globalRoom)

thread_handleConnections=threading.Thread(target=newConnection) #slusa za nove konekcije
thread_handleConnections.start()

