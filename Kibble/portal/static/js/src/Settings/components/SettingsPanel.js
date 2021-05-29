import React from 'react';
import { Map } from 'immutable';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import update from 'immutability-helper';
import { hashHistory } from 'react-router';

import {
  FormGroup,
  FormControl,
  ToggleButtonGroup,
  Radio,
  Button,
  Modal
} from 'react-bootstrap';

import { DNDTools } from './DNDTools';
import { Spinner } from 'base/components/misc.js';
import { changeSetting, setModalOpen, addPersonalDataType, deletePersonalDataType } from '../redux/modules/settings.js';
import { PersonalDataTypeCustomizationModal } from './PersonalDataTypeCustomizationModal';
import { setActiveRootFolder, setActiveUrl } from 'base/redux/modules/sidebar';

import '../scss/app.scss';
import '../scss/SettingsPanel.scss';

class ToggleSetting extends React.Component {
  render() {
    const { changeSetting, settingState, title, setting_name, hint } = this.props

    return(
      <div className="setting-wrapper">
        <div className="setting-content row-align">
          <div className="title-wrapper">
            <i className="fal fa-star" aria-hidden="true"/>
            <div>
              {title}
            </div>
          </div>
          <div className="toggle-color" onClick={() => changeSetting(setting_name, !settingState)}>
            <i className={`fal fa-toggle-${settingState ? 'on' : 'off'}`}/>
          </div>
        </div>
        <div className="hint-wrapper">
          {hint}
        </div>
      </div>
    )
  }
}

class SimpleInputSetting extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      threshold_value: this.props.settingState
    }

    this.onChangeString = this.onChangeString.bind(this);
  }

  onChangeString(e) {
    this.setState({
      threshold_value:e.target.value
    })
  }

  render() {
    const { changeSetting, title, setting_name } = this.props;

    return(
      <div className="setting-wrapper">
        <div className="setting-content row-align">
          <div className="title-wrapper">
            <i className="fal fa-minus-hexagon" aria-hidden="true"/>
            <div>
              {title}
            </div>
          </div>
          <div className="input-wrapper">
            <FormControl
              type="number"
              value={this.state.threshold_value}
              onChange={this.onChangeString}
            />
            <Button
              onClick={() => changeSetting(setting_name, this.state.threshold_value) }
            >
              Submit
            </Button>
          </div>
        </div>
        <div className="hint-wrapper">
          <div>
            <i className="fal fa-info-circle"/>
            Set minimum number of characters for found sentences inside{' '}
            <a onClick={() => this.props.navTo('/sentences', 'Sentence')}>Sentence Pulling </a>
          </div>
        </div>
      </div>
    )
  }
}

export class DefaultObfuscationSetting extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      obfuscation_string: this.props.obfuscationString
    }

    this.onChangeString = this.onChangeString.bind(this);
    this.onChangeObfuscationType = this.onChangeObfuscationType.bind(this);

    this.colors = [
      "black",
      "darkBlue",
      "blue",
      "darkGreen",
      "green",
      "darkRed",
      "darkMagenta",
      "darkCyan",
      "cyan",
      "red",
      "magenta",
      "yellow",
      "darkGray",
      "lightGray",
      "white"
    ];
  }

  onChangeObfuscationType(e) {
    const tool = e;
    this.props.changeSetting('obfuscate_type', tool);
  }

  onChangeString(e) {
    this.setState({
      obfuscation_string:e.target.value
    })
  }

  render() {
    const {
      changeSetting,
      defaultObfuscationTool,
      obfuscationString,
      highlightColor,
      setModalOpen
    } = this.props;

    return(
      <div className="setting-wrapper">
        <div className="setting-content column-align">
          <div className="title-wrapper">
            <i className="fal fa-user-secret" aria-hidden="true"/>
            <div>
              Default personal information export handling method
            </div>
          </div>
          <div className="hint-wrapper">
            <div className="multiple-row-info">
              <i className="fal fa-info-circle"/>
              <div>
                Choose the obfuscation method used to export files in{' '}
                <a onClick={() => this.props.navTo('/identifiable-information', 'Pre-process')}>
                  Identifiable information
                </a>
                <br/>
                The selected method will also be used in{' '}
                <a onClick={() => this.props.navTo('/sentences-obfuscation', 'Sentence')}>
                  Sentences Obfuscation
                </a>, when exporting (select none if you wish not to use it)
              </div>
            </div>
          </div>
          <div className="content-wrapper wide">
            <Button bsSize="small" onClick={(e) => {
              setModalOpen(true);
              e.stopPropagation(); //stop from collapsing in /PII
            }}>
              <i className="fal fa-cog"/> Manage personal data types
            </Button>

            <h4> String obfuscation </h4>
            <div className="string-form-wrapper">
              <FormControl
                type="text"
                value={this.state.obfuscation_string}
                onChange={this.onChangeString}
                onClick={(e) => {
                  e.stopPropagation(); //stop from collapsing in /PII
                }}
              />
              <Button
                onClick={(e) => {
                  changeSetting('obfuscate_string', this.state.obfuscation_string);
                  e.stopPropagation(); //stop from collapsing in /PII
                }}
              >
                Submit
              </Button>
            </div>

            <h4> Highlight Color </h4>
            <div className="colors-wrapper">
            {
              this.colors.map((color,key) => {
                return(
                  <div
                    key={key}
                    className="color-block"
                    onClick={(e) => {e.stopPropagation(); changeSetting('highlight_color', color)}}
                    style={{
                      backgroundColor:color.toLowerCase()
                    }}
                  >
                    { highlightColor === color &&
                      <i
                        className="fas fa-check"
                        style={{color:color==='white' || color==='yellow' ? 'black' : 'white'}}
                      /> }
                  </div>
                )
              })
            }
            </div>
          </div>
        </div>
      </div>
    )
  }
}

