import React, { Component, PropTypes } from 'react';
import { Button } from 'react-bootstrap';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import Confirm from 'react-confirm-bootstrap';
import Timestamp from 'react-time';
import ReportShared from './ReportShared';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import ShortUrl from 'base/components/ShortUrl';
import GitIcon from 'base/components/GitIcon';

const lowColor = {
  r:102,
  g:230,
  b:180
}

const highColor = {
  r:180,
  g:0,
  b:255
}

class Report extends Component {
    constructor(props) {
        super(props);
        this._getRiskColor = this._getRiskColor.bind(this);
        this.state = {};
    }

    _getRiskColor(score) {
        const redInterval = highColor.r - lowColor.r;
        const greenInterval = highColor.g - lowColor.g;
        const blueInterval = highColor.b - lowColor.b;

        const boxColor = {
            r:Math.floor(lowColor.r + ((redInterval * score)/100)),
            g:Math.floor(lowColor.g + ((greenInterval * score)/100)),
            b:Math.floor(lowColor.b + ((blueInterval * score)/100))
        }

        return `rgb(${boxColor.r},${boxColor.g},${boxColor.b})`;
    }

    render() {
        const { report, onViewClick, onReprocessClick, onRemoveClick, onPermalinkChange } = this.props;
        const url = report.get('url');
        const uuid = report.get('uuid');
        const date = report.get('created_at');
        const status = report.get('status');
        const className = status ? `report report--${status}` : 'report';
        const licensesCount = report.get('license_length');
        const score = report.get('overall_risk');
        const reportSharedCount = report.get('report_shared') ? report.get('report_shared').size : null;
        const isPrivate = report.get('is_private');

        return (
            <div>
                <div className={className}>
                    <div className="report-buttons">
                        { isPrivate && status === 'green' && (
                            <div className="report-private"><i className="fa fa-lock" /> Private</div>
                        ) }
                        { score !== null && score !== undefined && ( // could be 0
                            <OverlayTrigger placement="top" overlay={<Tooltip id="tooltip-top">Terry score</Tooltip>}>
                                <div
                                    className="report-score"
                                    style={{ backgroundColor: this._getRiskColor(score) }}>
                                    {`${100 - score}%`}
                                </div>
                            </OverlayTrigger>
                        ) }
                        {!!licensesCount && (
                            <div className="report-licenses">Licenses: {licensesCount}</div>
                        )}
                        <OverlayTrigger placement="top" overlay={<Tooltip id="tooltip-top">Share URL</Tooltip>}>
                            <Button
                                className="report-share-button"
                                bsStyle="info"
                                active={this.state.showShare}
                                disabled={status === 'red' || status === 'yellow'}
                                onClick={() => this.setState({ showShare: !this.state.showShare })}>
                                <i className="fa fa-share"></i>
                                { status === 'green' && !!reportSharedCount && <span className="report-share-count">{ reportSharedCount }</span> }
                            </Button>
                        </OverlayTrigger>

                        <OverlayTrigger placement="top" overlay={<Tooltip id="tooltip-top">Reprocess</Tooltip>}>
                            <Button
                                bsStyle="success"
                                onClick={() => { onReprocessClick(uuid, url) }}>
                                <i className="fa fa-repeat"></i>
                            </Button>
                        </OverlayTrigger>

                        <Confirm
                            onConfirm={() => { onRemoveClick(uuid) }}
                            title="Delete report from history"
                            body="Are you sure?">
                            <span>
                                <OverlayTrigger placement="top" overlay={<Tooltip id="tooltip-top">Delete</Tooltip>}>
                                    <Button
                                        bsStyle="danger" >
                                        <i className="fa fa-trash"></i>
                                    </Button>
                                </OverlayTrigger>
                            </span>
                        </Confirm>
                    </div>
                    <div
                        className="report-body"
                        onClick={() => { onViewClick(uuid) }} >
                        <Timestamp
                            value={ date }
                            className="report-date"
                            locale="en"
                            titleFormat="YYYY/MM/DD HH:mm"
                            relative />
                        <GitIcon
                            className="report-icon"
                            url={url}/>
                        <ShortUrl
                            url={url}
                            className="report-url" />
                    </div>

                    <div className="report-drop">
                        { this.state.showShare ? <ReportShared report={report} onPermalinkChange={onPermalinkChange} /> : ''}
                    </div>
                </div>
            </div>
        )
    }
}

Report.propTypes = {
    //  report: PropTypes.object.isRequired
}

export default Report;
