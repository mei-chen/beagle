import React, { Component } from 'react';
import { Provider, connect } from 'react-redux';
import {
  Router, Route, hashHistory, IndexRedirect
} from 'react-router';
import { render } from 'react-dom';

// App
import Header from 'common/components/Header';
import Footer from 'common/components/Footer';
import IntercomButton from 'common/components/IntercomButton';
import Profile from './components/Profile';
import Projects from './components/Projects';
import EditProfile from './components/EditProfile';
import LearnersDashboard from './components/LearnersDashboard';
import KeywordsDashboard from './components/KeywordsDashboard';
import SettingsDashboard from './components/SettingsDashboard';
import NotFound from './components/NotFound';

import store from './redux/store';
import { getFromServer as getUserDataFromServer } from 'common/redux/modules/user';
import { getFromServer as getSubscriptionFromServer } from 'common/redux/modules/subscription';
import { getFromServer as getSettingFromServer } from './redux/modules/setting';
import { setDropboxAccess } from './redux/modules/setting';

require('./components/styles/Account.scss');   //stylings for component

const ProjectsView = React.createClass({

  render() {
    return (
      <div className="summary-wrap">
        <div className="columns">
          <Profile viewMode={'project'}/>
          <Projects
            key={'projects'}
            user={this.props.user}
            openSection={this.props.openSection}
            changeOpenSection={this.props.changeOpenSection}
            {...this.props}
          />
        </div>
      </div>
    );
  }
});

const EditView = React.createClass({
  render() {
    return (
      <div className="summary-wrap">
        <EditProfile user={this.props.user}/>
      </div>
    );
  }
});

const LearnersView = React.createClass({
  render() {
    return (
      <div className="summary-wrap">
        <div className="columns">
          <Profile user={this.props.user} viewMode={'learners'}/>
          <LearnersDashboard/>
        </div>
      </div>
    );
  }
});

const KeywordsView = React.createClass({
  render() {
    return (
      <div className="summary-wrap">
        <div className="columns">
          <Profile user={this.props.user} viewMode={'keywords'}/>
          <KeywordsDashboard/>
        </div>
      </div>
    );
  }
});

const SettingsView = React.createClass({

  componentWillMount() {
    const { dispatch } = this.props;
    if (this.props.params && this.props.params.hash) {
      const groups = this.props.params.hash.match(/access_token=([^&]*)/);
      if (groups) {
        const token = groups[1];
        dispatch(setDropboxAccess(token));
      }
      this.props.router.replace('/settings');
    }
  },

  render() {
    return (
      <div className="summary-wrap">
        <div className="columns">
          <Profile user={this.props.user} viewMode={'settings'}/>
          <SettingsDashboard/>
        </div>
      </div>
    );
  }
});

const Account = React.createClass({
  getInitialState() {
    return {
      viewMode: 'project',  //or 'edit'
    };
  },

  componentDidMount() {
    // Get the data from the api here.
    const { dispatch } = this.props;
    dispatch(getUserDataFromServer());
    dispatch(getSubscriptionFromServer());
    dispatch(getSettingFromServer());
  },

  componentDidUpdate() {
    window.Intercom('update');
  },

  render() {
    const { viewMode, openSection } = this.state;
    const { user } = this.props;
    var view;
    var children;
    var changeOpenSection = this.openSection
    if (viewMode === 'project') {
      children = React.Children.map(this.props.children, function(child) {
        return React.cloneElement(child, {
          user: user,
          openSection: openSection,
          changeOpenSection: changeOpenSection
        })
      });
    } else {
      children = React.Children.map(this.props.children, function(child) {
        return React.cloneElement(child, {
          user: user
        })
      });
    }

    view = (
      <span>
        {children}
      </span>
    );

    return (
      <div className="react-account">
        <Header/>
          {view}
        <Footer/>
        <IntercomButton />
      </div>
    );
  }
});

const mapStateToProps = (state) => {
  return {
    user: state.user,
    isUserInitialized: state.user.isInitialized
  }
};

const AccountContainer = connect(mapStateToProps)(Account)
const SettingsViewContainer = connect(mapStateToProps)(SettingsView)

const router = (
  <Router history={hashHistory}>
    <Route path="/" component={AccountContainer}>
      <IndexRedirect to="/projects" />
      <Route path="/projects" component={ProjectsView}/>
      <Route path="/manage-keywords" component={KeywordsView}/>
      <Route path="/manage-learners" component={LearnersView}/>
      <Route path="/edit-account" component={EditView}/>
      <Route path="/settings" component={SettingsViewContainer}/>
      <Route path="/settings/:hash" component={SettingsViewContainer}/>
      <Route path="*" component={NotFound}/>
    </Route>
  </Router>
);

class Root extends Component {
  render() {
    return (
      <Provider store={store()}>
        { router }
      </Provider>
    )
  }
}


render((
  <Root />
),document.getElementById('react-account'))