class DefaultToolsSetting extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      auto_cleanup_tools: this.props.currentSelectedTools.map((tool,key) => {
        return {
          id: key,
          tool_name: tool.tool_name || tool
        }
      })
    }
    this.handleClickOnTool = this.handleClickOnTool.bind(this);
    this.moveTool = this.moveTool.bind(this);
    this.applyOnDrop = this.applyOnDrop.bind(this);
  }

  handleClickOnTool(tool){
    if(this.state.auto_cleanup_tools.includes(tool)){
      var aux_tools_list = this.state.auto_cleanup_tools;
      aux_tools_list.splice(aux_tools_list.indexOf(tool),1);
    }
    else{
      var aux_tools_list = this.state.auto_cleanup_tools;

      //get max id from current list and add 1 to obtain new id
      const new_id = Math.max.apply(Math, aux_tools_list.map(tool => tool.id)) + 1;
      aux_tools_list.push({id:new_id,tool_name:tool});
    }

    const { changeSetting } = this.props;
    changeSetting('auto_cleanup_tools',aux_tools_list.map(tool=>tool.tool_name));
  }

  moveTool(dragIndex, hoverIndex) {
    const { auto_cleanup_tools } = this.state
    const dragCard = auto_cleanup_tools[dragIndex]

    this.setState(
      update(this.state, {
        auto_cleanup_tools: {
          $splice: [[dragIndex, 1], [hoverIndex, 0, dragCard]],
        },
      }),
    )
  }

  applyOnDrop() {
    const { changeSetting } = this.props;
    changeSetting('auto_cleanup_tools',this.state.auto_cleanup_tools.map(tool=>tool.tool_name));
  }

  render() {
    const { cleanupTools } = this.props;

    return(
      <div className="setting-wrapper">
        <div className="setting-content column-align">
          <div className="title-wrapper">
            <i className="fal fa-list-ol" aria-hidden="true"/>
            <div>
              Auto process cleanup document configuration
            </div>
          </div>
          <div className="hint-wrapper">
            <div className="multiple-row-info">
              <i className="fal fa-info-circle"/>
              <div>
                When auto process new files setting is on use the following setup to clean your files
                <br/>
                You can clean your documents whenever you want with different setup in{' '}
                <a onClick={() => this.props.navTo('/cleanup-document', 'Pre-process')}>Cleanup Document</a>
              </div>
            </div>
          </div>
          <div className="content-wrapper">
            <div className="hint-wrapper">
              <div><i className="fal fa-arrows-v"/>Use drag and drop to sort tools as you prefer</div>
              <div>Click{' '}<i className="far fa-times"/>to disable a specific tool</div>
            </div>
            <DNDTools
              handleClickOnTool={this.handleClickOnTool}
              auto_cleanup_tools={this.state.auto_cleanup_tools}
              moveTool={this.moveTool}
              applyOnDrop={this.applyOnDrop}
              changeSetting={changeSetting}
            />
            <br/>
            <div className="hint-wrapper">
              <div>Click{' '}<i className="far fa-plus"/>{' '}to enable a specific tool</div>
            </div>
            {cleanupTools.map((tool,key) =>
              !this.state.auto_cleanup_tools.map(tool => tool.tool_name).includes(tool.tool) &&
              <div
                className="tool"
                key={key}
              >
                {tool.tool}
                <div className="indicator" onClick={() => this.handleClickOnTool(tool.tool)}>
                  <i className="far fa-plus" aria-hidden="true"/>
                </div>
              </div>)
            }
          </div>
        </div>
      </div>
    )
  }
}

