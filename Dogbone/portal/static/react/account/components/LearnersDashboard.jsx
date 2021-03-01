import React from 'react';
import { connect } from 'react-redux';
import { Tooltip, Popover, OverlayTrigger,Button } from 'react-bootstrap';
import CriticalActionButton from 'common/components/CriticalActionButton';
import classNames from 'classnames';
import ToggleActivateButton from './ToggleActivateButton';
import SpotImport from './SpotImport';
import AnalysisOptions from './AnalysisOptions.jsx';
import ReactTransitionGroup from 'react-addons-css-transition-group';

// App
import { updateSettings } from '../redux/modules/setting';
import {
  deleteLearner,
  activateLearner,
  deactivateLearner,
  resetLearner,
  changeColorTag,
  getFromServer as getLearnerFromServer
} from '../redux/modules/learner';
import {
  getFromServer as getExperimentsFromServer
} from '../redux/modules/experiment';


const colors = [
  '#f9f6fb',
  '#b7dbf3',
  '#cfb4d6',
  '#fcd3dd',
  '#fde0b4',
  '#fcf6b4',
  '#bee1cb'
]

/* Component Stylings */
require('./styles/LearnersDashboard.scss');

const LearnerColorPick = React.createClass({

  getInitialState() {
    return {
      isStatusIconVisible: false,
      color:this.props.color_code
    }
  },

  componentWillReceiveProps(nextProps) {
    const { color_code } = this.props;
    if (color_code !== nextProps.color_code) {
      // when icon is still visible clear timeout for its hiding
      if (this.statusIconTimeoutId) clearTimeout(this.statusIconTimeoutId)

      // show status icon
      this.setState({ isStatusIconVisible: 'success' })
      this.statusIconTimeoutId = setTimeout(() => {
        this.setState({ isStatusIconVisible: false })
        this.statusIconTimeoutId = null;
      }, this.statusIconTimeout)
    } else {
      if (this.state.color !== color_code) {
        this.setState({
          color: color_code
        })
        this.setState({ isStatusIconVisible: 'failed' })
        this.statusIconTimeoutId = setTimeout(() => {
          this.setState({ isStatusIconVisible: false })
          this.statusIconTimeoutId = null;
        }, this.statusIconTimeout)
      }
    }
  },

  componentWillUnmount() {
    if (this.statusIconTimeoutId) {
      clearInterval(this.statusIconTimeoutId)
    }
  },

  statusIconTimeout: 1500,
  statusIconTimeoutId: null,

  render() {
    const { color_code, onColorChange } = this.props;
    const popoverBottom = (
      <Popover id="popover-positioned-bottom" title="Popover bottom">
        <div className="color-palette">
          {colors.map((listColorCode, key) => {
            return (
              <div
              key={key}
              className={'color-option' + (listColorCode === color_code ? ' selected' : '')}
              style={{ backgroundColor: listColorCode }}
              onClick={
                () => {
                  onColorChange(listColorCode,color_code);
                  this.setState({ color: listColorCode })
                }}
              />
            )}
          )}
        </div>
      </Popover>
    );

    return (

      <OverlayTrigger trigger="focus" placement="bottom" overlay={popoverBottom}>
        <Button className="learner-color-tag" style={{ backgroundColor: this.state.color }}>
          <ReactTransitionGroup transitionName="color-status"
              transitionEnterTimeout={100}
              transitionLeaveTimeout={100}>
              { this.state.isStatusIconVisible === 'success' && <i className="fa fa-check" /> }
              { this.state.isStatusIconVisible === 'failed' && <i className="fa fa-times" /> }
          </ReactTransitionGroup>
        </Button>
      </OverlayTrigger>
    )
  }
})


