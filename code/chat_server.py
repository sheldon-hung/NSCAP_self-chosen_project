import socket
import select

from static_messages import *
from datastructures import *

def register(client: socket.socket, username: str, password:str):
    if username in usertable:
        client.sendall('Username is already used.\n'.encode())
        return
    else:
        usertable[username] = UserInfo(username, password)
        client.sendall('Register successfully.\n'.encode())

def login(client: socket.socket, username: str, password:str):
    if userdict[client] != None:
        client.sendall('Account is already logged in.'.encode())
        return

    if (username in usertable) and (usertable[username].password == password):
        usertable[username].status = 'online'
        userdict[client] = usertable[username]

        client.sendall(f'Welcome, {username}.\n'.encode())
    else:
        client.sendall('Wrong username or password.\n'.encode())

def logout(client: socket.socket):
    username = userdict[client].username
    userdict[client].status = 'offline'
    userdict[client].location = None
    usertable[username] = userdict[client]
    userdict[client] = None

    client.sendall(f'Bye, {username}.\n'.encode())

def client_handle(client: socket.socket, data: str):
    if userdict[client] is None:
        identified = False
    else:
        identified = True
        userinfo = userdict[client]

    if identified and (userinfo.location is not None): # user is in chatroom
        if data[0] == '/':
            cmd = data.split()

            match cmd[0]:
                case '/exit-chatroom':
                    if len(cmd) != 1:
                        client.sendall('Usage: /exit-chatroom\n'.encode())
                    else:
                        chatroomtable[userinfo.location].exit(client)

                        userinfo.location = None
                        userdict[client].location = None

                        client.sendall('% '.encode())
                case '/list-user':
                    if len(cmd) != 1:
                        client.sendall('Usage: /list-user\n'.encode())
                    else:
                        chatroomtable[userinfo.location].list_user(client)
                case '/get-whitelist':
                    if len(cmd) != 1:
                        client.sendall('Usage: /get-whitelist\n'.encode())
                    elif chatroomtable[userinfo.location].authority == 'public':
                        client.sendall('The chatroom is public(no whitelist).\n'.encode())
                    else:
                        chatroomtable[userinfo.location].get_access_control_list(client)
                case '/get-blacklist':
                    if len(cmd) != 1:
                        client.sendall('Usage: /get-blacklist\n'.encode())
                    elif chatroomtable[userinfo.location].authority == 'private':
                        client.sendall('The chatroom is private(no blacklist).\n'.encode())
                    else:
                        chatroomtable[userinfo.location].get_access_control_list(client)
                case '/kick-user':
                    if len(cmd) != 2:
                        client.sendall('Usage: /kick-user <username>\n'.encode())
                    elif chatroomtable[userinfo.location].owner != userinfo.username:
                        client.sendall('Only the owner can use this command.'.encode())
                    elif cmd[1] not in usertable:
                        client.sendall('The user does not exist.'.encode())
                    elif not chatroomtable[userinfo.location].find_user(cmd[1]):
                        client.sendall('The user is not in the chatroom.'.encode())
                    else:
                        fd = chatroomtable[userinfo.location].kick_user(cmd[1])

                        userdict[fd].location = None

                        fd.sendall('You are kicked out from the chatroom\n'.encode())
                        fd.sendall('% '.encode())
                case '/ban-user':
                    if len(cmd) != 2:
                        client.sendall('Usage: /ban-user <username>\n'.encode())
                    elif chatroomtable[userinfo.location].owner != userinfo.username:
                        client.sendall('Only the owner can use this command.'.encode())
                    elif cmd[1] not in usertable:
                        client.sendall('The user does not exist.'.encode())
                    else:
                        chatroomtable[userinfo.location].remove_user(client, cmd[1])

                        fd = chatroomtable[userinfo.location].kick_user(cmd[1])

                        if fd: # The user was in the chatroom
                            userdict[fd].location = None

                            fd.sendall('You are kicked out from the chatroom'.encode())
                            fd.sendall('% '.encode())
                case '/permit-user':
                    if len(cmd) != 2:
                        client.sendall('Usage: /permit-user <username>\n'.encode())
                    elif chatroomtable[userinfo.location].owner != userinfo.username:
                        client.sendall('Only the owner can use this command.'.encode())
                    elif cmd[1] not in usertable:
                        client.sendall('The user does not exist.'.encode())
                    else:
                        chatroomtable[userinfo.location].add_user(client, cmd[1])
                case '/help':
                    if len(cmd) != 1:
                        client.sendall('Usage: help\n'.encode())
                    else:
                        client.sendall(chatroom_help_message.encode())
                case _:
                    client.sendall('Unknown command\nUse "help" command to get more command information\n'.encode())
        else:
            message = data

            chatroomtable[userinfo.location].chat_message(client, message)
        
    else:   # user is not in chatroom
        cmd = data.split()

        if len(cmd) == 0:
            client.sendall('% '.encode())
            return

        match cmd[0]:
            case 'register':
                if len(cmd) != 3:
                    client.sendall('Usage: register <username> <password>\n'.encode())
                else:
                    register(client, cmd[1], cmd[2])
                
                client.sendall('% '.encode())
            case 'login':
                if len(cmd) != 3:
                    client.sendall('Usage: login <username> <password>\n'.encode())
                elif identified:
                    client.sendall('Please logout first.\n'.encode())
                else:
                    login(client, cmd[1], cmd[2])
                
                client.sendall('% '.encode())
            case 'logout':
                if len(cmd) != 1:
                    client.sendall('Usage: logout\n'.encode())
                elif not identified:
                    client.sendall('Please login first.\n'.encode())
                else:
                    logout(client)

                client.sendall('% '.encode())
            case 'exit':
                if len(cmd) != 1:
                    client.sendall('Usage: exit\n'.encode())
                else:
                    if identified:
                        logout(client)
                    
                    client.close()
                    clients.remove(client)
                    del userdict[client]
            case 'whoami':
                if len(cmd) != 1:
                    client.sendall('Usage: whoami\n'.encode())
                elif not identified:
                    client.sendall('Please login first.\n'.encode())
                else:
                    client.sendall(f'{userdict[client].view()}'.encode())

                client.sendall('% '.encode())
            case 'set-profile':
                if len(cmd) != 3:
                    client.sendall('Usage: set-profile\n'.encode())
                elif not identified:
                    client.sendall('Please login first.\n'.encode())
                else:
                    outputstr = userdict[client].set(cmd[1], cmd[2:])
                    usertable[userinfo.username].set(cmd[1], cmd[2:])

                    client.sendall(f'{outputstr}'.encode())
                client.sendall('% '.encode())
            case 'view-profile':
                if len(cmd) != 2:
                    client.sendall('Usage: view-profile <username>\n'.encode())
                elif not identified:
                    client.sendall('Please login first.\n'.encode())
                else:
                    client.sendall(f'{usertable[cmd[1]].view()}'.encode())
                client.sendall('% '.encode())
            case 'list-user':
                if len(cmd) != 1:
                    client.sendall('Usage: list-user\n'.encode())
                elif not identified:
                    client.sendall('Please login first.\n'.encode())
                else:
                    outputstr = '---------------------------------\n'
                    outputstr += 'username | status\n'
                    for user in usertable:
                        outputstr += f'{usertable[user].username} {usertable[user].status}\n'
                    outputstr += '---------------------------------\n'

                    client.sendall(outputstr.encode())

                client.sendall('% '.encode())
            case 'open-chatroom':
                if len(cmd) != 3:
                    client.sendall('Usage: open-chatroom <chatroom name> <public or private>\n'.encode())
                elif not identified:
                    client.sendall('Please login first.\n'.encode())
                elif cmd[1] in chatroomtable:
                    client.sendall('Chatroom name is already used.\n'.encode())
                elif cmd[2] != 'private' and cmd[2] != 'public':
                    client.sendall('Invalid chatroom authority (private or public only)\n'.encode())
                else:
                    chatroomtable[cmd[1]] = ChatRoom(cmd[1], userinfo.username, cmd[2])

                    userinfo.chatrooms.append(cmd[1])
                    userdict[client].chatrooms.append(cmd[1])

                    client.sendall('Chatroom opened succesfully.\n'.encode())
                
                client.sendall('% '.encode())
            case 'list-chatroom':
                if len(cmd) != 1:
                    client.sendall('Usage: list-chatroom\n'.encode())
                elif not identified:
                    client.sendall('Please login first.\n'.encode())
                else:
                    outputstr = '---------------------------------\n'
                    for chatroom in chatroomtable:
                        outputstr += 'chatroom name | owner | authority\n'
                        outputstr += f'{chatroomtable[chatroom].name} | {chatroomtable[chatroom].owner} | {chatroomtable[chatroom].authority}\n'
                    outputstr += '---------------------------------\n'

                    client.sendall(outputstr.encode())

                client.sendall('% '.encode())
            case 'enter-chatroom':
                if len(cmd) != 2:
                    client.sendall('Usage: enter-chatroom <chatroom name>\n'.encode())
                    client.sendall('% '.encode())
                elif cmd[1] not in chatroomtable:
                    client.sendall('The chatroom does not exist\n'.encode())
                    client.sendall('% '.encode())
                elif not identified:
                    client.sendall('Please login first.\n'.encode())
                    client.sendall('% '.encode())
                elif (chatroomtable[cmd[1]].authority == 'private') and \
                    (chatroomtable[cmd[1]].owner != userinfo.username) and \
                    (userinfo.username not in chatroomtable[cmd[1]].whitelist):

                    client.sendall(f'You do not have the permission.\n'.encode())
                    client.sendall('% '.encode())
                elif (chatroomtable[cmd[1]].authority == 'public') and \
                    (userinfo.username in chatroomtable[cmd[1]].blacklist):

                    client.sendall(f'You are banned from the chatroom.\n'.encode())
                    
                    client.sendall('% '.encode())
                else:
                    userinfo.location = cmd[1]
                    userdict[client].location = cmd[1]

                    chatroomtable[cmd[1]].enter(client, userinfo)
            case 'close-chatroom':
                if len(cmd) != 2:
                    client.sendall('Usage: close-chatroom <chatroom name>\n'.encode())
                elif not identified:
                    client.sendall('Please login first.\n'.encode())
                elif cmd[1] not in chatroomtable:
                    client.sendall('The chatroom does not exist.\n'.encode())
                elif chatroomtable[cmd[1]].owner != userinfo.username:
                    client.sendall('Only the owner can close this chatroom.\n'.encode())
                else:
                    for fd in chatroomtable[cmd[1]].userdict:
                        fd.sendall('[System]: The chatroom was closed\n'.encode())
                        userdict[fd].location = None

                    del chatroomtable[cmd[1]]

                    userinfo.chatrooms.remove(cmd[1])
                    userdict[client].chatrooms.remove(cmd[1])

                    client.sendall('The chatroom was closed\n'.encode())

                client.sendall('% '.encode())
            case 'help':
                if len(cmd) != 1:
                    client.sendall('Usage: help\n'.encode())
                else:
                    client.sendall(help_message.encode())
                
                client.sendall('% '.encode())
            case _:
                client.sendall('Unknown command\nUse "help" command to get more command information\n'.encode())
                client.sendall('% '.encode())
        
        cmd.clear()

if __name__ == '__main__':

    host = '0.0.0.0'
    port = 12345

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()

    clients = [server]

    usertable = {}       # key : username / value : userinfo
    userdict = {}        # key : socketfd / value : userinfo
    chatroomtable = {}   # key : chatroom name / value : chatroom

    while True:
        readable, _, _ = select.select(clients, [], [])

        for sockfd in readable:

            if sockfd == server: # new connection

                client, _ = server.accept()
                clients.append(client)

                userdict[client] = None     # add a new user that haven't login

                client.sendall(welcome_message.encode())
                client.sendall('% '.encode())        # show command prompt

            else:

                data = sockfd.recv(1024)

                if data:
                    client_handle(sockfd, data.decode())
                else:
                    sockfd.close()
                    clients.remove(sockfd)

                    del userdict[sockfd]    # remove a user
