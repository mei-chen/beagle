import React, { Component } from 'react';
import { withRouter } from 'react-router';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { toJS } from 'immutable';
import { Table } from 'react-bootstrap';
import Timestamp from 'react-time';
import DatasetLabels from 'base/components/DatasetLabels';
import EditableText from 'base/components/EditableText';
import Slider from 'base/components/Slider';

import { getFromServer, editOnServer } from 'dataset-details/redux/modules/dataset_details_module';

class DatasetDetails extends Component {
  constructor(props) {
    super(props);
    this._handleEditDetails = this._handleEditDetails.bind(this);
    this._handleEditSplit = this._handleEditSplit.bind(this);
    this._toggleSplitDrop = this._toggleSplitDrop.bind(this);
    this._handleSplitChange = this._handleSplitChange.bind(this);

    const { dataset } = props;

    this.state = {
      split: dataset.get('train_percentage') || 80,
      isSplitOpen: false,
      isSplitSaving: false
    }
  }

  _handleEditDetails(data) {
    const { id } = this.props.params;
    const { editOnServer } = this.props;
    return editOnServer(id, data);
  }

  _handleEditSplit(data) {
    this.setState({ isSplitSaving: true })
    this._handleEditDetails(data)
      .then(() => this.setState({ isSplitSaving: false, isSplitOpen: false }))
  }

  _toggleSplitDrop() {
    const { isSplitOpen } = this.state;
    this.setState({ isSplitOpen: !isSplitOpen });
  }

  _handleSplitChange(value) {
    this.setState({ split: value });
  }

  render() {
    const { dataset } = this.props;
    const { isSplitOpen, isSplitSaving, split } = this.state;

    return (
      <div className="dataset-details">
        { dataset.size > 0 && (
          <div className="card">
            <Table className="card-table">
              <tbody>
                <tr>
                  <td>Name</td>
                  <td>
                    <EditableText
                      text={ dataset.get('name') }
                      onSave={ name => this._handleEditDetails({ name }) }
                      asyncSave
                    />
                  </td>
                </tr>
                { dataset.get('description') && (
                  <tr>
                    <td>Description</td>
                    <td>
                      <EditableText
                        text={ dataset.get('description') }
                        onSave={ description => this._handleEditDetails({ description }) }
                        inputType="textarea"
                        asyncSave
                      />
                    </td>
                  </tr>
                ) }
                <tr>
                  <td>Created</td>
                  <td>
                    <Timestamp
                      value={ dataset.get('created') }
                      locale="en"
                      format="YYYY/MM/DD HH:mm"
                    />
                  </td>
                </tr>
                <tr>
                  <td>Size</td>
                  <td>{ `${dataset.get('samples')} rows` }</td>
                </tr>
                <tr>
                  <td>Split Ratio</td>
                  <td>
                    <div className="editable-split">
                      { isSplitOpen ? (
                        <div>
                          <Slider
                            sliderPercentage={split}
                            handleSliderChange={this._handleSplitChange} />
                          { !isSplitSaving ? (
                            <span>
                              <i
                                className="editable-split-icon fa fa-check text-success"
                                onClick={() => this._handleEditSplit({ train_percentage: split }) } />
                              <i
                                className="editable-split-icon fa fa-times"
                                onClick={this._toggleSplitDrop} />
                            </span>
                          ) : (
                            <i className="fa fa-spinner fa-spin" />
                          ) }
                        </div>
                      ) : (
                        <div>
                          <span>{`${dataset.get('train_percentage')} / ${100 - dataset.get('train_percentage')}`}</span>
                          <i
                            className="editable-split-icon editable-split-icon--edit fa fa-edit"
                            onClick={this._toggleSplitDrop} />
                        </div>
                      ) }
                    </div>
                  </td>
                </tr>
                { dataset.get('klasses') && (
                  <tr>
                    <td>Classes</td>
                    <td>
                      <DatasetLabels
                        labels={ dataset.get('klasses').toJS() }
                        modal={true}
                        saplesPerLabel={dataset.get('samples_per_klass').toJS()} />
                      <span className="klass-total">Total: { dataset.get('klasses').size }</span>
                    </td>
                  </tr>
                ) }
              </tbody>
            </Table>
          </div>
        )}
      </div>
    )
  }
}

const mapStateToProps = (state) => {
  return {
    dataset: state.datasetDetailsModule.get('dataset'),
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getFromServer,
    editOnServer
  }, dispatch)
}

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(DatasetDetails));
