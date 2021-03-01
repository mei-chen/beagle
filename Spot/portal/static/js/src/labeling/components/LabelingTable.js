import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { List } from 'immutable';
import { Table, OverlayTrigger, Popover } from 'react-bootstrap';
import LabelingControls from 'labeling/components/LabelingControls';
import LabelingSuggested from 'labeling/components/LabelingSuggested';

const ASSIGNEE = 'assignee';
const CREATOR = 'creator';

class LabelingTable extends Component {
  constructor(props) {
    super(props);
    this._renderSamples = this._renderSamples.bind(this);
    this._getRowClassName = this._getRowClassName.bind(this);
    this._renderGuessIcon = this._renderGuessIcon.bind(this);
  }

  _getRowClassName(skipped, label) {
    let rowClassName = 'labeling-row';

    if(skipped) {
      rowClassName += ' labeling-row--skipped'
    } else if(label === true) {
      rowClassName += ' labeling-row--true';
    } else if(label === false) {
      rowClassName += ' labeling-row--false';
    }

    return rowClassName;
  }

  _renderSamples(samples) {
    const { onSet, onSkip, onChange, stage, mode, allowChange } = this.props;

    return samples.map((sample, index) => (
      <tr
        key={index}
        className={this._getRowClassName(sample.get('skipped'), sample.get('label'))}>
        <td className="text-cell">{ sample.get('text') }</td>
        <td className="label-cell">
          <LabelingControls
            label={ sample.get('label') }
            skipped={ sample.get('skipped') }
            skipButton={ mode === ASSIGNEE }
            changeButton={ mode === CREATOR && allowChange }
            onSet={ label => onSet(index, label) }
            onSkip={ () => onSkip(index) }
            onChange={() => onChange(index)} />
        </td>
        { mode === ASSIGNEE && stage > 1 && (
          <td className="guess-cell">
            <LabelingSuggested suggested={sample.get('suggested_label')} />
          </td>
        ) }
      </tr>
    ));
  }

  _renderGuessIcon() {
    const popover = (
      <Popover id="spot-guess-popover" title="Spot's guess">
        Spot's prediction based on what you labeled so far.<br />
        Check it out, it's a smart pup.
      </Popover>
    );

    return (
      <OverlayTrigger placement="left" overlay={popover}>
        <img src="/static/img/pointing-dog-icon.svg" alt="Spot guess" />
      </OverlayTrigger>
    )
  }

  render() {
    const { samples, stage, mode } = this.props;

    return (
      <Table
        className="labeling-table">
        <thead>
          <tr>
            <th className="text-cell">Sample</th>
            <th className="label-cell">Label</th>
            { mode === ASSIGNEE && stage > 1 && <th className="guess-cell">{ this._renderGuessIcon() }</th> }
          </tr>
        </thead>
        <tbody>
        { this._renderSamples(samples) }
        </tbody>
      </Table>
    )
  }
}

LabelingTable.propTypes = {
  samples: PropTypes.instanceOf(List).isRequired,
  stage: PropTypes.number, // needed in ASSIGNEE mode
  mode: PropTypes.oneOf([ ASSIGNEE, CREATOR ]),
  onSet: PropTypes.func.isRequired,
  onSkip: PropTypes.func,
  onChange: PropTypes.func,
  allowChange: PropTypes.bool
};

LabelingTable.defaultProps = {
  mode: ASSIGNEE
}

const mapStateToProps = state => ({});

export default connect(mapStateToProps)(LabelingTable);
