import React, { Component, PropTypes } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import Result from './Result';
import { Map } from 'immutable';

// App
import {
  getDetailsFromServer
} from 'search/redux/modules/terry';
import '../scss/app.scss';

class ReportPage extends Component {
  constructor(props) {
    super(props);
  }

  componentWillMount() {
    const { getDetailsFromServer } = this.props;
    const { uuid } = this.props.params;

    getDetailsFromServer(uuid)
  }

  render() {
    const { result, isInitialized } = this.props;
    const { uuid } = this.props.params;

    if(!isInitialized) {
      return (
        <div className="spinner spinner--center"></div>
      );
    }

    return (
      <div className="wrap-page">
        { !result.isEmpty() && (
          <Result
            result={result.toJS()}
            uuid={uuid}
          />
        )}
      </div>
    );
  }
}

ReportPage.propTypes = {
  result: PropTypes.instanceOf(Map).isRequired,
  isInitialized: PropTypes.bool.isRequired
};

const mapStateToProps = state => {
  return {
    result: state.terry.get('result'),
    isInitialized: state.terry.get('isInitialized')
  };
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getDetailsFromServer
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(ReportPage);
