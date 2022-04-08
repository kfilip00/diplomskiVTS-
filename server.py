import socket
import threading
import json
import questionsAndAnswers
import random
import mysql.connector
from werkzeug.security import generate_password_hash,check_password_hash
import time
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


#-------------------Classes
class Room:
    def __init__(self,name):
        self.name=name
        self.players=[]
        self.status="open"

    def __str__(self):
        players=""
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
    def __init__(self,conn,name,playerId,friends,coins,points,boughtItems,selectedHero,gamesPlayed,gamesWon):
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
        #self.died=False
        self.gamesPlayed=gamesPlayed
        self.gamesWon=gamesWon

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
leaderboardPoints=[]
leaderboardWinrate=[]
questions=questionsAndAnswers.questions

#email
sender = "rr2inaf0001@gmail.com"
senderPass="Rr2rr2111"

#-------------------Functions

#rooms
def joinRoom(name,conn,invited=False):
    global maxPlayers
    for room in rooms:
        if room.name==name:
            if room.status=="full":
                clientSendMessage(conn,f"inf Room \"{room.name}\" is full!")
                return
            if room.status=="closed" and invited==False:
                clientSendMessage(conn,f"inf Room \"{room.name}\" is closed!")
                return
            if room.status=="inprogress":
                clientSendMessage(conn,f"inf Room \"{room.name}\" is in progress!")
                return
            client=getClient(conn)
            if client.room==name:
                clientSendMessage(conn,f"inf Already in room \"{name}\"")
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
                    clientSendMessage(player.conn,str(mess))

                if len(room.players)==maxPlayers:
                    startGame(conn)

            return

    clientSendMessage(conn,f"inf Cloudnt find room with name \"{name}\"")
def joinRandomRoom(conn):
    counter=0
    while True:
        if len(rooms)==1:
            clientSendMessage(conn,"inf No available room found,try again or create one")
            break
        room = rooms[random.randrange(1, len(rooms))]
        if len(room.players)<maxPlayers and room.status=="open":
            joinRoom(room.name,conn)
            break
        counter+=1
        if counter==10:
            clientSendMessage(conn,"inf No available room found,try again or create one")
            break
def createRoom(name,conn,closed=False):
    for room in rooms:
        if room.name==name:
            clientSendMessage(conn,"inf Room with this name already exsists!")
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

    if room.status=="inprogress": #and client.died==False:
        mess=f"req rpg:{clientIndex}" #remove player in game
        print(client.name+" has left,kick him")
        for player in room.players:
            clientSendMessage(player.conn,str(mess))

        deducePoints=0
        if client.points>10:
            deducePoints=random.randrange(6,10)
            client.points-=deducePoints
        sql=f"UPDATE players SET points=points-{deducePoints} WHERE playerId = %s;"
        value=(client.playerId,)
        connection.execute(sql,value)
        dataBase.commit()
        clientSendMessage(client.conn,f"req die:0,-{deducePoints}")


    elif room.status!="inprogress":
        mess="req lpl:" #load players in lobby
        if room.name!="global" and room.status!="closing":
            for player in room.players:
                mess+=player.name+","
            mess=mess[:-1]

            for player in room.players:
                clientSendMessage(player.conn,str(mess))

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
                elif command=="/qu": #izadji iz igrice (kopletno)jjikj,ikjjju, , j,,kj,kj uj jju
                    kickClient(conn)
                elif command=="/st": #pocni igru
                    startGame(conn)
                elif command=="/ca": #potvrdi izvresenu komandu
                    confirmAction(conn)
                elif command=="/an":
                    answer=message[4:]
                    setAnswer(conn,answer)
                elif command=="/si": # trazi prijatelje po idu
                    id=message[4:]
                    clientSendMessage(conn,f"req lfs:{searchFriends(search=id,searchBy='playerId')}")
                elif command=="/sn": #trazi prijatelje po imenu
                    name=message[4:]
                    clientSendMessage(conn,f"req lfs:{searchFriends(search=name,searchBy='name')}")
                elif command=="/af": #dodaj drugara
                    id=message[4:]
                    addFriend(id,conn)
                elif command=="/gf": #pokupi prijatelje
                    result=getFriends(getClient(conn))
                    clientSendMessage(conn,f"req lfm:{result}")
                elif command=="/iv":
                    id=int(message[4:])
                    inviteClient(client=getClient(conn),id=id)
                elif command=="/gp": #trazi leaderboard za pointse
                    clientSendMessage(conn,f"req ulp:{getLeaderBoardPoints()}")
                elif command=="/gw": #trazi leaderboard za pointse
                    clientSendMessage(conn,f"req ulw:{getLeaderBoardWinRate()}")
            else:
                    clientSendMessage(conn,"inf Wrong command!")
        except:

            break
