import React from "react";
import { connect } from "react-redux";
import { Grid, Col } from "react-bootstrap";
import { Spinner } from "base/components/misc";
import ContentComponent from 'LocalFolder/components/ContentComponent';
import 'LocalFolder/scss/app.scss';


class AppComponent extends React.Component {
  render() {
    if (!this.props.userStore.get('isInitialized')) {
      return <Spinner message="Loading..."/>
    }

    return (
      <div>
        <Grid fluid>
          <Col xs={12} md={12}>
            <h1 id="content-header">
              Local Folder
            </h1>
          </Col>
        </Grid>
        <ContentComponent />
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    userStore: state.global.user
  };
};

export default connect(mapStateToProps)(AppComponent);
