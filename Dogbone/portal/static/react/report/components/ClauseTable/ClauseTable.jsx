/* NPM Modules */
import _ from 'lodash';
import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux'

/* Utilities */
import backToTop from 'utils/backToTop';
import normalizeASCII from 'utils/normalizeASCII';

/* Components */
import ClauseTableHeader from './ClauseTableHeader';
import ClauseTablePagination from './ClauseTablePagination';
import ClauseTableBulkActions from './ClauseTableBulkActions';
import ClauseTableBody from './ClauseTableBody';
import {
  updateSelectedSentences
} from 'report/redux/modules/report';


/* Some Constants */
const OR = 'OR';
const AND = 'AND';
const RPP = 10;
require('utils/constants.js');

/* Style */
require('./styles/ClauseTable.scss');


const ClauseTable = React.createClass({
  propTypes: {
    analysis: React.PropTypes.object.isRequired,
    downloadCSV: React.PropTypes.func.isRequired,
  },

  contextTypes: {
    router: React.PropTypes.object.isRequired
  },

  getInitialState() {
    return {
      filters : {},
      queryFilter : null,
      annotationFilters : {},
      sort : (s => s.idx),
      page: 0,
      totalPages: 0,
      query : '',
      selectedSentences : [],
      commentMode: false,
    };
  },

  componentDidMount() {
    var queryString = this.getQuery();
    var filters = queryString;
    //apply initial query
    if (queryString.query) {
      var query = this.getQuery().query;
      this.onQueryEntry(query);
      //set the input field to match the query in the URL
      this.refs.clauseTableHeader.setState({ query: query });
      //get rid of the query filter
      delete queryString['query'];
    }
    //filter apply
    if (filters) {
      _.keys(filters).forEach(f => {
        if (filters[f] === 'r') {
          //tell the child component to toggle on the appropriate state.
          var filterState = {};
          filterState[f] = true;
          this.refs.clauseTableHeader.setState(filterState);
          //add that filter to the filter state object
          this.addFilter(f);
        } else if (filters[f] === 't') {
          //add annotation filter to tag filter state object
          this.addAnnotationFilter(f);
        }
      })
    }
  },

  getCurrentRouteName() {
    return this.context.router.location.pathname;
  },

  getParams() {
    return this.context.router.params;
  },

  getQuery() {
    return this.context.router.location.query;
  },

  // Update the URL with the current filters
  // updateDict is an object to me put as {key : value}
  // in the URL query.
  addToURL(updateDict) {
    const query = { ...this.getQuery() };
    const key = Object.keys(updateDict)[0];
    query[key] = updateDict[key];

    //No query? then don't put it in the URL dummy
    // if (!this.state.query) {
    //   delete query['query'];
    // }

    this.context.router.push({
      ... this.context.router.location,
      query
    });
  },

  // Remove the term from the URL represented by
  // the key provided
  removeFromURL(key) {
    const query = { ...this.getQuery() };
    delete query[key];

    this.context.router.push({
      ... this.context.router.location,
      query
    });
  },

  // Puts the current query into the URL
  addURLQuery() {
    this.addToURL({ 'query' : this.state.query });
  },

  filterSentences(allSentences) {
    // this is a basic filter. sentences with contents only
    const sentences = allSentences.filter(s => !!s.form);

    // this defines whether to OR or AND between filters;
    const filterOperation = OR; // AND;

    let { filters, annotationFilters } = this.state;
    // get a straight up array of just the filter functions
    filters = Object.keys(filters).map(k => filters[k]);
    annotationFilters = Object.keys(annotationFilters).map(k => annotationFilters[k]);
    // concat all the filter functions into one array
    const allFilters = filters.concat(annotationFilters);

    let filter = null; // NOT SURE WHAT FILTER IN LINE 170 IS FOR
    if (filterOperation === AND) {
      let filteredSentences = sentences;
      allFilters.forEach(filter => {
        filteredSentences = filteredSentences.filter(filter);
      });
      //query filter
      if (this.state.queryFilter) {
        filteredSentences = filteredSentences.filter(filter);
      }
      return filteredSentences;
    } else if (filterOperation === OR && (allFilters.length > 0 || !!this.state.queryFilter)) {
      let unselectedSentences = sentences;
      let selectedSentences = [];
      let selectedUUIDs = {};
      allFilters.forEach((filter) => {
        // remove sentences which have already been selected
        unselectedSentences = unselectedSentences.filter(s => selectedUUIDs[s.uuid] == null);
        // get all sentences matching filter
        let sentencesMatchingFilter = unselectedSentences.filter(filter)
        // add the new sentences to our selected UUID map
        sentencesMatchingFilter.forEach(s => selectedUUIDs[s.uuid] = true);
        // and finally add these sentences to our result set
        selectedSentences = selectedSentences.concat(sentencesMatchingFilter);
      });

      //query filter is always an 'AND'
      //see if any other filters exits, if so, use the existing 'selectedSentences' array.
      if (!!this.state.queryFilter && allFilters.length > 0) {
        selectedSentences = selectedSentences.filter(this.state.queryFilter);
      //otherwise, use the original 'sentences'
      } else if (!!this.state.queryFilter && allFilters.length <= 0) {
        selectedSentences = sentences.filter(this.state.queryFilter);
      }

      return selectedSentences;
    } else {
      return sentences;
    }
  },

  getFilteredSentences() {
    let { sentences } = this.props.analysis;
    return this.filterSentences(sentences);
  },

  sortSentences(sentences) {
    sentences = _.sortBy(sentences, this.state.sort);
    return sentences;
  },

  addAnnotationFilter(annotation) {
    //add annotation filter to URL
    var updateDict = {}
    updateDict[annotation] = 't';
    this.addToURL(updateDict);

    var filterFunction = s => {
      if (s.annotations) {
        return _.find(s.annotations, { 'label' : annotation });
      }
    };

    var newAnnotationFilters = this.state.annotationFilters;
    newAnnotationFilters[annotation] = filterFunction;

    this.setState({
      annotationFilters : newAnnotationFilters,
      page : 0
    });
  },

  addFilter(filterAlias) {
    //add regular filter to URL
    var updateDict = {}
    updateDict[filterAlias] = 'r';
    this.addToURL(updateDict);

    var filterFunction;
    switch (filterAlias) {
    case 'comments':
      filterFunction = s => {return s.comments !== null};
      if (filterAlias === 'comments') {
        this.toggleCommentModeOn();
      }
      break;

    case 'likes':
      filterFunction = s => {if (s.likes && s.likes.likes.length > 0) return true};
      break;

    case 'dislikes':
      filterFunction = s => {if (s.likes && s.likes.dislikes.length > 0) return true};
      break;

    case 'edits':
      filterFunction = s => {return s.accepted === false};
      break;

    case 'exref':
        //sometimes an array of external references does exist, it's just empty, the empty case is handled here
      filterFunction = s => {
        if (s.external_refs) {
          if (s.external_refs.length > 0) {
            return true
          } else {
            return false
          }
        } else {
          return false
        }
      };
      break;
    case 'systags':
      filterFunction = s => {
        if (s.annotations) {
            // DOESN"T MAKE SENSE i.e. window.
            //if a sentence tag has either a suggested tag or an annotation tag it's a 'System Tag'
          if (_.find(s.annotations, { 'type' : window.SUGGESTED_TAG_TYPE }) || _.find(s.annotations, { 'type' : window.ANNOTATION_TAG_TYPE })) {
            return true
          } else {
            return false
          }
        }
      };
      break;
    }
    if (filterFunction) {
      var newFilters = this.state.filters;
      newFilters[filterAlias] = filterFunction;
      this.setState({
        filters : newFilters,
        page : 0
      });
    }
  },

  toggleCommentModeOn() {
    this.setState({ commentMode: true });
  },

  toggleCommentModeOff() {
    this.setState({ commentMode: false });
  },


  onQueryEntry(query) {
    this.setState({ query: query });
    if (query.length > 0) {
      //filter on latest revision occurrence as well
      var queryFilter = s => {
        let textToSearch = s.form + (s.latestRevision ? s.latestRevision.form : '');
        return normalizeASCII(textToSearch).toLowerCase().indexOf(query.toLowerCase()) >= 0;
      };

      this.setState({
        queryFilter: queryFilter,
        page: 0
      });
    } else {
      // remove the query filter from the state.
      this.setState({
        queryFilter: null
      });
    }
  },

  removeFilter(filter) {
    if (filter === 'comments') {
      this.toggleCommentModeOff();
    }
    //remove regular filter from URL
    this.removeFromURL(filter);
    // apply the filter remove to the state.
    let newFilters = { ...this.state.filters };
    delete newFilters[filter];
    this.setState({
      filters: newFilters
    });
  },

  removeAnnotationFilter(annotation) {
    //remove annotation filter from URL
    this.removeFromURL(annotation);
    //apply the filter remove to the tag filter state
    let newAnnotationFilters = { ...this.state.annotationFilters };
    delete newAnnotationFilters[annotation];
    this.setState({
      annotationFilters: newAnnotationFilters
    });
  },

  addSort(sort, sortFunction) {
    this.setState({
      sort: sortFunction
    });
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

  setPageNum(num) {
    if (num > -1 && num < this.state.totalPages) {
      this.setState({ page: num });
    }
  },

  onSelectAllCheck(e, allDisplayedAreChecked, allFilteredAreChecked) {
    const { reportActions } = this.props;
    var sentences = [];
    var selectedSentences = this.state.selectedSentences;

    if (!allDisplayedAreChecked && !allFilteredAreChecked) {
      var start = this.state.page * RPP;
      sentences = this.getFilteredSentences();
      sentences = this.sortSentences(sentences);
      sentences = sentences.slice(start, start + RPP);
    } else if (allDisplayedAreChecked) {
      sentences = this.getFilteredSentences();
    } else if (allFilteredAreChecked) {
      selectedSentences = [];
    }
    sentences.forEach(s => {
      if (!_.includes(selectedSentences, s.idx)) {
        selectedSentences.push(s.idx);
      }
    });
    this.setState({ selectedSentences: selectedSentences });
    reportActions.updateSelectedSentences(selectedSentences);
  },

  downloadCSV() {
    var sentencesToExport;
    if (this.state.selectedSentences.length > 0) {
      sentencesToExport = this.props.analysis.sentences.filter(s => {
        return this.state.selectedSentences.indexOf(s.idx) > -1;
      });
    } else {
      sentencesToExport = this.getFilteredSentences();
    }
    this.props.downloadCSV(sentencesToExport);
  },

  onSelectClauseCheck(e, idx) {
    const { reportActions } = this.props;
    const selectedSentences = this.state.selectedSentences;
    if (e.target.checked) { //add the sentence to the list
      selectedSentences.push(idx);
    } else { //remove the sentence from the selected list
      selectedSentences.splice(selectedSentences.indexOf(idx), 1);
    }
    this.setState({ selectedSentences: selectedSentences });

    reportActions.updateSelectedSentences(selectedSentences);
  },

  getSelectedSentences() {
    const { sentences } = this.props.analysis;
    const selectedSentenceIdxs = this.state.selectedSentences;
    const selectedSentences = sentences.filter(s => selectedSentenceIdxs.indexOf(s.idx) > -1);
    return selectedSentences;
  },

  render() {
    const sentences = this.sortSentences(this.getFilteredSentences());

    let { user } = this.props;
    user = user.toJS();

    const start = this.state.page * RPP;
    const paginatedSentences = sentences.slice(start, start + RPP);

    //prep the pagination
    const currentPage = this.state.page;
    const totalPages = Math.ceil(sentences.length/10);

    const hasPagePrev = currentPage >= 1;
    const hasPageNext = currentPage < totalPages - 1;

    const bulkActions = this.state.selectedSentences.length > 0 ? (
      <ClauseTableBulkActions sentences={this.getSelectedSentences()} user={user} />
    ) : null;

    //if there is only one page, no need to show pagination at footer
    const pagination = (totalPages > 1) ? (
      <ClauseTablePagination
        pageCount={this.state.page + 1}
        totalPages={totalPages}
        incrementPage={this.incrementPage}
        decrementPage={this.decrementPage}
        hasPagePrev={hasPagePrev}
        hasPageNext={hasPageNext}
      />
    ) : null;

    var allFiltered = this.getFilteredSentences().map(sobj => {
      return sobj.idx;
    }).sort((a, b) => { return a - b; });

    return (
      <div className="clause-table">
        <ClauseTableHeader
          ref={'clauseTableHeader'}
          onQueryBlur={this.addURLQuery}
          allSelected={this.state.selectedSentences}
          allFiltered={allFiltered}
          onSelectAllCheck={this.onSelectAllCheck}
          addFilter={this.addFilter}
          addAnnotationFilter={this.addAnnotationFilter}
          onQueryEntry={this.onQueryEntry}
          removeFilter={this.removeFilter}
          removeAnnotationFilter={this.removeAnnotationFilter}
          filters={this.state.filters}
          annotationFilters={this.state.annotationFilters}
          addSort={this.addSort}
          pageCount={this.state.page + 1}
          totalPages={totalPages}
          sentenceCount={sentences.length}
          annotations={this.props.getDocumentAnnotations()}
          incrementPage={this.incrementPage}
          decrementPage={this.decrementPage}
          hasPageNext={hasPageNext}
          hasPagePrev={hasPagePrev}
          onCSVExport={this.downloadCSV}
          user={user}
        />
        {bulkActions}
        <ClauseTableBody
          commentMode={this.state.commentMode}
          user={user}
          query={this.state.query}
          sentences={paginatedSentences}
          onSelectClauseCheck={this.onSelectClauseCheck}
          allSelected={this.state.selectedSentences}/>
        <div className="clause-table-footer">
          {pagination}
          <span className="back-to-top" onClick={backToTop} >Back to Top</span>
        </div>
      </div>
    );
  }

});

const mapStateToProps = (state) => {
  return {
    user: state.user
  }
};

const mapDispatchToProps = (dispatch) => {
  return {
    reportActions: bindActionCreators({
      updateSelectedSentences
    }, dispatch)
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(ClauseTable)
