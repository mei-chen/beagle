import Button from 'react-bootstrap/lib/Button';
import React from 'react';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import uuidV4 from 'uuid/v4';
import ClassNames from 'classnames';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';
import Popover from 'react-bootstrap/lib/Popover';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import {
  reAnalyze,
  toggleDisplayComponentBoolean
} from 'report/redux/modules/report';


const InplaceEditParty = React.createClass({

  _sendChange(ev) {
    this.props.onPartyChange(this.props.id, ev.target.value);
  },

  render() {
    var { party , shrinked } = this.props;

    var confidenceTooltip = (party.confidence <= 100) ? (
      <Tooltip id={uuidV4()}><strong>{party.confidence}% Confidence</strong></Tooltip>
    ) : (
      <Tooltip id={uuidV4()}><strong>Manually set</strong></Tooltip>
    );

    var confidlineStyle = {
      width: Math.min(party.confidence, 100) + '%'
    }

    var inputClasses = ClassNames(
      'party_name',
      'party_edit'
    );
    var spanClasses = ClassNames(
      'party_name',
      'party_nonedit',
    );

    var overflowClasses = ClassNames(
      'overflow-party',
      (shrinked ? 'shrinked-summary' : '')
    )

    var container;
    if (this.props.editMode) {
      container = (
        <div className="header-party">
          <input
            id={this.props.id}
            ref="partyspan"
            className={inputClasses}
            onChange={this._sendChange}
            value={party.name}
          />
        </div>
      );
    } else {
      container = (
        <OverlayTrigger placement="bottom" overlay={confidenceTooltip}>
          <div className="header-party">
            <span className={overflowClasses}>
              <span id={this.props.id} ref="partyspan" className={spanClasses}>
                {party.name}
              </span>
            </span>
            <div className="confid-bg">
              <div className="confid-line" style={confidlineStyle} />
            </div>
          </div>
        </OverlayTrigger>
      );
    }

    return (
      <span className="wrap-party">
            {container}
      </span>
    );
  }
});


const InplaceEditButton = React.createClass({
  propTypes : {
    uuid : React.PropTypes.string.isRequired,
    showUnconfidentPopover : React.PropTypes.bool.isRequired
  },

  _onSubmit() {
    this.props.submitFn();
  },

  _onDiscard() {
    this.props.discardFn();
  },

  _onEdit() {
    this.props.onEdit();
    this.clearShowUnconfidentPopover();
  },

  setShowUnconfidentPopover() {
    this.props.reportActions.toggleDisplayComponentBoolean('showUnconfidentPopover', true);
  },

  clearShowUnconfidentPopover() {
    this.props.reportActions.toggleDisplayComponentBoolean('showUnconfidentPopover', false);
  },

  generateWeakAnalysisPopover() {
    if (this.props.showUnconfidentPopover) {
      return (
          <Popover style={{ right: -87, left:-90 }} placement="bottom" positionTop="100%"
            title="Uh Oh!"
            id="document-export-popover">
            <i className="fa fa-times close-weak-analysis-popover" onClick={this.clearShowUnconfidentPopover}/>
          Beagle can’t seem to figure out the parties with great confidence.  Click here to set them manually and we’ll reanalyze the agreement.
          </Popover>
      );
    } else {
      return null
    }
  },

  render() {
    var editMode = this.props.editMode;
    var changed = this.props.changed;
    var buttonClasses = ClassNames(
      'small-button',
    );

    var editPartiesTooltip = (
      <Tooltip id={uuidV4()}><strong>Edit parties</strong></Tooltip>
    );

    if (editMode || changed) {
      return (
        <span>
          <Button bsStyle="success" onClick={this._onSubmit} className={buttonClasses}>
            Re-analyze
          </Button>
          <Button bsStyle="default" onClick={this._onDiscard} className={buttonClasses}>
            <i className="fa fa-times" />
          </Button>
        </span>
      );
    } else {
      return (
        <span className="inplace-edit-parties-button">
          <OverlayTrigger placement="bottom" overlay={editPartiesTooltip}>
            <button onClick={this._onEdit} className="subtle-button">
              <i className="fa fa-pen-square" />
            </button>
          </OverlayTrigger>
          {this.generateWeakAnalysisPopover()}
        </span>
      );
    }
  }

});


