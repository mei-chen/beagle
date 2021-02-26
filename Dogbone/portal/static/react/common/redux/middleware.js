import {
  appendToNotifs,
  getFromServer,
  reset
} from 'common/redux/modules/persistentnotification';
// import log from 'utils/logging';


export const socketMiddleware = (socket) => {
  return ({ dispatch }) => {
    // Convert server response to redux actions without modifying the server\
    socket.on('message', resp => {
      // Check if the update is for the current document
      // log.info('received from socket:', resp);

      switch (resp.notif) {
      case 'ACTIVITY_UPDATE': {
        const update = resp.activity_update;
        dispatch(appendToNotifs(update));
        break;
      }

      case 'NOTIFICATIONS_FULL_UPDATE': {
        dispatch(reset());
        dispatch(getFromServer());
        break;
      }
      }
    });

    return next => action => {
      return next(action);
    }
  }
}
