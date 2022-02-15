import socket
import threading
import time
import json
import questionsAndAnswers
import random
import mysql.connector
from werkzeug.security import generate_password_hash,check_password_hash


#-------------------Classes
class Room:
    def __init__(self,name):
        self.name=name
        self.players=[]
        self.status="open"

    def __str__(self):
        players="";
        for player in self.players:
            players+=player.name+","

        if len(players)==0:
            players="None"
        else:
            players=players[:-1]
        return f"name={self.name}\nplayers={players}\nstatus={self.status}"

    def addPlayer(self,conn):
        self.players.append(conn)
        if len(self.players)>=5 and self.name!="global":
            self.status="full"

    def removePlayer(self,conn):
        self.players.remove(conn)
        self.status="open"
class Client:
    def __init__(self,conn,name,playerId,friends,coins,points,boughtItems,selectedHero):
        self.conn=conn
        self.name=name
        self.playerId=playerId
        self.friends=friends
        self.coins=coins
        self.points=points
        self.boughtItems=boughtItems
        self.room=""
        self.action=-1
        self.boxes=0
        self.selectedHero=selectedHero
        self.died=False

    def __str__(self):
        return f"""name={self.name},playerId={self.playerId},friends={self.friends},coins={self.coins},points={self.points},boughtItems={self.boughtItems},
        room={self.room},action={self.action},boxes={self.boxes}"""

    def getConn(self):
        return self.conn

#-------------------Variables
dataBase = mysql.connector.connect(
    passwd="", # lozinka za bazu
    user="root", # korisnicko ime
    database="zavrsnirad", # ime baze
    port=3306, # port na kojem je mysql server
    auth_plugin='mysql_native_password' # ako se koristi mysql 8.x
)
connection = dataBase.cursor(dictionary=True)

host = "" #ip adresa servera
port = 5000 #port na kome slusa server
encode_format="utf-8"
maxPlayers=5 #maksimalni broj igraca po sobi
minPlayers=2 #minimalni broj igraca po sobi

rooms=[]
clients=[]
questions=questionsAndAnswers.questions

#-------------------Functions

#rooms
def joinRoom(name,conn,invited=False):
    global maxPlayers
    for room in rooms:
        if room.name==name:
            if room.status=="full":
                conn.send(f"inf Room \"{room.name}\" is full!".encode(encode_format))
                return
            if room.status=="closed" and invited==False:
                conn.send(f"inf Room \"{room.name}\" is closed!".encode(encode_format))
                return
            if room.status=="inprogress":
                conn.send(f"inf Room \"{room.name}\" is in progress!".encode(encode_format))
                return
            client=getClient(conn)
            if client.room==name:
                conn.send(f"inf Already in room \"{name}\"".encode(encode_format))
                return
            if client.room!="":
                leaveRoom(client)
            room.addPlayer(client)
            client.room=name

            if room.name!="global":
                mess="req lpl:" #load players in lobby
                for player in room.players:
                    mess+=player.name+","
                mess=mess[:-1]

                for player in room.players:
                    player.conn.send(str(mess).encode(encode_format))

                if len(room.players)==maxPlayers:
                    startGame(conn)

            return

    conn.send(f"inf Cloudnt find room with name \"{name}\"".encode(encode_format))
def joinRandomRoom(conn):
    counter=0
    while True:
        if len(rooms)==1:
            conn.send("inf No available room found,try again or create one".encode(encode_format))
            break
        room = rooms[random.randrange(1, len(rooms))]
        if len(room.players)<maxPlayers and room.status=="open":
            joinRoom(room.name,conn)
            break
        counter+=1
        if counter==10:
            conn.send("inf No available room found,try again or create one".encode(encode_format))
            break
