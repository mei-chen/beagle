import React, { Component, PropTypes } from 'react';
import Timestamp from 'react-time';
import GitIcon from 'base/components/GitIcon';
import ShortUrl from 'base/components/ShortUrl';

class Recent extends Component {
  constructor() {
    super()
  }

  render() {
    const { reports, onClick } = this.props;

    return (
      <div className="recent-list">
        { reports.map(report => (
           <div
              key={report.uuid}
              className="recent"
              onClick={ () => { onClick(report.uuid)} }>
              <Timestamp
                value={report.created_at}
                className="recent-date"
                locale="en"
                titleFormat="YYYY/MM/DD HH:mm"
                relative />
              <div className="recent-body clearfix">
                <GitIcon
                  className="recent-icon"
                  url={report.url}/>
                <ShortUrl
                  url={report.url}
                  className="recent-url" />
              </div>
          </div>
        )) }
      </div>
    )
  }
}

Recent.propTypes = {
  reports: PropTypes.array.isRequired,
  onClick: PropTypes.func.isRequired
};

export default Recent;
