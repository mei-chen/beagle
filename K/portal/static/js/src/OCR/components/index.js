import React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Grid, Col } from 'react-bootstrap';
import { getProjects } from "base/redux/modules/projects";
import { pushMessage } from 'Messages/actions';
import { setTaskState } from 'OCR/redux/actions';
import ContentComponent from 'OCR/components/ContentComponent';
import 'OCR/scss/app.scss';


class AppComponent extends React.Component {
  componentDidMount() {
    this.props.getProjects()
  }

  componentWillReceiveProps({ taskState }) {
    if (taskState === null) return;
    if (!taskState) {
      this.props.pushMessage('OCR is done.', 'success');
      this.props.setTaskState(null);
    }
  }

  render() {
    return (
      <div>
        <Grid fluid>
          <Col xs={12} md={12}>
            <h1 id="content-header">
              OCR
            </h1>
          </Col>
        </Grid>
        <Grid>
          <Col xs={12} md={12}>
            <ContentComponent />
          </Col>
        </Grid>
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    taskState: state.ocrStore.get('taskState')
  };
};

const mapDispatchToProps = (dispatch) => {
  return bindActionCreators({
    pushMessage, getProjects, setTaskState
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(AppComponent);