def login(conn,acc):
    sql="SELECT * FROM players where email=%s"
    value=(acc[1],)

    connection.execute(sql,value)
    account=connection.fetchone()

    if account:
        if(check_password_hash(account["password"],acc[2])):
            #create client object
            client=Client(conn=conn,name=account["name"],playerId=account["playerId"],friends=account["friends"],
                          coins=account["coins"],
                          points=account["points"],
                          boughtItems=account["boughtItems"],
                          selectedHero=account["selectedHero"],
                          gamesPlayed=account["gamesPlayed"],
                          gamesWon=account["gamesWon"])
            clients.append(client)
            account["friends"]=client.friends=getFriends(getClient(conn))
            account.pop("password")
            clientSendMessage(client.conn,f"inf connected/{json.dumps(account)}")

            #pravi novi thread za klijenta kako bi mogao da opsluzi novog klijenta

            thread = threading.Thread(target=handleClient,args=(client.conn,))
            thread.start()
        else:
            clientSendMessage(conn,"err cre")
            conn.close()
    else:
        clientSendMessage(conn.send,"err cre")
        conn.close()
def newConnection():
    print(f"Server started on port {port}")

    while True:
        conn,address = server.accept() #ceka dok ne dodje do neke konekcije
        clientSendMessage(conn,"req acc")
        acc=conn.recv(1024).decode(encode_format).split(",") #ocekuje reg/log,email,lozinka,?nick
        if acc[0]=="/log":
            login(conn,acc)
        elif acc[0]=="/rp":
            thread_handlePasswordReset=threading.Thread(target=handlePasswordReset,args=(conn,acc[1]))
            thread_handlePasswordReset.start()
        else:
            thread_hadleAccountCreation=threading.Thread(target=handleAccountCreation,args=(conn,acc))
            thread_hadleAccountCreation.start()
def clientSendMessage(conn,message):
    try:
        conn.send(str(message).encode(encode_format))
        return True
    except:
        kickClient(conn)
        return False
def getClient(conn):
    for client in clients:
        if client.getConn() == conn:
            return client
def kickClient(conn):
    try:
        client=getClient(conn)
        leaveRoom(client)
        clients.remove(client)
    except:
        pass
        #client already left
def quitClient(conn):
    client=getClient(conn)
    clients.remove(client)
    clientSendMessage(conn,"req quit")
    conn.close()
def inviteClient(client,id): #client->sender,id->invited
    if client.room!="global":
        #check if room si closed
        room=None
        for _room in rooms:
            if _room.name==client.room:
                room=_room
        if room.status=="open":
            clientSendMessage(client.conn,"inf cio") #cant invite from open room
            return
        #get invited's client id
        clientInvited=None
        for _client in clients:
            if _client.playerId==id:
                clientInvited=_client

        if clientInvited:
            if clientInvited.room=="global":
                clientSendMessage(clientInvited.conn,f"req inv:{client.name},{client.room}")
            else:
                clientSendMessage(client.conn,f"inf iva:{clientInvited.name} is already in a room!")
        else:
            #clientInvited closed game,tell client to update friends list
            result=getFriends(getClient(client.conn))
            clientSendMessage(client.conn,f"req lfm:{result}")
    else:
        clientSendMessage(client.conn,"inf cig") #cant invite from global room
