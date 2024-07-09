import socket

class UserInfo:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        
        self.status = 'offline'
        self.location = None
        self.chatrooms = []

        self.age = '_'
        self.birthday = '_'
        self.job = '_'
        self.phone_number = '_'
        self.self_description = '_'
    
    def view(self)-> str:
        outputstr = '---------------------------------\n'
        outputstr += f'username         : {self.username}\n'
        outputstr += f'age              : {self.age}\n'
        outputstr += f'birthday         : {self.birthday}\n'
        outputstr += f'job              : {self.job}\n'
        outputstr += f'phone_number     : {self.phone_number}\n'
        outputstr += f'self_description : {self.self_description}\n'
        outputstr += '---------------------------------\n'
        return outputstr
    
    def set(self, attr: str, val: list) -> str:
        attr = attr.lower()
        match attr:
            case 'age':
                self.age = val[0]
            case 'birthday':
                self.birthday = val[0]
            case 'job':
                self.job = ' '.join(val)
            case 'phone_number':
                self.phone_number = val[0]
            case 'self_description':
                self.self_description = ' '.join(val)
            case _:
                return 'Invalid attribute(only age, birthday, job, phone_number, self_description available).\n'
        return f'Attribute {attr} set successfully.\n'

class ChatRoom:
    def __init__(self, name: str, owner: str, authority: str):
        self.name = name
        self.owner = owner
        self.authority = authority # {'private', 'public'}
        self.history = []
        self.userdict = {}  # key : file descriptor / value : UserInfo

        self.whitelist = [] # used for private chatroom
        self.blacklist = [] # used for public chatroom

    def enter(self, client: socket.socket, userinfo: UserInfo):

        for fd in self.userdict:
            fd.sendall(f'[System]: {userinfo.username} had enter the chatroom\n'.encode())

        client.sendall('---------------------------------\n'.encode())
        client.sendall(f'Welcome to the chatroom\nChatroom Name: {self.name}\nOwner: {self.owner}\n'.encode())
        client.sendall('---------------------------------\n'.encode())

        history_idx = max(0, len(self.history) - 10)
        for msg in self.history[history_idx:]:
            client.sendall(msg.encode())

        self.userdict[client] = userinfo

    def exit(self, client: socket.socket):
        for fd in self.userdict:
            fd.sendall(f'[System]: {self.userdict[client].username} had left the chatroom\n'.encode())

        del self.userdict[client]

    def list_user(self, client: socket.socket):
        outputstr = '---------------------------------\n'
        outputstr += 'username | status\n'
        for fd in self.userdict:
            outputstr += f'{self.userdict[fd].username} | {self.userdict[fd].status}\n'
        outputstr += '---------------------------------\n'

        client.sendall(outputstr.encode())

    def chat_message(self, client: socket.socket, message: str):
        for fd in self.userdict:
            fd.sendall(f'<{self.userdict[client].username}>: {message}'.encode())
        
        self.history.append(f'<{self.userdict[client].username}>: {message}')

    # Access Control Method

    def get_access_control_list(self, client: socket.socket):
        if self.authority == 'private':
            outputstr = '---------------------------------\n'
            outputstr += 'Permitted Users:\n'
            for username in self.whitelist:
                outputstr += (username + '  ')
            outputstr += '\n---------------------------------\n'

        elif self.authority == 'public':
            outputstr = '---------------------------------\n'
            outputstr += 'Banned Users:\n'
            for username in self.blacklist:
                outputstr += (username + '  ')
            outputstr += '\n---------------------------------\n'
        else:
            outputstr = 'Unknown chatroom authority.\n'
        
        client.sendall(outputstr.encode())

    def add_user(self, client: socket.socket, username: str):
        if self.authority == 'private':
            if username not in self.whitelist:
                self.whitelist.append(username)
                outputstr = 'The user is added to the whitelist successfully.\n'
            else:
                outputstr = 'The user is already in the whitelist.\n'
        elif self.authority == 'public':
            if username in self.blacklist:
                self.blacklist.remove(username)
                outputstr = 'The user is removed from the blacklist successfully.\n'
            else:
                outputstr = 'The user is already not in the blacklist.\n'
        else:
            outputstr = 'Unknown chatroom authority.\n'

        client.sendall(outputstr.encode())

    def remove_user(self, client: socket.socket, username: str):
        if self.authority == 'private':
            if username in self.whitelist:
                self.whitelist.remove(username)
                outputstr = 'The user is removed from the whitelist successfully.\n'
            else:
                outputstr = 'The user is already not in the whitelist.\n'
        elif self.authority == 'public':
            if username not in self.blacklist:
                self.blacklist.append(username)
                outputstr = 'The user is added to the blacklist successfully.\n'
            else:
                outputstr = 'The user is already in the blacklist.\n'
        else:
            outputstr = 'Unknown chatroom authority.\n'

        client.sendall(outputstr.encode())

    def kick_user(self, username: str)-> socket.socket:
        for fd in self.userdict:
            if self.userdict[fd].username == username:
                self.exit(fd)
                return fd
        
        return None

    def find_user(self, username: str)-> bool:
        is_here = False

        for fd in self.userdict:
            if self.userdict[fd].username == username:
                is_here = True
                break

        return is_here
            