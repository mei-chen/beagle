const http = require('http');
const redis = require('redis');
const url = require("url");
const log4js = require('log4js');
const cookie_reader = require('cookie');

const logger = log4js.getLogger();
const config = {
  listen_port: 4000,
  redis_url: 'redis://localhost:6379'
};

if(process.env.REDIS_URL) {
    config.redis_url = process.env.REDIS_URL;
}

const server = http.createServer().listen(config.listen_port);

// Create the server
if (server) {
    logger.info("Listening on port " + config.listen_port);
} else {
    logger.error("Could not start server. Exiting ...");
    process.exit(1);
}

const io = require('socket.io').listen(server);

if (io) {
    logger.info('Started socket.io');
} else {
    logger.error('Could not start socket.io. Exiting ...');
    process.exit(1);
}

//Configure socket.io to store cookie set by Django
io.set('authorization', function(data, accept){
    if(data.headers.cookie){
        data.cookie = cookie_reader.parse(data.headers.cookie);

        if (!('sessionid' in data.cookie)) {
            return accept('error', false);
        }

        logger.info("Accepting connection");
        return accept(null, true);
    }
    logger.warn("Not accepting connection")
    return accept('error', false);
});

logger.info('Starting connection');

io.sockets.on('connection', function (socket) {
  const channel = redis.createClient(config.redis_url);
  channel.subscribe('user-notifications.' + socket.conn.request.cookie['sessionid']);
  logger.info('Subscribed to user-notifications.' + socket.conn.request.cookie['sessionid']);

  channel.on('message', function(channel, payload){
    console.log(payload);
    const { event_name, message } = JSON.parse(payload);
    logger.info('Sending to: ', socket.conn.request.cookie['sessionid'], 'message=', message, socket.id);
    socket.emit('message', JSON.parse(payload));
  })

  socket.on('disconnect', function () {
    logger.info("Closing connection");
    channel.unsubscribe('user-notifications.' + socket.conn.request.cookie['sessionid']);
  });
});

io.sockets.on('connect_failed', function() {
    document.write("Sorry, there seems to be an issue with the connection!");
})
