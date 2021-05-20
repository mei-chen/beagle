import React, { Component } from "react";
import { connect } from "react-redux";
import { bindActionCreators } from "redux";
import { hashHistory } from 'react-router';
import {
  Col,
  Row,
  ControlLabel,
  OverlayTrigger,
  Popover
} from "react-bootstrap";
import uuid from 'uuid';
import { MODULE_NAME } from 'IdentifiableInformation/redux/constants';
import ProjectBatchSelectForm from "base/components/ProjectBatchSelectForm";
import { PROJECT_NOT_SELECTED, PROJECT_ALL } from "base/components/ProjectSelect";
import {
  getPersonalData,
  getStatistics,
  setActiveInfoBox,
  gatherPersonalData
} from 'IdentifiableInformation/redux/actions';
import { getDocForBatch } from 'base/redux/modules/documents';
import { getBatchForProject } from 'base/redux/modules/batches';
import { changeSetting, setModalOpen, addPersonalDataType, deletePersonalDataType } from 'Settings/redux/modules/settings.js';
import { Spinner } from 'base/components/misc.js';
import { FileInfoBox, FileListBox } from 'IdentifiableInformation/components/FileBoxes';
import { DefaultObfuscationSetting } from 'Settings/components/SettingsPannel';
import { PersonalDataTypeCustomizationModal } from 'Settings/components/PersonalDataTypeCustomizationModal';
import { setActiveRootFolder, setActiveUrl } from 'base/redux/modules/sidebar';
import { pushLogEntry } from 'ProgressNotification/actions';
const ENDPOINT = window.CONFIG.API_URLS.personalData;

import 'IdentifiableInformation/scss/FoundInformations.scss';
import 'Settings/scss/SettingsPannel.scss';

class InformationsOfStructures extends Component {
  constructor(props) {
    super(props);
    this.state = {
      project_statistics: {
        id: PROJECT_NOT_SELECTED,
        struct_name: 'project_statistics',
        name:'project',
        isLoading: false,
        statistics: null
      },
      batch_statistics: {
        id: 0,
        struct_name: 'batch_statistics',
        name:'batch',
        isLoading: false,
        statistics: null
      }
    };

    this.onProjectChange = this.onProjectChange.bind(this);
    this.onBatchChange = this.onBatchChange.bind(this);
    this.getFilePersonalInfoReport = this.getFilePersonalInfoReport.bind(this);
    this.fetchStatistics = this.fetchStatistics.bind(this);
    this.gatherBatchStatistics = this.gatherBatchStatistics.bind(this);
  }

  componentWillReceiveProps(nextProps) {
    if(
      this.props.gathering_status !== nextProps.gathering_status &&
      nextProps.gathering_status === 'completed'
    ) {
      this.props.pushLogEntry({message:'Successfully gathered personal data', level:'success'});
      const { batch_statistics } = this.state;
      this.fetchStatistics(batch_statistics);
    }
  }

  fetchStatistics(structure) {
    const { statistics } = structure;
    const { getStatistics } = this.props;

    // if not existing data
    if (!statistics || statistics.ALL === 0) {
      structure.isLoading = true;
      this.setState( this.state[structure.struct_name]: structure );
      getStatistics(structure.name,structure.id)
        .then(res => {
          const statistics =  res.data;
          structure.isLoading = false;
          structure.statistics = statistics;
          this.setState( this.state[structure.struct_name]: structure )
        })
        .catch(() => {
          structure.isLoading = false;
          this.setState( this.state[structure.struct_name]: structure )
        })
    }
  }

  gatherBatchStatistics() {
    const { batch_statistics } = this.state;
    const { gatherPersonalData } = this.props;
    gatherPersonalData(batch_statistics.id);
  }

  onProjectChange(projectId) {
    this.props.getBatchForProject(projectId, '/personal_data', projectId === PROJECT_ALL);
    var { project_statistics, batch_statistics } = this.state;
    project_statistics.id = projectId;
    batch_statistics.id = 0;
    project_statistics.statistics = null;
    this.setState({ project_statistics: project_statistics, batch_statistics: batch_statistics });
    this.fetchStatistics(project_statistics);
    this.props.setActiveInfoBox(null);
  };

