import React, { PropTypes } from 'react';

const LabelItem = ({ title, status, isStatic, onSetStatus, onResetStatus }) => {
  let className = status === 'def' ?
    'label-item' :
    (() => {
      return status === 'pos' ?
        'label-item label-item--pos' :
        'label-item label-item--neg'
    })();

  if(isStatic) className += ' label-item--static';

  return (
    <div className={className}>
      <span className="label-item-title">
        { !title ? <i className="empty-value-icon fa fa-circle" title="Empty label" /> : title }
      </span>
      { status === 'def' ? (
        <span className="label-item-buttons">
          <i
            className="fa fa-check-circle"
            onClick={() => { onSetStatus(title, 'pos') }} />
          <i
            className="fa fa-minus-circle"
            onClick={() => { onSetStatus(title, 'neg') }} />
        </span>
      ) : (
        <span className="label-item-buttons">
          <i
            className="fa fa-times"
            onClick={() => { onResetStatus(title, status) }} />
        </span>
      )}
    </div>
  )
}

LabelItem.propTypes = {
  title: PropTypes.string, // could be null in old datasets
  status: PropTypes.oneOf(['pos', 'neg', 'def']).isRequired,
  isStatic: PropTypes.bool,
  onSetStatus: PropTypes.func,
  onResetStatus: PropTypes.func
};

export default LabelItem;
