import React, { Component, PropTypes } from 'react';
import classNames from 'classnames';
import { connect } from 'react-redux';

import Filter from './Filter';
import MultiSelect from './MultiSelect.jsx';
import './styles/Filters.scss';

import { getFromServer as getLearners } from 'account/redux/modules/learner';
import { getFromServer as getKeywords } from 'account/redux/modules/keyword';
import { getUsers } from 'account/redux/modules/project';

class Filters extends Component {
  constructor(props) {
    super(props);
    this._handleChange = this._handleChange.bind(this);
  }

  componentWillMount() {
    const { dispatch } = this.props;
    dispatch(getLearners());
    dispatch(getKeywords());
    dispatch(getUsers());
  }

  _handleChange(propName, value) {
    const { onChange } = this.props;
    onChange(propName, value);
  }

  render() {
    const { learnersNames, keywordsNames, usernames, isLoading, onReset, isDirty } = this.props;
    const { owned, invited, track, learners, comments, keywords } = this.props.filters;
    const filtersClassNames = classNames('filters', {
      'filters--disabled': isLoading
    })

    return (
      <div className={filtersClassNames}>
        <div className="filters-types">

          {/* TRACK */}
          <Filter
            icon="fa fa-clock"
            title="Track changes"
            active={track}
            onClick={() => this._handleChange('track', !track)} />

          {/* COMMENTS */}
          {/* eventTypes is "react-onclickoutside" prop */}
          <Filter
            icon="fa fa-comment"
            title="Comments"
            active={comments.length > 0}
            eventTypes={['click', 'touchend']}>

            <MultiSelect
              options={usernames}
              selected={comments}
              placeholder="All users"
              entity={['user', 'users']}
              optionIcon="fa fa-user"
              onChange={comments => this._handleChange('comments', comments)} />
          </Filter>

          {/* LEARNERS */}
          <Filter
            icon="fa fa-lightbulb"
            title="Learners"
            active={learners.length > 0}
            eventTypes={['click', 'touchend']}>

            <MultiSelect
              options={learnersNames}
              selected={learners}
              placeholder="All learners"
              entity={['learner', 'learners']}
              optionIcon="fa fa-lightbulb"
              onChange={learners => this._handleChange('learners', learners)} />
          </Filter>

          {/* KEYWORDS */}
          <Filter
            icon="fa fa-bookmark"
            title="Keywords"
            active={keywords.length > 0}
            eventTypes={['click', 'touchend']}>

            <MultiSelect
              options={keywordsNames}
              selected={keywords}
              placeholder="All keywords"
              entity={['keyword', 'keywords']}
              optionIcon="fa fa-bookmark"
              onChange={keywords => this._handleChange('keywords', keywords)} />
          </Filter>
        </div>

        <div className="filters-categories">
          <span className="filters-category">
            <input
              type="checkbox"
              id="filter-owned"
              className="checkbox-blue"
              checked={owned}
              onChange={() => this._handleChange('owned', !owned)} />
            <label htmlFor="filter-owned">Owned</label>
          </span>

          <span className="filters-category">
            <input
              type="checkbox"
              id="filter-invited"
              className="checkbox-blue"
              checked={invited}
              onChange={() => this._handleChange('invited', !invited)} />
            <label htmlFor="filter-invited">Invited</label>
          </span>
        </div>

        { isDirty && (
          <span
            className="filters-reset"
            onClick={() => onReset()}>
            <i className="fa fa-times" /> Clear filters
          </span>
        ) }
      </div>
    )
  }
}

Filters.propTypes = {
  onChange: PropTypes.func.isRequired,
  onReset: PropTypes.func.isRequired,
  filters: PropTypes.object.isRequired,
  learnersNames: PropTypes.array.isRequired,
  keywordsNames: PropTypes.array.isRequired,
  usernames: PropTypes.array.isRequired,
  isLoading: PropTypes.bool.isRequired,
  isDirty: PropTypes.bool.isRequired
};

const mapStateToProps = state => ({
  learnersNames: state.learner.get('learners').map(l => l.get('name')).toJS(),
  keywordsNames: state.keyword.get('keywords').map(k => k.get('keyword')).toJS(),
  usernames: state.project.get('users').toJS(),
  isLoading: state.project.get('isLoading')
});

export default connect(mapStateToProps)(Filters);
