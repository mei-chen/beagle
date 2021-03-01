import React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Grid, Col } from 'react-bootstrap';
import { getProjects } from "base/redux/modules/projects";
import ContentComponent from 'SentencesObfuscation/components/ContentComponent';
import 'SentencesObfuscation/scss/app.scss';


class AppComponent extends React.Component {
  componentDidMount() {
    this.props.getProjects()
  }

  render() {
    return (
      <div>
        <Grid fluid>
          <Col xs={12} md={12}>
            <h1 id="content-header">
              Sentences Obfuscation
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
  };
};

const mapDispatchToProps = (dispatch) => {
  return bindActionCreators({
    getProjects
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(AppComponent);
