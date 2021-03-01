import React from 'react';
import { Provider, connect } from 'react-redux';
import { render } from 'react-dom';

// App
import Header from 'common/components/Header';
import Footer from 'common/components/Footer';
import IntercomButton from 'common/components/IntercomButton';
import SubscriptionSection from './components/SubscriptionSection';
import SampleDocumentSection from 'getstarted/components/SampleDocumentSection';
import UploadAreaV2 from 'common/components/UploadArea/UploadAreaV2';
import { getFromServer as getUserDataFromServer } from 'common/redux/modules/user';
import store from './redux/store';

require('./components/styles/GetStarted.scss');   //stylings for component

const Separator = React.createClass({

  render() {
    return (
      <div className="separator">
        <div className="heading">Or</div>
      </div>
    );
  }
});

const GetStartedComponent = React.createClass({

  componentDidMount() {
    // Get the data from the api here.
    const { dispatch } = this.props;
    dispatch(getUserDataFromServer());
  },

  /* onDragEnter(e)
  *
  * toggle on the absolutely placed dropzone overlay when the user has a
  * dragged element
  */
  onDragEnter(e) {
    if (UserStore.isPaidUser()) {
      e.preventDefault();
      //dive down to Dropzone through refs and toggle the state
      this.refs.UploadAreaV2.refs.DragAndDrop.refs.Dropzone.setState({isActive : true});
      e.dataTransfer.dropEffect = 'copy';
    } else {
      return //do nothing.
    }
  },


  /* generateLoadingView()
  *
  * returns a generic loading view until information about
  * the user is present
  *
  */
  generateLoadingView() {
    return (<div/>);
  },

  /* generateFreeUserView()
  *
  * returns a component offering a trial (if non has yet been done)
  * or encourages a purchase
  *
  */
  generateFreeUserView() {
    const { user } = this.props;
    return (<SubscriptionSection hasHadTrial={user.get('had_trial')}/>);
  },

  /* generatePaidUserView()
  *
  * returns a the upload component for paid users
  * that are just getting started
  *
  */
  generatePaidUserView() {
    return ( <UploadAreaV2 ref="UploadAreaV2" fileSelected={this.setFileSelected} /> );
  },

  render() {
    var view;
    const { user } = this.props;

    if (!user.get('isInitialized')) {
      view = this.generateLoadingView();
    } else if (user.get('is_paid')) {
      view = this.generatePaidUserView();
    } else {
      view = this.generateFreeUserView();
    }

    return (
      <div className="app" onDragEnter={this.onDragEnter} >
        <Header />
        <div className="summary-wrap">
          <div className="heading">Getting Started</div>
          {view}
          <Separator />
          <SampleDocumentSection />
        </div>
        <Footer />
        <IntercomButton />
      </div>
    );
  }

});

const mapStateToProps = (state) => {
  return {
    user: state.user
  }
};
const GetStarted = connect()(GetStartedComponent);

class Root extends React.Component {
  render() {
    return (
      <Provider store={store()}>
        <GetStarted />
      </Provider>
    )
  }
}

render(<Root />, document.getElementById('react-get-started'));
