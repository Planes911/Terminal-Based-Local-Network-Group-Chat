# Terminal-Based-Local-Network-Group-Chat

A simple terminal-based program that run on local network (LAN/WiFi). Build purely with python using socket TCP and multithreading, with out any external library.
A single device act as the server, while the device get into the same network as client to chatting together and send a private massage.

## Feature

- **Group Chat**: Send a massage to all user online
- **Private Massage (PM)**: Send a message to a specific user with '/pm'
- **List of online users**: Show who is currently connected to the network with '/users'
- **Join/Leave Notification**: All user is notify when someone joining or leaving
- **Validating Name**: Name cannot be empty, no space, maximum  50 characters, no duplicates, and 'SERVER' is reserved
- **Chat from Server Side**: Server/Host operator able to send massage to all users online
- **Timestamp** on all massage
- **No dependencies**: uses only the Python standard library

## Program Structure

```
.
├── server.py   # Server chat (menerima koneksi & meneruskan pesan)
├── client.py   # Client chat (antarmuka terminal untuk user)
└── README.md
```

## Prerequisite
- Python **3.6+** (using f-string)
- All device are in the same network (WiFi/the same LAN)

## How to Run

### 1. Run server

In laptop that becoming the server:

```bash
python server.py
```

### 2. Find Server IP Address

For the other device to be able to connect, you need local IP from server device:

| OS | Commands |
|---|---|
| Windows | `ipconfig` (look for *IPv4 Address*) |
| Linux | `ip a` atau `hostname -I` |
| macOS | `ipconfig getifaddr en0` |

### 3. Run Client

On all device that want to join:

```bash
# Cara 1: with server IP address and port
python client.py 192.168.1.10
python client.py 192.168.1.10 5000

# Cara 2: without server IP address, latter you will be ask for the IP address
python client.py
```
## Client Commands

| Command | Function |
|---|---|
| `<message>` | Send a message to all users |
| `/all <message>` | Send a message to all users (same as above) |
| `/pm <name> <message>` | Send a private message to a specific user |
| `/users` | View the list of online users |
| `/help` | Display help |
| `/quit` | Exit the chat |

## Server Commands

| Command | Function |
|---|---|
| `<message>` | Send a message to all users on behalf of `SERVER` |
| `/users` | View the list of online users |

## Usage Example

```
Server address [127.0.0.1]: 192.168.1.10
Enter name (no spaces): Budi
* Welcome, Budi! There are 2 users online. Type /help for assistance.
> Hello everyone!
[14:32] You: Hello everyone!
[14:32] Siti: Hello Budi!
> /pm Siti want to have lunch together later?
[14:33] (PM to Siti) want to have lunch together later?
[14:33] (PM from Siti) sure, let's meet at 12
```

## How The System Work

### Architecture

The application employs a **client-server** model using the **TCP** protocol:

- The **server** creates a dedicated thread for each connected client, ensuring that one client does not block others. An additional thread is used to handle input from the server console.
- The **client** utilizes two execution flows: a main thread to read user input, and a separate thread to receive messages from the server, allowing incoming messages to be displayed even while the user is typing.
- **Synchronization**: Two `threading.Lock` instances are used—one to protect the list of clients from concurrent access, and another to ensure that messages from different threads do not become intermingled during transmission. Checks for duplicate usernames and the client registration process are performed under a single lock to prevent *race conditions*.

### Message Protocol

Communication uses **line-delimited JSON** (each message is a single JSON object terminated by `\n`) with UTF-8 encoding.

**Client → Server**

| `type` | Field | Description |
|---|---|---|
| `join` | `name` | Register a user name |
| `all` / `msg` | `text` | Message to all users |
| `pm` | `to`, `text` | Private message |
| `users` | - | Request a list of online users |
| `quit` | - | Leave the chat |

**Server → Client**

| `type` | Field | Description |
|---|---|---|
| `join_ok` | - | Name accepted |
| `chat` | `from`, `text`, `time` | Group message |
| `pm` | `from`, `text`, `time` | Received private message |
| `pm_sent` | `to`, `text`, `time` | Confirmation that a private message was sent |
| `info` | `text` | System information |
| `error` | `text` | Error message |

## Writer

**Made By Planes911**
