import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import 'Settings/scss/app.scss';
import { getFromServer, getCustomPersonalData } from '../redux/modules/settings.js'
import { getCleanupDocTools } from 'base/redux/modules/tools';
import SettingsPannel from './SettingsPannel'
import { Spinner } from 'base/components/misc.js'

class ContentComponent extends React.Component {
  componentWillMount() {
    const { getFromServer, getCustomPersonalData, getCleanupDocTools } = this.props;
    getCleanupDocTools();
    getFromServer();
    getCustomPersonalData();
  }
  render() {
    const { isInitialized, isInitializedCustomPersonalData, cleanupTools } = this.props;
    return (
      <div className="wrapper online-wrapper">
        {isInitialized && isInitializedCustomPersonalData && cleanupTools.size > 0 ?
        <SettingsPannel/> :
        <Spinner/>
        }
      </div>
    );
  }
}
ContentComponent.defaultProps = {
};
const mapStateToProps = (state) => {
  return {
    isInitialized: state.settings.isInitialized,
    isInitializedCustomPersonalData: state.settings.isInitializedCustomPersonalData,
    cleanupTools: state.CleanupDocument.get('tools')
  };
};
const mapDispatchToProps = dispatch => bindActionCreators({
  getCleanupDocTools,
  getFromServer,
  getCustomPersonalData
}, dispatch);
export default connect(mapStateToProps,mapDispatchToProps)(ContentComponent);
