import React, { Component, PropTypes } from 'react';
import { Map } from 'immutable';
import { Popover, OverlayTrigger } from 'react-bootstrap';
import MappingPreview from 'base/components/MappingPreview';
import Truncate from 'base/components/Truncate';

class DatasetItem extends Component {
  constructor(props) {
    super(props);
    this.state = {}
  }

  render() {
    const { title, index, onRemove, mapping, inaccessible, owner } = this.props;
    const popover = <Popover id="popover-no-access" placement="bottom" title="No access">Dataset owner: { owner }</Popover>;

    return (
      <div className={`dataset-item ${inaccessible ? 'dataset-item--inaccessible' : ''}`}>
        { inaccessible ? (
          <span className="dataset-item-icons">
            <OverlayTrigger placement="left" overlay={popover}>
              <i className="dataset-item-icon fa fa-ban" />
            </OverlayTrigger>
          </span>
        ) : (
          <span className="dataset-item-icons">
            { !!mapping && (
              <MappingPreview mapping={ mapping } />
            ) }
            <i
              className="dataset-item-icon fa fa-times"
              onClick={() => { onRemove(index) }} />
          </span>
        ) }
        <span
          className="dataset-item-title">
          <Truncate maxLength={35}>{ title }</Truncate>
        </span>
      </div>
    )
  }
}

DatasetItem.propTypes = {
  index: PropTypes.number,
  title: PropTypes.string.isRequired,
  mapping: PropTypes.instanceOf(Map), // could be null
  inaccessible: PropTypes.bool
}

export default DatasetItem;