def createRoom(name,conn,closed=False):
    for room in rooms:
        if room.name==name:
            conn.send("inf Room with this name already exsists!".encode(encode_format))
            return

    room= Room(name)
    room.maxPlayers=5
    rooms.append(room)
    if closed:
        room.status="closed"
    else:
        room.status="open"
    joinRoom(name,conn,True)

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
    clientIndex=room.players.index(client)
    room.players.remove(client)

    if room.status=="inprogress" and client.died==False:
        mess=f"req rpg:{clientIndex}" #remove player in game
        for player in room.players:
            player.conn.send(str(mess).encode(encode_format))

        deducePoints=0
        if client.points>10:
            deducePoints=random.randrange(6,10)
            client.points-=deducePoints
        sql=f"UPDATE players SET points=points-{deducePoints} WHERE playerId = %s;"
        value=(player.playerId,)
        connection.execute(sql,value)
        dataBase.commit()
        client.conn.send(f"req die:0,-{deducePoints}".encode(encode_format))


    elif room.status!="inprogress":
        mess="req lpl:" #load players in lobby
        if room.name!="global" and room.status!="closing":
            for player in room.players:
                mess+=player.name+","
            mess=mess[:-1]

            for player in room.players:
                player.conn.send(str(mess).encode(encode_format))

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
                elif command=="/cc": #napravi zatvorenu sobu
                    name=message[4:]
                    createRoom(name,conn,True)
                elif command=="/jr": #udji u sobu
                    name=message[4:]
                    joinRoom(name,conn)
                elif command=="/rr": #udji u nasumicnu sobu
                    joinRandomRoom(conn)
                elif command=="/jc": #udji u sobu
                    name=message[4:]
                    joinRoom(name,conn,True)
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
                elif command=="/si": # trazi prijatelje po idu
                    id=message[4:]
                    conn.send(f"req lfs:{searchFriends(search=id,searchBy='playerId')}".encode(encode_format))
                elif command=="/sn": #trazi prijatelje po imenu
                    name=message[4:]
                    conn.send(f"req lfs:{searchFriends(search=name,searchBy='name')}".encode(encode_format))
                elif command=="/af": #dodaj drugara
                    id=message[4:]
                    addFriend(id)
                elif command=="/gf": #pokupi prijatelje
                    result=getFriends(getClient(conn))
                    conn.send(f"req lfm:{result}".encode(encode_format))
            else:
                    conn.send("inf Wrong command!".encode(encode_format))
        except:

            break