const LearnerListItem = React.createClass({

  propTypes: {
    name: React.PropTypes.string,
    noninfered_set_size: React.PropTypes.number,
    positive_set_size: React.PropTypes.number,
    total_set_size: React.PropTypes.number,
    pretrained: React.PropTypes.bool,
    is_mature: React.PropTypes.bool,
    maturity: React.PropTypes.number,
    active: React.PropTypes.bool,
    onActivate: React.PropTypes.func,
    onDeactivate: React.PropTypes.func,
    onReset: React.PropTypes.func,
    onDelete: React.PropTypes.func
  },

  matureIconLevels: {
    '1': 'start',
    '2': 'half',
    '3': 'end'
  },

  toggleActive() {
    if (this.props.active) {
      // It's just been deactivated
      this.props.onDeactivate(this.props.name);
    } else {
      // It's just been activated
      this.props.onActivate(this.props.name);
    }
  },

  onReset() {
    this.props.onReset(this.props.name);
  },

  onDelete() {
    this.props.onDelete(this.props.name);
  },

  onColorChange(color, oldColor) {
    this.props.onColorChange(this.props.name, color, oldColor);
  },

  render() {
    const name = this.props.name;
    const noninfered_set_size = this.props.noninfered_set_size;
    const positive_set_size = this.props.positive_set_size;
    const total_set_size = this.props.total_set_size;
    const is_mature = this.props.is_mature;
    const maturity_score = this.props.maturity;
    const pretrained = this.props.pretrained;
    const color_code = this.props.color_code

    const positive_percent = (positive_set_size * 100 / total_set_size) | 0;
    const negative_percent = 100 - positive_percent;

    const rowClasses = classNames('learners-row');
    const learnerNameClasses = classNames('learner-name', this.props.active ? null : 'inactive', is_mature ? null : 'immature');

    let activation;

    if (!is_mature) {
      const icon_level = ((maturity_score / 0.3333) | 0) + 1; // Js way of rounding down
      const iconClass = classNames('fa', 'fa-hourglass-' + this.matureIconLevels[icon_level]);
      activation = (
        <span className="learner-maturity">
          <OverlayTrigger placement="right" overlay={<Tooltip id={this.props.name}>Not mature yet</Tooltip>}>
            <i className={iconClass} />
          </OverlayTrigger>
        </span>
      );
    } else {
      activation = (
        <span className="learner-active-btn">
          <ToggleActivateButton active={this.props.active} onClick={this.toggleActive}/>
        </span>
      );
    }

    var pretrainedIcon;
    if (pretrained) {
      pretrainedIcon = (
        <OverlayTrigger placement="right" overlay={<Tooltip id={this.props.name}>Pre-trained</Tooltip>}>
          <i className="fa fa-magic" />
        </OverlayTrigger>
      );
    }

    var deleteButton;
    if (!pretrained) {
      deleteButton = (
        <CriticalActionButton
          title="Delete"
          mode="active"
          action={this.onDelete}
          id={this.props.name}
        />
      );
    } else {
      // You can't delete a pretrained, only reset it
      deleteButton = (
        <CriticalActionButton
          title="Delete"
          mode="inactive"
          tooltipMessage="Pre-trained learners cannot be deleted. Use Reset or Deactivate it."
          id={this.props.name}
        />
      );
    }

    var resetButton;
    if (total_set_size > 0) {
      resetButton = (
        <CriticalActionButton
          title="Reset"
          mode="active"
          action={this.onReset}
          id={this.props.name}
        />
      );
    } else {
      resetButton = (
        <CriticalActionButton
          title="Reset"
          mode="inactive"
          id={this.props.name}
        />
      );
    }

    var plural = (noninfered_set_size != 1) ? 's' : null;

    return (
      <div className={rowClasses}>
        <LearnerColorPick
          color_code={color_code}
          onColorChange={this.onColorChange}
        />
        <span className={learnerNameClasses}>
          <span className="learner-label">
            {name}
            <span className="learner-activation">{activation}</span>
          </span>
        </span>
        <span className="learner-pretrained">{pretrainedIcon}</span>
        <span className="learner-size">
          <span>
            {noninfered_set_size} <span className="descr">sample{plural}</span>
          </span>
          <div className="bar-indication">
            <div className="green-bar" style={{ width: positive_percent + '%' }} />
            <div className="red-bar" style={{ width: negative_percent + '%' }} />
          </div>
        </span>
        <span className="learner-reset">
          {resetButton}
        </span>
        <span className="learner-reset">
          {deleteButton}
        </span>
      </div>
    );
  }
});

