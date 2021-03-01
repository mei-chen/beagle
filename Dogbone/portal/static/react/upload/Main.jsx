import React, { Component } from 'react';
import { render } from 'react-dom';
import { Provider, connect } from 'react-redux';

// App
import Upload from './components/Upload';
import Header from 'common/components/Header';
import Footer from 'common/components/Footer';
import IntercomButton from 'common/components/IntercomButton';
import store from './redux/store';
import { getFromServer as getUserDataFromServer } from 'common/redux/modules/user';
import { getFromServer as getSubscriptionFromServer } from 'common/redux/modules/subscription';
import { getFromServer as getSettingFromServer } from 'account/redux/modules/setting';


class App extends Component {

  componentDidMount() {
    // Get the data from the api here.
    const { dispatch } = this.props;
    dispatch(getUserDataFromServer());
    dispatch(getSubscriptionFromServer());
    dispatch(getSettingFromServer());
  }

  render() {
    return (
      <div>
        <div id="react-header">
          <Header />
        </div>
        <div className="layout">
          <div style={{ background: '#5D101A' }}>
            <Upload />
          </div>
        </div>
        <Footer />
        <IntercomButton />
      </div>
    )
  }
}

const mapStateToProps = (state) => {
  return {
    user: state.user,
    isInitialized: state.user.get('isInitialized')
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

render(<Root />, document.getElementById('react-upload'));
