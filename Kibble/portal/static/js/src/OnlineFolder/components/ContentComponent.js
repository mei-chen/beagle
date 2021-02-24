import React from 'react';
import { connect } from 'react-redux';
import 'OnlineFolder/scss/app.scss';
import { setDropboxAccess, getAccessInfo } from '../redux/modules/onlineFolder.js'
import ListOfBatches from 'base/components/ListOfBatches';
import PickerPanel from './PickerPanel';

class ContentComponent extends React.Component {
  componentWillMount() {
    const { dispatch } = this.props;
    if (window.location.hash) {
      const groups = window.location.hash.match(/token=([^&]*)/);
      if (groups) {
        const token = groups[1];
        dispatch(setDropboxAccess(token));
      }
    }
    location.hash="#/online-folder";
  }
  render() {
    return (
      <div className="wrapper online-wrapper">
        <PickerPanel />
        <ListOfBatches />
      </div>
    );
  }
}
ContentComponent.defaultProps = {
};
const mapStateToProps = (state) => {
  return {
    OnlineFolder: state.OnlineFolder
  };
};
export default connect(mapStateToProps)(ContentComponent);
