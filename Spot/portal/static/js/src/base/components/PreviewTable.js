import React, { Component, PropTypes } from 'react';
import { List } from 'immutable';

class PreviewTable extends Component {
  constructor(props) {
    super(props);
    this._renderData = this._renderData.bind(this);
    this._renderEllipsisItem = this._renderEllipsisItem.bind(this);
  }

  _renderData(data) {
    return data.map((item, i) => {
      let className = 'dataset-preview-item';
      const label = item.get('label');
      if(typeof label === 'boolean') className += label === true ? ' dataset-preview-item--pos' : ' dataset-preview-item--neg';
      return <div key={i} className={className}>{ item.get('text') }</div>
    })
  }

  _renderEllipsisItem() {
    return <div className="dataset-preview-item">...</div>
  }

  render() {
    const { data } = this.props;

    return (
      <div>
        { this._renderData( data ) }
        { this._renderEllipsisItem() }
      </div>
    )
  }
}

PreviewTable.propTypes = {
  data: PropTypes.instanceOf(List).isRequired
}

export default PreviewTable;
