import React, { Component, PropTypes } from 'react';
import { List, Map } from 'immutable';
import Confirm from 'react-confirm-bootstrap';
import Propgress from 'base/components/Progress';
import EvalScore from 'labeling/components/EvalScore';
import CustomSlider from 'base/components/Slider';

class AssigneesTable extends Component {
  constructor(props) {
    super(props);
    this._renderAssignments = this._renderAssignments.bind(this);
  }

  _renderAssignments(assignments) {
    const { onRemove, extended, trustById, defaultTrust, onTrustChange, taskId } = this.props;

    return assignments.map((assignment, i) => {
      const assignee = assignment.get('assignee');
      const stats = assignment.get('stats');
      const assignmentId = assignment.get('id');

      return (
        <tr
          key={i}
          className="task-assignee">
          <td className="task-assignee-name">
            <i className="fa fa-user" />
            { assignee.get('username') }
          </td>
          { extended && (
            <td className="task-assignee-trust">
              <CustomSlider
                sliderPercentage={trustById.get(assignmentId) === undefined ? defaultTrust : trustById.get(assignmentId) /* can be 0 */}
                handleSliderChange={value => onTrustChange(assignmentId, value)}
                sliderOptions={{step: 5}}
                inputOptions={{step: 5}}
                small />
            </td>
          ) }
          <td className="task-assignee-score">
            { typeof assignment.get('score') === 'number' ?  ( /* could be 0 */
              <EvalScore
                taskId={taskId}
                assignmentId={assignmentId}
                value={assignment.get('score') * 10}
                max={10} />
            ) : (
              <span>-</span>
            )}
          </td>
          <td className="task-assignee-score">{ stats.get('skipped') }</td>
          <td className="task-assignee-stage">{ stats.get('stage') }</td>
          <td
            className="task-assignee-progress">
            <Propgress value={stats.get('labeled') / stats.get('total')} />
          </td>
          <td>
            <Confirm
              onConfirm={() => onRemove(assignment.get('id'))}
              title="Remove assignment"
              body="Are you sure?">
              <i className="task-assignee-remove fa fa-times" />
            </Confirm>
          </td>
        </tr>
      )
    })
  }

  render() {
    const { assignments, extended } = this.props;

    if(assignments.size === 0) return <div className="task-assignees-placeholder">No assignees</div>;

    return (
      <table className="task-assignees">
        <thead>
          <tr className="task-assignee">
            <th className="task-assignee-name">Assignee</th>
            { extended && <th className="task-assignee-trust">Trust</th> }
            <th className="task-assignee-score">Eval Score</th>
            <th className="task-assignee-skipped">Skipped</th>
            <th className="task-assignee-stage">Stage</th>
            <th className="task-assignee-progress">Progress</th>
            <th className="task-assignee-actions"></th>
          </tr>
        </thead>
        <tbody>
          { this._renderAssignments(assignments) }
        </tbody>
      </table>
    )
  }
};

AssigneesTable.propTypes = {
  taskId: PropTypes.number.isRequired,
  assignments: PropTypes.instanceOf(List).isRequired,
  trustById: PropTypes.instanceOf(Map),
  defaultTrust: PropTypes.number,
  onRemove: PropTypes.func.isRequired,
  onTrustChange: PropTypes.func,
  extended: PropTypes.bool, // add additional trust column
};

export default AssigneesTable;
