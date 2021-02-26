import {
  documentSentenceChangedSocket,
  getFromServer,
  lockChangedSocket,
  documentSentenceTagsResponse,
  toggleDisplayComponentBoolean,
  removeCollaborator,
  releaseLockOnDisconnect
} from 'report/redux/modules/report';
// import log from 'utils/logging';

const node = document.getElementById('_uuid');
const docUUID = node != null ? node.value : null;

export const socketMiddleware = (socket) => {
  return ({ dispatch }) => {
    // Convert server response to redux actions without modifying the server\
    socket.on('message', resp => {
      // Check if the update is for the current document
      const msgDocUUID = resp.documentUUID || (resp.document && resp.document.uuid) || (resp.sentence && resp.sentence.doc);
      if (!msgDocUUID || msgDocUUID !== docUUID) return;
      // log.info('received from socket:', resp);

      switch (resp.notif) {
      case 'DOCUMENT_CHANGED': {
        const { sentenceIdx, sentence } = resp;
        dispatch(documentSentenceChangedSocket({ idx: sentenceIdx, sentence }));
        break;
      }

      case 'DOCUMENT_LOCK_CHANGED': {
        const { sentenceIdx, sentence } = resp;
        dispatch(lockChangedSocket({ idx: sentenceIdx, sentence }));
        break;
      }

      case 'DOCUMENT_BULK_TAGS_CREATED': {
        const { sentences } = resp;
        dispatch(documentSentenceTagsResponse(sentences));
        break;
      }

      case 'DOCUMENT_BULK_TAGS_DELETED': {
        const { sentences } = resp;
        dispatch(documentSentenceTagsResponse(sentences));
        break;
      }

      case 'DOCUMENT_BULK_TAGS_UPDATED': {
        const { sentences } = resp;
        dispatch(documentSentenceTagsResponse(sentences));
        break;
      }

      case 'COMMENT_ADDED': {
        const { sentence } = resp;
        dispatch(documentSentenceChangedSocket({ idx: sentence.idx, sentence }));
        break;
      }

      case 'DOCUMENT_COMPLETED': {
        dispatch(getFromServer());
        break;
      }

      case 'WEAK_DOCUMENT_ANALYSIS': {
        dispatch(getFromServer());
        dispatch(toggleDisplayComponentBoolean('showUnconfidentPopover', true));
        break;
      }

      case 'DOCUMENT_EXPORT_READY': {
        dispatch(toggleDisplayComponentBoolean('exportState', {
          isLoading: false,
          isReady: true,
          hasError: false,
          hasExportIcon: false
        }));
        break;
      }

      case 'DOCUMENT_EXPORT_ERROR': {
        dispatch(toggleDisplayComponentBoolean('exportState', {
          isLoading: false,
          isReady: true,
          hasError: true,
          hasExportIcon: true
        }));
        break;
      }

      case 'DOCUMENT_INVITE_REJECTED_REVOKED': {
        const { invitee } = resp;
        dispatch(removeCollaborator(invitee));
        break;
      }
      }
    });

    socket.on('disconnect', () => {
      dispatch(releaseLockOnDisconnect())
    })

    return next => action => {
      return next(action);
    }
  }
}
