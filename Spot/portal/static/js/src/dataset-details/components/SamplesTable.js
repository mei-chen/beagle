import React, { Component, PropTypes } from 'react';
import { withRouter, browserHistory } from 'react-router';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { List } from 'immutable';
import { Table } from 'react-bootstrap';
import { FormControl, Pagination, Modal, ModalHeader, ModalBody } from 'react-bootstrap';
import Confirm from 'react-confirm-bootstrap';
import EditableText from 'base/components/EditableText';
import SelectableLabel from 'base/components/SelectableLabel';
import SortIcon from './SortIcon';

import { getFromServer as getDatasetFromServer, getSamplesFromServer, editSampleOnServer, deleteSampleFromServer, setUsed } from 'dataset-details/redux/modules/dataset_details_module';

class SamplesTable extends Component {
  constructor(props) {
    super(props);

    this._getSamples = this._getSamples.bind(this);
    this._rederSamples = this._rederSamples.bind(this);
    this._handlePaginationClick = this._handlePaginationClick.bind(this);
    this._handleSortClick = this._handleSortClick.bind(this);
    this._handleFilterChange = this._handleFilterChange.bind(this);

    this.WAIT_BEFORE_FILTER_REQUEST = 300;
    this._timeoutId = null;

    this.state = {
      sortedBy: null,
      sortingOrder: null,
      filter: ''
    }
  }

  componentWillReceiveProps(nextProps) {
    const { id, page } = this.props.params;
    if(page !== nextProps.params.page) {
      this._getSamples(nextProps.params.page)
    }
  }

  _getSamples(page) {
    const { id } = this.props.params;
    const { sortedBy, sortingOrder, filter } = this.state;
    const reqPage = page || this.props.params.page;
    return this.props.getSamplesFromServer(id, reqPage, sortedBy, sortingOrder, filter);
  }

  _rederSamples(samples) {
    const { id } = this.props.params;
    const { getDatasetFromServer, editSampleOnServer, deleteSampleFromServer, klasses } = this.props;

    return samples.map(sample => {
      const index = sample.get('index');

      return (
        <tr key={index}>
          <td className="samples-body">
            <EditableText
               text={ sample.get('text') }
               asyncSave
               onSave={ (text) => {
                 return editSampleOnServer(id, index, { text }).then(this._getSamples)
               } } />
          </td>
          { klasses && (
            <td className="samples-label">
              <SelectableLabel
                label={ sample.get('label') || '' /* could be null in old datasets */}
                options={ klasses }
                asyncSave
                onSave={ (label) => {
                  return editSampleOnServer(id, index, { label }).then(() => {
                    this._getSamples()
                    getDatasetFromServer(id) // update samples_per_klass
                  })
                } } />
            </td>
          ) }
          <td className="samples-actions">
            <Confirm
              onConfirm={() => {
                deleteSampleFromServer(id, index).then(() => {
                  this._getSamples()
                  getDatasetFromServer(id) // update samples_per_klass
                })
              }}
              title="Delete sample"
              body="Are you sure?">
              <i className="fa fa-times text-danger" />
            </Confirm>
          </td>
        </tr>
      )
    })
  }

  _handlePaginationClick(pageNum) {
    const { id } = this.props.params;
    browserHistory.push(`/datasets/${id}/page/${pageNum}`)
  }

  _handleSortClick(e, category) {
    // if click on filter input: do nothing
    if(e.target.classList.contains('filter-wrap') || e.target.classList.contains('filter')) return false;

    const { sortedBy, sortingOrder } = this.state;
    let newOrder = sortedBy === category && sortingOrder === 'asc' ? 'desc' : 'asc';
    this.setState({ sortedBy: category, sortingOrder: newOrder }, () => this._getSamples());
  }

  _handleFilterChange(e) {
    this._timeoutId && clearTimeout(this._timeoutId);

    const { id, page } = this.props.params;
    const filter = e.target.value;
    this.setState({ filter })

    // to prevent frequent server requests
    this._timeoutId = setTimeout(() => {
      // if it's first page: just get filtered results
      if(+page === 1) {
        this._getSamples()
      // else go to the first page (filtered result will be gotten in componentWillReceiveProps)
      } else {
        browserHistory.push(`/datasets/${id}/page/1`)
      }
    }, this.WAIT_BEFORE_FILTER_REQUEST)
  }

  render() {
    const { samples, count, klasses, usedInLabelingTask, setUsed } = this.props;
    const { id, page } = this.props.params;
    const { sortedBy, sortingOrder, filter } = this.state;

    return (
      <div className="samples">

          <div>
            <div className="samples-icons">
              <a href={`/api/v1/dataset/${id}/export/`} className="action-button">
                <i className="fa fa-download" />
              </a>
            </div>
            <h2>Samples</h2>
            <Table striped bordered condensed hover className="samples-table">
              <thead>
                <tr>
                  <th
                    className="samples-table-sortable"
                    onClick={(e) => { this._handleSortClick(e, 'body') } }>
                    Body
                    <div className="filter-wrap">
                      <FormControl
                        type="text"
                        className="filter"
                        value={filter}
                        onChange={this._handleFilterChange} />
                    </div>
                    <SortIcon order={ sortedBy === 'body' ? sortingOrder : null } />
                  </th>
                  { klasses && (
                    <th
                      className="samples-table-sortable"
                      onClick={(e) => { this._handleSortClick(e, 'label') } }>
                      Label
                      <SortIcon order={ sortedBy === 'label' ? sortingOrder : null } />
                    </th>
                  ) }
                  <th></th>
                </tr>
              </thead>
              { samples.size > 0 ? (
                <tbody>
                  { this._rederSamples(samples) }
                </tbody>
              ) : (
                <tbody><tr><td colSpan="3" className="text-center">No samples found</td></tr></tbody>
              ) }
            </Table>

            <div className="samples-pagination">
              <Pagination
                activePage={+page}
                items={ Math.ceil(count/10) }
                prev
                next
                first
                last
                boundaryLinks
                ellipsis
                maxButtons={5}
                onSelect={this._handlePaginationClick}
              />
            </div>

            <Modal
              show={usedInLabelingTask}
              onHide={() => setUsed(false)}
              enforceFocus={false}>
              <ModalHeader closeButton><h4>Not allowed</h4></ModalHeader>
              <ModalBody>Dataset has labeling tasks associated with it. Make sure to finish them all first.</ModalBody>
            </Modal>
          </div>

      </div>
    )
  }
}

SamplesTable.propTypes = {
  samples: PropTypes.instanceOf(List).isRequired
};

const mapStateToProps = (state) => {
  return {
    samples: state.datasetDetailsModule.get('samples'),
    count: state.datasetDetailsModule.get('count'),
    klasses: state.datasetDetailsModule.get('dataset').get('klasses'),
    usedInLabelingTask: state.datasetDetailsModule.get('usedInLabelingTask')
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getDatasetFromServer,
    getSamplesFromServer,
    editSampleOnServer,
    deleteSampleFromServer,
    setUsed
  }, dispatch)
};

export default withRouter( connect(mapStateToProps, mapDispatchToProps)(SamplesTable) );
