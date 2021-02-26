import React from 'react';
import { connect } from 'react-redux';

// App
import ResponsibilitiesWidget from './ResponsibilitiesWidget';
import LiabilitiesWidget from './LiabilitiesWidget';
import TerminationsWidget from './TerminationsWidget';
import CountDetailsWidget from './CountDetailsWidget';
import ExtRefsWidget from './ExtRefsWidget';
require('./styles/WidgetPanel.scss');
import constants from '../constants';
import { sendUserEventToServer } from '../redux/modules/userEventsStatistics';

const userEvents = constants.UserEvents;

const WidgetPanelComponent = React.createClass({
  getInitialState() {
    return {}
  },

  componentDidMount() {
    const { dispatch } = this.props;
    dispatch(sendUserEventToServer(userEvents.OPEN_WIDGET_VIEW))
    this.introJsWidgetViewEvoke();
  },

  //Housekeeping: clear away the introJs object state varible when done with it.
  removeIntroJsState() {
    this.setState({ introJsObject : null });
  },

  //if there is an active introJs wizard, we must kill it if the user interacts with the contents
  // inside the widget panel.
  killIntroJsWizard() {
    if (this.state.introJsObject) {
      this.state.introJsObject.exit();
    }
  },

    //Starts the overlay intro wizard
  introJsWidgetViewEvoke() {
    //if the scripts are in the Template, then this is the user's first visit
    if (typeof window.introJs !== 'undefined' && !window.INTROJS_STEPS_WIDGET_VIEW_DONE) {
      var intro = window.introJs();
      intro.setOptions(window.INTROJS_STEPS_WIDGET_VIEW);
      intro.oncomplete(this.removeIntroJsState);
      intro.onexit(this.removeIntroJsState);
      intro.start();
      this.setState({ introJsObject : intro });
      window.INTROJS_STEPS_WIDGET_VIEW_DONE = true; //set the steps to be completed so not to show again this session.
    }
  },

  render() {
    const { annotations } = this.props;
    const analysis = annotations.get('analysis').toJS();

    let row1, row2, row3;
    if (annotations.get('agreement_type') != 'NDA') {
      row1 = (
        <div className="row">
          <ResponsibilitiesWidget analysis={analysis} />
          <LiabilitiesWidget analysis={analysis} />
        </div>
      );
      row2 = (
        <div className="row">
          <TerminationsWidget analysis={analysis} />
          <ExtRefsWidget analysis={analysis} />
        </div>
      );
    } else { // NDA
      row1 = (
        <div className="row">
          <CountDetailsWidget analysis={analysis}
                              tag="Return-Destroy-Information"
                              header="Return/Destroy Confidential Information"
                              klass="returndestroy" />
          <CountDetailsWidget analysis={analysis}
                              tag="Definition-on-Confidential-Information"
                              header="Definition on Confidential Information"
                              klass="definitionconfidential" />
        </div>
      );
      row2 = (
        <div className="row">
          <CountDetailsWidget analysis={analysis}
                              tag="Jurisdiction"
                              header="Jurisdiction"
                              klass="jurisdiction" />
          <CountDetailsWidget analysis={analysis}
                              tag="Term-of-NDA"
                              header="Term of the NDA (Experimental)"
                              klass="termofnda" />
        </div>
      );
      row3 = (
        <div className="row">
          <TerminationsWidget analysis={analysis} />
          <ExtRefsWidget analysis={analysis} />
        </div>
      );
    }
    return (
      <div className="beagle-widget-panel" id="step3" onClick={this.killIntroJsWizard}>
        {row1}
        {row2}
        {row3}
      </div>
    );
  }

});


const mapStateToProps = (state) => {
  return {
    annotations: state.report
  }
};

export default connect(mapStateToProps)(WidgetPanelComponent)