var InplacePartiesFlipButton = React.createClass({

  _onClick() {
    this.props.onFlip();
  },

  render() {
    var content;
    if (this.props.editMode) {
      content = (
        <button className="subtle-button" onClick={this._onClick}>
          <i className="fa fa-exchange" />
        </button>
      );
    } else {
      content = 'and'
    }

    return (
      <span>
        {content}
      </span>
    );
  }
});


var InplaceEditFormComponent = React.createClass({
  getInitialState() {
    return {
      editmode: false,
      changed: false,
      partyY: null,
      partyT: null
    };
  },

  onEditRequest() {
    if (!this.state.editmode) {
      const { parties } = this.props;

      this.setState({
        editmode: true,
        partyY: parties.you,
        partyT: parties.them
      });
    }
  },

  onEditOffRequest() {
    if (this.state.editmode) {
      this.setState({
        editmode: false,
        partyY: null,
        partyT: null
      });
    }
  },

  formSubmit() {
    // Gather new parties and send request
    const { reportActions } = this.props;
    reportActions.reAnalyze(this.state.partyY.name,this.state.partyT.name);
    // Hide the editing form
    this.setState({
      changed: false,
      editmode: false
    });
  },

  formDiscard() {
    // Hide the editing form
    this.setState({
      changed: false,
      editmode: false,
      partyY: null,
      partyT: null
    });
  },

  flipParties() {
    this.setState({ changed: true });

    this.setState({
      partyY: this.state.partyT,
      partyT: this.state.partyY
    });
  },

  onPartyChange(id, name) {
    var modif_party;
    this.setState({ changed: true });
    if (id == 'partya') {
      modif_party = this.state.partyY;
      modif_party.name = name;
      this.setState({ partyY: modif_party });
    } else {
      modif_party = this.state.partyT;
      modif_party.name = name;
      this.setState({ partyT: modif_party });
    }
  },

  render() {
    const {
      report,
      parties,
      isOwner, //Disable the InplaceEditsButton if the user isn't the owner
      shrinked,
      reportActions
    } = this.props;

    // If editing else it's the props;
    const partyY = this.state.partyY || parties.you;
    const partyT = this.state.partyT || parties.them;

    const inplaceEditButton = (
      isOwner && !shrinked ?
      (
        <InplaceEditButton
          editMode={this.state.editmode}
          changed={this.state.changed}
          onEdit={this.onEditRequest}
          discardFn={this.formDiscard}
          submitFn={this.formSubmit}
          uuid={report.get('uuid')}
          showUnconfidentPopover={report.get('showUnconfidentPopover')}
          reportActions={reportActions}
        />
      ) : null
    );

    return (
      <span>
        { partyY.name !== undefined && partyT.name !== undefined &&
          (<span className="parties party-editor">
            between
            <InplaceEditParty
              id="partya"
              party={partyY}
              ref="youPartyNode"
              editMode={this.state.editmode}
              onEdit={this.onEditRequest}
              onEditOff={this.onEditOffRequest}
              onPartyChange={this.onPartyChange}
              changed={this.state.changed}
              shrinked={shrinked}
            />

            <InplacePartiesFlipButton
              editMode={this.state.editmode}
              onFlip={this.flipParties}
            />

            <InplaceEditParty
              id="partyb"
              party={partyT}
              ref="themPartyNode"
              editMode={this.state.editmode}
              onEdit={this.onEditRequest}
              onEditOff={this.onEditOffRequest}
              onPartyChange={this.onPartyChange}
              changed={this.state.changed}
              shrinked={shrinked}
            />
            {inplaceEditButton}
          </span>)
        }
      </span>
    );
  }
});

const mapInplaceEditFormComponentStateToProps = (state) => {
  return {
    report: state.report,
    isOwner: (
      state.report.get('uuid') && // Make sure that report has been fetched
      state.report.get('owner').get('username') == state.user.get('username')
    )
  }
};

function mapInplaceEditFormComponentDispatchToProps(dispatch) {
  return {
    reportActions: bindActionCreators({
      reAnalyze,
      toggleDisplayComponentBoolean
    }, dispatch)
  };
}

export default connect(
  mapInplaceEditFormComponentStateToProps,
  mapInplaceEditFormComponentDispatchToProps
)(InplaceEditFormComponent)