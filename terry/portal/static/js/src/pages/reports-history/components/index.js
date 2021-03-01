import React, { Component } from 'react';
import { connect } from 'react-redux';
import { browserHistory } from 'react-router';
import { bindActionCreators } from 'redux';
import { Pagination } from 'react-bootstrap';
import Report from './Report';
import immutable from 'immutable';

// App
import {
  getFromServer,
  removeFromServer
} from 'reports-history/redux/modules/history';
import { getFromServer as getUserFromServer } from 'base/redux/modules/user';
import 'reports-history/scss/app.scss';


class AppComponent extends Component {
  constructor(props) {
    super(props);
    this._getReports = this._getReports.bind(this);
    this._removeReport = this._removeReport.bind(this);
    this._viewReport = this._viewReport.bind(this);
    this._reprocessReport = this._reprocessReport.bind(this);
    this._handlePaginationClick = this._handlePaginationClick.bind(this);
    this._handleFilterChange = this._handleFilterChange.bind(this);
    this.WAIT_BEFORE_FILTER_REQUEST = 300;
    this._timeoutId = null;
    this.state = {
      filter: '',
      isFocus: false
    }
  }

  componentDidMount() {
    this._getReports();
  }

  componentWillReceiveProps(nextProps) {
    const { filter } = this.state;
    const { page } = this.props.params;

    // if page changed
    if(page !== nextProps.params.page) {
      this.props.getFromServer(nextProps.params.page, filter);
    }
  }

  _getReports() {
    const { page } = this.props.params;
    const { filter } = this.state;
    return this.props.getFromServer(page, filter);
  }

  _removeReport(id) {
    const { removeFromServer, getUserFromServer } = this.props;
    removeFromServer(id)
      .then(this._getReports) // update reports
      .then(getUserFromServer) // update user data (reports_public_count, reports_private_count)
  }

  _viewReport(id) {
    browserHistory.push(`/report/${id}`);
  }

  _reprocessReport(uuid, url) {
    browserHistory.push({ pathname: `/dashboard/`, state: { reprocess: true, url, uuid } })
  }

  _handlePaginationClick(pageNum) {
    browserHistory.push(`/history/${pageNum}`)
  }

  _handleFilterChange(e) {
    this._timeoutId && clearTimeout(this._timeoutId);

    const { page } = this.props.params;
    const filter = e.target.value;
    this.setState({ filter })

    // to prevent frequent server requests
    this._timeoutId = setTimeout(() => {
      // if it's first page: just get filtered results
      if(+page === 1) {
        this.props.getFromServer(page, filter)
      // else go to the first page (filtered result will be gotten in componentWillReceiveProps)
      } else {
        browserHistory.push(`/history/1`)
      }
    }, this.WAIT_BEFORE_FILTER_REQUEST)
  }



  render() {
    const { history } = this.props;
    const isInitialized = history.get('isInitialized');
    const reports = history.get('reports');
    const pageCount = history.get('pageCount');
    const { page } = this.props.params;
    const isReports = reports.size;

    if (!isInitialized) {
      return (
        <div className="spinner spinner--center"></div>
      );
    }

    return (
      <div className="wrap-page">
        <div className="reposts-heading">
          <h1>History</h1>
          <div className="filter">
            <i className={`filter-icon fa fa-search ${this.state.isFocus ? 'filter-icon--focused' : ''}`} />
            <input
              className="filter-input"
              type="text"
              value={this.state.filter}
              onChange={this._handleFilterChange}
              onFocus={() => {this.setState({isFocus: true})}}
              onBlur={() => {this.setState({isFocus: false})}} />
          </div>
        </div>
        <hr />
        {!isReports ? (
          <div>There are no reports yet</div>
        ) : (
          <div className="reports">
            {
              reports.map(report => (
                <Report
                  key={report.get('uuid')}
                  report={report}
                  onViewClick={this._viewReport}
                  onReprocessClick={this._reprocessReport}
                  onRemoveClick={this._removeReport}
                  onPermalinkChange={this._getReports}
                />
              ))
            }

            <div className="reports-pagination">
              <Pagination
                activePage={+page}
                items={ Math.ceil(pageCount / 10) }
                prev
                next
                first
                last
                boundaryLinks
                ellipsis
                maxButtons={5}
                onSelect={this._handlePaginationClick}
              />
            </div>
          </div>
        )}
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    history: state.history
  }
};


const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getFromServer,
    removeFromServer,
    getUserFromServer
  }, dispatch)
}

export default connect(mapStateToProps, mapDispatchToProps)(AppComponent);
