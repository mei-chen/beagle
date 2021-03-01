import React, { Component, PropTypes } from 'react';
import { connect } from 'react-redux';
import { Alert, OverlayTrigger, Tooltip } from 'react-bootstrap';

class Publish extends Component {
  constructor(props) {
    super(props);
    this._handleCopyClick = this._handleCopyClick.bind(this);
    this._getCopyTooltip = this._getCopyTooltip.bind(this);
    this._copyToClipboard = this._copyToClipboard.bind(this);

    this.state = {
      copyTooltipText: 'Copy to clipboard'
    }
  }

  _handleCopyClick() {
    this.setState({ copyTooltipText: 'Copied!'});
    this._copyToClipboard();
  }

  _getCopyTooltip() {
      return <Tooltip id="tooltip">{ this.state.copyTooltipText }</Tooltip>
  }

  _copyToClipboard() {
      window.getSelection().removeAllRanges(); // chrome error fix

      const range = document.createRange();  
      range.selectNode(this.line);
      window.getSelection().addRange(range);
      document.execCommand('copy');
      window.getSelection().removeAllRanges();
  }

  render() {
    const { uuid, errorMessage } = this.props;

    if(errorMessage) {
        return <Alert bsStyle="warning">{ errorMessage }</Alert>
    }

    return (
      <div className="publish">
        <strong className="publish-subtitle">Use your experiment UUID to work with online learners</strong>
        <span
          ref={node => this.line = node} 
          className="publish-uuid">{ uuid }</span>
          <OverlayTrigger shouldUpdatePosition={true} ref={(obj) => {this.trigger = obj}} placement="top" overlay={this._getCopyTooltip()}>
            <i 
              className="publish-copy fa fa-clipboard"
              onClick={this._handleCopyClick}
              onMouseOver={this._handleCopyMouseOver} />
          </OverlayTrigger>
      </div>
    )
  }
}

Publish.propTypes = {
  uuid: PropTypes.string.isRequired,
  errorMessage: PropTypes.string
}

const mapStateToProps = (state) => {
  return {
    uuid: state.createExperimentModule.get('uuid'),
  }
};

export default connect(mapStateToProps)(Publish);
