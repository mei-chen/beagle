import React from 'react';
import { render } from 'react-dom';
import { Provider, connect } from 'react-redux';

// App
import { getFromServer as getUserDataFromServer } from 'common/redux/modules/user';
import { getFromServer as getSubscriptionFromServer } from 'common/redux/modules/subscription';
import Header from './components/Header';
import store from './redux/store';

class MainComponent extends React.Component {
  componentDidMount() {
    // Get the data from the api here.
    const { dispatch } = this.props;
    dispatch(getUserDataFromServer());
    dispatch(getSubscriptionFromServer());
  }

  render() {
    return <Header />
  }
}

const Main = connect()(MainComponent);

class Root extends React.Component {
  render() {
    return (
      <Provider store={store()}>
        <Main />
      </Provider>
    )
  }
}

render(<Root />, document.getElementById('react-header'));