  onBatchChange(batchId) {
    this.props.getDocForBatch(batchId, '/personal_data');
    var { batch_statistics } = this.state;
    batch_statistics.id = batchId;
    batch_statistics.statistics = null;
    this.setState({ batch_statistics: batch_statistics });
    this.fetchStatistics(batch_statistics)
    this.props.setActiveInfoBox(null);
  };

  getFilePersonalInfoReport(id) {
    this.props.setActiveInfoBox(id);
  }

  render() {
    const {
      batches,
      getStatistics,
      files,
      displayed_document_id,
      gathering_status,
    } = this.props;
    const { project_statistics, batch_statistics } = this.state;
    const batchId = batch_statistics.id;
    const projectId = project_statistics.id;
    const selectedBatch = batches.find(batch => {
      return batch.id === batch_statistics.id
    })

    const projectPopover = (
      <Popover id="popover-project-statistics" title="Project statistics">
        <div className="statistics-pannel">
          {project_statistics.isLoading ?
            <Spinner/> :
            <div className="statistics-wrapper">
              {
                project_statistics.statistics &&
                Object.keys(project_statistics.statistics).map((item, key) =>
                  <div key={key}>{item}: {project_statistics.statistics[item]}</div>
                )
              }
            </div>
          }
        </div>
      </Popover>
    );

    const batchPopover = (
      <Popover id="popover-batch-statistics" title="Batch statistics">
        <div className="statistics-pannel">
          {batch_statistics.isLoading ?
            <Spinner/> :
            <div className="statistics-wrapper">
            {
              batch_statistics.statistics &&
              Object.keys(batch_statistics.statistics).map((item, key) =>
                <div key={key}>{item}: {batch_statistics.statistics[item]}</div>
              )
            }
            </div>
          }
        </div>
      </Popover>
    )

    return (
      <span>
        <Col xs={12} md={12} className="margin-bot">
          <ProjectBatchSelectForm
            onProjectChange={this.onProjectChange}
            onBatchChange={this.onBatchChange}
            batches={batches}
          />
          <Row>
            <div className="bathc-project-statistics">
              <div className={`statistics-actions ${project_statistics.id !== PROJECT_NOT_SELECTED ? 'showing' : ''}`}>
              {
                project_statistics.id !== PROJECT_NOT_SELECTED &&
                  <div className="actions-pannel">
                    <OverlayTrigger
                      trigger="click"
                      placement="bottom"
                      overlay={projectPopover}
                      container={document.getElementById('statistics-popover')}
                    >
                      <div
                        className="statistics-action-button"
                      >
                        <i className="fal fa-angle-down"></i>
                        Show Project statistics
                      </div>
                    </OverlayTrigger>
                    <a
                      className="statistics-action-button"
                      href={ENDPOINT+`export_csv/?project=${projectId}`}
                    >
                      <i className="fal fa-download"></i>
                      Download data as CSV
                    </a>
                  </div>
              }
              </div>
              <div className={`statistics-actions ${batch_statistics.id > 0 ? 'showing' : ''}`}>
              {
                batch_statistics.id > 0 &&
                <span>
                  {selectedBatch.personal_data_gathered || gathering_status === 'completed' ?
                    <div className="actions-pannel">
                      <OverlayTrigger
                        trigger="click"
                        placement="bottom"
                        overlay={batchPopover}
                        container={document.getElementById('statistics-popover')}
                      >
                        <div
                          className="statistics-action-button"
                        >
                          <i className="fal fa-angle-down"></i>
                          Show Batch statistics
                        </div>
                      </OverlayTrigger>
                      <a
                        className="statistics-action-button"
                        href={ENDPOINT+`export_csv/?batch=${batchId}`}
                      >
                        <i className="fal fa-download"></i>
                        Download data as CSV
                      </a>
                      <a
                        className="statistics-action-button"
                        href={`/api/v1/batch/${batchId}/obfuscate/`}
                      >
                        <i className="fal fa-file-archive"></i>
                        Download obfuscated batch
                      </a>
                    </div> :
                    <div className="actions-pannel">
                    {gathering_status === 'loading' ?
                      <div
                        className="statistics-action-button"
                      >
                        <i className="fas fa-circle-notch fa-spin"></i>
                        Gathering personal data
                      </div>
                      :
                      <div
                        className="statistics-action-button"
                        onClick={this.gatherBatchStatistics}
                      >
                        <i className="fal fa-inbox-in"></i>
                        Gather personal data
                      </div>
                    }
                    </div>
                  }
                </span>
              }
              </div>
            </div>
          </Row>
        </Col>

        {selectedBatch && selectedBatch.personal_data_gathered || gathering_status === 'completed' ?
          <Col xs={12} md={12} className="margin-bot">
            {files.length >0 && <ControlLabel>Documents</ControlLabel>}
            <div className="files-wrapper">
              <div className="files-list-wrapper">
                {
                  files.map((item,key) => {
                    return(
                      <div key={uuid.v4()}>
                        <FileListBox
                          opened={displayed_document_id === item.id}
                          file={item}
                          getFilePersonalInfoReport={this.getFilePersonalInfoReport}
                        />
                      </div>
                    )
                  })
                }
              </div>
              {
                displayed_document_id &&
                <div className="file-statistics-wrapper">
                  <FileInfoBox/>
                </div>
              }
            </div>
          </Col> :
          (
            gathering_status == 'loading' ?
              <Spinner style={{margin: '250px auto'}}/>:
              null
          )
        }
      </span>
    )
  }
}

