import React, { Component, PropTypes } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { Map } from 'immutable';

// App
import { getDetailsFromServer } from 'search/redux/modules/terry';
import Result from 'search/components/Result';

class AppComponent extends Component {
  constructor(props) {
    super(props);
    this.props.getDetailsFromServer(
      window.reportUUID,
      { share_token: window.reportSharedToken }
    );
  }

  render() {
    const { terry } = this.props;
    const result = terry.get('result');

    return (
      <div className="wrap-page">
        { !result.isEmpty() && (
          <Result
            result={result.toJS()}
            uuid={terry.get('id')}
            isPermalink />
        ) }
      </div>
    );
  }
}

AppComponent.propTypes = {
  terry: PropTypes.instanceOf(Map)
};

const mapStateToProps = state => {
  return {
    terry: state.terry
  };
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getDetailsFromServer
  }, dispatch)
}

export default connect(mapStateToProps, mapDispatchToProps)(AppComponent);
