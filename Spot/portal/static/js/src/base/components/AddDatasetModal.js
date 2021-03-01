import React, { Component, PropTypes } from 'react';
import { Modal, ModalHeader, ModalBody, Button, Checkbox } from 'react-bootstrap';
import { List, Map, fromJS } from 'immutable';
import AllUnmarked from 'base/components/AllUnmarked';
import LabelItem from 'base/components/LabelItem';
import InfoIcon from 'base/components/InfoIcon';
import Truncate from 'base/components/Truncate';
import InCollaborationIcon from 'base/components/InCollaborationIcon';
import FilterableSelect from 'base/components/FilterableSelect';

const EVALUATE = 'evaluate';
const TRAINING = 'training';

class AddDatasetModal extends Component {
  constructor(props) {
    super(props)
    this._renderLabels = this._renderLabels.bind(this);
    this._setLabelStatus = this._setLabelStatus.bind(this);
    this._resetLabelStatus = this._resetLabelStatus.bind(this);
    this._handleAddClick = this._handleAddClick.bind(this);
    this._getLabelStatus = this._getLabelStatus.bind(this);
    this._setUnmarkedStatus = this._setUnmarkedStatus.bind(this);
    this._renderDatasetValue = this._renderDatasetValue.bind(this);
    this._getListValue = this._getListValue.bind(this);
    this._chooseDataset = this._chooseDataset.bind(this);
    this._handleCheckboxChange = this._handleCheckboxChange.bind(this);
    this.emptyLabelsStatuses = fromJS({ pos: [], neg: [] });

    this.state = {
      chosen: null,
      labelsStatuses: null,
      useAsUnsupervised: false
    }

    this.defaultSearchPlaseholder = 'Select a dataset'
  }

  _getListValue(list, value) {
    return list.filter(el => el.toLowerCase() === value.toLowerCase()).get(0);
  }

  _chooseDataset(dataset) {
    const labels = dataset.get('klasses');
    let labelsStatuses;

    if(labels === null) {
      labelsStatuses = null;
    } else {
      const trueValue = this._getListValue(labels, 'true');
      const falseValue = this._getListValue(labels, 'false');

      // if the only two labels are "true" and "false" add them to mapping
      if(labels.size === 2 && trueValue && falseValue) {
        labelsStatuses = fromJS({ pos: [trueValue], neg: [falseValue] })
      } else {
        labelsStatuses = this.emptyLabelsStatuses;
      }
    }

    this.setState({
      chosen: dataset,
      labelsStatuses
    })
  }

  _filterDatasets(datasets, query) {
    return datasets.filter(dataset => dataset.get('name').toLowerCase().indexOf(query) !== -1);
  }

  _getLabelStatus(label, pos, neg) {
    if(pos.size && pos.indexOf(label) !== -1) {
      return 'pos';
    } else if(neg.size && neg.indexOf(label) !== -1) {
      return 'neg';
    } else {
      return 'def';
    }
  }

  _renderLabels(labels) {
    const { labelsStatuses } = this.state;
    const pos = labelsStatuses.get('pos');
    const neg = labelsStatuses.get('neg');

    return labels.map((label, i) => (
      <LabelItem
        key={i}
        title={label}
        status={this._getLabelStatus(label, pos, neg)}
        onSetStatus={this._setLabelStatus}
        onResetStatus={this._resetLabelStatus}
      />
    ))
  }

  _handleCheckboxChange(e) {
    this.setState({ useAsUnsupervised: e.target.checked })
    if(e.target.checked) {
      this.setState({ labelsStatuses: null })
    } else {
      this.setState({ labelsStatuses: this.emptyLabelsStatuses })
    }
  }


  _setLabelStatus(label, status) {
    this.setState({ labelsStatuses: this.state.labelsStatuses.update(status, list => list.push(label).sort()) });
  }

  _resetLabelStatus(label, status) {
    this.setState({ labelsStatuses: this.state.labelsStatuses.update(status, list => {
      const index = list.indexOf(label);
      return list.remove(index)
    }) });
  }