const LearnersDashboard = React.createClass({

  componentDidMount() {
    const { dispatch } = this.props;
    dispatch(getLearnerFromServer());
    dispatch(getExperimentsFromServer());
  },

  onLearnerReset(name) {
    const { dispatch } = this.props;
    dispatch(resetLearner(name));
  },

  onLearnerDelete(name) {
    const { dispatch } = this.props;
    dispatch(deleteLearner(name));
  },

  onLearnerActivate(name) {
    const { dispatch } = this.props;
    dispatch(activateLearner(name));
  },

  onLearnerDeactivate(name) {
    const { dispatch } = this.props;
    dispatch(deactivateLearner(name));
  },

  onColorChange(name,color,oldColor) {
    const { dispatch } = this.props;
    dispatch(changeColorTag(name,color,oldColor));
  },

  renderLearnerHelpText() {
    const { setting, dispatch } = this.props;

    //hipster rename
    const settings = setting;

    if (settings && settings.get('show_learner_help_text') !== false) {
      // Covering the initial case where the settings might not be set, or the show_learner_help_text
      // might not be set,the newState should default to false if the close button is clicked.
      const newState = (
        settings.get('show_learner_help_text') === undefined ?
        false :
        !settings.get('show_learner_help_text')
      );

      return (
        <div className="learners-helptext">
          <img src="/static/img/new_tag_demo.png" width="239px" alt="Use the 'Enter tags here...' field on clauses" />
          <i className="fa fa-info-circle" /> To create a new learner, start tagging clauses
          <i
            className="fa fa-times learners-helptext-close"
            onClick={() => dispatch(updateSettings({ show_learner_help_text: newState }))}
          />
        </div>
      )
    }
  },

  render() {
    let dashBoardContent;
    const { learner, experiment } = this.props;

    //if the learners have loaded
    if (learner.get('isInitialized') && experiment.get('isInitialized')) {
      const learners = learner.get('learners');
      const experiments = experiment.get('experiments')
      //if there are indeed learners (more than 0)
      if (learners.size > 0 || experiments.size > 0) {
        const learnersList = learners.map(item => {
          return (
            <LearnerListItem
              key={item.get('name')}
              name={item.get('name')}
              noninfered_set_size={item.get('noninfered_set_size')}
              positive_set_size={item.get('positive_set_size')}
              total_set_size={item.get('total_set_size')}
              active={item.get('active')}
              pretrained={item.get('pretrained')}
              is_mature={item.get('is_mature')}
              maturity={item.get('maturity')}
              color_code = {item.get('color_code')}
              onActivate={this.onLearnerActivate}
              onDeactivate={this.onLearnerDeactivate}
              onReset={this.onLearnerReset}
              onDelete={this.onLearnerDelete}
              onColorChange={this.onColorChange}
            />);
        });

        dashBoardContent = (
          <span>
            {learnersList}
            <SpotImport />
          </span>
        );
      } else { //there are no learners
        dashBoardContent = (
          <span>
            <div className="learners-listing-no-data">
              <span className="learner-message">
                Sorry, no learners found
              </span>
            </div>
            <SpotImport />
          </span>
        );
      }
    } //the learners have yet to load
    else {
      //spinning gear if still loading, message if none found.
      var loadingSpin = (
          <div>
            <i className="fa fa-cog fa-spin" />
            <div className="learner-message">Loading</div>
          </div>
      );
      dashBoardContent = (
        <div className="learners-listing-no-data">
          {loadingSpin}
        </div>
      );
    }
    return (
      <div className="learners-container">
        { this.renderLearnerHelpText() }
        <AnalysisOptions />
        {dashBoardContent}
      </div>
    );
  }
});

const mapLearnersDashboardStateToProps = (state) => {
  return {
    learner: state.learner,
    setting: state.setting,
    experiment: state.experiment
  }
};

export default connect(mapLearnersDashboardStateToProps)(LearnersDashboard)
