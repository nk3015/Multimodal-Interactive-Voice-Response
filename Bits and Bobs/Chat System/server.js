// server.js
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

const PORT = process.env.PORT || 3000;

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const users = {};

io.on('connection', (socket) => {
    console.log('New connection');
    
    socket.on('join', (username) => {
        if (Object.values(users).includes(username)) {
            socket.emit('username-taken');
            return;
        }
        
        users[socket.id] = username;
        socket.broadcast.emit('user-joined', username);
        io.emit('update-users', Object.values(users));
        socket.emit('welcome', `Welcome to the chat, ${username}!`);
    });
    
    socket.on('send-message', (message) => {
        const username = users[socket.id];
        if (!username) return;
        
        // Broadcast to others, don't echo back to sender
        socket.broadcast.emit('receive-message', { 
            username, 
            message,
            timestamp: new Date().toLocaleTimeString()
        });
    });
    
    socket.on('disconnect', () => {
        const username = users[socket.id];
        if (username) {
            delete users[socket.id];
            socket.broadcast.emit('user-left', username);
            io.emit('update-users', Object.values(users));
        }
    });
});

server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});