import React, { Component, PropTypes } from 'react';
import { FormControl } from 'react-bootstrap';
import Confirm from 'react-confirm-bootstrap';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';

class Shared extends Component {
    constructor(props) {
        super(props);
        this._enableEdit = this._enableEdit.bind(this);
        this._saveEdit = this._saveEdit.bind(this);
        this._cancelEdit = this._cancelEdit.bind(this);
        this._handleInputChange = this._handleInputChange.bind(this);
        this._copyToClipboard = this._copyToClipboard.bind(this);
        this._getCopyTooltip = this._getCopyTooltip.bind(this);
        this._handleCopyClick = this._handleCopyClick.bind(this);
        this._handleCopyMouseOver = this._handleCopyMouseOver.bind(this);
        this.state = {
            isEdit: false,
            name: this.props.link.get('name') || 'New link',
            copyTooltipText: 'Copy to clipboard',
            isEditingNameOnServer: false
        };
    }

    _getCopyTooltip() {
        return <Tooltip id="tooltip">{ this.state.copyTooltipText }</Tooltip>
    }

    _handleCopyClick() {
        this.setState({ copyTooltipText: 'Copied!'});
        this._copyToClipboard()
    }

    _handleCopyMouseOver() {
        this.setState({ copyTooltipText: 'Copy to clipboard' })
    }

    _enableEdit() {
        this.setState({ isEdit: true });
    }

    _cancelEdit() {
        this.setState({ isEdit: false, isEditingNameOnServer: false })
    }

    _saveEdit() {
        const { link, onEdit } = this.props;
        const { name } = this.state;
        const id = link.get('id');
        this.setState({ isEditingNameOnServer: true })
        onEdit( id, name )
            .then(this._cancelEdit)
            .catch(this._cancelEdit)
    }

    _handleInputChange(e) {
        this.setState({ name: e.target.value })
    }

    _copyToClipboard() {
        window.getSelection().removeAllRanges(); // chrome error fix

        const range = document.createRange();
        range.selectNode(this.url);
        window.getSelection().addRange(range);
        document.execCommand('copy');
        window.getSelection().removeAllRanges();
    }

    render() {
        const { onRemoveClick, link } = this.props;
        const { isEdit, name } = this.state;

        return (
            <div className='shared'>
                <div className="shared-buttons">
                    <Confirm
                        onConfirm={() => { onRemoveClick(link.get('id')) }}
                        title="Delete sharable url"
                        body="Are you sure?">
                        <i className="text-danger fa fa-trash" />
                    </Confirm>
                </div>

                <div className="shared-name">
                    { isEdit ? (
                        <div>
                            <FormControl
                                className="shared-input"
                                type="text"
                                value={name}
                                onChange={this._handleInputChange}
                            />
                            { this.state.isEditingNameOnServer ? (
                                <i className="fa fa-spinner fa-pulse fa-fw" />
                            ) : (
                                <span>
                                    <i
                                        className="text-success fa fa-check"
                                        onClick={this._saveEdit} />
                                    <i
                                        className="fa fa-times"
                                        onClick={this._cancelEdit} />
                                </span>
                            ) }

                        </div>
                    ) : (
                        <div>
                            <span className="shared-name-value">{ link.get('name') || 'New link' }</span>
                            <i
                                className="fa fa-edit"
                                onClick={this._enableEdit} />
                        </div>
                    ) }

                </div>
                <div className="shared-url">
                    <a
                        href={`${location.origin}${link.get('share_url')}`}
                        ref={(node) => { this.url = node }}
                        className="shared-url-value">{ `${location.origin}${link.get('share_url')}` }</a>
                    <OverlayTrigger shouldUpdatePosition={true} ref={(obj) => {this.trigger = obj}} placement="top" overlay={this._getCopyTooltip()}>
                        <i
                            className="fa fa-clipboard"
                            onClick={this._handleCopyClick}
                            onMouseOver={this._handleCopyMouseOver} />
                    </OverlayTrigger>
                </div>
            </div>
        )
    }
}

export default Shared;
