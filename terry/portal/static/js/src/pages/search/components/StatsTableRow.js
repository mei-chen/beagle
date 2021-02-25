import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import CopyLeft from './CopyLeft';
import Risk from './Risk';
import LicenseInfo from './LicenseInfo';
import RiskChart from './RiskChart';
import { getLicenseInfoServer, ERROR, NOT_SPECIFIED } from 'search/redux/modules/terry';
import uuidV4 from 'uuid/v4';

class StatsTableRow extends Component {
  constructor(props) {
    super(props);
    this._toggleDrop = this._toggleDrop.bind(this);
    this.state = {
      isOpen: false,
      isGetting: false,
      info: null
    }
  }

  _toggleDrop(e) {
    // don't close on globe icon click
    if(e.target.classList.contains('license-link')) return false;

    const { isOpen, info } = this.state;
    const { license, getLicenseInfoServer } = this.props;

    if(!isOpen) {
      if(!info) {
        this.setState({ isGetting: true, isOpen: true })
        getLicenseInfoServer(license)
          .then(res => {
            this.setState({ isGetting: false, info: res.data })
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

  render() {
    const { index, license, amount, copyleft, commercialRisk, IPRisk, droppable } = this.props;
    const { isOpen, info, isGetting } = this.state;
    const iconClassName = isOpen ? 'fa-chevron-up' : 'fa-chevron-down';
    const src = info ? info.risks.source : null;

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
                { license === ERROR || license === NOT_SPECIFIED ? (
                  <span className="license-error">{ license }</span>
                ) : (
                  <strong className="license-name">{ license }</strong>
                ) }
                { isOpen && !!src && <a href={src} target="_blank" className="license-link fa fa-globe"></a> }
              </span>
            </div>
            <div className="table-cell">
              <span className="license-count">
                <span className="license-count-num">{ amount }</span> { amount > 1 ? 'libs' : 'lib' }
              </span>
            </div>
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
                { !!info ? (
                  <LicenseInfo
                    info={info}
                    isGetting={isGetting} />
                ) : (
                  <span className="droppable-row-error">Error while getting info</span>
                ) }
              </div>
            ) }
          </div>
        ) }

      </div>
    )
  }
}

StatsTableRow.propTypes = {
  index: PropTypes.number.isRequired,
  license: PropTypes.string.isRequired,
  amount: PropTypes.number.isRequired,
  copyleft: PropTypes.bool.isRequired,
  commercialRisk: PropTypes.number, // could be null
  IPRisk: PropTypes.number, // could be null
  droppable: PropTypes.bool,
  getLicenseInfoServer: PropTypes.func.isRequired
};

const mapStateToProps = (state, ownProps) => {
  return {};
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getLicenseInfoServer
  }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(StatsTableRow);
