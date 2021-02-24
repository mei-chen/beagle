import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { changeSetting } from '../redux/modules/settings.js'
import { Spinner } from 'base/components/misc.js'
import {
  ButtonToolbar,
  ToggleButtonGroup,
  ToggleButton
} from 'react-bootstrap';

import 'Settings/scss/app.scss';
import 'Settings/scss/SettingsPannel.scss'

class DefaultExportSwitch extends React.Component {

  constructor(props) {
    super(props);
    this.handleChangeDefaultExport = this.handleChangeDefaultExport.bind(this);
  }

  handleChangeDefaultExport(e) {
    this.props.changeSetting('obfuscated_export_ext',e);
  }

  render() {
    const { changeSetting, settingState, title, setting_name } = this.props

    return(
      <div className="setting-wrapper out-context">
        <div className="setting-content row-allign">
          <div className="title-wrapper">
            <i className="fal fa-cloud-upload" aria-hidden="true"/>
            <div>
              Selected export format:
            </div>
          </div>
          <ButtonToolbar>
            <ToggleButtonGroup
              onChange={this.handleChangeDefaultExport}
              type="radio"
              name="options"
              value={this.props.default_export}
            >
              <ToggleButton value={"PDF"}>PDF</ToggleButton>
              <ToggleButton value={"DOCX"}>DOCX</ToggleButton>
            </ToggleButtonGroup>
          </ButtonToolbar>
        </div>
      </div>
    )
  }
}

const mapDispatchToProps = dispatch => bindActionCreators({
  changeSetting
}, dispatch);

export default connect(null, mapDispatchToProps)(DefaultExportSwitch);