class FoundInformations extends Component {
  constructor(props) {
    super(props);
    this.state = {
      collapsed_setting: false
    };
    this.currentLocationPath = () => hashHistory.getCurrentLocation().pathname;
    this.handelCollapseSetting = this.handelCollapseSetting.bind(this);
    this.navTo = this.navTo.bind(this);
  }

  handelCollapseSetting() {
    this.setState({
      collapsed_setting: !this.state.collapsed_setting
    })
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
      batches,
      files,
      getStatistics,
      getPersonalData,
      getBatchForProject,
      getDocForBatch,
      changeSetting,
      setModalOpen,
      addPersonalDataType,
      deletePersonalDataType,
      setActiveInfoBox,
      displayed_document_id,
      gathering_status,
      settings,
      gatherPersonalData,
      pushLogEntry
    } = this.props;
    const {
      collapsed_setting
    } = this.state;

    return (
      <div id="statistics-popover">
        <div
          className={`settings-wrapper collapsible-wrapper ${collapsed_setting ? 'collapsed' : ''}`}
          onClick={this.handelCollapseSetting}
        >
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
          <div className="chevron-wrapper">
            {collapsed_setting ?
              <i className="fal fa-chevron-up"></i> :
              <i className="fal fa-chevron-down"></i>
            }
          </div>
          {settings.isInitialized && 
            <span>
              <DefaultObfuscationSetting
                changeSetting={changeSetting}
                defaultObfuscationTool={settings.obfuscate_type}
                obfuscationString={settings.obfuscate_string}
                highlightColor={settings.highlight_color}
                setModalOpen={setModalOpen}
                navTo={this.navTo}
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
            </span>
          }
        </div>
        <InformationsOfStructures
          getDocForBatch={getDocForBatch}
          getBatchForProject={getBatchForProject}
          batches={batches}
          getStatistics={getStatistics}
          files={files}
          setActiveInfoBox={setActiveInfoBox}
          displayed_document_id={displayed_document_id}
          gathering_status={gathering_status}
          gatherPersonalData={gatherPersonalData}
          pushLogEntry={pushLogEntry}
        />
      </div>
    )
  }
}

export default connect(
  (state) => ({
    personalData: state[ MODULE_NAME ].get('personalData'),
    batches: state[ MODULE_NAME ].get('batches'),
    files: state[ MODULE_NAME ].get('files').toJSON(),
    displayed_document_id :state[ MODULE_NAME ].get('displayed_document_id'),
    gathering_status: state[ MODULE_NAME ].get('gathering_status'),
    settings: state.settings,
  }),
  (dispatch) => bindActionCreators({
    getPersonalData,
    getBatchForProject,
    getDocForBatch,
    getStatistics,
    setActiveInfoBox,
    changeSetting,
    setModalOpen,
    addPersonalDataType,
    deletePersonalDataType,
    gatherPersonalData,
    setActiveUrl,
    setActiveRootFolder,
    pushLogEntry
  }, dispatch)
)(FoundInformations)
