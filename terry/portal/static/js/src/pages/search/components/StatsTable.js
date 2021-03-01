import React, { Component, PropTypes } from 'react';
import StatsTableRow from './StatsTableRow';
import { ERROR, NOT_SPECIFIED } from 'search/redux/modules/terry';

class StatsTable extends Component {
  _renderData(data) {
    return data.map((row, i) => {
      const [ license, amount, copyleft, commercialRisk, IPRisk ] = row;
      return (
        <StatsTableRow
          key={i}
          index={i}
          license={license}
          amount={amount}
          copyleft={copyleft}
          commercialRisk={commercialRisk}
          IPRisk={IPRisk}
          droppable={license !== ERROR && license !== NOT_SPECIFIED && commercialRisk !== null && IPRisk !== null}
        />
      )
    })
  }

  render() {
    const { data } = this.props;

    return (
      <div className="table statistics-table">
        <div className="table-header green clearfix">
          <div className="table-cell"><span>License</span></div>
          <div className="table-cell"><span>#</span></div>
          <div className="table-cell"><i className="fa fa-copyright fa-fw fa-rotate-180" /></div>
          <div className="table-cell"><span>Risk</span></div>
        </div>
        <div className="table-body">
          { this._renderData(data) }
        </div>
      </div>
    )
  }
}

StatsTable.propTypes = {
  data: PropTypes.array.isRequired
};

export default StatsTable;