def newConnection():
    def login(conn,acc):
        sql="SELECT * FROM players where email=%s"
        value=(acc[1],)

        connection.execute(sql,value)
        account=connection.fetchone()

        if account:

            if(check_password_hash(account["password"],acc[2])):
                #create client object
                if account["friends"] != "-" :
                    friendsIds=str(account["friends"]).split(',')
                    friends=""
                    for id in friendsIds:
                        friends+=searchFriends(searchBy="playerId",search=id)+","
                    friends=friends[:-1]
                    account["friends"]=friends
                client=Client(conn=conn,
                              name=account["name"],
                              playerId=account["playerId"],
                              friends=account["friends"],
                              coins=account["coins"],
                              points=account["points"],
                              boughtItems=account["boughtItems"],
                              selectedHero=account["selectedHero"])
                clients.append(client)
                account.pop("password")
                client.conn.send(f"inf connected/{json.dumps(account)}".encode(encode_format))

                #pravi novi thread za klijenta kako bi mogao da opsluzi novog klijenta

                thread = threading.Thread(target=handleClient,args=(client.conn,))
                thread.start()
            else:
                conn.send("err cre".encode(encode_format))
                conn.close()
        else:
            conn.send("err cre".encode(encode_format))
            conn.close()


    print(f"Server started on port {port}")
    while True:
        conn,address = server.accept() #ceka dok ne dodje do neke konekcije
        conn.send("req acc".encode(encode_format)) #pita za account info
        acc=conn.recv(1024).decode(encode_format).split(",") #ocekuje reg/log,email,lozinka,?nick
        if acc[0]=="/log":
            login(conn,acc)
        else:
            #proveri da li emajl vec postoji
            sql="SELECT email from players where email=%s"
            value=(acc[1],)

            connection.execute(sql,value)
            exsists=connection.fetchall()

            if exsists:
                conn.send("err exsists".encode(encode_format))
                conn.close()
            else:
                sql="INSERT INTO `players`(  `email`, `password`,`name`) VALUES (%s,%s,%s)"
                value=(acc[1],generate_password_hash(acc[2]),acc[3])

                connection.execute(sql,value)
                dataBase.commit()

                login(conn,acc)


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
            room.players[count].boxes+=int(str(amount[count]).split('-')[0])
            count+=1
        message=message[:-1]
        broadCast(message)
    def waitForPlayers(waitTime):
        #ceka da igrac izvrsi
        wait=True
        counter=0
        while wait:
            wait=False
            for player in room.players:
                if player.action!=1:
                    wait=True
            time.sleep(1)
            counter+=1
            if counter>waitTime:
                break

        for player in room.players:
            player.action=-1

    def resetAnswers():
        for player in room.players:
            player.answer=""
    def checkAnswers(question):
        addBoxes=[]
        for player in room.players:
            foundAnswer=False
            for answer in question[2:]:
                if player.answer==answer:
                    addBoxes.append(str(len(answer))+"- "+player.answer)
                    foundAnswer=True
                    break
            if foundAnswer==False:
                addBoxes.append("0- "+player.answer)

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
                player.died=True
                deducePoints=0
                if player.points>10:
                    deducePoints=random.randrange(6,10)
                    player.points-=deducePoints
                player.coins+=60
                sql=f"UPDATE players SET coins = coins+60,points=points-{deducePoints} WHERE playerId = %s;"
                value=(player.playerId,)
                connection.execute(sql,value)
                dataBase.commit()

                player.conn.send(f"req die:60,-{deducePoints}".encode(encode_format))
                joinRoom("global",player.conn)
    def rewardPlayers():
        for player in room.players:
            reward=player.boxes*3+100
            points=random.randrange(5,8)

            player.points+=points
            player.coins+=reward

            sql=f"UPDATE players SET coins = coins+{reward},points=points+{points} WHERE playerId = %s;"
            value=(player.playerId,)
            connection.execute(sql,value)
            dataBase.commit()

            player.conn.send(f"req win:{reward},{points}".encode(encode_format))


    #ucitaj gameplay scenu
    broadCast("req load gameplay scene")
    waitForPlayers(10)

    #uzmi imena igraca i postavi im da nisu umrli
    playersNames=""
    for player in room.players:
        playersNames+=f"{str(player.name)}-{player.selectedHero},"
        player.boxes=0
        player.died=False
    playersNames=playersNames[:-1]

    #spawnuj igrace sa imenima
    broadCast("req spawn players: "+str(playersNames))
    waitForPlayers(5)

    #daj svim igracima po 3 kutije
    startingBoxes=[]
    for player in room.players:
        startingBoxes.append(f"3-{player.name}")
    addBoxes(startingBoxes) #dodaje pocetne kutije
    waitForPlayers(5)

    round=1
    while True:


        resetAnswers()

        question=random.choice(questions)
        broadCast("req show question:"+question[1])

        waitForPlayers(13)#ceka dok igraci odgovore na pitanje

        boxes=checkAnswers(question)

        addBoxes(boxes)

        waitForPlayers(10)

        removeBoxes(round+2)

        waitForPlayers(5)

        checkIfSomeoneDied()

        round+=1

        if round==5:
            break

        if len(room.players)<=1:
            break

    rewardPlayers()

    room.status="closing"

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
            room.status="inprogress"
            thread_handleGame=threading.Thread(target=handleGame,args=(room,))
            thread_handleGame.start()
        else:
            client.conn.send(f"inf Cant start game,need minimum of {minPlayers}. players!".encode(encode_format))
def setAnswer(conn,answer):
    client=getClient(conn)
    if client.room!="global:":
        client.answer=str(answer).lower()
        confirmAction(conn)
    else:
        client.conn.send("err Cant use this command now!".encode(encode_format))
