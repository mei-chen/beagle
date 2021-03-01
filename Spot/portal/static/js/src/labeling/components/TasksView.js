import React, { Component, PropTypes } from 'react';
import { Map } from 'immutable';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { browserHistory } from 'react-router';
import { Grid, Button } from 'react-bootstrap';
import AssignmentsTable from 'labeling/components/AssignmentsTable';
import Task from 'labeling/components/Task';

import 'labeling/scss/app.scss';

import {
  getFromServer as getTasks,
  removeFromServer as removeTask,
  assignOnServer as assignUser,
  unassignOnServer as unassignUser,
  getAssignmentsFromServer as getAssignments,
  rejectAssignmentOnServer as rejectAssignment
} from 'labeling/redux/modules/tasks_module';

class TasksView extends Component {
  constructor(props) {
    super(props);
    this._getData = this._getData.bind(this);
    this._renderTasks = this._renderTasks.bind(this);
  }

  componentDidMount() {
    this._getData()
  }

  _getData() {
    const { getTasks, getAssignments } = this.props;
    getTasks();
    getAssignments();
  }

  _renderTasks(tasks) {
    const { removeTask, assignUser, unassignUser } = this.props;

    return tasks.map((task, i) => (
      <Task
        key={i}
        task={task}
        onRemoveTask={id => removeTask(id).then(this._getData)}
        onRemoveAssignment={(taskId, assignmentId) => unassignUser(taskId, assignmentId).then(this._getData)}
        onAssign={(taskId, assigneeIds) => assignUser(taskId, assigneeIds).then(this._getData)} />
    ))
  }

  render() {
    const { tasks, assignments, rejectAssignment, getAssignments } = this.props;

    if(tasks.get('isLoading') || assignments.get('isLoading')) return <div className="spinner spinner--center" />;

    return (
      <Grid fluid={true}>
        <h1>Labeling</h1>
        <hr />

        {/* 'create new task' button */}
        <Button
          bsStyle="primary"
          onClick={() => browserHistory.push('/create-task')}>
          Create new
        </Button>
        <hr />

        {/* labeling tasks */}
        <div className="tasks">
          <h3>Labeling tasks</h3>
          { !tasks.get('data').isEmpty() ? this._renderTasks(tasks.get('data')) : <div>You have no labeling tasks</div> }
        </div>

        {/* assignments */}
        <div className="tasks">
          <h3>Assignments</h3>
          { !assignments.get('data').isEmpty() ? (
            <AssignmentsTable
              assignments={assignments.get('data')}
              onReject={id => rejectAssignment(id).then(this._getData)} />
          ) : <div>You have no assignments</div> }
        </div>
      </Grid>
    )
  }
}

TasksView.propTypes = {
  tasks: PropTypes.instanceOf(Map).isRequired,
  assignments: PropTypes.instanceOf(Map).isRequired
};

const mapStateToProps = state => ({
  tasks: state.tasksModule.get('tasks'),
  assignments: state.tasksModule.get('assignments')
});

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getTasks,
    getAssignments,
    removeTask,
    assignUser,
    unassignUser,
    rejectAssignment
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(TasksView);
