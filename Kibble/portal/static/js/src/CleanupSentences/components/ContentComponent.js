import React from 'react';
import { connect } from 'react-redux';
import { Grid, Col } from 'react-bootstrap';
import 'OnlineFolder/scss/app.scss';
import BatchList from './BatchList';


class ContentComponent extends React.Component {
  render() {
    return (
      <div>
        <Grid>
          <Col xs={12} md={12}>
            <BatchList />
          </Col>
        </Grid>
      </div>
    );
  }
}

ContentComponent.defaultProps = {
};

const mapStateToProps = (state) => {
  return {
    OnlineFolder: state.OnlineFolder
  };
};

export default connect(mapStateToProps)(ContentComponent);
