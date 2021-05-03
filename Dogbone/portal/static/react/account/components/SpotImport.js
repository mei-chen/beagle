import React, { Component } from 'react';
import { connect } from 'react-redux';
import { Tooltip, OverlayTrigger } from 'react-bootstrap';
import CriticalActionButton from 'common/components/CriticalActionButton';
import { postOnServer, deleteFromServer, resetOnServer, getSuggetstionsFromServer, spotAuthorize } from '../redux/modules/experiment';
require('./styles/SpotImport.scss');

class SpotImport extends Component {
  constructor(props) {
    super(props);
    this._handleChange = this._handleChange.bind(this);
    this._handleFocus = this._handleFocus.bind(this);
    this._handleBlur = this._handleBlur.bind(this);
    this._handleSubmit = this._handleSubmit.bind(this);
    this._handleDeleteClick = this._handleDeleteClick.bind(this);
    this._handleSpotAuthorize = this._handleSpotAuthorize.bind(this);
    this._renderExperiments = this._renderExperiments.bind(this);
    this._filterSuggestions = this._filterSuggestions.bind(this);
    this._renderSuggestions = this._renderSuggestions.bind(this);
    this.state = { uuid: '', showSuggestions: false };
  }

  componentWillMount() {
    const { dispatch } = this.props;
    dispatch(getSuggetstionsFromServer());
  }

  _handleFocus() {
    this.setState({ showSuggestions: true });
  }

  _handleBlur() {
    this.setState({ showSuggestions: false });
  }

  _handleChange(e) {
    this.setState({ uuid: e.target.value });
  }

  _handleSubmit(e) {
    e.preventDefault();

    const { dispatch } = this.props;
    const { uuid } = this.state;

    uuid && dispatch(postOnServer(uuid))
    uuid && this.setState({ uuid: '' })
  }

  _handleDeleteClick(uuid) {
    const { dispatch } = this.props;
    dispatch(deleteFromServer(uuid))
  }

  _handleResetClick(uuid) {
    const { dispatch } = this.props;
    dispatch(resetOnServer(uuid))
  }

  _handleSpotAuthorize() {
    spotAuthorize()
  }

  _renderExperiments(experiments, disabled) {
    return experiments.keySeq().map(uuid => {
      const exp = experiments.get(uuid);
      const disabledMessage = disabled.get(uuid);

      return (
        <div
          key={uuid}
          className={disabledMessage ? 'experiment experiment--disabled' : 'experiment'}>
          <div
            className="experiment-body">

            <span className="experiment-name">{ exp.get('name') }</span>

            <span className="experiment-uuid">
              <span className="experiment-uuid-tile">{ uuid }</span>
            </span>

            <span className="experiment-reset">
              <CriticalActionButton
                title="Reset"
                mode={exp.get('samples') > 0 ? 'active' : 'inactive'}
                action={() => { this._handleResetClick(uuid) }}/>
            </span>

            <span className="experiment-remove">
              <CriticalActionButton
                title="Delete"
                mode="active"
                action={() => { this._handleDeleteClick(uuid) }}/>
            </span>
          </div>

          { disabledMessage && (
            <div className="experiment-error">{ disabledMessage }</div>
          ) }
        </div>
      )
    })
  }

  _filterSuggestions(suggestions) {
    const { uuid } = this.state;
    return suggestions.filter(suggestion => (
      suggestion.get('uuid').toLowerCase().indexOf(uuid.toLocaleLowerCase()) !== -1 ||
      suggestion.get('name').toLowerCase().indexOf(uuid.toLocaleLowerCase()) !== -1
    ));
  }

  _renderSuggestions(suggestions) {
    return suggestions.map((suggestion, i) => (
      <div
        key={i}
        className="spot-import-suggestion"
        onMouseDown={() => this.setState({ uuid: suggestion.get('uuid') })}>
        <div className="spot-import-suggestion-name">{ suggestion.get('name') }</div>
        <div className="spot-import-suggestion-uuid">{ suggestion.get('uuid') }</div>
      </div>
    ))
  }

  render() {
    const { uuid, showSuggestions } = this.state;
    const { experiments, suggestions, disabled, errorMessage } = this.props;

    return (
      <div>
        <div className="experiments">
          { !experiments.isEmpty() && <strong className="experiments-title">Experiments</strong> }
          { this._renderExperiments(experiments, disabled) }
        </div>
        <form
          className="spot-import"
          onSubmit={this._handleSubmit}>

          <OverlayTrigger placement="left" overlay={<Tooltip id="tooltip-left">Access Spot</Tooltip>}>

            <button className="spot-import-label" onClick={() => { this._handleSpotAuthorize() }}>
              <img src="/static/img/Spot-logo-small-black.svg"/>Import from Spot:
            </button>
          </OverlayTrigger>
          <div className="spot-import-uuid">
            <input
              className="spot-import-input"
              placeholder="UUID"
              value={uuid}
              onChange={this._handleChange}
              onFocus={this._handleFocus}
              onBlur={this._handleBlur} />
            { showSuggestions && (
              <div className="spot-import-suggestions">
                { this._renderSuggestions(this._filterSuggestions(suggestions)) }
              </div>
            ) }
          </div>

          <button
            type="submit"
            className="spot-import-button">
            <i className="fa fa-plus" />
          </button>

          <OverlayTrigger placement="right" overlay={<Tooltip id="tooltip-right">Ask us about this feature</Tooltip>}>
            <button className="spot-import-info-button" onClick={() => {window.Intercom('show')}}>
                <i className="fa fa-info-circle"/>
            </button>
          </OverlayTrigger>
        </form>
        { !!errorMessage && (
          <div className="spot-import-error">{ errorMessage }</div>
        )}
      </div>
    )
  }
}

const mapStateToProps = state => {
  return {
    experiments: state.experiment.get('experiments'),
    suggestions: state.experiment.get('suggestions'),
    disabled: state.experiment.get('disabled'),
    errorMessage: state.experiment.get('errorMessage')
  }
}

export default connect(mapStateToProps)(SpotImport);
