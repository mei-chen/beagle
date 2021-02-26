import React, { Component } from 'react';
import { Router, Route ,hashHistory,IndexRedirect } from 'react-router';
import { render } from 'react-dom';
import { Provider, connect } from 'react-redux';

// App
import store from './redux/store';
import Header from 'common/components/Header';
import Footer from 'common/components/Footer';
import IntercomButton from 'common/components/IntercomButton';
import Spinner from 'report/components/Spinner';
import Sidebar from 'report/components/Sidebar';
import DetailView from 'report/components/DetailView';
import ContextViewContainer from 'report/components/ContextView';
import WidgetPanel from 'report/components/WidgetPanel';
import ClauseTableView from 'report/components/ClauseTableView';
import NotFound from 'report/components/NotFound';
import CollapsibleDocSummary from 'report/components/CollapsibleDocSummary.jsx';
import { getFromServer as getReportFromServer } from 'report/redux/modules/report';
import { getFromServer as getUserDataFromServer } from 'common/redux/modules/user';
import { getFromServer as getKeywordFromServer } from 'account/redux/modules/keyword';
import { getFromServer as getLearnerFromServer } from 'account/redux/modules/learner';

require('./components/styles/Main.scss');
require('./components/styles/TopBar.scss');


const App = React.createClass({
  getInitialState() {
    return {
      introObject: null,
    };
  },

  componentWillMount() {
    const { dispatch } = this.props;
    dispatch(getUserDataFromServer());
    dispatch(getReportFromServer());
    dispatch(getKeywordFromServer());
    dispatch(getLearnerFromServer());
  },

  componentDidUpdate() {
    window.Intercom('update');
  },

  renderContents() {
    const { isInitialized } = this.props;
    if (!isInitialized) {
      return (
        <div id="step2" className="report-wrap">
          <div>
            <Spinner inline /> Your document is being analyzed
          </div>
        </div>
      );
    } else {
      return (
        <span>
          <CollapsibleDocSummary/>
          <div className="report-wrap">
            <div className="content-wrap">
              {this.props.children}
            </div>
          </div>
        </span>
      )
    }
  },

  render() {
    return (
      <div className="app">
        <Sidebar/>
        <main>
          <Header ref="Header" shouldShrink />
          { this.renderContents() }
          <Footer/>
          <IntercomButton />
        </main>
      </div>
    );
  }

});

const mapStateToProps = (state) => {
  return {
    user: state.user,
    report: state.report,
    isInitialized: (
      state.report.get('isInitialized')
    )
  }
};

const AppContainer = connect(mapStateToProps)(App)

class Root extends Component {
  render() {
    return (
      <Provider store={store()}>
        <Router history={hashHistory}>
          <Route name="app" path="/" component={AppContainer}>
            <IndexRedirect to="/widget-panel"/>
            <Route path="/widget-panel" component={WidgetPanel}/>
            <Route path="/detail-view" component={DetailView}/>
            <Route path="/clause-table" component={ClauseTableView}/>
            <Route path="/context-view" component={ContextViewContainer}/>
            <Route path="*" component={NotFound}/>
          </Route>
      </Router>
      </Provider>
    )
  }
}


render((
  <Root />
),document.getElementById('react-app'))
