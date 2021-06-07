var http = require('http');
var cookie_reader = require('cookie');
var querystring = require('querystring');
var redis = require('redis');
var url = require("url");
var argv = require('minimist')(process.argv.slice(2));
var log4js = require('log4js');
require('dotenv').config({ silent: true });

// Set logger
if (argv.hasOwnProperty('syslog')) {
    log4js.configure({
        appenders: [{
            type: "log4js-syslog-appender",
            tag: "node_notifications",
            facility: "daemon",
            path: "/dev/log",
            transport: "socket"
        }]
    });
    var logger = log4js.getLogger('syslog');
} else {
    var logger = log4js.getLogger();
}

// Init the logger and log level
logger.setLevel('INFO');

config = { listen_port: 4003, redis_url: process.env.REDIS_URL || 'redis://localhost:6379' };
//config = { listen_port: 4003, redis_url: 'redis://host.docker.internal:6379' };

if(process.env.PORT) {
    config.listen_port = process.env.PORT;
}

if(process.env.REDIS_URL) {
    config.redis_url = process.env.REDIS_URL;
}

logger.info('Loaded config: ', config);

const healthCheckListener = function (req, res) {
    if (req.url == '/healthcheck') {
        res.writeHead(200);
        res.end();
    }
};

var server = http.createServer(healthCheckListener).listen(config.listen_port, '0.0.0.0');

// Create the server
if (server) {
    logger.info("Listening on port " + config.listen_port);
} else {
    logger.error("Could not start server. Exiting ...");
    process.exit(1);
}



// Attach socket.io
var io = require('socket.io').listen(server);

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


io.sockets.on('connection', function (socket) {
    var user_channel = redis.createClient(config.redis_url);

    // subscribe to the user channel
    user_channel.subscribe('user-notifications.' + socket.conn.request.cookie['sessionid']);

    user_channel.on('message', function(channel, payload){
        logger.info('Received message on channel=', channel)
        payload = JSON.parse(payload);

        var message = payload.message;
        var event_name = 'message';

        if ('event_name' in payload) {
            event_name = payload.event_name;
        }

        logger.info('Sending to: ', socket.conn.request.cookie['sessionid'], 'notif=', message.notif, socket.id);
        socket.emit(event_name, message);
    });

    socket.on('disconnect', function () {
        logger.info("Closing connection");
        user_channel.unsubscribe('user-notifications.' + socket.conn.request.cookie['sessionid']);
    });

});
