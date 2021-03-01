import _ from 'lodash';
var React = require('react');
var Reflux = require('reflux');
var $ = require('jquery');
var { Navigation, State } = require('react-router');
var invariant = require('invariant');

/* Components */
var Spinner = require('report/components/Spinner');
var ClauseBody = require('./InvitedView/ClauseBody');
var Pagination = require('./InvitedView/Pagination');

/* Stores & Actions */
var UserStore = require('common/stores/UserStore');
var ReportStore = require('report/stores/ReportStore');

/* Some Constants */
const AND = "AND";
const OR = "OR";
const REQUIRED_POSITIVE = "R";
const REQUIRED_NEGATIVE = "N";
const FILTER_STRING = [
  {name: "edits", type: REQUIRED_POSITIVE, order: 1, operator: OR},
  {name: "comments", type: REQUIRED_POSITIVE, order: 2, operator: OR},
  {name: "likes", type: REQUIRED_NEGATIVE, order: 3, operator: AND},
  {name: "idx", type: REQUIRED_POSITIVE, order: 4, operator: OR},
];


/* Style */
require('./styles/InvitedView.scss');


var InvitedView = React.createClass({

  mixins: [
    Reflux.connect(ReportStore, "annotations")
  ],

  propTypes: {
    idx: React.PropTypes.number.isRequired,
  },

  render() {
    var analysis = this.state.annotations.analysis || null;
    if (!analysis) {
      return <Spinner/>;
    }

    return (
      <InvitedViewBody analysis={analysis} {...this.props} />
    );
  }

});


