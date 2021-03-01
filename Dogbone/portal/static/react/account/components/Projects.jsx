import React from 'react';
import { connect } from 'react-redux';
import { Modal, ModalBody } from 'react-bootstrap';
import DebounceInput from 'react-debounce-input';
import { hashHistory } from 'react-router';
import _ from 'lodash';

// App
import ProjectsTiles from './ProjectsTiles';
import Filters from './Filters';
import ConfirmDeleteModalContents from './ConfirmDeleteModalContents';
import {
  defaultFilters,
  parseFilters,
  clearFiltersForUrl,
  isFiltersDirty,
  setFilters,
  updatePage,
  getFromServer as getProjectFromServer
} from '../redux/modules/project';


require('./styles/Projects.scss');


const TileProjectsViewComponent = React.createClass({
  render() {
    var { user, isInitialized } = this.props;
    let projectListing;
    let freeUserMessage;
    if (!isInitialized) {
      projectListing = (
        <div className="projects-listing-no-data">
          <div>
            <i className="fa fa-cog fa-spin" />
            <div className="learner-message">Loading</div>
          </div>
        </div>
      );
    } else {
      projectListing = (
        <ProjectsTiles
          defaultRepView={this.props.defaultRepView}
          user={this.props.user}
          openDeleteModal={this.props.openDeleteModal}
          openRejectModal={this.props.openRejectModal}
        />
      );
    }

    if (user.get('is_paid') !== undefined && !user.get('is_paid')) {
      const line1 = 'As a free user, you can\'t upload any new documents for a Beagle analysis.';
      const line2 = 'Upgrade to a paid account! :)';
      freeUserMessage = (
        <div className="project-listing-no-data">
          {line1}<br/>{line2}
        </div>
      );
    }

    const projectsSection = (
      <div className="projects-section added">
        {freeUserMessage}
        {projectListing}
      </div>
    );

    return (
      <div>
        {projectsSection}
      </div>
    );
  }
});

const TileProjectsView = TileProjectsViewComponent;

const Projects = React.createClass({
  getInitialState() {
    return {
      tileActive: false,
      deleteModalIsOpen: false, // or the project object
      rejectModalIsOpen: false,
      isFiltersDropOpen: false
    };
  },

  componentDidMount() {
    const { dispatch } = this.props;
    const queryFilters = parseFilters(this.getQueryParams());
    const mergedFilters = Object.assign({}, defaultFilters, queryFilters);
    dispatch(setFilters(mergedFilters));
    this.sendQuery(mergedFilters);
  },

  componentWillReceiveProps(nextProps) {
    const { dispatch } = this.props;
    // if query params (filters) change: get new projects
    if (!_.isEqual(this.props.location.query, nextProps.location.query)) {
      const queryFilters = parseFilters(this.getQueryParams(nextProps));
      const mergedFilters = Object.assign({}, defaultFilters, queryFilters);
      dispatch(setFilters(mergedFilters));
      this.sendQuery(queryFilters);
    }
  },

  openDeleteModal(project,callback_close_tile) {
    this.setState({
      deleteModalIsOpen: project,
      closeTileCallback: callback_close_tile
    });
  },

  closeDeleteModal() {
    this.setState({ deleteModalIsOpen: false });
  },

  openRejectModal(project,callback_close_tile) {
    this.setState({
      rejectModalIsOpen: project,
      closeTileCallback: callback_close_tile
    });
  },

  closeRejectModal() {
    this.setState({ rejectModalIsOpen: false });
  },

  toggleFilterDrop() {
    this.setState({ isFiltersDropOpen: !this.state.isFiltersDropOpen })
  },

  handleInputChange(e) {
    const { dispatch } = this.props;
    const queryFilters = parseFilters(this.getQueryParams());
    const filters = { ...queryFilters, 'q': e.target.value };

    dispatch(updatePage(0));
    dispatch(setFilters(filters));
    this.setQueryParams(filters);
  },

  handleInputFocus() {
    const { isFiltersDropOpen } = this.state;
    !isFiltersDropOpen && this.setState({ isFiltersDropOpen: true })
  },

  handleFiltersChange(propName, value) {
    const { dispatch } = this.props;
    const queryFilters = parseFilters(this.getQueryParams());
    const filters = { ...queryFilters, [propName]: value };

    dispatch(updatePage(0));
    dispatch(setFilters(filters));
    this.setQueryParams(filters);
  },

  handleFiltersReset() {
    const { dispatch } = this.props;

    dispatch(updatePage(0));
    dispatch(setFilters({}));
    this.setQueryParams({});
  },

  getQueryParams(props) {
    return props ? props.location.query : this.props.location.query;
  },

  setQueryParams(filters) {
    hashHistory.push({
      pathname: '/projects',
      query: clearFiltersForUrl(filters)
    }); // pushing new query params triggers projects GET request
  },

  sendQuery(filters) {
    const { dispatch } = this.props;
    dispatch(getProjectFromServer(true, filters)); // true is clearing cache argument
  },

  render() {
    const { user, setting, isInitialized } = this.props;
    const { isFiltersDropOpen } = this.state;

    const queryFilters = parseFilters(this.getQueryParams());
    const mergedFilters = Object.assign({}, defaultFilters, queryFilters);
    const isDirty = isFiltersDirty(queryFilters);


    const projects = (
      <TileProjectsView
        defaultRepView={setting.get('default_report_view')}
        user={user}
        openDeleteModal={this.openDeleteModal}
        openRejectModal={this.openRejectModal}
        isInitialized={isInitialized}
      />
    );

    return (
      <div className="projects-column">
        <div className="projects-project-header">
          <div className="projects-searchbar">
            <div className="projects-searchbox">
              <span className="projects-search"><i className="fa fa-search" /></span>

              <DebounceInput
                type="text"
                value={mergedFilters.q}
                name="search-projects"
                placeholder="Search"
                minLength={2}
                debounceTimeout={300}
                onChange={this.handleInputChange}
                onFocus={this.handleInputFocus}
              />

              <span
                className="projects-filter"
                onClick={this.toggleFilterDrop}>
                { isFiltersDropOpen ? (
                  <i className="fa fa-chevron-up" />
                ) : (
                  <i className={`projects-filter-icon ${isDirty ? 'projects-filter-icon--active' : ''} fa fa-filter`} />
                ) }
              </span>
            </div>
          </div>

          { isFiltersDropOpen && (
            <Filters
              filters={mergedFilters}
              onChange={this.handleFiltersChange}
              onReset={this.handleFiltersReset}
              isDirty={isDirty} />
          ) }

        </div>

        {projects}

        <Modal
          show={Boolean(this.state.deleteModalIsOpen) || Boolean(this.state.rejectModalIsOpen)}
          onHide={this.state.deleteModalIsOpen ? this.closeDeleteModal : this.closeRejectModal}>
          <ModalBody>
            <ConfirmDeleteModalContents
              closeProp={this.state.deleteModalIsOpen ? this.closeDeleteModal : this.closeRejectModal}
              project={this.state.deleteModalIsOpen || this.state.rejectModalIsOpen}
              isDelete={this.state.deleteModalIsOpen}
              isReject={this.state.rejectModalIsOpen}
              closeTile={this.state.closeTileCallback}
            />
          </ModalBody>
        </Modal>
      </div>
    );
  }
});

const mapStateToProps = (state) => {
  return {
    user: state.user,
    setting: state.setting,
    isInitialized: (
      state.user.get('isInitialized') &&
      state.setting.get('isInitialized') &&
      state.project.get('isInitialized')
    )
  }
};

export default connect(mapStateToProps)(Projects)
