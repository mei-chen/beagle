import React, { Component } from 'react';
import { List, toJS } from 'immutable';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Button, Tabs, Tab, Table } from 'react-bootstrap';
import EditableText from 'base/components/EditableText';
import SelectableLabel from 'base/components/SelectableLabel';
import Confirm from 'react-confirm-bootstrap';

import {
  getFromServer as getSamplesFromServer,
  postToServer as postUpdatesToServer,
  editSample,
  removeSample,
  TAGGED,
  INFERRED,
  mapToList
} from 'create-experiment/redux/modules/online_db_module';

class SamplesTable extends Component {
  constructor(props) {
    super(props);
    this._getSamples = this._getSamples.bind(this);
    this._renderTagged = this._renderTagged.bind(this);
  }

  componentWillMount() {
    this._getSamples()
  }

  _getSamples() {
    const { getSamplesFromServer, uuid, tag } = this.props;
    getSamplesFromServer(uuid, tag);
  }

  _renderTagged(samples) {
    const { editSample, removeSample } = this.props;

    return samples.map((sample, i) => {
      const index = sample.get('index');

      return (
        <tr key={i}>
          <td>
            <EditableText
              text={ sample.get('text') }
              onSave={ text => editSample(TAGGED, index, { index, text }) } />
          </td>
          <td>
            <SelectableLabel
              label={ sample.get('label').toString() }
              options={ List([ 'true', 'false' ]) }
              onSave={ label => editSample(TAGGED, index, { index, label: label === 'true' /* string to boolean */ }) } />
          </td>
          <td>
            <Confirm
              onConfirm={() => removeSample(TAGGED, index)}
              title="Delete sample"
              body="Are you sure?">
              <i className="fa fa-times text-danger" />
            </Confirm>
          </td>
        </tr>
      )
    });
  }

  _renderInferred(samples) {
    const { editSample, removeSample } = this.props;

    return samples.map((sample, i) => {
      const index = sample.get('index');

      return (
        <tr key={i}>
          <td>
            <EditableText
              text={ sample.get('text') }
              onSave={ text => editSample(INFERRED, index, { index, text }) } />
          </td>
          {/* inferred label is always false */}
          <td>
            false
          </td>
          <td>
            <Confirm
              onConfirm={() => removeSample(INFERRED, index)}
              title="Delete sample"
              body="Are you sure?">
              <i className="fa fa-times text-danger" />
            </Confirm>
          </td>
        </tr>
      )
    });
  }

  render() {
    const { tagged, inferred, add, edit, remove, postUpdatesToServer, uuid, tag } = this.props;
    const upToDate = add.size === 0 && edit.size === 0 && remove.size === 0;

    return (
      <div className="online-db">
        <Tabs defaultActiveKey={1} id="online-db-samples">
          {/* TAGGED */}
          <Tab eventKey={1} title="Tagged">
            { tagged.size > 0 ? (
              <Table className="online-db-samples" striped>
                <thead>
                  <tr>
                    <th>Body</th>
                    <th>Label</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  { this._renderTagged(tagged) }
                </tbody>
              </Table>
            ) : (
              <div className="online-db-placeholder">No data found...</div>
            )}
          </Tab>

          {/* INFERRED */}
          <Tab eventKey={2} title="Inferred">
            { inferred.size > 0 ? (
              <Table className="online-db-samples" striped>
                <thead>
                  <tr>
                    <th>Body</th>
                    <th>Label</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  { this._renderInferred(inferred) }
                </tbody>
              </Table>
            ) : (
              <div className="online-db-placeholder">No data found...</div>
            ) }
          </Tab>

        </Tabs>

        {/* BUTTON */}
        {/* show when there are samples OR all samples removed by user */}
        {/* disable when data is up-to-date */}
        { ((tagged.size > 0 || inferred.size > 0) || remove.size > 0) && (
          <Button
            onClick={() => postUpdatesToServer(uuid, {
              tag,
              add: add.toJS(),
              edit: edit.toJS(),
              remove: remove.toJS()
            })}
            disabled={upToDate}
            bsStyle="primary">Save changes</Button>
        ) }
      </div>
    )
  }
}

const mapStateToProps = state => {
  return {
    uuid: state.createExperimentModule.get('uuid'),
    tagged: mapToList( state.onlineDbModule.get('tagged') ),
    inferred: mapToList( state.onlineDbModule.get('inferred') ),
    add: mapToList( state.onlineDbModule.getIn(['updates', 'add']) ),
    edit: mapToList( state.onlineDbModule.getIn(['updates', 'edit']) ),
    remove: state.onlineDbModule.getIn(['updates', 'remove'])
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getSamplesFromServer,
    postUpdatesToServer,
    editSample,
    removeSample
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(SamplesTable);
