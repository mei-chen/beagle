import { Notification } from 'common/redux/modules/transientnotification';
import { getFromServer as getProjectFromServer } from 'account/redux/modules/project';


export const socketMiddleware = (socket) => {
  return ({ dispatch, store }) => {
    // Convert server response to redux actions without modifying the server\
    socket.on('message', resp => {
      switch (resp.notif) {
      case 'DOCUMENT_OWNER_CHANGED':
      case 'DOCUMENT_INVITE_RECEIVED':
      case 'DOCUMENT_INVITE_RECEIVED_REVOKED':
      case 'DOCUMENT_INVITE_REJECTED_REVOKED':
      case 'DOCUMENT_PROCESSING_STARTED':
      case 'BATCH_PROCESSING_COMPLETED':
      case 'DOCUMENT_COMPLETED': {
        dispatch(getProjectFromServer());
        break;
      }

      case 'DOCUMENT_DELETED': {
        dispatch(getProjectFromServer());

        const user = store.getState().user;

        if (user.get('email') !== resp.document.owner.email) {
          dispatch(
            Notification.error(
              'A document in which you were invited has just been deleted',
              undefined,
              resp.document.uuid
            )
          );
        }
        break;
      }
      }
    });

    return next => action => {
      return next(action);
    }
  }
}
