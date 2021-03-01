import React, { Component } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';
import Subscription from 'base/components/Subscription';

// App
import 'settings/scss/app.scss';

import { getFromServer, deleteFromServer, GITHUB, BITBUCKET, GITLAB } from 'settings/redux/modules/settings';

class AccessButton extends Component {
  render() {
    const { authenticated, login, placeholder, iconClassName, href, onRefuseClick } = this.props;
    const Tag = authenticated ? 'span' : 'a';
    const attr = !authenticated ? { href } : {};
    const className = authenticated ? 'authenticated' : 'not-authenticated';

    return(
      <div className="access-button">
        <Tag {...attr}>
          <div  className={className}>
            <div className="icon-wrapper">
              <i className={iconClassName} />
            </div>
            <div className="text-wraper">
              { authenticated ? (
                <span>Authorized as <span className="github-name">{ login }</span></span>
              ) : (
                <span>{ placeholder }</span>
              )}
            </div>
            { authenticated && (
              <div className="deny-icon">
                <i className="fa fa-times" aria-hidden="true" onClick={onRefuseClick} />
              </div>
            ) }
          </div>
        </Tag>
      </div>
    );
  }
};

class AppComponent extends Component {
  constructor(props) {
    super(props);
  }

  componentDidMount() {
    this.props.getFromServer(GITHUB);
    this.props.getFromServer(BITBUCKET);
    this.props.getFromServer(GITLAB)
  }

  render() {
    const { GITHUB_OAUTH_CLIENT_ID, BITBUCKET_OAUTH_CLIENT_ID, GITLAB_OAUTH_CLIENT_ID } = window;
    const { settings, user, deleteFromServer } = this.props;
    const details = user.get('details');
    const subscription = details.get('subscription');
    const publicReports = details.get('public_reports_count');
    const privateReports = details.get('private_reports_count');

    const isInitialized = settings.get('isInitialized') && user.get('isInitialized');

    if(!isInitialized) return <div className="spinner spinner--center"></div>;

    return (
      <div className="wrap-page">
        <h1>Settings</h1>
        <hr />

        <h2 className="settings-subtitle">Grant access to private repos</h2>
        <ul className="auth-list">
          {/* github button */}
          <li>
            <AccessButton
              authenticated={ settings.get('isGithubToken') }
              login={ details.get('github_login') }
              href={`https://github.com/login/oauth/authorize?scope=user%20repo&client_id=${GITHUB_OAUTH_CLIENT_ID}`}
              placeholder="Authorization with GitHub"
              iconClassName="fab fa-github"
              onRefuseClick={() => { deleteFromServer(GITHUB) }}
            />
          </li>

          {/* bitbucket button */}
          <li>
            <AccessButton
              authenticated={ settings.get('isBitbucketToken') }
              login={ details.get('bitbucket_login') }
              href={`https://bitbucket.org/site/oauth2/authorize?client_id=${BITBUCKET_OAUTH_CLIENT_ID}&response_type=code`}
              placeholder="Authorization with Bitbucket"
              iconClassName="fab fa-bitbucket"
              onRefuseClick={() => { deleteFromServer(BITBUCKET) }}
            />
          </li>

          {/* gitlab button */}
          <li>
            <AccessButton
              authenticated={ settings.get('isGitlabToken') }
              login={ details.get('gitlab_login') }
              href={`https://gitlab.com/oauth/authorize?client_id=${GITLAB_OAUTH_CLIENT_ID}&response_type=code&redirect_uri=${window.location.origin}/api/v1/OAuthCallback/gitlab/`}
              placeholder="Authorization with GitLab"
              iconClassName="fab fa-gitlab"
              onRefuseClick={() => { deleteFromServer(GITLAB) }}
            />
          </li>
        </ul>

        <h2 className="settings-subtitle">Subscription</h2>
        <Subscription
          hasSubscription={!!subscription}
          plan={subscription.get('name')}
          expires={subscription.get('expires')}
          repos={{
            public: publicReports,
            private: privateReports
          }} />
      </div>
    );
  }
}

const mapStateToProps = state => {
  return {
    settings: state.settings,
    user: state.user
  }
}

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getFromServer,
    deleteFromServer
  }, dispatch)
}

export default connect(mapStateToProps, mapDispatchToProps)(AppComponent);
