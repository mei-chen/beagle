/* NPM Modules */
import _ from 'lodash';
var React = require('react');
var Reflux = require('reflux');
var classNames = require('classnames');

/* Bootstrap Requirements */
//var Input = require('react-bootstrap/lib/Input');
var Tooltip = require('react-bootstrap/lib/Tooltip');
var OverlayTrigger = require('react-bootstrap/lib/OverlayTrigger');

/* Components */
var ClauseTablePagination = require('./ClauseTablePagination');
var TagFilterPopover = require('./TagFilterPopover');

/* Style */
require('./styles/ClauseTableHeader.scss');


var ClauseTableHeader = React.createClass({

  propTypes: {
    onQueryBlur: React.PropTypes.array.isRequired,
    allSelected: React.PropTypes.array.isRequired,
    onSelectAllCheck: React.PropTypes.func.isRequired,
    addFilter: React.PropTypes.func.isRequired,
    addAnnotationFilter : React.PropTypes.func.isRequired,
    removeFilter: React.PropTypes.func.isRequired,
    removeAnnotationFilter : React.PropTypes.func.isRequired,
    addSort: React.PropTypes.func.isRequired,
    sentenceCount: React.PropTypes.number.isRequired,
    onQueryEntry: React.PropTypes.func.isRequired,
    pageCount : React.PropTypes.number.isRequired,
    totalPages : React.PropTypes.number.isRequired,
    incrementPage : React.PropTypes.func.isRequired,
    decrementPage : React.PropTypes.func.isRequired,
    onCSVExport : React.PropTypes.func.isRequired,
    hasPagePrev : React.PropTypes.bool.isRequired,
    hasPageNext : React.PropTypes.bool.isRequired,
    annotations : React.PropTypes.array.isRequired,
    filters : React.PropTypes.object.isRequired,
    annotationFilters : React.PropTypes.object.isRequired,
  },

  getInitialState() {
    return {
      query : '',
      inputFocus : false,
      comments : false,
      likes : false,
      edits : false,
      resp : false,
      liab : false,
      term : false,
      exref : false,
      systags : false,
      filterSelectMode : false,
      sortSelectMode : false,
      sortOptions : [
        {name : 'origin', display : 'Document Order', isCurrent : true},
        {name : 'recent', display : 'Last Activity', isCurrent : false}
      ],
    };
  },

  /*
   * buildAnnotationFilters()
   *
   * Iterate through the annotations prop and build an object
   * list to be displayed in the popover
   */
  buildAnnotationFilters() {
    //init tag filters
    var annotationFilters = [];
    var activeAnnotationFilterKeys = Object.keys(this.props.annotationFilters);
    //User added tags
    this.props.annotations.map(a => {

      var obj = {};
      obj['name'] = a.label;
      obj['display'] = a.label;
      obj['isCurrent'] = activeAnnotationFilterKeys.indexOf(a.label) > -1 ? true : false; //current if in the filters list exists the name of the filter option.
      annotationFilters.push(obj);
    });
    //provide user feedback of toggled filters
    // AnnotationFilters.forEach((f, i) => {
    //   if (f.name in this.props.filters || f.name in this.props.AnnotationFilters) {
    //     f.isCurrent = true;
    //     AnnotationFilters[i] = f;
    //   }
    // });
    return annotationFilters;
  },

  /*
   * updateSorts(selection)
   *
   * Alter the sortsOptions state object to have the
   * selected option from the popover's isCurrent
   * attribute be toggled to 'true'.
   */
  updateSorts(selection) {
    //sort options
    var sortOptions = [];
    this.state.sortOptions.forEach((f, idx) => {
      if (f.name === selection.name && f.isCurrent === false) {
        f.isCurrent = true;
        sortOptions.push(f);
        this.addSort(f.name);
      } else {
        f.isCurrent = false;
        sortOptions.push(f);
      }
    });
    this.setState({sortOptions : sortOptions});
  },

  /*
   * updateFilters(selection)
   *
   */
  updateFilters(selection) {
    //Annotation filters
    var annotationFilters = [];
    _.forEach(this.buildAnnotationFilters(), (f, idx) => {
      if (f.name === selection.name && f.isCurrent === false) {
        f.isCurrent = true;
        annotationFilters.push(f.label);
        this.addAnnotationFilter(f.name);

      } else if (f.name === selection.name && f.isCurrent === true) {
        f.isCurrent = false;
        annotationFilters.push(f.label);
        //if it has an icon, it's a regular filter
        this.removeAnnotationFilter(f.name);
      } else {
        annotationFilters.push(f);
      }
    });
    this.setState({
      userInputFilters : annotationFilters,
    });
  },

  /* tagsFilterMode()
   *
   * called from the tag
   * filter carrot onClick. Toggles the
   * filterSelectMode on, which displays the
   * popover.
   */
  tagsFilterMode() {
    this.setState({
      filterSelectMode : true,
    });
  },

  /* disableFilterSelectMode()
   *
   * Toggles off the filter select
   * mode, effectively closing the
   * filter selection popover
   */
  disableFilterSelectMode() {
    this.setState({
      filterSelectMode : false
    });
  },

  /* sortSelectMode()
   *
   * called from the sort button onClick.
   * Toggles the filterSelectMode on,
   * which displays the popover.
   */
  sortSelectMode() {
    this.setState({
      sortSelectMode : true,
      options : this.state.sortOptions,
    });
  },

  /* disableSortSelectMode()
   *
   * Toggles off the sort select
   * mode, effectively closing the
   * sort selection popover
   */
  disableSortSelectMode() {
    this.setState({
      sortSelectMode : false
    });
  },

  /* onSelectFilter(selection)
   *
   * Callback from an option being
   * selected from the filter popover.
   * calls the function to apply the
   * filter to the list, as well as
   * update the filter options state object
   */
  onSelectFilter(selection) {
    this.updateFilters(selection);
  },

  /* onSelectSort(selection)
   *
   * Callback from an option being
   * selected from the sort popover.
   * calls the function to apply the
   * sort to the list, as well as
   * update the sort options state object
   */
  onSelectSort(selection) {
    this.updateSorts(selection);
  },

  /* addSort(sort)
   *
   * given the string name of a sort type
   * this function returns the appropriate
   * function to pass into a _.sortBy
   */
  addSort(sort) {
    var sortFunction;
    switch(sort) {
      case 'origin':
        sortFunction = s => {return (c => c.idx)}
      break;
      //TODO: Sort based on last activity timestamp
      case 'recent':
        sortFunction = s => {return (c => c.idx)}
      break;
    }
    if(sortFunction) {
      this.props.addSort(sort, sortFunction);
    }
  },


  /* addTagFilter(tag)
   *
   * given the string name of a tag filter
   * this function returns the appropriate
   * function to pass into a _.filter
   */
  addAnnotationFilter(annotation) {
    this.props.addAnnotationFilter(annotation);
  },

  /*
   * removeAnnotationFilter(tag)
   *
   * calls the removeAnnotationFilter function
   * passed in as a prop to the component
   */
  removeAnnotationFilter(tag) {
    this.props.removeAnnotationFilter(tag);
  },

  /* addFilter(filter)
   *
   * given the string name of a filter type
   * this function returns the appropriate
   * function to pass into a _.filter
   */
  addFilter(filterAlias) {
    this.props.addFilter(filterAlias);
  },

  /*
   * removeFilter(filter)
   *
   * calls the removeFilter function
   * passed in as a prop to the component
   */
  removeFilter(filter) {
    this.props.removeFilter(filter);
  },

  /*
   * onQueryKeyDown(e)
   *
   * Updates the query string state variable
   * called on keydown in the input field then
   * applies a query filter to the sentence list
   */
  onQueryKeyDown(e) {
    var query = e.target.value;
    this.props.onQueryEntry(query);
    this.setState({query : query});
  },

  onSelectAllCheck(e) {
    this.props.onSelectAllCheck(e);
  },

  onFilterButtonClick(name) {
    var mode = !this.state[name];
    if (mode) {
      this.addFilter(name);
    } else {
      this.removeFilter(name);
    }
    this.setState({ [name]: mode });
  },

  setInputFocus() {
    this.setState({ inputFocus : true });
  },

  removeInputFocus() {
    this.setState({ inputFocus : false });
    this.props.onQueryBlur();
  },

  getCurrentRouteName() {
    var routes = this.getRoutes();
    invariant(routes.length === 2, "unexpected route path");
    return routes[1].name;
  },

  isAnnotationFilters() {
    var isAnnotationFilters = false
    this.buildAnnotationFilters().forEach(f => {
      if (f.isCurrent === true) {
        isAnnotationFilters = true;
      }
    });
    return isAnnotationFilters
  },

  generatePagination() {
    var pagination;
    if (this.props.totalPages > 1){
      pagination =
      (<ClauseTablePagination
        pageCount={this.props.pageCount}
        totalPages={this.props.totalPages}
        incrementPage={this.props.incrementPage}
        decrementPage={this.props.decrementPage}
        hasPagePrev={this.props.hasPagePrev}
        hasPageNext={this.props.hasPageNext}/>)
    }
    return pagination
  },

  render() {
    var tagStyle = classNames(
      'filter-option',
      { 'enabled' : this.isAnnotationFilters() }
    );

    var editStyle = classNames(
      'filter-option',
      { 'enabled' : this.state.edits }
    );

    var commentStyle = classNames(
      'filter-option',
      { 'enabled' : this.state.comments }
    );

    var likeStyle = classNames(
      'filter-option',
      { 'enabled' : this.state.likes }
    );

    var systagStyle = classNames(
      'filter-option',
      { 'enabled' : this.state.systags }
    );

    var inputStyle = classNames(
      'search-icon',
      { 'active' : this.state.inputFocus }
    );

    var selectedSentencesCount = this.props.allSelected && this.props.allSelected.length > 0 ? this.props.allSelected.length : null;
    //if all the sentences show are checked (either a result of a filter or a manual check)
    //go ahead and pre-check the 'all seleced' checkbox
    //TODO: If the sentencecount per page ever changes, the hardcoded 10 MUST BE CHANGED.
    var allDisplayedAreChecked = this.props.allSelected.length === this.props.sentenceCount || this.props.allSelected.length === 10;

    var pagination = this.generatePagination();

    //Generate the CSV export tooltip message
    //If clauses are selected ensure that's communicated in the tooltip
    var plural;
    var csvTooltipMessage;
    if (selectedSentencesCount) {
      plural = selectedSentencesCount !== 1 ? 's' : '';
      csvTooltipMessage = `Export ${selectedSentencesCount} selected clause${plural} as CSV`;
    } else {
      plural = this.props.sentenceCount !== 1 ? 's' : '';
      csvTooltipMessage = `Export ${this.props.sentenceCount} clause${plural} as CSV`;
    }
    var csvTooltip = <Tooltip><strong>{csvTooltipMessage}</strong></Tooltip>;

    //Generate the popover that contains all the tags to filter on
    var filterPopover = (this.state.filterSelectMode) ?
      ( <div className="filter-popover">
        <TagFilterPopover disableSortSelectMode={this.disableFilterSelectMode}
          options={this.buildAnnotationFilters()}
          type="Select Filter"
          onSelectOption={this.onSelectFilter}/>
      </div>
      ) : null;

      // var sortPopover = (this.state.sortSelectMode) ?
      //   ( <Popover
      //       options={this.state.options}
      //       disableSortSelectMode={this.disableSortSelectMode}
      //       onSelectOption={this.onSelectSort}
      //       type='sort'/>
      //   ) : null;

      // var sort = (
      //   <div className="header-tools">
      //     <div className="sort-popover-container">
      //       <Button onClick={this.sortSelectMode}>Sort</Button>
      //       {sortPopover}
      //     </div>
      //   </div>
      //   );

      return (
        <div className="clause-table-header">
          <div className="header-search" id="ct-step1">
            <div className="search-container">
              <div className={inputStyle}><i className="fa fa-search" /></div>
              <input ref="filterQuery" value={this.state.query} type='text' onChange={this.onQueryKeyDown} onFocus={this.setInputFocus} onBlur={this.removeInputFocus}/>
            </div>
            <div className="header-tools">
              <OverlayTrigger placement="bottom" overlay={csvTooltip}>
                <div className="csv-export">
                  <i className="fa fa-file-excel-o" onClick={this.props.onCSVExport} />
                </div>
              </OverlayTrigger>
              <div className="count-container">
                <span>{this.props.sentenceCount}</span>
              </div>
            </div>
          </div>
          <div className="header-toolbar">
            <div className="selection-tools">
              <span className="selected-count">{selectedSentencesCount}</span>
              <OverlayTrigger placement="bottom" overlay={<Tooltip><strong>Select All Visible Clauses</strong></Tooltip>}>
                <input onChange={this.onSelectAllCheck} type="checkbox" checked={allDisplayedAreChecked}/>
              </OverlayTrigger>
            </div>
            <div className="filter-bar" id="ct-step2">
              <OverlayTrigger placement="bottom" overlay={<Tooltip><strong>Apply Tag Filter</strong></Tooltip>}>
                <div className={tagStyle} onClick={this.tagsFilterMode}>
                  <span name="tags"><i className="fa fa-filter" /></span>
                </div>
              </OverlayTrigger>
              <OverlayTrigger placement="bottom" overlay={<Tooltip><strong>Toggle Edited</strong></Tooltip>}>
                <div name="edits" className={editStyle} onClick={this.onFilterButtonClick.bind(this, 'edits')} >
                  <span><i className="fa fa-clock-o" /></span>
                </div>
              </OverlayTrigger>
              <OverlayTrigger placement="bottom" overlay={<Tooltip><strong>Toggle Commented</strong></Tooltip>}>
                <div name="comments" className={commentStyle} onClick={this.onFilterButtonClick.bind(this, 'comments')}>
                  <span><i className="fa fa-comment" /></span>
                </div>
              </OverlayTrigger>
              <OverlayTrigger placement="bottom" overlay={<Tooltip><strong>Toggle Liked/Disliked</strong></Tooltip>}>
                <div name="likes" className={likeStyle} onClick={this.onFilterButtonClick.bind(this, 'likes')}>
                  <span><i className="fa fa-thumbs-up" /></span>
                </div>
              </OverlayTrigger>
              <OverlayTrigger placement="bottom" overlay={<Tooltip><strong>Show Auto Tags</strong></Tooltip>}>
                <div name="systags" className={systagStyle} onClick={this.onFilterButtonClick.bind(this, 'systags')}>
                  <span><i className="fa fa-tag" /></span>
                </div>
              </OverlayTrigger>
            </div>
            <div className="tool-gap"></div>
            {pagination}
          </div>
          {filterPopover}
        </div>
      );
  }

});

module.exports = ClauseTableHeader;