def handleAccountCreation(conn,acc):
    #proveri da li emajl vec postoji
    sql="SELECT email from players where email=%s"
    value=(acc[1],)

    connection.execute(sql,value)
    exsists=connection.fetchall()

    if exsists:
        clientSendMessage(conn,"err exs") #client with this email already exsists
        conn.close()
    else:
        verificationNumber=random.randrange(100000,999999)
        if sendEmail(receiver=acc[1],subject="Account verification",text=f"Hello {acc[3]},\n \nYour verification code is:{verificationNumber}\n \nIf you didnt create account in 'gamename' please ignore this message."):
            while True:
                try:
                    clientSendMessage(conn,"req ver") #request verification
                    answer=conn.recv(1024).decode(encode_format)
                    if(answer==str(verificationNumber)):
                        sql="INSERT INTO `players`(  `email`, `password`,`name`) VALUES (%s,%s,%s)"
                        value=(acc[1],generate_password_hash(acc[2]),acc[3])

                        connection.execute(sql,value)
                        dataBase.commit()

                        sendEmail(receiver=acc[1],subject="Account information",text=f"Wellcome!\n\nThank you for playing our game,your account informations:\n\nemail:{acc[1]}\n\npassword:{acc[2]}\n\nPlease dont share this information with anyone!")

                        login(conn,acc)
                        return
                    elif (answer=="cancel"):
                        conn.close()
                        break
                    else:
                        clientSendMessage(conn,"inf vvr") #inform client that he sent wrong verification
                except:
                    break
        else:
            clientSendMessage(conn,"inf wve") # wrong verification email
def handlePasswordReset(conn,email):
    #proveri da li emajl vec postoji
    sql="SELECT email from players where email=%s"
    value=(email,)

    connection.execute(sql,value)
    exsists=connection.fetchall()
    if exsists:
        verificationNumber=random.randrange(100000,999999)
        if sendEmail(receiver=email,subject="Account password reset",text=f"Hello,\n\nYou requested password reset,\n\nyour verification code is:{verificationNumber}\n \nIf you didnt request password reset please ignore this message."):
            while True:
                clientSendMessage(conn,"req prc") #request password reset code
                try:
                    mess=conn.recv(1024).decode(encode_format)
                    if mess=="cancel":
                        conn.close()
                        break
                    else:
                        answer=mess.split(',') #answer=verification code,new password
                        if(answer[0]==str(verificationNumber)):
                            sql="UPDATE `players` SET `password`=%s WHERE email=%s"
                            value=(generate_password_hash(answer[1]),email)

                            connection.execute(sql,value)
                            dataBase.commit()

                            sendEmail(receiver=email,subject="Account password reseted",text=f"Password has been successfully changed\n\nNew password:{answer[1]}")
                            login(conn,("/log",email,answer[1]))
                            return
                        else:
                            clientSendMessage(conn,"inf vvp") #inform client that he sent wrong verification
                except:
                    break
        else:
            clientSendMessage(conn,"inf wve") # wrong verification email
    else:
        clientSendMessage(conn,"err edx") #email doesnt exsists
        conn.close()