def confirmAction(conn):
    client=getClient(conn)
    if client.room!="global":
        client.action=1
    else:
        client.conn.send("err Cant use this command now!".encode(encode_format))


#friends
def searchFriends(search,searchBy):
    upit=f"SELECT playerId,name,points FROM players where {searchBy}=%s"
    values=(search,)
    connection.execute(upit,values)
    friends=connection.fetchall()

    #form string
    if friends:
        message="" #load friends search
        for friend in friends:
            message+=f"{friend.get('playerId')}-{friend.get('name')}-{friend.get('points')},"
        message=message[:-1]
        return str(message)
    else:
        message="None"
        return str(message)
def addFriend(_ids):
    def checkIfRequestExsists(): #proverava da li vec postoji zahtev za prijateljstvo
        ids=str(_ids).split(',')
        sql="SELECT requestId FROM friendrequests where sender=%s and receiver=%s"
        values=(ids[0],ids[1])

        connection.execute(sql,values)
        request=connection.fetchone()

        if request:
            return True
        else:
            return False
    def checkToBecameFriends(): #proverava da li vec postoji zahtev za prijateljstvo
        ids=str(_ids).split(',')
        sql="SELECT requestId FROM friendrequests where sender=%s and receiver=%s"
        values=(ids[1],ids[0])

        connection.execute(sql,values)
        request=connection.fetchone()

        if request:
            return True
        else:
            return False

    if checkIfRequestExsists()==False:
        if checkToBecameFriends()==False:
            #dodaj zahtev za prijateljstvo
            ids=str(_ids).split(',')
            sql="INSERT INTO `friendrequests`(`sender`, `receiver`) VALUES (%s,%s)"
            values=(ids[0],ids[1])

            connection.execute(sql,values)
            dataBase.commit()

        else:
            #become friends

            #delete request
            ids=str(_ids).split(',')
            sql="DELETE FROM `friendrequests` WHERE sender=%s and receiver=%s"
            values=(ids[1],ids[0])

            connection.execute(sql,values)
            dataBase.commit()

            #dodaj prijatelja
            sql="UPDATE `players` SET `friends`=friends+%s WHERE playerId=%s"
            value=(ids[0],ids[1])

            connection.execute(sql,value)
            dataBase.commit()

            #dodaj prijatelja
            sql="UPDATE `players` SET `friends`=friends+%s WHERE playerId=%s"
            value=(ids[1],ids[0])

            connection.execute(sql,value)
            dataBase.commit()
def getFriends(client):

    #get ids of friends
    upit=f"SELECT friends FROM players where playerId=%s"
    values=(client.playerId,)
    connection.execute(upit,values)
    friends=connection.fetchone() #friends=id,id,

    #get data of frinds
    ids=friends["friends"].split(',')
    upit="SELECT playerId,name,points FROM players where "
    for id in ids:

        upit+=f"playerId={id} or "

    upit=upit[:-3]

    connection.execute(upit)
    friends=connection.fetchall() #friends=id,id,id

    #form string
    if friends:
        message="" #load friends search
        for friend in friends:
            message+=f"{friend.get('playerId')}-{friend.get('name')}-{friend.get('points')},"
        message=message[:-1]
        return str(message)
    else:
        message="None"
        return str(message)

def handleServerCommands():
    while True:
        command=input()
        if command=="rooms":
            output="----------------\n"
            for room in rooms:
                output+=str(room)+"\n----------------\n"
            print(output)
#-------------------StartsServer

server= socket.socket(socket.AF_INET,socket.SOCK_STREAM) #ozncava da cemo da radimo sa ipv4 adresama i da cemo koristiti TCP
server.bind((host,port)) #binduje server
server.listen() #pokrece

globalRoom=Room("global")
globalRoom.maxPlayers=-1
rooms.append(globalRoom)


thread_handleConnections=threading.Thread(target=newConnection) #slusa za nove konekcije
thread_handleConnections.start()

thread_handleServerCommands=threading.Thread(target=handleServerCommands) #izvrsava serverske komande
thread_handleServerCommands.start()

