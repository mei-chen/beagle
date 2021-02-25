import React, { Component, PropTypes } from 'react';
import { Map, toJS } from 'immutable';
import { browserHistory } from 'react-router';
import { Button } from 'react-bootstrap';
import Timestamp from 'react-time';
import Confirm from 'react-confirm-bootstrap';
import AssignUsers from 'labeling/components/AssignUsers';
import AssigneesTable from 'labeling/components/AssigneesTable';

class Task extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    const { task, onRemoveTask, onRemoveAssignment, onAssign } = this.props;

    return (
      <div
        className="task">
        <div className="task-header">
          <div className="task-actions">
            <AssignUsers
              datasetId={task.get('dataset').get('id')}
              notAllowed={task.get('assignments').map(assignment => assignment.get('assignee'))}
              assignButton
              onAssign={users => onAssign(task.get('id'), users.map(user => user.get('id')).toJS())} />
            <span className="task-divider" />
            <Button
              bsStyle="primary"
              bsSize="small"
              onClick={() => browserHistory.push(`/export-supervised-dataset/${task.get('id')}`)}>
              Export Supervised Dataset
            </Button>
            <span className="task-divider" />
            <Confirm
              onConfirm={() => onRemoveTask(task.get('id'))}
              title="Remove task"
              body="Are you sure?">
              <i className="task-remove fa fa-trash" />
            </Confirm>
          </div>
          <div className="task-info">
            <span className="task-label">Owner: </span>{ task.get('owner').get('username') }
            <span className="task-divider task-divider--small" />
            <span className="task-label">Size: </span>
            <strong>{ task.get('dataset').get('samples') }</strong> rows
          </div>
          <div className="task-dataset">
            <time className="task-dataset-created">
              <Timestamp
                value={ task.get('created') }
                locale="en"
                titleFormat="YYYY/MM/DD HH:mm"
                relative />
            </time>
            <strong>{ task.get('name') }</strong>
          </div>
        </div>
        <AssigneesTable
          taskId={task.get('id')}
          assignments={task.get('assignments')}
          onRemove={assignmentId => onRemoveAssignment(task.get('id'), assignmentId)}/>
      </div>
    );
  }
}

Task.propTypes = {
  task: PropTypes.instanceOf(Map).isRequired,
  onRemoveTask: PropTypes.func.isRequired,
  onRemoveAssignment: PropTypes.func.isRequired
};

export default Task;
