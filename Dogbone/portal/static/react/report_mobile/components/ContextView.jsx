var React = require('react');
var Reflux = require('reflux');
var $ = require('jquery');
var assign = require('object-assign');
var invariant = require('invariant');
var classNames = require('classnames');
var { Navigation, State } = require('react-router');

var InvitedView = require('./InvitedView');
var Spinner = require('report/components/Spinner');
var DocumentSummary = require('./DocumentSummary');
var ListOfTerms = require('./ListOfTerms');

var ReportStore = require('report/stores/ReportStore');

require('./styles/ContextView.scss');

var ContextViewContainer = React.createClass({

  mixins: [Reflux.connect(ReportStore, "analysis"), Navigation, State],

  render() {

    var queryString = this.getQuery();
    if (queryString["idx"]) {
      return (
        <InvitedView idx={parseInt(queryString["idx"])} />
      );
    }

    var analysis = this.state.analysis;
    if (analysis.analysis === undefined) {
      return (
        <div className="beagle-context-view loading">
            <Spinner center /> Your document is being analyzed
        </div>
    );
    } else {
      // this.props contains ReactRouter params that are useful
      return <ContextView analysis={analysis} {...this.props} />;
    }
  }

});


var ContextView = React.createClass({

  mixins: [Navigation, State],

  propTypes: {
    analysis: React.PropTypes.object.isRequired,
  },

  getInitialState() {
    return {
      openSection: this.props.query.s || null,
    };
  },

  getCurrentRouteName() {
    var routes = this.getRoutes();
    invariant(routes.length === 2, "Unexpected routes list");
    if (routes[1].path === "/") {
      return "context-view";
    } else {
      return routes[1].name;
    }
  },

  /**
   * openSection
   *
   * Opens the section with the given section string
   * In the URL query string, the param `s` is for `section`
   *
   * @param {string} section a string like "liabilities", "responsibilities"...
   */
  openSection(section) {
    // if clicked on the currently open section, toggle it off
    var newOpenSection = (section !== this.state.openSection) ? section : null;

    // this object is will be the new state
    var stateChange = {
      openSection: newOpenSection
    };

    // will be invoked after successful `setState`
    var updateQueryString = () => {
      var query = this.props.query;
      var newQuery;
      if (newOpenSection) {
        newQuery = assign(query, { s: newOpenSection });
      } else {
        newQuery = assign({}, query); // clone the query obj
        delete newQuery['s']; // delete the `s` key if exists
      }
      this.replaceWith(
        this.getCurrentRouteName(),
        null, // no URL params to provide
        newQuery // new query object (the `s` param)
      );
    };
    // update state, then invoke callback to update URL query string
    this.setState(stateChange, () => {
      updateQueryString();
    });
  },

  render() {
    var analysis = this.props.analysis;

    return (
      <div className="beagle-context-view">
        <div className="center-content">
          <DocumentSummary
            analysis={analysis}
          />
          <ListOfTerms
            className="dialog-section list-of-terms"
            analysis={analysis}
            openSection={this.state.openSection}
            changeOpenSection={this.openSection}
            subsectionCollapsed={true}
          />
        </div>
      </div>
    );
  }
});


module.exports = ContextViewContainer;