#game
def handleGame(room):
    def broadCast(mess):
        for player in room.players:
            clientSendMessage(player.conn,str(mess))
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
        kickPlayers=[]
        for player in room.players:
            if player.boxes<0:
                kickPlayers.append(player)
                #player.died=True
                deducePoints=0
                if player.points>10:
                    deducePoints=random.randrange(6,10)
                    player.points-=deducePoints
                player.coins+=60

                clientSendMessage(player.conn,f"req die:60,-{deducePoints}")

                sql=f"UPDATE players SET coins = coins+60,points=points-{deducePoints} WHERE playerId = %s;"
                value=(player.playerId,)
                connection.execute(sql,value)
                dataBase.commit()

        for player in kickPlayers:
            joinRoom("global",player.conn)

    def rewardPlayers():
        upit="UPDATE `players` SET `gamesWon`=gamesWon + 1 where "
        for player in room.players:
            upit+=f"playerId={player.playerId} or "
            reward=player.boxes*3+100
            points=random.randrange(5,8)

            player.points+=points
            player.coins+=reward

            clientSendMessage(player.conn,f"req win:{reward},{points}")

            sql=f"UPDATE players SET coins = coins+{reward},points=points+{points} WHERE playerId = %s;"
            value=(player.playerId,)
            connection.execute(sql,value)
            dataBase.commit()

        upit=upit[:-3]
        connection.execute(upit)
        dataBase.commit()

    #update gamesplayer
    upit="UPDATE `players` SET `gamesPlayed`=gamesPlayed + 1 where "
    for player in room.players:
        upit+=f"playerId={player.playerId} or "
    upit=upit[:-3]
    connection.execute(upit)
    dataBase.commit()

    #ucitaj gameplay scenu
    broadCast("req load gameplay scene")
    waitForPlayers(10)

    #uzmi imena igraca i postavi im da nisu umrli
    playersNames=""
    for player in room.players:
        playersNames+=f"{str(player.name)}-{player.selectedHero},"
        player.boxes=0
        #player.died=False
    playersNames=playersNames[:-1]

    #spawnuj igrace sa imenima
    broadCast("req spawn players:"+str(playersNames))
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

    if len(room.players)==0:
        return
    rewardPlayers()
    room.status="closing"
    #close game
    playersClose=list.copy(room.players)
    for player in playersClose:
        joinRoom("global",player.conn)
def startGame(conn):
    global minPlayers
    client=getClient(conn)
    room=getRoom(client.room)
    if room.name=="global": #ne radi
        clientSendMessage(conn,f"err Cant start game from \"{room.name}\" room!")
        return
    else:
        if len(room.players)>=minPlayers:
            room.status="inprogress"
            thread_handleGame=threading.Thread(target=handleGame,args=(room,))
            thread_handleGame.start()
        else:
            clientSendMessage(client.conn,f"inf Cant start game,need minimum of {minPlayers}. players!")
def setAnswer(conn,answer):
    client=getClient(conn)
    if client.room!="global:":
        client.answer=str(answer).lower()
        confirmAction(conn)
    else:
        clientSendMessage(client.conn,"err Cant use this command now!")
def confirmAction(conn):
    client=getClient(conn)
    if client.room!="global":
        client.action=1
    else:
        clientSendMessage(client.conn,"err Cant use this command now!")


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
def addFriend(_ids,conn):
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
            sql="UPDATE players SET friends = CONCAT(friends, ','),friends = CONCAT(friends, %s) WHERE playerId=%s"
            value=(ids[0],ids[1])

            connection.execute(sql,value)
            dataBase.commit()

            #dodaj prijatelja
            sql="UPDATE players SET friends = CONCAT(friends, ','),friends = CONCAT(friends, %s) WHERE playerId=%s"
            value=(ids[1],ids[0])

            connection.execute(sql,value)
            dataBase.commit()

            #updejtuj prijatelje na klijentu
            result=getFriends(getClient(conn))
            clientSendMessage(conn,f"req lfm:{result}")
def getFriends(client):

    #get ids of friends
    upit=f"SELECT friends FROM players where playerId=%s"
    values=(client.playerId,)
    connection.execute(upit,values)
    friends=connection.fetchone() #friends=id,id,

    if friends["friends"]!= "0":
        #get data of frinds
        ids=friends["friends"].split(',')
        upit="SELECT playerId,name,points FROM players where "
        for id in ids:
            if str(id)!="0":
                upit+=f"playerId={id} or "
        upit=upit[:-3]
        connection.execute(upit)
        friends=connection.fetchall() #friends=id,id,id

        #form string
        if friends:
            message="" #load friends search
            for friend in friends:
                online=checkIfFriendIsOnline(friend.get('playerId'))
                message+=f"{friend.get('playerId')}-{friend.get('name')}-{friend.get('points')}-{online},"
            message=message[:-1]
            return str(message)
        else:
            message="None"
            return str(message)
    else:
        message="None"
        return str(message)
def checkIfFriendIsOnline(friendId):
    for client in clients:
        if friendId==client.playerId:
            return True
    return False

