import React, { PropTypes } from 'react';
import Progress from './Progress';

const ScoresList = ({ f1, precision, recall, className }) => {
  return (
    <ul className={ className ? `scores-list ${className}` : 'scores-list' }>
      <li className="scores-row scores-row--main">
        <span className="scores-title">F1: </span>
        <Progress value={f1} />
      </li>
      <li className="scores-row scores-row--fade">
        <span className="scores-title">Precision: </span>
        <Progress value={precision} />
      </li>
      <li className="scores-row scores-row--fade">
        <span className="scores-title">Recall: </span>
        <Progress value={recall} />
      </li>
    </ul>
  )
}

ScoresList.propTypes = {
  f1: PropTypes.number.isRequired,
  precision: PropTypes.number.isRequired,
  recall: PropTypes.number.isRequired,
  className: PropTypes.string // additional class
}

export default ScoresList;
