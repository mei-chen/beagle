import React, { Component, PropTypes } from 'react';
import { List } from 'immutable';
import { FormControl, Button } from 'react-bootstrap';

class AssignUsersList extends Component {
  constructor(props) {
    super(props);
    this._filterUsers = this._filterUsers.bind(this);
    this._checkUser = this._checkUser.bind(this);
    this._uncheckUser = this._uncheckUser.bind(this);
    this._assignUsers = this._assignUsers.bind(this);
    this._handleInputChange = this._handleInputChange.bind(this);
    this._handleUserClick = this._handleUserClick.bind(this);
    this._renderUsers = this._renderUsers.bind(this);

    this.state = {
      searchValue: '',
      checked: props.checked || List()
    }
  }

  _filterUsers(query, users) {
    return users.filter(user => user.get('username').toLowerCase().indexOf(query.toLowerCase()) !== -1);
  }

  _handleInputChange(e) {
    this.setState({ searchValue: e.target.value })
  }

  _checkUser(user) {
    const { checked } = this.state;
    const { onCheck } = this.props;
    this.setState({ checked: checked.push(user) });
    onCheck && onCheck(user)
  }

  _uncheckUser(user) {
    const { checked } = this.state;
    const { onUncheck } = this.props;
    this.setState({ checked: checked.filter(x => x.get('id') !== user.get('id')) });
    onUncheck && onUncheck(user)
  }

  _handleUserClick(isChecked, user) {
    isChecked ? this._uncheckUser(user) : this._checkUser(user);
  }

  _assignUsers() {
    const { checked } = this.state;
    const { onAssign } = this.props;
    onAssign(checked);
  }

  _renderUsers(users) {
    const { checked } = this.state;

    return users.map((user, i) => {
      const isChecked = checked.find(x => x.get('id') === user.get('id'));
      return (
        <div
          key={i}
          className={`assign-user ${isChecked ? 'assign-user--checked' : ''}`}
          onClick={() => this._handleUserClick(isChecked, user)}>
          { isChecked ? <i className="fa fa-check fa-fw" /> : <i className="fa fa-user fa-fw" /> }
          { user.get('username') }
        </div>
      )
    });
  }

  render() {
    const { users, assignButton, onAssign } = this.props;
    const { searchValue, checked } = this.state;
    const filteredUsers = this._filterUsers(searchValue, users);

    return (
      <div className="assign clearfix">
        <FormControl
          type="text"
          value={searchValue}
          onChange={this._handleInputChange}
          className="assign-search" />
        { filteredUsers.size > 0 ? (
          <div className="assign-list">
            {this._renderUsers(this._filterUsers(searchValue, users))}
          </div>
        ) : (
          <div className="assign-placeholder">No users to assign</div>
        ) }
        <span className="assign-info">Only dataset collaborators can be assigned</span>

        { assignButton && (
          <Button
            bsStyle="primary"
            disabled={checked.size === 0}
            onClick={() => onAssign(checked)}>
            Assign
          </Button>
        ) }
      </div>
    )
  }
}

AssignUsersList.propTypes = {
  users: PropTypes.instanceOf(List),
  assignButton: PropTypes.bool, // used for assigning all checked users
  onAssign: PropTypes.func,
  onCheck: PropTypes.func,
  onUncheck: PropTypes.func
};

export default AssignUsersList;
