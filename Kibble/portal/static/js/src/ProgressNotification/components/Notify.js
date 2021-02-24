import React from "react";
import { connect } from "react-redux";
import { bindActionCreators } from 'redux';
import { ProgressBar } from 'react-bootstrap'
import { MODULE_NAME } from "ProgressNotification";


class ProgressNotificationComponent extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    const {
      initialized,
      max,
      current,
      failed
    } = this.props;

    return (
      <span>
        <div>
          Your documents are being processed
        </div>
        {initialized &&
          <ProgressBar>
            <ProgressBar max={max} now={current} label={`${current}/${max} files processed`} />
            <ProgressBar bsStyle="warning" max={max} now={failed} label={`${failed}/${max} files failed`} />
          </ProgressBar>
        }
      </span>
    );
  }
}

const mapProgressStateToProps = (state) => {
  return {
    initialized: state[ MODULE_NAME ].get('initialized'),
    max: state[ MODULE_NAME ].get('max'),
    current: state[ MODULE_NAME ].get('current'),
    failed: state[ MODULE_NAME ].get('failed')
  };
};


// const mapDispatchToProps = dispatch => bindActionCreators({
// }, dispatch);


export const ProgressNotification=connect(mapProgressStateToProps)(ProgressNotificationComponent);

class LogNotificationComponent extends React.Component {
  constructor(props) {
    super(props);

    this.updateScroll = this.updateScroll.bind(this);
    this.scrolledBottom = true;
  }

  updateScroll(){
    //updated scroll if scrilled down
    var element = document.getElementById("scroll-bottom");
    if(this.scrolledBottom){
        element.scrollTop = element.scrollHeight;
    }
  }

  componentDidUpdate(prevProps, prevState) {
    if(prevProps.log_list !== this.props.log_list) {
      this.updateScroll()
    }
  }

  componentWillUpdate(prevProps, prevState) {
    //check if scrolled down
    var element = document.getElementById("scroll-bottom");
    var scrolledBottom = Math.abs(element.scrollHeight - (element.scrollTop+element.clientHeight)) < 3;
    this.scrolledBottom = scrolledBottom;
  }

  render() {
    const {
      triggered_log,
      log_list
    } = this.props;

    return (
      <span>
        <div>
          <h4>Notifications log</h4>
        </div>
        <div
          id="scroll-bottom"
          style={{
            background:'white',
            border:'1px solid lightgray',
            overflowY:'scroll',
            height:'200px',
          }}
        >
        {
          log_list.map((entry,key) => {
            return (
              <div
                style={{
                  padding:'3px',
                  margin: '3px',
                  background:`${
                    entry.level==='error'?'#ec3d3d':
                    entry.level==='warning'?'#ebad1a':
                    entry.level==='info'?'#369cc7':'#5ea400'
                  }`
                  ,color:'white'
                }}
                key={key}
              >
                {entry.message}
              </div>
            )
          })
        }
        </div>
      </span>
    );
  }
}

const mapLogStateToProps = (state) => {
  return {
    triggered_log: state[ MODULE_NAME ].get('triggered_log'),
    log_list: state[ MODULE_NAME ].get('log_list')
  };
};


// const mapDispatchToProps = dispatch => bindActionCreators({
// }, dispatch);


export const LogNotification=connect(mapLogStateToProps)(LogNotificationComponent);
