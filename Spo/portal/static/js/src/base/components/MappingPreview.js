import React, { PropTypes } from 'react';
import { Map } from 'immutable';
import Popover from 'react-bootstrap/lib/Popover';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';

const MappingPreview = ({ mapping }) => {

  const _renderLabelsPopover = () => {
      const labels = [];
      mapping.get('pos').forEach((label, i) => labels.push(
        <span key={i} className="popover-label popover-label--pos">
          { label === '' ? <i className="empty-value-icon fa fa-circle" title="Empty label" /> : label }
        </span>
      ))
      mapping.get('neg').forEach((label, i) => labels.push(
        <span key={labels.length + i} className="popover-label popover-label--neg">
          { label === '' ? <i className="empty-value-icon fa fa-circle" title="Empty label" /> : label }
        </span>
      ))

      return (
        <Popover id="popover-labels" title="Labels mapping">
            { labels.length > 0 ? labels : 'No labels mapping...' }
        </Popover>
      )
  }

  return (
    <OverlayTrigger placement="bottom" overlay={_renderLabelsPopover()}>
      <i
        className="mapping-preview-icon fa fa-adjust" />
    </OverlayTrigger>
  )
};

MappingPreview.propTypes = {
  mapping: PropTypes.instanceOf(Map)
};

export default MappingPreview;