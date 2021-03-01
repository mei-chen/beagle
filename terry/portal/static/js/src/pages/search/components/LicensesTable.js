import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import LicensesTableRow from './LicensesTableRow';
import SortIcon from './SortIcon';
import { sortLicenses, ERROR, NOT_SPECIFIED } from 'search/redux/modules/terry';

class LicensesTable extends Component {
  constructor(props) {
    super(props);
    this._handleSortClick = this._handleSortClick.bind(this);
    this._renderData = this._renderData.bind(this);
    this.state = {
      sortedColumnIndex: null,
      sortedDirection: null
    }
  }

  _handleSortClick(columnIndex) {
    const { sortedColumnIndex, sortedDirection } = this.state;
    const { sortLicenses } = this.props;

    if(sortedColumnIndex !== columnIndex) {
      this.setState({ sortedColumnIndex: columnIndex, sortedDirection: 'asc' }, () => {
        sortLicenses(columnIndex, this.state.sortedDirection);
      })
    } else {
      const direction = sortedDirection === 'asc' ? 'desc' : 'asc';
      this.setState({ sortedColumnIndex: columnIndex, sortedDirection: direction }, () => {
        sortLicenses(columnIndex, this.state.sortedDirection);
      })
    }
  }

  _renderData(data) {
    return data.map((row, i) => {
      const [ library, link, moduleName, version, licenses, copyleft, commercialRisk, IPRisk, pickedLicense ] = row;
      return (
        <LicensesTableRow
          key={i}
          index={i}
          moduleName={moduleName}
          library={library}
          link={link}
          version={version}
          licenses={licenses}
          pickedLicense={pickedLicense}
          copyleft={copyleft}
          commercialRisk={commercialRisk}
          IPRisk={IPRisk}
          droppable={licenses[0] !== ERROR && licenses[0] !== NOT_SPECIFIED && commercialRisk !== null && IPRisk !== null}
        />
      )
    })
  }

  render() {
    const { data } = this.props;
    const { sortedColumnIndex, sortedDirection } = this.state;
    const sortIconProps = { sortedColumnIndex, sortedDirection, onClick: this._handleSortClick }

    return (
      <div className="table licenses-table">
        <div className="table-header blue clearfix">
          <div className="table-cell"><span>Library<SortIcon columnIndex={0} {...sortIconProps} /></span></div>
          <div className="table-cell"><span>Module<SortIcon columnIndex={2} {...sortIconProps} /></span></div>
          <div className="table-cell"><span>License<SortIcon columnIndex={4} {...sortIconProps} /></span></div>
          <div className="table-cell"><i className="fa fa-copyright fa-fw fa-rotate-180" /></div>
          <div className="table-cell">Risk</div>
        </div>
        <div className="table-body">
          { this._renderData(data) }
        </div>
      </div>
    )
  }
}

LicensesTable.propTypes = {
  data: PropTypes.array.isRequired
};

const mapStateToProps = (state, ownProps) => {
  return {};
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    sortLicenses
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(LicensesTable);
