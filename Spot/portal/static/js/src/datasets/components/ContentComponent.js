import React from 'react';
import { Link } from 'react-router';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import DataTable from 'base/components/DataTable';

import 'datasets/scss/app.scss';

import { uninviteOnServer, DATASET } from 'base/redux/modules/collaborators_module'
import { getFromServer, deleteFromServer } from 'datasets/redux/modules/datasets_module';

class ContentComponent extends React.Component {
  constructor(props) {
    super(props);
    this._handleDelete = this._handleDelete.bind(this);
    this._revokeInvitation = this._revokeInvitation.bind(this);
  }

  _handleDelete(id) {
    this.props.deleteFromServer(id);
  }

  _revokeInvitation(id) {
    const { uninviteOnServer, getFromServer } = this.props;
    uninviteOnServer(DATASET, id).then(getFromServer);
  }

  render() {
    const { datasetsModule } = this.props;
    const isInitialized = datasetsModule.get('isInitialized');
    const datasets = datasetsModule.get('datasets');
    const isData = !!datasets && datasets.size > 0;

    return (
      <div>
        <Link to="/create-dataset" className="btn btn-primary">Create new</Link>
        <hr />
        {
          isInitialized && isData ? (
            <DataTable
              type="datasets"
              data={datasets}
              onDelete={this._handleDelete}
              onRevoke={this._revokeInvitation} />
          ) : (
            <div className="empty-list">
              <span>No dataset</span>
            </div>
          )
        }
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    datasetsModule: state.datasetsModule
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getFromServer,
    deleteFromServer,
    uninviteOnServer
  }, dispatch)
}

export default connect(mapStateToProps, mapDispatchToProps)(ContentComponent);
