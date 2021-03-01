import React, { Component } from 'react';
import io from 'socket.io-client';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';
import Tooltip from 'react-bootstrap/lib/Tooltip';

const socket = io(window.socketServerAddr);

require('./styles/SummaryPage.scss');

const SummaryItem = React.createClass({
  getInitialState() {
    return {
      title: '',
      analyzed: this.props.value.analyzed,
      url: '',
      error: false,
      error_message: '',
    }
  },

  componentDidMount() {
    this.socketListener();
  },

  componentWillReceiveProps() {
    this.setItemState();
  },

  setItemState() {
    const { title, document_id, original_name } = this.props.value;
    this.setState({
      title,
      document_id,
      original_name
    });
  },

  socketListener() {
    socket.on('message', msg => {
      const type = msg.notif;
      if (type === 'DOCUMENT_COMPLETED' && msg.document.document_id === this.state.document_id) {
        this.setState({
          analyzed: true,
          url: msg.document.report_url,
        });
      }
      else if (type === 'DOCUMENT_ERROR_MALFORMED' && msg.document.document_id === this.state.document_id) {
        this.setState({
          error: true,
          error_message: 'The document you uploaded is malformed.',
        });
      }
      else if (type === 'DOCUMENT_ERROR_UNSUPPORTED_LANGUAGE' && msg.document.document_id === this.state.document_id) {
        this.setState({
          error: true,
          error_message: 'Only English is supported at the moment. A different language has been detected.',
        });
      }
      else if (type === 'DOCUMENT_ERROR_NOT_FOUND' && msg.document.document_id === this.state.document_id) {
        this.setState({
          error: true,
          error_message: 'We encountered an unexpected error. Please try again later.',
        });
      }
      else if (type === 'DOCUMENT_ERROR_FORMAT_UNSUPPORTED' && msg.document.document_id === this.state.document_id) {
        this.setState({
          error: true,
          error_message: 'The document file type you uploaded is currently unsupported by Beagle. Please try again with a .txt, .docx, .doc or a .pdf',
        });
      }
      else if (type === 'DOCUMENT_ERROR_TOO_LARGE_TO_OCR' && msg.document.document_id === this.state.document_id) {
        this.setState({
          error: true,
          error_message: 'The document you uploaded is too large to be OCRed',
        });
      }
      else if (type === 'EASYPDF_ERROR' && msg.document.document_id === this.state.document_id) {
        this.setState({
          error: true,
          error_message: 'We are sorry, there was an unexpected error with processing your PDF. The Beagle team has been alerted. Please try a different version of the document.',
        });
      }
    });
  },
  render() {
    const { original_name, analyzed, url, error, error_message } = this.state;
    var item = (
      <li className="summary-item">
        <i className="fa fa-cog fa-spin" aria-hidden="true" />
        {original_name || 'Loading...'}
      </li>
    );
    if (analyzed) {
      item = (
        <li className="summary-item">
          <i className="fa fa-check" aria-hidden="true" />
          {original_name}
          <a target="_blank" href={url || '#'}> Go to report page</a>
        </li>
      );
    }
    else if (error) {
      item = (
        <li className="summary-item">
          <OverlayTrigger placement="left" overlay={<Tooltip id="tooltip-left">{error_message}</Tooltip>}>
            <div>
              <i className="fa fa-ban" aria-hidden="true" />
              {original_name}
            </div>
          </OverlayTrigger>
        </li>
      )
    }
    /*In case of not receiving DOCUMENT_COMPLETED notification,
     *on BATCH_PROCESSING_COMPLETED notification switch all unconfirmed
     *documents to Unknown analysis conclusion (this bug is usually present on local environment
     *due to inconsistent notification transmissions).
     **/
    else if (this.props.completed) {
      item = (
        <li className="summary-item">
          <OverlayTrigger placement="left" overlay={<Tooltip id="tooltip-left">Unknown analysis conclusion</Tooltip>}>
            <span>
              <i className="fa fa-question" aria-hidden="true" />
              {original_name}
              <a target="_blank" href={url || '#'}> Go to report page</a>
            </span>
          </OverlayTrigger>
        </li>
      );
    }
    return item;
  }
});

SummaryItem.propTypes = {
  val: React.PropTypes.object
}

const SummaryPageWrap = (ComposedComponent) => {
  return class SummaryPageHOC extends Component {
    render() {
      return this.props.documentsList.length
        ? <ComposedComponent {...this.props} />
        : <i className="fa fa-spinner fa-spin fa-3x fa-fw" />;
    }
  }
}

const SummaryList = ({ documentsList, completed, url }) => {
  const docsList = documentsList.map(
    (val, key) =>
      <SummaryItem
        key={key}
        value={val}
        completed={completed}
      />
  );

  return (
    <div>
      <ul>
        {docsList}
      </ul>
      {completed && <a className="btn" href={url}>Go to summary page</a>}
    </div>
  );
}

SummaryList.propTypes = {
  documentsList: React.PropTypes.array,
}

const SummaryListComponent = SummaryPageWrap(SummaryList);

const SummaryPage = React.createClass({
  propTypes: {
    close: React.PropTypes.func,
    show: React.PropTypes.bool,
    reload: React.PropTypes.func,
    finished: React.PropTypes.bool,
  },

  defaultProps: {
    list: []
  },

  getInitialState() {
    return {
      documentsList: [],
      completed: false,
    }
  },

  componentDidMount() {
    this.props.reload();
    this.socketListener();
    this.setListState();
  },

  componentWillReceiveProps() {
    this.setListState();
  },

  socketListener() {
    socket.on('message', msg => {
      var type = msg.notif;
      if (type === 'BATCH_PROCESSING_COMPLETED') {
        this.setState({
          completed: true,
        });
      }
    });
  },

  setListState() {
    let list = this.props.list.sort(function(a, b) {
      return a.document_id - b.document_id;
    });
    this.setState({
      documentsList: list,
    })
  },

  render() {
    let reportUrl = this.props.batch ? `/summary/${this.props.batch}` : '#';
    return (
      <div>
        <h2 className="zip-password-header">Uploaded files</h2>
        <br/>
        <SummaryListComponent
          documentsList={this.state.documentsList}
          completed={this.state.completed}
          url={reportUrl}
        />
      </div>
    )
  }
})


module.exports = SummaryPage;
