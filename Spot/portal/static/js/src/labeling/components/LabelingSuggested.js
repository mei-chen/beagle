import React, { PropTypes } from 'react';

const LabelingSuggested = ({ suggested }) => {
  if(suggested === true) {
    return <img src="/static/img/spot-true.svg" alt="True" title="True" />
  } else if(suggested === false) {
    return <img src="/static/img/spot-false.svg" alt="False" title="False" />
  }
};

LabelingSuggested.propTypes = {
  suggested: PropTypes.bool.isRequired
};

export default LabelingSuggested;