var InvitedViewBody = React.createClass({

  mixins: [Navigation, State, Reflux.connect(UserStore, 'user')],

  propTypes: {
    analysis: React.PropTypes.object.isRequired,
    idx: React.PropTypes.number.isRequired,
  },

  getInitialState() {
    return {
      filters: [],
      sort: (s => s.idx),
      page: 0,
      totalPages: 0,
    };
  },

  componentDidMount() {
    this.setupByIdx(this.props.idx);
  },

  componentWillReceiveProps(nextProps) {
    if (this.props.idx != nextProps.idx) {
      this.setupByIdx(nextProps.idx);
    }
  },

  setupByIdx(idx) {
    var filters = FILTER_STRING;

    if (filters) {
      filters.forEach(f => {
        this.addFilter(f, idx);
      });
    }

    var page = 0;
    var sentences = this.props.analysis.sentences;

    sentences = this.filterSentences(sentences);
    sentences = this.sortSentences(sentences);

    if (idx) {
      for(var i = 0; i < sentences.length; i++) {
        if (sentences[i].idx == idx) {
          page = i;
          break;
        }
      }
    }

    this.setState({ page: page });
  },

  addFilter(filter, idx) {

    var filterFunction;
    switch(filter.name) {
      case 'idx':
        if (filter.type === REQUIRED_POSITIVE) {
          filterFunction = s => { return s.idx && s.idx == idx };
        } else if (filter.type === REQUIRED_NEGATIVE) {
          filterFunction = s => { return s.idx && s.idx != idx };
        }
        break;
      case 'comments':
        if (filter.type === REQUIRED_POSITIVE) {
          filterFunction = s => { return s.comments !== null };
        } else if (filter.type === REQUIRED_NEGATIVE) {
          filterFunction = s => { return s.comments === null };
        }
        break;
      case 'likes':
        if (filter.type === REQUIRED_POSITIVE) {
          filterFunction = s => { return s.likes };
        } else if (filter.type === REQUIRED_NEGATIVE) {
          filterFunction = s => {
            if (s.likes === null) {
              return true;
            } else if (s.likes.likes.length === 0) {
              return true;
            } else if (s.likes.likes.length > 0) {
              var likes = s.likes.likes.filter(
                l => l.email.toLowerCase() === this.state.user.email.toLowerCase()
              );
              return likes.length === 0;
            } else {
              return false;
            }
          };
        }
        break;
      case 'edits':
        if (filter.type === REQUIRED_POSITIVE) {
          filterFunction = s => { return s.accepted === false };
        } else if (filter.type === REQUIRED_NEGATIVE) {
          filterFunction = s => { return s.accepted === true };
        }
        break;
    }
    if (filterFunction) {
      var newFilters = this.state.filters;
      newFilters.push({
        name: filter.name,
        filter: filterFunction,
        order: filter.order,
        operator: filter.operator,
      });
      this.setState({
        filters : newFilters
      });
    }
  },

  filterSentences(allSentences) {
    // this is a basic filter. sentences with contents only
    var unselectedSentences = allSentences.filter(s => !!s.form);

    let { filters, annotationFilters } = this.state;

    filters = _.sortBy(filters, (f => f.order));

    let selectedSentences = [];
    let selectedUUIDs = {};

    filters.forEach(f => {
      if (f.operator === OR) {
        selectedSentences = this.orFilterSentences(
          unselectedSentences, selectedSentences, selectedUUIDs, f.filter);
      } else if (f.operator === AND) {
        selectedSentences = this.andFilterSentences(selectedSentences, selectedUUIDs, f.filter);
      }
    });

    return selectedSentences;
  },

  orFilterSentences(unselectedSentences, selectedSentences, selectedUUIDs, filter) {

    // remove sentences which have already been selected
    unselectedSentences = unselectedSentences.filter(s => selectedUUIDs[s.uuid] == null);
    // get all sentences matching filter
    let sentencesMatchingFilter = unselectedSentences.filter(filter);
    // add the new sentences to our selected UUID map
    sentencesMatchingFilter.forEach(s => selectedUUIDs[s.uuid] = true);
    // and finally add these sentences to our result set
    selectedSentences = selectedSentences.concat(sentencesMatchingFilter);

    return selectedSentences;
  },

  andFilterSentences(selectedSentences, selectedUUIDs, filter) {

    // mark all sentences unselected
    selectedSentences.forEach(s => selectedUUIDs[s.uuid] = null);
    // filter sentences
    selectedSentences = selectedSentences.filter(filter);
    // mark selected sentences selected
    selectedSentences.forEach(s => selectedUUIDs[s.uuid] = true);

    return selectedSentences;
  },

  sortSentences(sentences) {
    sentences = _.sortBy(sentences, this.state.sort);
    return sentences;
  },

  incrementPage() {
    var page = this.state.page + 1;
    this.setState({ page: page });
  },

  decrementPage() {
    var page = this.state.page - 1;
    if (page > -1) {
      this.setState({ page: page });
    }
  },

  getCurrentRouteName() {
    var routes = this.getRoutes();
    invariant(routes.length === 2, "unexpected route path");
    return routes[1].name;
  },

  updateQueryString(sentences, page) {
    if (sentences[page]) {
      let { idx, query } = this.getQuery();
      const newIdx = sentences[page].idx;
      this.replaceWith(
        this.getCurrentRouteName(),
        this.getParams(), // don't change URL params
        {...query, idx: newIdx }
      );
    }
  },

  render() {
    var sentences = this.props.analysis.sentences;

    sentences = this.filterSentences(sentences);
    sentences = this.sortSentences(sentences);

    let { user, page } = this.state;

    //prep the pagination
    var currentPage = page;
    var totalPages = sentences.length;

    var sentence = sentences[currentPage];
    this.updateQueryString(sentences, currentPage);

    var hasPagePrev = currentPage >= 1;
    var hasPageNext = currentPage < totalPages - 1;

    //if there is only one page, no need to show pagination at footer
    var pagination = (
      <Pagination
        pageCount={totalPages == 0 ? 0 : currentPage + 1}
        totalPages={totalPages}
        incrementPage={this.incrementPage}
        decrementPage={this.decrementPage}
        hasPagePrev={hasPagePrev}
        hasPageNext={hasPageNext}
      />
    );

    return (
      <div className="invited-container">
        <div className="invited-header">
          {pagination}
        </div>
        <ClauseBody
          user={user}
          sentence={sentence} />
      </div>
    );
  }

});



module.exports = InvitedView;
