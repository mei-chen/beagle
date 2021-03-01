import React from 'react';
import { triggerLog } from 'ProgressNotification/actions'
import { connect } from "react-redux";
import { MODULE_NAME } from "ProgressNotification";
import { pushMessage } from 'Messages/actions';
import { LogNotification } from 'ProgressNotification/components/Notify';

class NotificationLogTrigger extends React.Component {
  constructor(props) {
    super(props);
  }

  render () {
    const logNotifComponent = (
    <div>
      <LogNotification/>
    </div>
  )

    return (
       <div
          className="notification-trigger-button"
          title="Show notification log"
          onClick={() =>{
            this.props.dispatch(triggerLog(this.props.triggered_log));
            this.props.dispatch(pushMessage(logNotifComponent, 'info'));
          }}
        >
          <span className="far fa-bars">
          </span>
          {this.props.new_log_marker ?
            <i className="fas fa-circle fa-xs"></i> : null
          }
          Show log
      </div>
    )
  }
}


const mapStateToProps = (state) => {
  return {
    triggered_log: state[ MODULE_NAME ].get('triggered_log'),
    new_log_marker: state[ MODULE_NAME ].get('new_log_marker'),
  };
};


export default connect(mapStateToProps)(NotificationLogTrigger);
