import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { List, fromJS } from 'immutable';
import { Button, Modal, ModalHeader, ModalBody } from 'react-bootstrap';
import AssignUsersList from 'labeling/components/AssignUsersList';

import { getUsersFromServer as getUsers } from 'labeling/redux/modules/tasks_module';

class AssignUsers extends Component {
  constructor(props) {
    super(props);
    this._showModal = this._showModal.bind(this);
    this._hideModal = this._hideModal.bind(this);
    this._handleAssign = this._handleAssign.bind(this);
    this._getUsers = this._getUsers.bind(this);
    this._prepareUsers = this._prepareUsers.bind(this);

    this.state = {
      showModal: false,
      isLoading: false,
      users: List()
    }
  }

  _getUsers() {
    const { datasetId, getUsers } = this.props;

    this.setState({ isLoading: true });
    getUsers(datasetId)
      .then(res => this.setState({ isLoading: false, users: this._prepareUsers(fromJS(res.data)) }));
  }

  _prepareUsers(users) {
    const { notAllowed } = this.props;
    return notAllowed ? users.filter(user => !notAllowed.find(x => x.get('id') === user.get('id'))) : users;
  }

  _showModal() {
    this.setState({ showModal: true });
    this._getUsers();
  }

  _hideModal() {
    this.setState({ showModal: false });
  }

  _handleAssign(users) {
    const { onAssign } = this.props;
    onAssign(users)
    this._hideModal()
  }

  render() {
    const { checked, assignButton, onCheck, onUncheck } = this.props;
    const { showModal, isLoading, users } = this.state;

    return (
      <div className="assign-button-wrap">
        <Button
          bsStyle="default"
          bsSize="small"
          className="assign-button"
          onClick={this._showModal}>
          <i className="fa fa-user-plus" />
          Assign
        </Button>

        <Modal
          show={showModal}
          onHide={this._hideModal}>
          <ModalHeader closeButton>
            <h4>Assign users</h4>
          </ModalHeader>
          <ModalBody>
            { isLoading ? (
              <div><i className="fa fa-spinner fa-spin" /></div>
            ) : (
              <AssignUsersList
                users={users}
                checked={checked}
                assignButton={assignButton}
                onCheck={onCheck}
                onUncheck={onUncheck}
                onAssign={this._handleAssign} />
            ) }
          </ModalBody>
        </Modal>
      </div>
    )
  }
}

const mapStateToProps = state => ({});

const mapDispatchToProps = dispatch => (
  bindActionCreators({
    getUsers
  }, dispatch)
)

AssignUsers.propTypes = {
  datasetId: PropTypes.number.isRequired,
  assignButton: PropTypes.bool,
  onAssign: PropTypes.func,
  onCheck: PropTypes.func,
  onUncheck: PropTypes.func,
  notAllowed: PropTypes.instanceOf(List),
  checked: PropTypes.instanceOf(List)
};

export default connect(mapStateToProps, mapDispatchToProps)(AssignUsers);
