import React, { Component } from "react";
import { connect } from "react-redux";
import { bindActionCreators } from "redux";
import {
  ControlLabel
} from "react-bootstrap";
import { MODULE_NAME } from 'IdentifiableInformation/redux/constants';
import {
  getPersonalDataForDoc,
  getStatisticsForDoc,
  markPersonalDataEntry,
  initializeFileData,
} from 'IdentifiableInformation/redux/actions'
import { Spinner } from 'base/components/misc.js'

export const ENDPOINT = window.CONFIG.API_URLS.personalData;

class FileInfoBoxComponent extends Component {
  constructor(props) {
    super(props);
    this.state = {
    };
    const {
      getPersonalDataForDoc,
      getStatisticsForDoc,
      filesData,
      displayed_document_id,
      initializeFileData
    } = this.props;
    if(filesData[displayed_document_id] === undefined){
      initializeFileData(displayed_document_id);
      getStatisticsForDoc(displayed_document_id);
      getPersonalDataForDoc(displayed_document_id);
    }
  }

  componentWillReceiveProps(nextProps) {
    const {
      getPersonalDataForDoc,
      getStatisticsForDoc,
      filesData,
      displayed_document_id,
      initializeFileData
    } = this.props;
    if (displayed_document_id !== nextProps.displayed_document_id) {
      if(nextProps.filesData[nextProps.displayed_document_id] === undefined){
        initializeFileData(nextProps.displayed_document_id);
        getStatisticsForDoc(nextProps.displayed_document_id);
        getPersonalDataForDoc(nextProps.displayed_document_id);
      }
    }
  }

  handlePersonalDataSelect(entry,key) {
    const { markPersonalDataEntry, displayed_document_id } = this.props;
    markPersonalDataEntry(entry.uuid, !entry.selected, displayed_document_id, key );
  }

  render() {
    const { filesData, displayed_document_id } = this.props;
    const displaiedData = filesData[displayed_document_id];

    return (
      <div className="file-statistics">
        <ControlLabel>Downloads</ControlLabel>
        <div className="file-btns-wrapper">
          <a
            className="statistics-action-button"
            href={ENDPOINT+`export_csv/?document=${displayed_document_id}`}
          >
            <i className="fal fa-download"></i>
            Download data as CSV
          </a>
          <a
            className="statistics-action-button"
            href={`/api/v1/document/${displayed_document_id}/obfuscate`}
          >
            <i className="fal fa-code"></i>
            Download obfuscated docx
          </a>
        </div>
        <ControlLabel>Statistics</ControlLabel>
        <div className="statistics-wrapper">
        {
          displaiedData !== undefined &&
          (displaiedData.isLoadingStatistics ?
          <Spinner/> :
          (
            <span>
            {
              Object.keys(displaiedData.statistics).map((item, key) =>
                <div key={key}>{item}: {displaiedData.statistics[item]}</div>
              )
            }
            </span>
          ))
        }
        </div>
        <ControlLabel>Personal data found</ControlLabel>
        <div className="personal-data-wrapper">
        {
          displaiedData !== undefined &&
          (displaiedData.isLoadingPersonalData ?
          <Spinner/> :
          (
            <span>
            {
              displaiedData.personalData.map((item, key )=> {
                return (
                  <div key={key} className="perosnal-data-entry">
                    <div className="personal-data-select" onClick={()=>this.handlePersonalDataSelect(item,key)}>
                      {item.selected ?
                        <i className="fal fa-check-square"></i> :
                        <i className="fal fa-square"></i>
                      }
                    </div>
                    <div className="personal-data-info">
                      <div>Type: {item.type}</div>
                      <div>Text: {item.text}</div>
                      <div>Location: {item.location}</div>
                    </div>
                  </div>
                )
              })
            }
            </span>
          ))
        }
        </div>
      </div>
    )
  }
}

export const FileInfoBox = connect(
  (state) => ({
    filesData: state[MODULE_NAME].get('files_data').toJSON(),
    displayed_document_id :state[MODULE_NAME].get('displayed_document_id')
  }),
  (dispatch) => bindActionCreators({
    getStatisticsForDoc,
    getPersonalDataForDoc,
    markPersonalDataEntry,
    initializeFileData,
  }, dispatch)
)(FileInfoBoxComponent)


export class FileListBox extends Component {
  constructor(props) {
    super(props);
    this.state = {
    };

    this.onCollapseClick = this.onCollapseClick.bind(this);
  }

  onCollapseClick() {
    const { getFilePersonalInfoReport, file } = this.props;
    getFilePersonalInfoReport(file.id);
  }

  render() {
    const { file, opened } = this.props;
    const { isActive, isLoading, statistics } = this.state;
    return (
      <div
        className={`file-selector ${opened ? 'opened' : ''}`}
        onClick={this.onCollapseClick}
      >
        <h5>Document:</h5>
        <div className="title" title={file.name}>{file.name}</div>
        <div className="pointy"/>
      </div>
    )
  }
}
