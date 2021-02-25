import React, { Component, PropTypes } from 'react';
import { browserHistory } from 'react-router';
import { Alert, OverlayTrigger, Tooltip } from 'react-bootstrap';
import Visualize from './Visualize';
import StatsTable from './StatsTable';
import LicensesTable from './LicensesTable';
import CsvLink from './CsvLink';
import RiskBox from './RiskBox';
import GitIcon from 'base/components/GitIcon';
import NotFound from './NotFound';
import Exceeded from './Exceeded';
import { ERROR, NOT_SPECIFIED } from 'search/redux/modules/terry';

const PRIVATE_EXCEPTIONS = ['RepositoryNotFound', 'InvalidUrl'];
const EXCEEDED_EXEPTION = 'AllowedPrivateReposCountExceeded';

class Result extends Component {
  constructor(props) {
    super(props);
    this._getDate = this._getDate.bind(this);
    this._normalizeUrl = this._normalizeUrl.bind(this);
    this._getExportFileName = this._getExportFileName.bind(this);
    this._removeColumnsFromData = this._removeColumnsFromData.bind(this);
    this._prepareData = this._prepareData.bind(this);
    this._renderException = this._renderException.bind(this);
    this._reprocessReport = this._reprocessReport.bind(this);
  }

  _getDate(date) {
    const d = date || new Date;
    return `${d.getDate()}-${d.getMonth()}-${d.getFullYear()}`
  }

  _normalizeUrl(url) {
    return url.replace(/http[s]?:\/\//gi, '');
  }

  _getExportFileName(url, title) {
    const date = this._getDate(),
          normalizedUrl = this._normalizeUrl(url);
    return `Terry_${normalizedUrl}-${title.toLowerCase()}-${date}.csv`;
  }

  _removeColumnsFromData(data, columnsToRemove) {
    if(columnsToRemove) {
      return data.map(row => {
        let newRow = Object.assign([], row);
        columnsToRemove.forEach(ignoreColumn => newRow.splice(ignoreColumn, 1));
        return newRow;
      })
    }

    return data;
  }

  _prepareData(data, columnIndex, changeFn) {
    return data.map(row => {
      let newRow = Object.assign([], row);
      newRow[columnIndex] = changeFn(newRow[columnIndex]);
      return newRow;
    });
  }

  _renderException(exception, url) {
    if(PRIVATE_EXCEPTIONS.filter(e => exception.indexOf(e) === 0).length) {
      return <NotFound url={url} />
    } else if(exception.indexOf(EXCEEDED_EXEPTION) === 0) {
      return <Exceeded />
    } else {
      return <Alert bsStyle="danger">{ exception }</Alert>
    }
  }

  _reprocessReport(uuid, url) {
    browserHistory.push({ pathname: `/dashboard/`, state: { reprocess: true, url, uuid } })
  }

  render() {
    const {
      git_url,
      exception,
      error,
      stats,
      licenses,
      stats_by_pm,
      overall_risk,
      is_private,
      repo_name,
      branch
    } = this.props.result;

    const { uuid, isPermalink } = this.props;

    const exportTooltip = <Tooltip id="pdf_report">PDF Report</Tooltip>;
    const exportChangeMap = { [ERROR]: '', [NOT_SPECIFIED]: '' };

    let licPrepared;

    if(licenses) {
      // join arrays in "Licenses" column
      licPrepared = this._prepareData(licenses, 4, value => value.join(','));

      // remove "LibraryLink" & "PickedLicense" columns
      licPrepared = this._removeColumnsFromData(licPrepared, [1, 7]);
    }


    return (
      <div className="result">
        {/* heading */}
        <div className="result-header clearfix">

          <div className="result-header-left">
            {/* git icon */}
            <div className="result-icon">
              <GitIcon url={git_url} />
              { is_private && <i className="result-lock fa fa-lock" /> }
            </div>

            <div className="result-details">
              {/* title */}
              <span className="result-title">
                <span className="result-title-overflow">{ repo_name }</span>
              </span>

              {/* branch */}
              { branch && (
                <span className="result-branch">
                  <i className="fa fa-code-branch" />
                  { branch }
                </span>
              ) }

              <div className="result-info">
                {/* url */}
                <a className="result-url" target="_blank" href={git_url}>{ git_url }</a>

                {/* report */}
                { !exception && !error && (
                  <span>
                    <span className="separator"></span>
                    <a href={`/api/v1/reports/pdf/${uuid}/`} className="result-export">PDF Report</a>
                  </span>
                ) }

                {!isPermalink && <span className="separator"></span>}

                {/* reprocess */}
                { !isPermalink && (
                  <OverlayTrigger placement="top" overlay={<Tooltip id="tooltip-top">Reprocess this repository</Tooltip>}>
                    <i
                      className="result-reprocess fa fa-repeat"
                      onClick={() => this._reprocessReport(uuid, git_url)} />
                  </OverlayTrigger>
                )}
              </div>
            </div>
          </div>

          <div className="result-header-right">
            { overall_risk !== undefined && ( // could be 0
              <RiskBox score={overall_risk}/>
            )}
          </div>
        </div>

        <div className="result-content">
        {/* errors */}
        { !!exception && this._renderException(exception, git_url) }
        { !!error && <Alert bsStyle="warning">{ error }</Alert> }

        { !exception && !error && (
          <div>
            {/* Charts */}
            <Visualize
              stats={stats}
              statsByPm={stats_by_pm}
            />

            {/* StatsTable */}
            <h3>Licenses</h3>
            <div className="table-links">
              <CsvLink
                data={stats}
                headers={['License', '#', 'Copyleft', 'Commercial Risk', 'IP Risk']}
                changeMap={exportChangeMap}
                filename={this._getExportFileName(git_url, 'Statistics')}
              />
            </div>
            <StatsTable data={stats} />

            {/* LicensesTable */}
            <h3>Libraries</h3>
            <div className="table-links">
              <CsvLink
                data={licPrepared}
                headers={['Library', 'Module', 'Version', 'License', 'Copyleft', 'Commercial Risk', 'IP Risk']}
                changeMap={exportChangeMap}
                filename={this._getExportFileName(git_url, 'Licenses')}
              />
            </div>
            <LicensesTable data={licenses} />
          </div>
          )
        }
        </div>
      </div>
    )
  }
};

Result.propTypes = {
  result: PropTypes.object.isRequired,
  uuid: PropTypes.string.isRequired,
  isPermalink: PropTypes.bool
};

export default Result;
