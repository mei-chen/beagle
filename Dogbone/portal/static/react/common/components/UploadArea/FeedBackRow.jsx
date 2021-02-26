// LOOKS UNUSED



/* NPM Modules */
import React from 'react';
import io from 'socket.io-client';
import log from 'utils/logging';
import { Notification } from 'common/redux/modules/transientnotification';
import classNames from 'classnames';

/* Utilities */
import easing from 'utils/easing';

const socket = io(window.socketServerAddr);

/* Style */
require('./styles/FeedBackRow.scss');


const FeedBackRow = React.createClass({

  propTypes: {
    enabled : React.PropTypes.bool.isRequired,
    onClickUploadFile : React.PropTypes.func,
    cancelDocument : React.PropTypes.func,
    documentTitle : React.PropTypes.string,
    children : React.PropTypes.element
  },

  getInitialState() {
    return {
      upload : null,
      conversion : null,
      docUUID : null,
    };
  },

  componentDidMount() {
    this.socketListener();
  },

  componentDidUpdate() {
    if (this.state.enabled) { this.animateOpen() }
  },


  //Thanks jorge
  animateOpen() {
    // animate the editor window
    var node = this.getDOMNode();
    var styles = window.getComputedStyle(node);
    var targetHeight = parseInt(styles.getPropertyValue('height'), 10);

    // initial state: height 0, show no overflow
    node.style.height = '0px';
    node.style.overflow = 'hidden';

    // animation settings
    var start = null;
    var animationLength = 450; // milliseconds
    var easingFn = easing.easeOutCubic;

    // this is the function that executes on each animation frame
    var animateFrame = function(timestamp) {
      if (!start) {
        start = timestamp; // initialize start time
      }
      var elapsed = timestamp - start;
      var percentDone = elapsed / animationLength;
      var easedPercentDone = easingFn(percentDone);
      var stepHeight = targetHeight * easedPercentDone;
      var nodeHeight = `${stepHeight}px`;
      node.style.height = nodeHeight;
      if (percentDone < 1) {
        requestAnimationFrame(animateFrame);
      } else {
        node.style.height = null;
        node.style.overflow = null;
      }
    };
    // animate!
    requestAnimationFrame(animateFrame);
  },

  socketListener() {
    socket.on('message', msg => {
      log('msg received', msg);
      var type = msg.notif;

      if (
        msg.document && msg.document.uuid &&
        this.state.docUUID !== msg.document.uuid
      ) {
        return; // do nothing
      }

      else if (type === 'DOCUMENT_UPLOADED') {
        this.setState({
          upload: 'finished',
          conversion: 'started'
        });
      }

      else if (type === 'DOCUMENT_CONVERTED') {
        this.setState({
          conversion: 'finished'
        });
        setTimeout(
          () => {
            window.location = msg.document.report_url;
          }, 1500
        );
      }

      else if (type === 'DOCUMENT_ERROR_MALFORMED') {
        Notification.error('The document you uploaded is malformed. Please try again.');
        this.errorReset();
      }

      else if (type === 'DOCUMENT_ERROR_NOT_FOUND') {
        Notification.error('We encountered an unexpected error. Please try again later.');
        this.errorReset();
      }

      else if (type === 'DOCUMENT_ERROR_FORMAT_UNSUPPORTED') {
        Notification.error('The document file type you uploaded is currently unsupported by Beagle. Please try again with a .txt, .docx, .doc or a .pdf');
        this.errorReset();
      }

      else if (type === 'DOCUMENT_ERROR_TOO_LARGE_TO_OCR') {
        Notification.error('The document you uploaded is too large to be OCRed');
        this.errorReset();
      }

      else if (type === 'EASYPDF_ERROR') {
        Notification.error('We are sorry, there was an unexpected error with processing your PDF. The Beagle team has been alerted. Please try a different version of the document.');
        this.errorReset();
      }
    });
  },

  /*
  * errorReset()
  *
  * Resets the state of the feedback row, and also calls the parent cancelDocument
  * function to reset it's state and clear the file input
  */
  errorReset() {
    this.setState({
      upload : null,
      conversion : null,
    });
    this.props.cancelDocument()
  },

  /*
  * generateButton()
  *
  * This generates the markup that displays the document title
  * an option to cancel said document, and the famous 'sniff'
  * button
  */

  generateButton() {
    return (
       <div className="row feedback-row">
          <div className="action-title">You are uploading</div>
          <div className="document-title">{this.props.documentTitle} <i className="fa fa-times abort" onClick={this.props.cancelDocument}/></div>
          <div className="button-panel">
            <button onClick={this.props.onClickUploadFile}>Sniff</button>
          </div>
        </div>
    );
  },


  /*
  * generateLoadingFeedback()
  *
  * This generates the markup that displays the 'Uploading'
  * and 'Converting' feedback the user sees after clicking the 'sniff'
  * button
  */
  generateLoadingFeedback() {
    let uploadClass = classNames(
       'feedback-icon',
      { 'fa fa-cog fa-spin fa-2x' : this.state.upload === 'started' },
      { 'fa fa-check fa-2x' : this.state.upload === 'finished' },
      { 'icon-invisible' : this.state.upload === null }
    );

    let conversionClass = classNames(
      'feedback-icon',
      { 'fa fa-cog fa-spin fa-2x' : this.state.conversion === 'started' },
      { 'fa fa-check fa-2x' : this.state.conversion === 'finished' },
      { 'icon-invisible' : this.state.conversion === null }
    );
    return (
          <div className="row feedback-row">
            <div className="feedback-item">
                <i className={uploadClass} />
                <span className="feedback-text">Uploading</span>
            </div>
            <div className="feedback-item">
                <i className={conversionClass} />
                <span className="feedback-text">Converting</span>
            </div>
          </div>
    );
  },

  render() {
    if (this.props.enabled) {
      return this.generateButton()
    } else if (this.state.upload === 'started' || this.state.upload === 'finished') {
      return this.generateLoadingFeedback()
    } else {
      return (
        <div>
          {this.props.children}
        </div>
      );
    }
  }
});

module.exports = FeedBackRow;
