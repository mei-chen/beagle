import React, { Component, PropTypes } from 'react';
import { List } from 'immutable';
import { Link } from 'react-router';
import { Table } from 'react-bootstrap';
import Timestamp from 'react-time';
import Confirm from 'react-confirm-bootstrap';
import Progress from 'base/components/Progress';

class AssignmentsTable extends Component {
  constructor(props) {
    super(props);
    this._renderAssignments = this._renderAssignments.bind(this);
  }

  _renderAssignments(assignments) {
    const { onReject } = this.props;

    return assignments.map(assignment => {
      const stats = assignment.get('stats');

      return (
        <tr key={assignment.get('id')}>
          <td>
            <Link to={`/assignments/${assignment.get('id')}`}>
              { assignment.get('labeling_task').get('name') }
            </Link>
          </td>
          <td>{ assignment.get('owner').get('username') }</td>
          <td>
            <Timestamp
              value={ assignment.get('created') }
              locale="en"
              titleFormat="YYYY/MM/DD HH:mm"
              relative />
          </td>
          <td>{ stats.get('stage') }</td>
          <td>
            <Progress value={stats.get('labeled')/stats.get('total')} />
          </td>
          <td>
            <Confirm
              onConfirm={() => onReject(assignment.get('id'))}
              title="Reject assignment"
              body="Are you sure?">
              <i className="delete-icon fa fa-times" />
            </Confirm>
          </td>
        </tr>
      )
    });
  }

  render() {
    const { assignments } = this.props;
    return (
      <Table className="assignments-table">
        <thead>
          <tr>
            <th>Labeling task</th>
            <th>Owner</th>
            <th>Created</th>
            <th>Stage</th>
            <th>Progress</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          { this._renderAssignments(assignments) }
        </tbody>
      </Table>
    )
  }
}

AssignmentsTable.propTypes = {
  assignments: PropTypes.instanceOf(List).isRequired,
  onReject: PropTypes.func.isRequired
};

export default AssignmentsTable;
