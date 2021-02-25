import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Table, Button, ButtonGroup } from 'react-bootstrap';
import { toJS } from 'immutable';
import Reset from './Reset';
import StatusButtons from './StatusButtons';

import { setLabel, setBody, resetLabel, resetBody, toggleHeader, setDefaultLabelsStatuses } from 'create-dataset/redux/modules/create_dataset_module';

class DataTable extends Component {
    constructor(props) {
        super(props);
        this._renderData = this._renderData.bind(this);
        this._renderEllipsisRow = this._renderEllipsisRow.bind(this);
        this._handleMouseEnter = this._handleMouseEnter.bind(this);
        this._handleMouseLeave = this._handleMouseLeave.bind(this);
        this._renderHeaders = this._renderHeaders.bind(this);
        this._renderHeaderContent = this._renderHeaderContent.bind(this);
        this._handleCheckboxChange = this._handleCheckboxChange.bind(this);
        this._getRowsAmount = this._getRowsAmount.bind(this);
        this.state = {
            activeIndex: null,
        }
    }

    _renderEllipsisRow(columnsAmount) {
      const columns = [];
      const { activeIndex } = this.state;

      for(let i = 0; i < columnsAmount; i++) {
        columns.push(
          <td
              className="dataset-cell"
              key={i}
              data-index={i}
              data-active={ i === activeIndex }
              data-status={ this._getStatus(i) }
              onMouseEnter={this._handleMouseEnter}
              onMouseLeave={this._handleMouseLeave} >
              ...
          </td>
        );
      }
      return <tr>{ columns }</tr>;
    }

    _renderHeaders(columnsAmount) {
      const { activeIndex } = this.state;
      const columns = [];

      for(let i = 0; i < columnsAmount; i++) {
        columns.push(
          <td
            key={i}
            className="dataset-header"
            data-index={i}
            data-active={i === activeIndex}
            data-status={this._getStatus(i)}
            onMouseEnter={this._handleMouseEnter}
            onMouseLeave={this._handleMouseLeave}>
            { this._renderHeaderContent(i) }
          </td>
        );
      }

      return <tr>{ columns }</tr>;
    }

    _renderHeaderContent(i) {
      const { labelIndex, bodyIndex, setBody, setLabel, resetBody, resetLabel, setDefaultLabelsStatuses } = this.props;
      const { activeIndex } = this.state;

      switch(i) {
        case bodyIndex:
          return <Reset title="Body" onReset={resetBody} />
        case labelIndex:
          return <Reset title="Labels" onReset={resetLabel} />
        case activeIndex:
          return (
            <StatusButtons
              onSetBody={() => setBody(i)}
              onSetLabel={() => { setLabel(i); setDefaultLabelsStatuses() }}
            />
          )
        default:
          return null;
      }
    }

    _getStatus(i) {
      const { labelIndex, bodyIndex } = this.props;
      switch(i) {
        case bodyIndex: return "body";
        case labelIndex: return "label";
        default: return "default";
      }
    }

    _renderData(data) {
      const DISPLAY_ROWS = 3;
      const displayData = data.slice(0, DISPLAY_ROWS);
      const { activeIndex } = this.state;
      const { isHeaderRemoved } = this.props;
      const emptyColumn = <i className="empty-value-icon fa fa-circle" title="Empty label" />

      return displayData.map((row, i) => (
        <tr key={i} className={i === 0 && isHeaderRemoved ? 'dataset-row dataset-row--removed' : 'dataset-row'}>
          { row.map((column, i) => (
            <td
              className="dataset-cell"
              key={i}
              data-index={i}
              data-active={ i === activeIndex }
              data-status={ this._getStatus(i) }
              onMouseEnter={this._handleMouseEnter}
              onMouseLeave={this._handleMouseLeave} >
              { column === '' ? emptyColumn : column }
            </td>
          )) }
        </tr>
      ))
    }

    _handleMouseEnter(e) {
      const i = +e.target.getAttribute('data-index');
      const { activeIndex } = this.state;
      i !== activeIndex && this.setState({ activeIndex: i })
    }

    _handleMouseLeave(e) {
      const i = +e.relatedTarget.getAttribute('data-index');
      const { activeIndex } = this.state;
      i !== activeIndex && this.setState({ activeIndex: null })
    }

    _handleCheckboxChange(e) {
      const { toggleHeader } = this.props;
      toggleHeader(e.target.checked);
    }

    _getRowsAmount() {
      const { data, pos, neg, labelIndex, isHeaderRemoved } = this.props;
      const isMapping = pos.size > 0 || neg.size > 0;
      let amount;

      // if mapping exists count only pos/neg samples
      if(isMapping) {
        amount = data.filter(sample => {
          const label = sample.get(labelIndex);
          return pos.includes(label) || neg.includes(label)
        }).size;
      } else {
        amount = data.size;
      }

      return isHeaderRemoved ? amount - 1 : amount;
    }

    render() {
      const { data, setBody, setLabel, onSave, bodyIndex, labelIndex, isHeaderRemoved } = this.props;
      const { activeIndex } = this.state;

      if(data.size) {
        const columnsAmount = data.get(0).size;

        return (
          <div>
            {/* table */}
            <div className="dataset-table-wrapper">
              <Table className="dataset-table">
                <thead>
                  { this._renderHeaders(columnsAmount) }
                </thead>
                <tbody>
                  { this._renderData(data) }
                  { this._renderEllipsisRow(columnsAmount) }
                </tbody>
              </Table>
            </div>

            <div>
              { this._getRowsAmount() } rows
              <label className="option">
                <input
                  type="checkbox"
                  checked={isHeaderRemoved}
                  onChange={this._handleCheckboxChange} />
                Remove Header
              </label>
            </div>
          </div>
        )
      }

      return null;
  }
}

DataTable.propTypes = {
}

const mapStateToProps = (state) => {
  return {
    bodyIndex: state.createDatasetModule.get('bodyIndex'),
    labelIndex: state.createDatasetModule.get('labelIndex'),
    isHeaderRemoved: state.createDatasetModule.get('isHeaderRemoved'),
    pos: state.createDatasetModule.get('pos'),
    neg: state.createDatasetModule.get('neg')
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    setBody,
    setLabel,
    resetLabel,
    resetBody,
    toggleHeader,
    setDefaultLabelsStatuses
  }, dispatch)
}

export default connect(mapStateToProps, mapDispatchToProps)(DataTable);
