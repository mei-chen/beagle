import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from "redux";
import {
  Grid, Col, Button, Panel, Glyphicon
} from 'react-bootstrap';

import { MODULE_NAME } from 'IdentifiableInformation/redux/constants';
import FoundInformations from 'IdentifiableInformation/components/FoundInformations';
import { getProjects } from "base/redux/modules/projects";
import { getFromServer as getSettings, getCustomPersonalData } from 'Settings/redux/modules/settings.js'


class ContentComponent extends React.Component {
  constructor(props) {
    super(props);
  }

  componentDidMount() {
    this.props.getSettings();
    this.props.getProjects();
    this.props.getCustomPersonalData();
  }


  render() {
    const { isInitialized } = this.props;
    return (
      <div>
        <Grid>
          <FoundInformations/>
        </Grid>
      </div>
    );
  }
}

export default connect(
  (state) => ({
    isInitialized: state[ MODULE_NAME ].get('isInitialized')
  }),
  (dispatch) => bindActionCreators({
    getProjects,
    getSettings,
    getCustomPersonalData
  }, dispatch)
)(ContentComponent);
