import React, { Component, PropTypes } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { browserHistory } from 'react-router';
import { Grid, Alert } from 'react-bootstrap';
import uuidV4 from 'uuid/v4';
import RequestForm from './RequestForm';
import Recent from './Recent';
import { Map, List } from 'immutable';

// App
import {
  analyzeProject,
  getRecentFromServer
} from 'search/redux/modules/terry';
import {
  getFromServer as getUserFromServer
} from 'base/redux/modules/user'
import '../scss/app.scss';

class AppComponent extends Component {
  constructor(props) {
    super(props);
    this._analyze = this._analyze.bind(this);
    this._onRecentClick = this._onRecentClick.bind(this);
    this._getDefaultValue = this._getDefaultValue.bind(this);
  }

  componentDidMount() {
    const { getRecentFromServer, getUserFromServer } = this.props;
    const locationState = this.props.location.state;

    getUserFromServer(); // get actual repo suggestions
    getRecentFromServer(3);

    // reprocess scenario
    if(locationState && locationState.reprocess) {
      this._analyze(locationState.url, locationState.uuid);
    }

    // redirect from landing scenario
    if(window.GIT_URL) {
      this._analyze(window.GIT_URL)
      delete window.GIT_URL;
    }
  }

  _onRecentClick(id) {
    browserHistory.push(`/report/${id}`)
  }

  _analyze(value, uuid) {
    const taskUuid = uuidV4();
    this.props.analyzeProject(taskUuid, value, uuid);
  }

  _getDefaultValue() {
    const locationState = this.props.location.state;

    // reprocess scenario
    if(locationState && locationState.reprocess) return locationState.url;

    // redirect from landing scenario
    if(window.GIT_URL) return window.GIT_URL;

    return '';
  }

  render() {
    const { isNotify, packageManager, recent, suggestions, hasAccessToPrivate } = this.props;
    const locationState = this.props.location.state;

    return (
      <div className="wrap-page">
        {/* Form */}
        <RequestForm
          isProcessing={isNotify}
          packageManager={packageManager}
          onSubmit={this._analyze}
          defaultValue={this._getDefaultValue()}
          suggestions={suggestions}
          hasAccessToPrivate={hasAccessToPrivate} />

        {/* Warning */}
        { packageManager === 'maven' && (
          <div>
            <hr />
            <Alert bsStyle="warning">We've detected Maven, which is slow, so it may take a little longer</Alert>
          </div>
        ) }

        {/* Recent */}
        { !isNotify && recent.size > 0 && (
          <div className="recent-wrap">
            <h2 className="recent-heading">Recent</h2>
            <Recent
              reports={recent.toJS()}
              onClick={this._onRecentClick}
            />
          </div>
        )}
      </div>
    );
  }
}

AppComponent.propTypes = {
  isNotify: PropTypes.bool.isRequired,
  packageManager: PropTypes.string.isRequired,
  recent: PropTypes.instanceOf(List).isRequired,
  suggestions: PropTypes.instanceOf(List),
  hasAccessToPrivate: PropTypes.bool
};

const mapStateToProps = (state, ownProps) => {
  const user = state.user.get('details');
  return {
    isNotify: state.terry.get('isNotify'),
    packageManager: state.terry.get('packageManager'),
    recent: state.terry.get('recent'),
    suggestions: user.get('suggestions'),
    hasAccessToPrivate: user.get('gitlab_access_token') || user.get('bitbucket_access_token') || user.get('github_access_token')
  };
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    analyzeProject,
    getRecentFromServer,
    getUserFromServer
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(AppComponent);