#leaderboard
def updateLeaderBoardPoints():
    #select data from all clients
    sql="SELECT name,points from players"
    connection.execute(sql)
    playersScores=connection.fetchall()

    #update leaderboard
    for playerScore in playersScores:
        for score in leaderboardPoints:
            if playerScore.get('points')>score[1]:
                leaderboardPoints.insert(leaderboardPoints.index(score),[str(playerScore.get('name')),int(playerScore.get('points'))])
                break
        del leaderboardPoints[10:]
def updateLeaderBoardWinrate():
    #select data from all clients
    sql="SELECT name,gamesPlayed,gamesWon from players"
    connection.execute(sql)
    playersScores=connection.fetchall()

    #update leaderboard
    for playerScore in playersScores:
        if playerScore.get('gamesPlayed')>=100: #minimalno 100 gejmova mora da se odigra kako bi usao u statistiku
            winrate=int((int(playerScore.get('gamesWon'))/int(playerScore.get('gamesPlayed')))*100)
            for score in leaderboardWinrate:
                if winrate>score[1]:
                    leaderboardWinrate.insert(leaderboardWinrate.index(score),[str(playerScore.get('name')),winrate])
                    break
            del leaderboardWinrate[10:]
def getLeaderBoardPoints():
    scores=""
    for score in leaderboardPoints:
        scores+=f"{score[0]},{score[1]}-"
    scores=scores[:-1]
    return scores
def getLeaderBoardWinRate():
    scores=""
    for score in leaderboardWinrate:
        scores+=f"{score[0]},{score[1]}-"
    scores=scores[:-1]
    return scores
def handleUpdates():
    updateLeaderBoardPoints()
    updateLeaderBoardWinrate()
    lastUpdate=datetime.now()
    while True:
        currentTime = datetime.now()
        if((currentTime.day>lastUpdate.day or currentTime.month>lastUpdate.month or currentTime.year>lastUpdate.year) and currentTime.hour>=13):
            updateLeaderBoardPoints()
            updateLeaderBoardWinrate()
        time.sleep(60)


#email
def sendEmail(receiver,text,subject):
    try:
        message = MIMEMultipart()
        message['From'] = sender
        message['To'] = receiver
        message['Subject'] = subject
        message.attach(MIMEText(text, 'plain'))
        session = smtplib.SMTP('smtp.gmail.com', 587)
        session.starttls()
        session.login(sender, senderPass) #login with mail_id and password
        text = message.as_string()
        session.sendmail(sender, receiver, text)
        session.quit()
        return True
    except:
        return False

def handleServerCommands():
    while True:
        command=input()
        if command=="get rooms":
            output="----------------\n"
            for room in rooms:
                output+=str(room)+"\n----------------\n"
            print(output)
        if command=="get leaderboard points":
            output="----------------\n"
            for score in leaderboardPoints:
                output+=str(score)+"\n----------------\n"
            print(output)
        if command=="get leaderboard winrate":
            output="----------------\n"
            for score in leaderboardWinrate:
                output+=str(score)+"\n----------------\n"
            print(output)
        if command=="get clients":
            output="----------------\n"
            if len(clients)>0:
                for client in clients:
                    output+=str(client)+"\n----------------\n"
            else:
                output+="None"
            print(output)
#-------------------StartsServer

server= socket.socket(socket.AF_INET,socket.SOCK_STREAM) #ozncava da cemo da radimo sa ipv4 adresama i da cemo koristiti TCP
server.bind((host,port)) #binduje server
server.listen() #pokrece

globalRoom=Room("global")
globalRoom.maxPlayers=-1
rooms.append(globalRoom)

#set def leaderboard for points
for i in range(10):
    leaderboardPoints.append(["placeHolder",0])

#set def leaderboard for win rate
for i in range(10):
    leaderboardWinrate.append(["placeHolder",0])


thread_handleUpdates=threading.Thread(target=handleUpdates) #jednom dnevno updejtuje leaderboarde
thread_handleUpdates.start()


thread_handleConnections=threading.Thread(target=newConnection) #slusa za nove konekcije
thread_handleConnections.start()

thread_handleServerCommands=threading.Thread(target=handleServerCommands) #izvrsava serverske komande
thread_handleServerCommands.start()

