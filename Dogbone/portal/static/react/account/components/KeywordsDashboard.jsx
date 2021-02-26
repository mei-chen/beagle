import React from 'react';
import { connect } from 'react-redux';
import CriticalActionButton from 'common/components/CriticalActionButton';
import classNames from 'classnames';

// App
import {
  addKeyword,
  deleteKeyword,
  activateKeyword,
  deactivateKeyword,
  getFromServer as getKeywordFromServer
} from '../redux/modules/keyword';

/* Component Stylings */
require('./styles/KeywordsDashboard.scss');


const ToggleActivateButton = React.createClass({

  render() {
    var toggle_status = this.props.active ? 'on' : 'off';
    var toggleIconClass = classNames('fa', 'fa-toggle-' + toggle_status, toggle_status);

    return (
      <span className="toggleActiveButton" onClick={this.props.onClick}>
        <i className={toggleIconClass} />
      </span>
    );
  }
});


const KeywordListItem = React.createClass({

  propTypes: {
    name: React.PropTypes.string,
    active: React.PropTypes.bool,
    onActivate: React.PropTypes.func,
    onDeactivate: React.PropTypes.func,
    onDelete: React.PropTypes.func
  },

  getInitialState() {
    return {
      active: this.props.active,
      resetBtnActive: true,
      deleted: false,
    }
  },

  toggleActive() {
    const activation_status = this.state.active;
    this.setState({ active: !activation_status });
    if (activation_status) {
      // It's just been deactivated
      this.props.onDeactivate(this.props.name);
    } else {
      // It's just been activated
      this.props.onActivate(this.props.name);
    }
  },

  onReset() {
    this.setState({ resetBtnActive: false });
    this.props.onReset(this.props.name);
  },

  onDelete() {
    this.props.onDelete(this.props.name);
  },

  render() {
    const name = this.props.name;

    const rowClasses = classNames('keywords-row');
    const keywordNameClasses = classNames('keyword-name', this.state.active ? null : 'inactive');

    const activation = (
      <span className="keyword-active-btn">
        <ToggleActivateButton active={this.state.active} onClick={this.toggleActive}/>
      </span>
    );

    const deleteButton = (
      <CriticalActionButton title="Delete"
                            mode="active"
                            action={this.onDelete}/>
    );

    return (
      <div className={rowClasses}>
        {activation}
        <span className={keywordNameClasses}>{name}</span>
        <span className="keyword-delete">
          {deleteButton}
        </span>
      </div>
    );
  }
});

const KeywordsDashboard = React.createClass({
  componentDidMount() {
    const { dispatch } = this.props;
    dispatch(getKeywordFromServer());
  },

  onKeywordAdd() {
    const { dispatch } = this.props;
    const keyword = this.refs.keyword.value;
    if (keyword) {
      dispatch(addKeyword(keyword));
    }
    this.refs.keyword.value = '';
  },

  onKeywordDelete(name) {
    const { dispatch } = this.props;
    dispatch(deleteKeyword(name));
  },

  onKeywordActivate(name) {
    const { dispatch } = this.props;
    dispatch(activateKeyword(name));
  },

  onKeywordDeactivate(name) {
    const { dispatch } = this.props;
    dispatch(deactivateKeyword(name));
  },

  handleKeyPress(e) {
    if (e.which === 13) {  // enter pressed
      this.onKeywordAdd();
    }
  },

  render() {
    let docs;
    const {
      keywords
    } = this.props;
    if (keywords.get('isInitialized')) {
      if (keywords.get('keywords')) {
        if (keywords.get('keywords').size > 0) {
          docs = keywords.get('keywords').map(item => {
            return (<KeywordListItem key={item.get('keyword')}
                                     name={item.get('keyword')}
                                     active={item.get('active')}
                                     onDelete={this.onKeywordDelete}
                                     onActivate={this.onKeywordActivate}
                                     onDeactivate={this.onKeywordDeactivate}/>);
          });
        } else {
          docs = (
            <div className="no-keywords">
              No keywords just yet
              <div className="keywords-tutorial">
                <i className="fa fa-info" /> Keywords are terms you want to be looked up in your contracts
                <br/><br/>
                Simple text search is applied for <i className="fa fa-bookmark" /> Keywords; for more complex patterns, use <i className="fa fa-lightbulb" /> Learners
              </div>
            </div>
          );
        }
      }
    } else {
      var contents = (
          <div>
            <i className="fa fa-cog fa-spin" />
            <div className="learner-message">Loading</div>
          </div>
      );
      docs = (
        <div className="learners-listing-no-data">
          {contents}
        </div>
      );
    }
    return (
      <div className="keywords-column">
        <div className="keywords-header">
          <div className="keyword-add-wrap">
            <i className="keyword-add-icon fa fa-plus" />
            <input type="text"
                   className="keyword-add-box"
                   ref="keyword"
                   placeholder="Keyword"
                   onKeyDown={this.handleKeyPress}
                    />
            <button type="button"
                    className="keyword-add-button"
                    onClick={this.onKeywordAdd}>
              Add
            </button>
          </div>
        </div>
        <div className="keywords-container">
          {docs}
        </div>
      </div>
    );
  }
});

const mapKeywordsDashboardStateToProps = (state) => {
  return {
    keywords: state.keyword
  }
};

export default connect(mapKeywordsDashboardStateToProps)(KeywordsDashboard)
