import React from 'react';

import './styles/Tag.scss';

const Tag = React.createClass({
  render() {
    const { learners, suggested, name, onTokenApprove, onTokenRemove } = this.props;

    let colorCode;
    if (learners) {
      learners.map(learner => {
        if (learner.name.toLowerCase() === name)
        {
          colorCode=learner.color_code;
        }
      })
    }

    return (
      <div className="manual-tag" style={{ backgroundColor: colorCode }}>
        {name}
        {suggested && (<i className="fa fa-check" aria-hidden="true" onClick={() => {onTokenApprove(name)}}/>)}
        <i className="fa fa-times" aria-hidden="true" onClick={() => {onTokenRemove(name)}}/>
      </div>
    )
  }
})

export default Tag