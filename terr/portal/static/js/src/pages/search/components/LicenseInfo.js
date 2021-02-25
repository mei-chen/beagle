import React, { PropTypes } from 'react';
import Score from './Score';

const LicenseInfo = ({ info, title, isGetting }) => {
  const { commercial_score, commercial_description, ip_score, ip_description } = info.risks;
  const isInfoAvailable = commercial_score !== null && ip_score !== null; // could be 0

  return (
    <div className="license-info">
      <div>
        { !!title && <span className="license-info-title">{ title }</span> }
        { isInfoAvailable ? (
          <table>
            <tbody>
              <tr>
                <td>Commercial Risk</td>
                <td>
                  <Score value={+commercial_score} />
                </td>
                <td>{ commercial_description }</td>
              </tr>
              <tr>
                <td>IP Risk</td>
                <td>
                  <Score value={+ip_score} />
                </td>
                <td>{ ip_description }</td>
              </tr>
            </tbody>
          </table>
        ) : (
          <span className="license-info-error">No info available</span>
        ) }
      </div>
    </div>
  )
}

LicenseInfo.propTypes = {
  info: PropTypes.object.isRequired,
  title: PropTypes.string // could be null
};

export default LicenseInfo;
