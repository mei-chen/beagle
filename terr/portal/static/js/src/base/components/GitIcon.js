import React, { PropTypes } from 'react';

const GITHUB_RE = /^(http[s]?:\/\/)?github.com/;
const BITBUCKET_RE = /^(http[s]?:\/\/)?bitbucket.org/;
const GITLAB_RE = /^(http[s]?:\/\/)?gitlab.com/;

const GitIcon = ({ url, className }) => {
  let icon;

  if(GITHUB_RE.test(url)) {
    icon = 'fab fa-github';
  } else if(BITBUCKET_RE.test(url)) {
    icon = 'fab fa-bitbucket';
  } else if(GITLAB_RE.test(url)) {
    icon = 'fab fa-gitlab';
  } else {
    icon = 'fa fa-question-circle';
  }

  return <i className={`${icon} ${className || ''}`} />

};

GitIcon.propTypes = {
  url: PropTypes.string.isRequired,
  className: PropTypes.string
};

export default GitIcon;
