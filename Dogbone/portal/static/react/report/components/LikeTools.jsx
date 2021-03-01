import React from 'react';
import { connect } from 'react-redux';
import _ from 'lodash';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import classNames from 'classnames';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';

// App
import userDisplayName from 'utils/userDisplayName';
import {
  likeSentence,
  dislikeSentence,
  clearLikeSentence,
  clearDislikeSentence
} from 'report/redux/modules/report';


require('./styles/LikeTools.scss');


const LikeTools = React.createClass({

  propTypes: {
    sentence: React.PropTypes.object.isRequired,
    username: React.PropTypes.string.isRequired,
  },

  getInitialState() {
    return {
      likeIsLoading: false,
      dislikeIsLoading: false
    }
  },

  componentWillReceiveProps(nextProps) {
    const { likeIsLoading, dislikeIsLoading } = this.state;

    // no-like -> like or vise versa
    if (likeIsLoading && this.userDoesLike() !== this.userDoesLike(nextProps)) {
      this.setState({ likeIsLoading: false });
    }

    // no-dislike -> dislike or vise versa
    if (dislikeIsLoading && this.userDoesDislike() !== this.userDoesDislike(nextProps)) {
      this.setState({ dislikeIsLoading: false });
    }
  },

  userDoesLike(props) {
    const { username, sentence } = props || this.props;
    const likes = sentence.likes ? sentence.likes.likes : [];
    const matchesUsername = _.matchesProperty('username', username);
    return !!_.find(likes, matchesUsername);
  },

  userDoesDislike(props) {
    const { username, sentence } = props || this.props;
    const dislikes = sentence.likes ? sentence.likes.dislikes : [];
    const matchesUsername = _.matchesProperty('username', username);
    return !!_.find(dislikes, matchesUsername);
  },

  onLikeSentence() {
    const { dispatch, sentence } = this.props;
    const idx = sentence.idx;

    this.setState({ likeIsLoading: true });
    //if it's already liked, user is trying to clear
    if (this.userDoesLike()) {
      dispatch(clearLikeSentence(idx));
    } else { // if there is no existing like, apply one.
      dispatch(likeSentence(idx));
    }
  },

  onDislikeSentence() {
    const { dispatch, sentence } = this.props;
    const idx = sentence.idx;

    this.setState({ dislikeIsLoading: true });
    //if it's already disliked, user is trying to clear
    if (this.userDoesDislike()) {
      dispatch(clearDislikeSentence(idx));
    } else { //if there is no existing dislike, apply one.
      dispatch(dislikeSentence(idx));
    }
  },

  generateLikeTooltip() {
    const likedUsers = this.props.sentence.likes ? this.props.sentence.likes.likes : [];
    if (likedUsers.length > 0) {
      const names = likedUsers.map(u => {
        let name = userDisplayName(u);
        return <li key={u.username}><strong>{name}</strong></li>;
      });
      return <Tooltip id="1"><ul className="tooltip-ul">{names}</ul></Tooltip>;
    } else {
      return <Tooltip id="2"><strong>Like this clause</strong></Tooltip>;
    }
  },

  generateDislikeTooltip() {
    const dislikedUsers = this.props.sentence.likes ? this.props.sentence.likes.dislikes : [];
    if (dislikedUsers.length > 0) {
      const names = dislikedUsers.map(u => {
        const name = userDisplayName(u);
        return <li key={u.username}><strong>{name}</strong></li>;
      });
      return <Tooltip id="3"><ul className="tooltip-ul">{names}</ul></Tooltip>;
    } else {
      return <Tooltip id="4"><strong>Dislike this clause</strong></Tooltip>;
    }
  },

  render() {
    const likes = this.props.sentence.likes;
    const { likeIsLoading, dislikeIsLoading } = this.state;

    let otherLikes, otherDislikes;
    if (likes) {
      otherLikes = likes.likes.length > 0;
      otherDislikes = likes.dislikes.length > 0;
    }

    const isLiked = this.userDoesLike();
    const isDisliked = this.userDoesDislike();

    const likeStyle = classNames(
      'fa',
      'fa-thumbs-up',
      'like',
      { 'liked': isLiked },
      { 'other-likes': otherLikes && !isLiked } //only show if others have likes AND not already liked by user
    );

    const dislikeStyle = classNames(
      'fa',
      'fa-thumbs-down',
      'dislike',
      { 'disliked': isDisliked },
      { 'other-dislikes': otherDislikes && !isDisliked } //only show if others have dislikes AND not already disliked by user
    );

    const likeTooltip = this.generateLikeTooltip();
    const dislikeTooltip = this.generateDislikeTooltip();

    const loader = <i className="fa fa-spinner fa-spin" />;

    return (
      <div className="like-tools">
        { likeIsLoading ? loader : (
          <OverlayTrigger placement="top" overlay={likeTooltip}>
            <i onClick={this.onLikeSentence} className={likeStyle} />
          </OverlayTrigger>
        ) }
        { dislikeIsLoading ? loader : (
          <OverlayTrigger placement="top" overlay={dislikeTooltip}>
            <i onClick={this.onDislikeSentence} className={dislikeStyle} />
          </OverlayTrigger>
        ) }
      </div>
    );
  }

});

export default connect()(LikeTools)
