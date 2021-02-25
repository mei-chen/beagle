import React, { Component, PropTypes } from 'react';
import { browserHistory } from 'react-router';
import { Button } from 'react-bootstrap';
import { List } from 'immutable';
import GitIcon from 'base/components/GitIcon';

class RequestForm extends Component {
  constructor(props) {
    super(props);
    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleKeyUp = this.handleKeyUp.bind(this);
    this.handleFocus = this.handleFocus.bind(this);
    this.handleBlur = this.handleBlur.bind(this);
    this.handleSugClick = this.handleSugClick.bind(this);
    this.handleSugHover = this.handleSugHover.bind(this);
    this.renderSuggestions = this.renderSuggestions.bind(this);
    this._valueBackup = '';
    this.state = {
      showPlaceholder: false,
      value: props.defaultValue || '',
      filtered: List(),
      step: -1
    };
  }

  handleChange(e) {
    const { hasAccessToPrivate, suggestions } = this.props;
    const value = e.target.value;

    if(!hasAccessToPrivate) {
      this.setState({ showPlaceholder: !value });
    };

    this.setState({
      value,
      filtered: suggestions ? this.filterSuggestions(suggestions, value) : List(),
    });

    this._valueBackup = value;
  }

  handleFocus(e) {
    const { hasAccessToPrivate, suggestions } = this.props;
    const value = e.target.value;

    if(!hasAccessToPrivate && !value) return this.setState({ showPlaceholder: true });

    this.setState({
      filtered: suggestions ? this.filterSuggestions(suggestions, value) : List(),
    });
  }

  handleKeyUp(e) {
    const { hasAccessToPrivate } = this.props;
    const { step, filtered } = this.state;

    if(!hasAccessToPrivate) return false;

    // start up
    if(e.keyCode === 38 && step === -1) return this.setState({ step: filtered.size - 1, value: filtered.get(0) });

    // start down
    if(e.keyCode === 40 && step === -1) return this.setState({ step: 0, value: filtered.get(0) });

    // navigate up
    if(e.keyCode === 38) {
      return step > 0 ?
        this.setState({ step: step - 1, value: filtered.get(step - 1) }) :
        this.setState({ step: -1, value: this._valueBackup });
    }

    // navigate down
    if(e.keyCode === 40) {
      return step < filtered.size -1 ?
        this.setState({ step: step + 1, value: filtered.get(step + 1) }) :
        this.setState({ step: -1, value: this._valueBackup });
    }

    // esc
    if(e.keyCode === 27) return this.setState({ filtered: List(), value: this._valueBackup, step: -1 })
  }

  handleBlur(e) {
    const { hasAccessToPrivate } = this.props;

    if(!hasAccessToPrivate) return this.setState({ showPlaceholder: false });

    if(e.relatedTarget && e.relatedTarget.classList.contains('suggestion')) return false;
    this.setState({ step: -1, filtered: List() })
  }

  handleSubmit(e) {
    const { onSubmit } = this.props;
    const { value } = this.state;
    if(value) onSubmit(value);
    this.setState({ filtered: List() })
    e.preventDefault();
  }

  handleSugClick(suggestion) {
    this.setState({ value: suggestion, filtered: List(), step: -1 });
  }

  handleSugHover(step) {
    this.setState({ step })
  }

  filterSuggestions(suggestions, value) {
    return suggestions.filter(suggestion => suggestion.toLowerCase().indexOf( value.toLowerCase() ) !== -1)
  }

  renderSuggestions(suggestions) {
    const { step } = this.state;

    if(suggestions.size === 0) return null;

    return suggestions
      .map((suggestion, i) => (
        <div
          key={i}
          tabIndex={i}
          className={`suggestion ${i === step ? 'suggestion--active' : ''}`}
          onClick={() => { this.handleSugClick(suggestion) }}
          onMouseOver={() => { this.handleSugHover(i) }}>
          <GitIcon url={suggestion} className="suggestion-icon" />
          { suggestion }
        </div>
      ));
  }

  render() {
    const { value, filtered, showPlaceholder } = this.state;
    const { isProcessing, packageManager, suggestions, hasAccessToPrivate } = this.props;

    return (
      <div className="form">
        <h1 className="form-title">Check your project's dependencies</h1>
        <form onSubmit={this.handleSubmit}>
          <div className="form-input-container">
            <div className="form-input-wrap">
              <div className="form-icons">
                <i className="fab fa-github" />
                <i className="fab fa-bitbucket" />
                <i className="fab fa-gitlab" />
              </div>
              <input
                ref={node => this.input = node}
                className="form-input"
                placeholder="Repository URL"
                type="text"
                value={value}
                onChange={this.handleChange}
                onKeyUp={this.handleKeyUp}
                onFocus={this.handleFocus}
                onBlur={this.handleBlur} />
            </div>
            <div className="suggestions">
              { showPlaceholder ? (
                <div
                  className="suggestion suggestion--placeholder"
                  onMouseDown={() => { browserHistory.push('/settings') }} >
                  <i className="fa fa-info-square suggestion-icon" />
                  Terry can only see public repos. Give it access to your private repos in <span className="suggestion-page"><i className="fa fa-cog" /> Settings</span>
                </div>
              ) : (
                this.renderSuggestions(filtered)
              ) }
            </div>
          </div>
          <div className="form-button-wrap">
            <Button
              className="form-button"
              bsStyle="success"
              onClick={this.handleSubmit}
              disabled={isProcessing}>

              <img src="/static/img/sniffing-dog-icon.svg" />
            </Button>


            { isProcessing && (
              <div className="processing">
                <i className="fa fa-spinner fa-pulse fa-fw" />
                { !!packageManager ? (
                  <span>Working on the<strong className="processing-pm">{ packageManager }</strong>libraries...</span>
                ) : (
                  <span>Reading the repository</span>
                ) }
              </div>
            ) }
          </div>
        </form>
      </div>
    );
  }
}

RequestForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  isProcessing: PropTypes.bool.isRequired,
  packageManager: PropTypes.string,
  defaultValue: PropTypes.string,
  suggestions: PropTypes.instanceOf(List),
  hasAccessToPrivate: PropTypes.bool
};

export default RequestForm;
