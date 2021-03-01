import React from 'react';
import { connect } from 'react-redux';
import Checkbox from 'react-bootstrap/lib/Checkbox';
import Popover from 'react-bootstrap/lib/Popover';
import ButtonToolbar from 'react-bootstrap/lib/ButtonToolbar';
import Button from 'react-bootstrap/lib/Button';
import ReactTransitionGroup from 'react-addons-css-transition-group';
import ClassNames from 'classnames';

import { getFromServer } from 'common/redux/modules/annotations';

require('./styles/ExportPopover.scss')

const ExportPopoverComponent = React.createClass({

  getInitialState() {
    this.annotationsThatAreIncluded={};
    return {
      includeAnnotations:false,
    }
  },

  componentDidMount() {
    const { dispatch } = this.props;
    dispatch(getFromServer(this.props.uuid));
  },

  showDropdown() {
    this.setState({ includeAnnotations: !this.state.includeAnnotations })
  },

  handleSelectAll(e) {
    // select or deselect all annotations
    for (let a in this.annotationsThatAreIncluded) {
      this.annotationsThatAreIncluded[a].checked = e.target.checked;
    }
  },

  handleAnnotationChange(e) {
    if (!e.target.checked) {
      this.selectAll.checked = false;
    // if all annotations checked
    } else if (Object.keys(this.annotationsThatAreIncluded).filter(a => this.annotationsThatAreIncluded[a].checked === false).length === 0) {
      this.selectAll.checked = true;
    }
  },

  buildAnnotationsCheckboxes() {
    let annotations_checkboxes = [];
    const { annotations } = this.props;
    let annotations_list = annotations.get('annotations');

    annotations_list.map(a => {
      //exclude the keywords
      annotations_checkboxes.push(
        <Checkbox
          key={a}
          inputRef={ref => { this.annotationsThatAreIncluded[a] = ref; }}
          onChange={this.handleAnnotationChange}>
          {a}
        </Checkbox>
      )
    })
    return annotations_checkboxes;
  },

  handleExport() {
    var data;
    data = {
      include_track_changes: this.includeTrackChanges.checked,
      include_comments: this.includeComments.checked,
      include_annotations: this.includeAnnotations.checked,
    };

    //this should be an object with all the annotations checked or unchecked
    if (this.state.includeAnnotations) {
      data['included_annotations'] = {};
      const { annotations } = this.props;
      let annotations_list = annotations.get('annotations');
      annotations_list.map(a => {
        data['included_annotations'][a] = this.annotationsThatAreIncluded[a].checked;
      });
    }

    this.props.setLoading();
    this.props.prepareDocxExport(data);
    this.props.handleDocumentExportCancel();
  },

  render() {
    let annotationsList;
    let content;
    const { annotations } = this.props;
    let isInitialized = annotations.get('isInitialized');
    if (this.state.includeAnnotations) {
      if (isInitialized) {
        content = (
          <div>
            <div className="annotations-select-all-wrap">
              <input
                type="checkbox"
                id="annotations-select-all"
                className="annotations-select-all"
                ref={node => this.selectAll = node}
                onChange={this.handleSelectAll} />
              <label htmlFor="annotations-select-all">Select All</label>
            </div>
            { this.buildAnnotationsCheckboxes() }
          </div>
        )
      } else {
        content = (
          <div className="loading-annotations">
            <i className="fa fa-cog fa-spin fa-3x fa-fw" />
          </div>
        );
      }
      annotationsList = (
        <div className="annotations">
          {content}
        </div>
      );
    }
    const dialog = (
     <span>
        <Checkbox
          inputRef={ref => { this.includeTrackChanges = ref; }}
          disabled={!(this.props.hasTrackChanges>0)}>
          Include track-changes
        </Checkbox>

        <Checkbox
          inputRef={ref => { this.includeComments = ref; }}
          disabled={!this.props.hasComments}>
          Include comments
        </Checkbox>

        <Checkbox onClick={this.showDropdown}
          inputRef={ref => { this.includeAnnotations = ref; }}
          disabled={false}>
          Include Beagle annotations
        </Checkbox>
        <ReactTransitionGroup transitionName="annotations_list"
          transitionEnterTimeout={100}
          transitionLeaveTimeout={100}>
          {annotationsList}
        </ReactTransitionGroup>
      </span>
    );
    const title = 'Add extras';

    const tooltip_classes = ClassNames({
      'popover-tooltip': true,
      'report': this.props.report_style,
      'account': this.props.account_style
    });

    return (
      <span className={tooltip_classes}>
        <div className="popup-overlay" onClick={this.props.handleDocumentExportCancel} />
        <Popover id="document-export-popover" placement="bottom" title={title} className="document-export-popover" style={{ width:'100%' }}>
          <div className="dialog">
            {dialog}
          </div>
          <ButtonToolbar>
            <Button bsStyle="info" onClick={this.handleExport}>Export</Button>
            <Button onClick={this.props.handleDocumentExportCancel}>Cancel</Button>
          </ButtonToolbar>
        </Popover>
      </span>
    );
  }
});


const mapStateToProps = (state) => {
  return {
    annotations: state.annotations
  }
};

export let ExportPopover = connect(mapStateToProps)(ExportPopoverComponent)

export const ExportBatchPopover = React.createClass({

  getInitialState() {
    this.annotationsThatAreIncluded={};
    return {
      includeAnnotations:false,
      annotations:[]
    }
  },

  handleExportAnyways() {
    const data = {
      include_track_changes: this.includeTrackChanges.checked,
      include_comments: this.includeComments.checked,
      include_annotations: this.includeAnnotations.checked,
    };

    this.props.setLoading();
    this.props.prepareDocxExport(data);
    this.props.handleDocumentExportCancel(data);
  },

  render() {
    const dialog = (
     <span>
        <Checkbox
          inputRef={ref => { this.includeTrackChanges = ref; }}
          disabled={!(this.props.changedSentencesCount>0)}>
          Include track-changes
        </Checkbox>

        <Checkbox
          inputRef={ref => { this.includeComments = ref; }}
          disabled={!this.props.hasComments}>
          Include comments
        </Checkbox>

        <Checkbox
          inputRef={ref => { this.includeAnnotations = ref; }}>
          Include Beagle annotations
        </Checkbox>
      </span>
    );
    const title = 'Add extras';

    const tooltip_classes = ClassNames({
      'popover-tooltip': true,
      'report': this.props.report_style,
      'account': this.props.account_style
    });

    return (
      <span className={tooltip_classes}>
        <div className="popup-overlay" onClick={this.props.handleDocumentExportCancel} />
        <Popover id="document-export-popover" placement="bottom" title={title} className="document-export-popover" style={{ width:'100%' }}>
          <div className="dialog">
            {dialog}
          </div>
          <ButtonToolbar>
            <Button bsStyle="info" onClick={this.handleExportAnyways}>Export</Button>
            <Button onClick={this.props.handleDocumentExportCancel}>Cancel</Button>
          </ButtonToolbar>
        </Popover>
      </span>
    );
  }
});