  _setUnmarkedStatus(status) {
    const { labelsStatuses, chosen } = this.state;

    const unmarked = chosen.get('klasses').filter(label => !(labelsStatuses.get('pos').includes(label) || labelsStatuses.get('neg').includes(label)));
    this.setState({ labelsStatuses: labelsStatuses.update(status, list => list.concat(unmarked)) })
  }

  _handleAddClick() {
    const { chosen, labelsStatuses } = this.state;
    this.props.onAddDataset(new Map({ id: chosen.get('id'), name: chosen.get('name'), mapping: labelsStatuses }))
    this.setState({ chosen: null, query: '', labelsStatuses: this.emptyLabelsStatuses, useAsUnsupervised: false });
  }

  _renderDatasetValue(dataset) {
    return (
      <span>
        <Truncate maxLength={80}>{ dataset.get('name') }</Truncate>
        { dataset.get('is_owner') === false && <InCollaborationIcon /> }
      </span>
    )
  }

  render() {
    const { show, onHide, datasets, onAddDataset, mode } = this.props;
    const { chosen, labelsStatuses, useAsUnsupervised } = this.state;
    const isChosen = !!chosen;
    const isChosenDatasetUnsupervised = isChosen && chosen.get('klasses') === null;
    const isLessThanTwoLables = labelsStatuses && ( labelsStatuses.get('pos').size < 1 || labelsStatuses.get('neg').size < 1 );
    const canNotBeAdded = (
      !isChosen ||
      (mode === TRAINING && isChosenDatasetUnsupervised) ||
      (!isChosenDatasetUnsupervised && isLessThanTwoLables)
    )
    const infoMessagesMap = {
      "Choose dataset": !isChosen,
      "Unsupervised Datasets can't be used for training": mode === TRAINING && isChosenDatasetUnsupervised,
      "Choose at least one positive and one negative label": (!isChosenDatasetUnsupervised && isLessThanTwoLables)
    }

    return (
      <Modal
        show={show}
        onHide={onHide}
        className="add-dataset-modal">

        <ModalHeader closeButton>
          <h2>Add dataset</h2>
        </ModalHeader>

        <ModalBody>
          { datasets.size > 0 ? (
            <div>

              {/* Dropdown */}
              <FilterableSelect
                items={datasets}
                getter={dataset => dataset.get('name')}
                renderer={this._renderDatasetValue}
                onClick={this._chooseDataset}
                placeholder="Select a dataset" />

              {/* Content */}
              { isChosen && (
                <div>

                  { mode === EVALUATE && (
                    <Checkbox
                      readOnly
                      onChange={this._handleCheckboxChange}
                      checked={isChosenDatasetUnsupervised || useAsUnsupervised}
                      disabled={isChosenDatasetUnsupervised}>
                      Use as unsupervised
                    </Checkbox>
                  ) }

                  { !isChosenDatasetUnsupervised && !useAsUnsupervised && (
                    <div>
                      <hr />

                      <AllUnmarked
                        onPosClick={() => { this._setUnmarkedStatus('pos') }}
                        onNegClick={() => { this._setUnmarkedStatus('neg') }} />

                      <div key={chosen.get('id')} className="label-items-list">
                        { this._renderLabels( chosen.get('klasses') ) }
                      </div>
                    </div>
                  ) }
                </div>
              ) }

              <hr />

              {/* Add button */}
              <Button
                bsStyle="primary"
                disabled={canNotBeAdded}
                onClick={this._handleAddClick}>Add</Button>

              { canNotBeAdded && <InfoIcon messagesMap={infoMessagesMap} /> }
            </div>
          ) : (
            <div>No datasets available...</div>
          )}

        </ModalBody>
      </Modal>
    )
  }
}

AddDatasetModal.propTypes = {
  show: PropTypes.bool.isRequired,
  onHide: PropTypes.func.isRequired,
  onAddDataset: PropTypes.func.isRequired,
  datasets: PropTypes.instanceOf(List),
  mode: PropTypes.oneOf([EVALUATE, TRAINING])
}

AddDatasetModal.defaultProps = {
  mode: EVALUATE
}

export default AddDatasetModal;
