import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import LicenseMarker from './LicenseMarker';
import CopyLeft from './CopyLeft';
import Risk from './Risk';
import { getLicenseInfoServer, ERROR, NOT_SPECIFIED } from 'search/redux/modules/terry';
import RiskChart from './RiskChart';
import uuidV4 from 'uuid/v4';
import LicenseInfo from './LicenseInfo';

class LicensesTableRow extends Component {
  constructor(props) {
    super(props);
    this._renderLicense = this._renderLicense.bind(this);
    this._renderLicenseInfo = this._renderLicenseInfo.bind(this);
    this._toggleDrop = this._toggleDrop.bind(this);
    this._moveToStart = this._moveToStart.bind(this);
    this.state = {
      isOpen: false,
      isGetting: false,
      info: null
    }
  }

  _toggleDrop(e) {
    // don't open on .lib-link click
    if(e.target.classList.contains('lib-link')) return false;

    const { isOpen, info } = this.state;
    const { licenses, getLicenseInfoServer, pickedLicense } = this.props;

    if(!isOpen) {
      if(!info) {
        this.setState({ isGetting: true, isOpen: true })
        getLicenseInfoServer(licenses)
          .then(res => {
            this.setState({ isGetting: false, info: this._moveToStart(res.data, pickedLicense, lic => lic.name) })
          })
          .catch(err => {
            this.setState({ isGetting: false, info: null });
          })
      }
      this.setState({ isOpen: true })
    } else {
      this.setState({ isOpen: false })
    }
  }

  _renderLicense(licenses, pickedLicense) {
    if(licenses[0] === ERROR) return <LicenseMarker type="error" />
    if(licenses[0] === NOT_SPECIFIED) return <LicenseMarker type="not-specified" />
    // move picked license to the first position if there is one
    const ordered = this._moveToStart(licenses, pickedLicense, lic => lic);
    return (
      <div>
        {ordered.map((license, i) => {
          return (
            <span key={i} className={`license-highlight ${license !== pickedLicense ? 'license-highlight--secondary' : ''}`}>{license}</span>
          )
        })}
      </div>
    )
  }

  _moveToStart(array, value, getterFn) {
    if(array.length <= 1 || !value) return array;
    return [ array.find(item => getterFn(item) === value) ].concat( array.filter(item => getterFn(item) !== value) );
  }

  _renderLicenseInfo(info) {
    return info.map((item, i) => (
      <LicenseInfo
        key={i}
        title={item.name}
        info={item} />
    ))
  }

  render() {
    const { index, moduleName, library, link, version, licenses, pickedLicense, copyleft, commercialRisk, IPRisk, droppable } = this.props;
    const { isOpen, isGetting, info } = this.state;
    const iconClassName = isOpen ? 'fa-chevron-up' : 'fa-chevron-down';

    return (
      <div
        className={`droppable-row ${droppable ? 'droppable-row--active' : ''} ${isOpen ? 'droppable-row--open' : ''}`}
        onClick={droppable ? this._toggleDrop : null}>

        <div className="droppable-row-content">
          {/* chevron */}
          { droppable && <i className={`droppable-row-toggle fa ${iconClassName}`} /> }

          {/* row */}
          <div className="table-row clearfix">
            <div className="table-cell">
              <span>
                { link !== null ? (
                  <a href={link} target="_blank" className="lib-link">{ library }</a>
                ) : (
                  <span className="lib-name">{ library }</span>
                )}
                <span className="lib-version">{ version }</span>
              </span>
            </div>
            <div className="table-cell">{ moduleName }</div>
            <div className="table-cell">{ this._renderLicense(licenses, pickedLicense) }</div>
            <div className="table-cell">
              <CopyLeft value={copyleft} />
            </div>
            <div className="table-cell">
              { commercialRisk !== null && IPRisk !== null && (
                <RiskChart
                  id={uuidV4()} // needs to be globally unique
                  data={[ commercialRisk/100, commercialRisk/100, IPRisk/100, IPRisk/100 ]} />
              ) }
            </div>
          </div>
        </div>

        {/* drop */}
        { droppable && isOpen && (
          <div className="droppable-row-drop">
            { isGetting ? (
              <div className="text-center"><div className="spinner"></div></div>
            ) : (
              <div>
                { !!info ? this._renderLicenseInfo(info) : <span className="droppable-row-error">Error while getting info</span> }
              </div>
            ) }
          </div>
        ) }
      </div>
    )
  }
}

LicensesTableRow.propTypes = {
  index: PropTypes.number.isRequired,
  moduleName: PropTypes.string.isRequired,
  library: PropTypes.string.isRequired,
  link: PropTypes.string, // could be null
  version: PropTypes.string.isRequired,
  licenses: PropTypes.array.isRequired,
  pickedLicense: PropTypes.string, // could be undefined if ERROR or NOT_SPECIFIED
  copyleft: PropTypes.bool.isRequired,
  commercialRisk: PropTypes.number, // could be null
  IPRisk: PropTypes.number, // could be null
  droppable: PropTypes.bool
};

const mapStateToProps = (state, ownProps) => {
  return {};
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getLicenseInfoServer
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(LicensesTableRow);
