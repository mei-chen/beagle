import React from 'react';
import classNames from 'classnames';

require('./styles/Widget.scss');

const Information = React.createClass({
  render() {
    //style for the information button
    var information = {
      position: 'relative',
      float: 'right'
    };

    return (
      <div className="info-icon" style={information}
        onMouseEnter={this.props.onMouseEnter}
        onMouseLeave={this.props.onMouseLeave}>
        <i className="fa fa-info" />
      </div>
    );
  }

});


const InformationOverlay = React.createClass({

  render() {
    const parties = this.props.parties;
    const themName = parties.them.name;
    const youName = parties.you.name;

    return (
      <div className="information-overlay">
        <div className="grid">
          <div className="grid-cell">
            <div className="cell-contents">
              {themName}: Assumed Liability
            </div>
          </div>
          <div className="grid-cell">
            <div className="cell-contents">
              {youName}: Assumed Liability
            </div>
          </div>
        </div>
        <div className="grid">
          <div className="grid-cell">
            <div className="cell-contents">
              {themName}: Waived Liability
            </div>
          </div>
          <div className="grid-cell">
            <div className="cell-contents">
              {youName}: Waived Liability
            </div>
          </div>
        </div>
      </div>
    );
  }

});


const Widget = React.createClass({
  contextTypes: {
    router: React.PropTypes.object.isRequired
  },

  getInitialState() {
    return { info: false };
  },

  openContextView(sectionName) {
    this.context.router.push({
      pathname: 'context-view',
      query: { s: sectionName }
    });
  },

  openClauseView(sectionName) {
    const destination = {};
    if (sectionName) {
      destination[sectionName] = 't';
    }

    this.context.router.push({
      pathname: 'clause-table',
      query: { s: sectionName }
    });
  },

  informationShow() {
    this.setState({ info: true });
  },

  informationHide() {
    this.setState({ info: false });
  },

  render() {
    var parties = this.props.parties;

    var icon;
    if (this.props.icon) {
      icon = (
        <Information
          onMouseEnter={this.informationShow}
          onMouseLeave={this.informationHide}/>
      );
    }

    var informationOverlay = this.state.info ? <InformationOverlay parties={parties}/> : null;

    var openClauseView = () => this.openClauseView(this.props.className);
    var openContextView = () => this.openContextView(this.props.className);

    var clickTrigger;
    if (this.props.isNDA) {
      clickTrigger = openClauseView;
    } else {
      clickTrigger = openContextView;
    }

    var widgetClasses = classNames(
      'widget', this.props.className
    );

    var cornerClasses = classNames(
      'cornerTag', `${this.props.title.substring(0, 5)}Color`
    );
    return (
      <div {...this.props.attributes} className={widgetClasses} onClick={clickTrigger}>
        {icon}
        <div className={cornerClasses}>
          <span><i className="fa fa-th-list"/></span>
        </div>
        <h2>{this.props.title}</h2>
        {informationOverlay}
        {this.props.children}
      </div>
    );
  }
});


module.exports = Widget;
