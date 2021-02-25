import React, { Component, PropTypes } from 'react';
import CSV from 'comma-separated-values';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';

class CsvLink extends Component {
  constructor(props) {
    super(props);
    this._changeData = this._changeData.bind(this);
    this._getCSVString = this._getCSVString.bind(this);
    this._buildHref = this._buildHref.bind(this);
  }

  _changeData(data, changeMap) {
    return data.map(row => row.map(value => changeMap.hasOwnProperty(value) ? changeMap[value] : value))
  }

  _getCSVString(data, header) {
    const csv = new CSV(data, { header })
    return csv.encode();
  }

  _buildHref(CSVString) {
    return `data:text/csv;charset=utf-8,${encodeURI(CSVString)}`;
  }

  render() {
    let   { data } = this.props;
    const { changeMap, headers, filename } = this.props;

    data = changeMap ? this._changeData(data, changeMap) : data;

    const CSVString = this._getCSVString(data, headers),
          href = this._buildHref(CSVString),
          tooltip = <Tooltip id="tooltip">Export to csv</Tooltip>

    return (
      <OverlayTrigger placement="bottom" overlay={tooltip}>
        <a
          className="download-link fa fa-download"
          href={href}
          download={filename}>
        </a>
      </OverlayTrigger>
    )
  }
}

CsvLink.propTypes = {
  data: PropTypes.array.isRequired,
  headers: PropTypes.array.isRequired,
  changeMap: PropTypes.object,
  filename: PropTypes.string.isRequired
};

export default CsvLink;
