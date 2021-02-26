import React, { Component } from 'react';
import { render } from 'react-dom';
import { Provider, connect } from 'react-redux';
import Time from 'react-time';

//App
import store from './redux/store';
import Header from 'common/components/Header';
import Footer from 'common/components/Footer';
import IntercomButton from 'common/components/IntercomButton';
// import Spinner from 'report/components/Spinner';
import ReportContainer from './components/ReportContainer';

//Redux
import { getFromServer as getUserDataFromServer } from 'common/redux/modules/user';
import { getFromServer as getReportFromServer } from './redux/modules/summary';
import { getFromServer as getSettingsFromServer } from 'account/redux/modules/setting'

//Styles
require('report/components/styles/Main.scss');
require('./components/styles/Main.scss');
require('report/components/styles/TopBar.scss');

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
    dispatch(getSettingsFromServer());
  },

  renderContents() {
    var batchDate;
    if (this.props.uploadDate) {
      batchDate = (<div className="upload-date">
            Uploaded by {this.props.batch_owner} on
            <Time locale="en"
              value={this.props.uploadDate} format="MMMM DD, YYYY hh:mm a"
            />
        </div>)
    } else {
      batchDate = <div className="upload-date">Loading</div>
    }
    return (
      <div className="report-wrap">
        <ReportContainer/>
        {batchDate}
        <div className="content-wrap">
          {this.props.children}
        </div>
      </div>
    )
  },

  render() {
    return (
      <div className="app">
        <main>
          <Header ref="Header" shouldShrink />
          {this.renderContents()}
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
    uploadDate: (
      state.summary.get('created')
    ),
    batch_owner: (
      state.summary.get('batch_owner')
    )
  }
};

const AppContainer = connect(mapStateToProps)(App)

class Root extends Component {
  render() {
    return (
      <Provider store={store()}>
        <AppContainer />
      </Provider>
    )
  }
}

render((
  <Root />
),document.getElementById('react-summary'))
