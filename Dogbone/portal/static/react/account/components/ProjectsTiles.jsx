import React from 'react';
import { connect } from 'react-redux';
import _ from 'lodash';
import ClassNames from 'classnames';
import DummyTiles from './DummyTiles';

// App
import {
  SingularDocumentTile,
  BatchTile,
  PendingTileComponent,
  FailedTileComponent
} from './TileTypes'
import {
  getPage,
  projectsByDate
} from '../redux/modules/project';
import userDisplayName from 'utils/userDisplayName';

require('./styles/ProjectTiles.scss');

const ProjectsTilesComponent = React.createClass({
  propTypes: {
    user: React.PropTypes.object.isRequired,
    meta: React.PropTypes.object.isRequired,
    projectsByDate: React.PropTypes.object.isRequired,
    isLoading: React.PropTypes.bool.isRequired,
    goPageBack: React.PropTypes.func.isRequired,
    goPageNext: React.PropTypes.func.isRequired,
    setPageNum: React.PropTypes.func.isRequired,
  },

  getDefaultProps() {
    return {
      meta: {},
      projectsByDate: {},
      MAX_PER_PAGE: 6,
    };
  },

  componentWillReceiveProps(nextProps) {
    const { pagination } = nextProps.meta;

    // if projects count is changed (by deleting or rejecting)
    if (this.props.meta.pagination.object_count !== pagination.object_count) {
      // if this is the last page && we delete the last project
      if (pagination.page === pagination.page_count) this.pageBack();
    }
  },

  setPageNum(pageNum) {
    this.props.setPageNum(pageNum);
  },

  pageBack() {
    this.props.goPageBack();
  },

  pageNext() {
    this.props.goPageNext();
  },

  getFullUTCDate(date) {
    return new Date(
      Date.UTC(
        date.getUTCFullYear(),
        date.getUTCMonth(),
        date.getUTCDate(),
        date.getUTCHours(),
        date.getUTCMinutes(),
        date.getUTCSeconds()
      )
    )
  },

  checkTimeout(processing_begin_timestamp) {
    const nowtime = new Date();
    const nowUTCtime = this.getFullUTCDate(nowtime);
    const startProcessingTime = new Date(processing_begin_timestamp);
    const startProcessingUTCtime = this.getFullUTCDate(startProcessingTime)
    const processingTime = ((nowUTCtime.getTime() - startProcessingUTCtime.getTime())/60000);
    //timeout limit is 60 minutes
    if (processingTime > 60) {
      return true;
    }
    return false;
  },

  generatePaginator() {
    let { meta } = this.props;
    let pagination = meta.pagination || {};
    let pageNumber = pagination.page || 0;
    let pageCount = pagination.page_count || 0;

    //if one page only, don't display paginator
    if (!(pageCount > 1)) {
      return;
    }

    const hasPagePrev = pageNumber >= 1;
    const hasPageNext = pageNumber < pageCount - 1;

    const pagePrevClasses = ClassNames(
      'paging', 'prev', (hasPagePrev) ? 'active' : 'inactive'
    );

    const pageNextClasses = ClassNames(
      'paging', 'next', (hasPageNext) ? 'active' : 'inactive'
    );

    return (
      <div className="paginator noselect">
        <span className={pagePrevClasses} onClick={this.pageBack}>
          <i className="fa fa-chevron-left" />
        </span>
        {_.range(pageCount).map(pageMarkerNum => {
          var pgClasses = ClassNames(
            (pageMarkerNum === pageNumber) ? 'button page active' : 'button page'
          );
          return (
            <span
              key={pageMarkerNum}
              onClick={() => this.setPageNum(pageMarkerNum)}
              className={pgClasses}>
              <i className="fa fa-circle" />
            </span>
          );
        })}
        <span className={pageNextClasses} onClick={this.pageNext}>
          <i className="fa fa-chevron-right" />
        </span>
      </div>
    );
  },

  generateProjectTiles(projects) {
    const { user, openDeleteModal, openRejectModal, defaultRepView } = this.props;
    const userId = user.get('id');

    // loaded scenario
    const projectTiles = projects.map((project, key) => {
      const isOwner = project.owner.id === userId;

      // SINGLE DOCUMENT CASE
      if (project.documents_count === 1) {
        const failed = project.meta.failed;
        const pending = project.meta.status === 0;
        const timeout = pending && this.checkTimeout(project.created);

        // failed
        if (failed) {
          return (
            <FailedTileComponent
              key={key}
              uuid={project.meta.uuid}
              batchId={project.meta.batch_id}
              isOwner={isOwner}
              title={project.meta.title}
              username={userDisplayName(project.owner)}
              image={project.owner.avatar}
              openRejectModal={openRejectModal}
              openDeleteModal={openDeleteModal}
              errorMessage="Error encountered"
              detailedErrorMessage={
                (project.meta.error_message != '' ? project.meta.error_message :
                "Something went terribly wrong. We're looking into it. Sometimes it's the dog chewing on the cables.")
              }
            />
          )
        }
        // timeout
        else if (timeout) {
          return (
            <FailedTileComponent
              key={key}
              uuid={project.meta.uuid}
              batchId={project.meta.batch_id}
              isOwner={isOwner}
              title={project.meta.title}
              username={userDisplayName(project.owner)}
              image={project.owner.avatar}
              openRejectModal={openRejectModal}
              openDeleteModal={openDeleteModal}
              errorMessage="Timeout exceeded"
              detailedErrorMessage="The processing takes longer than we exceeded. Most likely something went wrong. Please retry."
            />
          )
        }
        // pending
        else if (pending) {
          return (
            <PendingTileComponent
              key={key}
              defaultRepView={defaultRepView || ''}
              batchId={project.meta.batch_id}
              isOwner={isOwner}
              title={project.meta.title}
              username={userDisplayName(project.owner)}
              image={project.owner.avatar}
              reportUrl={project.report_url}
            />
          )
        }
        // normal
        else {
          return (
            <SingularDocumentTile
              key={key}
              defaultRepView={defaultRepView || ''}
              uuid={project.meta.uuid}
              batchId={project.meta.batch_id}
              isOwner={isOwner}
              owner={project.owner}
              agreementType={project.meta.agreement_type}
              title={project.meta.title}
              username={userDisplayName(project.owner)}
              image={project.owner.avatar}
              parties={project.meta.parties}
              created={project.created}
              reportUrl={project.report_url}
              openRejectModal={openRejectModal}
              openDeleteModal={openDeleteModal} />
          )
        }
      }

      // BATCH CASE
      else {
        const pending = !project.meta.analyzed;
        const timeout = pending && this.checkTimeout(project.created);

        // timeout
        if (timeout) {
          return (
            <FailedTileComponent
              key={key}
              isBatch={true}
              uuid={project.meta.uuid}
              batchId={project.meta.batch_id}
              isOwner={isOwner}
              title={project.meta.batch_name}
              username={userDisplayName(project.owner)}
              image={project.owner.avatar}
              openRejectModal={openRejectModal}
              openDeleteModal={openDeleteModal}
              errorMessage="Timeout exceeded"
              detailedErrorMessage="The processing takes longer than we exceeded. Most likely something went wrong. Please retry."
            />
          )
        }
        // pending
        else if (pending) {
          return (
            <PendingTileComponent
              key={key}
              isBatch={true}
              defaultRepView={defaultRepView || ''}
              batchId={project.meta.batch_id}
              isOwner={isOwner}
              title={project.meta.title}
              username={userDisplayName(project.owner)}
              image={project.owner.avatar}
              reportUrl={project.report_url}
            />
          )
        // normal
        } else {
          return (
            <BatchTile
              key={key}
              defaultRepView={defaultRepView || ''}
              batchId={project.meta.batch_id}
              isOwner={isOwner}
              title={project.meta.batch_name}
              documentsCount={project.documents_count}
              username={userDisplayName(project.owner)}
              image={project.owner.avatar}
              created={project.created}
              reportUrl={project.report_url}
              openDeleteModal={openDeleteModal} />
          )
        }
      }
    });

    const projectListingLeft = projectTiles.filter((p, i) => i % 2 === 0);
    const projectListingRight = projectTiles.filter((p, i) => i % 2 === 1);

    return (
      <div className="project-tiles">
        <div className="project-column">
          {projectListingLeft}
        </div>
        <div className="project-column">
          {projectListingRight}
        </div>
      </div>
    )
  },

  render() {
    const { projectsByDate, isLoading } = this.props;
    let tilesContent;
    const dates = Object.keys(projectsByDate);

    if (dates.length > 0) {
      tilesContent = (
        <span>
          { dates.map((date, i) => (
            <div
              key={i}
              className="project-date-section">
              <div className="project-date">{ date }</div>
              {this.generateProjectTiles(projectsByDate[date])}
            </div>
          )) }
          {this.generatePaginator()}
        </span>
      );
    } else {
      tilesContent = (
        <span className="no-documents">
          <div>No documents yet</div>
          <span>
            Upload a new document using
            <div className="upload-button">
              <i className="header-nav-item-icon fa fa-plus" /> Upload
            </div>
              button above
          </span>
        </span>
      );
    }
    return (
      <div className="project-tile-section">
        {isLoading ? <DummyTiles /> : tilesContent}
      </div>
    );
  }
});

const mapProjectsTilesStateToProps = (state) => {
  return {
    projectsByDate: projectsByDate(state.project.getIn(['current', 'objects'])),
    meta: state.project.getIn(['current', 'meta']),
    MAX_PER_PAGE: state.project.get('MAX_PER_PAGE'),
    isLoading: state.project.get('isLoading')
  }
};

const mapProjectsTilesDispatchToProps = (dispatch) => {
  return {
    goPageBack: () => {
      dispatch(getPage({ prev: true }))
    },

    goPageNext: () => {
      dispatch(getPage({ next: true }))
    },

    setPageNum: (page) => {
      dispatch(getPage({ page }))
    }
  }
}

export default connect(
  mapProjectsTilesStateToProps,
  mapProjectsTilesDispatchToProps
)(ProjectsTilesComponent)