class SettingsPanel extends React.Component {
  constructor(props) {
    super(props);

    this.currentLocationPath = () => hashHistory.getCurrentLocation().pathname;
    this.navTo = this.navTo.bind(this);
  }

  navTo(page, rootFolder = null) {
    if (this.currentLocationPath() !== page) {
      hashHistory.push(page);
    }
    if (rootFolder) {
      this.props.setActiveRootFolder(rootFolder)
    }
    this.props.setActiveUrl(page);
  }

  render() {
    const {
      settings,
      user,
      changeSetting,
      setModalOpen,
      addPersonalDataType,
      deletePersonalDataType,
      cleanupTools
    } = this.props;

    const fileAutoProcessHint = (
      <div>
        <i className="fal fa-info-circle"/>
        Automatically convert, cleanup and split into sentences newly uploaded files
      </div>
    );

    const autoGatheringHint = (
      <div className="multiple-row-info">
        <i className="fal fa-info-circle"/>
        <div>
          Automatically find and gather personal data information when upload files
          <br/>
          You can manually gather data for batches that were uploaded when this option was off in{' '}
          <a onClick={() => this.navTo('/identifiable-information', 'Pre-process')}>
            Identifiable Information
          </a>
        </div>
      </div>
    );

    return (
      <div className="settings-wrapper">
        <div className="check-mark-wrapper">
          { settings.change_success === 'success' &&
            <div className="check-mark">
              <i className="fal fa-check"/> Successfully changed settings
            </div>
          }
          { settings.change_success === 'fail' &&
            <div className="check-mark">
              <i className="fal fa-times"/> Failed changing settings
            </div>
          }
        </div>
        <ToggleSetting
          settingState={settings.file_auto_process}
          changeSetting={changeSetting}
          title="Auto process new files"
          setting_name="file_auto_process"
          hint={fileAutoProcessHint}
        />
        <SimpleInputSetting
          title="Set sentence finding threshold value"
          setting_name="sentence_word_threshold"
          changeSetting={changeSetting}
          settingState={settings.sentence_word_threshold}
          navTo={this.navTo}
        />
        <DefaultToolsSetting
          cleanupTools={cleanupTools}
          changeSetting={changeSetting}
          currentSelectedTools={settings.auto_cleanup_tools}
          navTo={this.navTo}
        />
        <ToggleSetting
          settingState={settings.auto_gather_personal_data}
          changeSetting={changeSetting}
          title="Auto gathering personal data"
          setting_name="auto_gather_personal_data"
          hint={autoGatheringHint}
          navTo={this.navTo}
        />
        <DefaultObfuscationSetting
          changeSetting={changeSetting}
          defaultObfuscationTool={settings.obfuscate_type}
          obfuscationString={settings.obfuscate_string}
          highlightColor={settings.highlight_color}
          navTo={this.navTo}
          setModalOpen={setModalOpen}
        />
        <PersonalDataTypeCustomizationModal
          changeSetting={changeSetting}
          addPersonalDataType={addPersonalDataType}
          deletePersonalDataType={deletePersonalDataType}
          personal_data_types={settings.personal_data_types}
          isOpen={settings.isModalOpen}
          onClose={setModalOpen}
          change_success={settings.change_success}
          custom_personal_data={settings.custom_personal_data}
          custom_type_names={settings.custom_type_names}
        />
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    settings: state.settings,
    cleanupTools: state.CleanupDocument.get('tools').toJS()
  };
};

const mapDispatchToProps = dispatch => bindActionCreators({
  changeSetting,
  setActiveRootFolder,
  setActiveUrl,
  setModalOpen,
  addPersonalDataType,
  deletePersonalDataType
}, dispatch);

export default connect(mapStateToProps,mapDispatchToProps)(SettingsPanel);
