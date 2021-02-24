import React, { PropTypes } from 'react';
import { Link } from 'react-router';
import Timestamp from 'react-time';
import Confirm from 'react-confirm-bootstrap';
import { List, toJS } from 'immutable';
import { BootstrapTable, TableHeaderColumn } from 'react-bootstrap-table';
import DatasetLabels from './DatasetLabels';
import InCollaborationIcon from './InCollaborationIcon';

import 'react-bootstrap-table/css/react-bootstrap-table.css';
import 'base/scss/data-table.scss';

class DataTable extends React.Component {
  constructor(props) {
    super(props);
    this._formatName = this._formatName.bind(this);
    this._formatSamples = this._formatSamples.bind(this);
    this._formatKlasses = this._formatKlasses.bind(this);
    this._formatActions = this._formatActions.bind(this);
    this._formatSplit = this._formatSplit.bind(this);
    this._renderTable = this._renderTable.bind(this);
    this._handleDeleteClick = this._handleDeleteClick.bind(this);
    this._handleRevokeClick = this._handleRevokeClick.bind(this);

    this.tableOptions = {
      sizePerPage: 10,
      hideSizePerPage: true,
      hidePageListOnlyOnePage: true
    };

    this.tableProps = {
      striped: true,
      bordered: false,
      options: this.tableOptions,
      pagination: true
    };

    this.columnsTitles = [
      'Title',
      'Created',
      '' // for last column with trash icon
    ];

    this.columnsProps = [
      {
        dataField: "name",
        isKey: true,
        dataFormat: this._formatName,
        dataSort: true,
        filter: { type: 'TextFilter', placeholder: ' ' },
      },

      {
        dataField: "created",
        dataFormat: this._formatCreated,
        dataSort: true,
        width:'130px'
      },

      {
        dataField: "id",
        dataFormat: this._formatActions,
        width: '60px'
      }
    ];

    // if it's datasets table:
    // 1) insert additional column for Sample at second position
    // 2) insert additional column for Labels at third position
    // 2) insert additional column for Split ratio at fouth position
    if(this.props.type === 'datasets') {
      this.columnsTitles.splice(1, 0, 'Samples');

      this.columnsProps.splice(1, 0, {
        dataField: "samples",
        dataFormat: this._formatSamples,
        dataSort: true,
        width: '130px'
      })

      this.columnsTitles.splice(2, 0, 'Labels');

      this.columnsProps.splice(2, 0, {
        dataField: "klasses",
        dataFormat: this._formatKlasses,
        tdStyle: { whiteSpace: 'normal' }
      })

      this.columnsTitles.splice(3, 0, 'Split ratio');

      this.columnsProps.splice(3, 0, {
        dataField: "train_percentage",
        dataFormat: this._formatSplit,
        width: '130px'
      })
    }
  }

  _handleDeleteClick(id) {
    this.props.onDelete(id)
  }

  _handleRevokeClick(id) {
    this.props.onRevoke(id)
  }

  _formatName(name, row) {
    const href = this.props.type === 'datasets' ? `/datasets/${row.id}/page/1` : `/experiments/${row.id}/edit`
    return (
      <span>
        <Link to={href}>{ name }</Link>
        { row.is_owner === false && <InCollaborationIcon /> }
      </span>
    )
  }

  _formatSamples(samples, row) {
    return samples;
  }

  _formatKlasses(klasses, row) {
    if(!klasses) return null;
    return <DatasetLabels labels={klasses} />
  }

  _formatCreated(created, row) {
    return (
      <Timestamp
        value={ created }
        locale="en"
        titleFormat="YYYY/MM/DD HH:mm"
        relative
      />
    )
  }

  _formatActions(id, row) {
    const iconClassName = row.is_owner === false ? 'fa fa-times' : 'fa fa-trash';
    const title = row.is_owner === false ? 'Revoke your invitation' : 'Delete';
    const handler = row.is_owner === false ? () => { this._handleRevokeClick(id) } : () => { this._handleDeleteClick(id) };

    return (
      <Confirm
        onConfirm={handler}
        title={title}
        body="Are you sure?">
        <i title={title} className={`delete-icon ${iconClassName}`} />
      </Confirm>
    )
  }

  _formatSplit(split) {
    return split / 100;
  }

  _renderTable(type, data) {
    const plainData = data.toJS();

    const columns = [];

    this.columnsProps.forEach((props, i) => {
      columns.push(<TableHeaderColumn key={i} {...props}>{this.columnsTitles[i]}</TableHeaderColumn>)
    })

    return (
      <BootstrapTable data={plainData} {...this.tableProps} >
        { columns }
      </BootstrapTable>
    );
  }

  render() {
    const { type, data } = this.props;
    return this._renderTable(type, data)
  }
}

DataTable.propTypes = {
    type: PropTypes.oneOf(['datasets', 'experiments']).isRequired,
    data: PropTypes.instanceOf(List).isRequired,
    onDelete: PropTypes.func.isRequired
}

export default DataTable;
