var React = require('react');
var classNames = require('classnames');
require('./styles/Infobar.scss');



var PartyUser = React.createClass({
  render() {
    if (this.props.Party == 'both') {
      return (
        <div className="both_parties_wrapper">
          <div className="bothSize"><i id="user_icon" className="fa fa-user" aria-hidden="true" /> {this.props.User.you.name}</div>
          <div className="bothSize"><i id="user_icon" className="fa fa-user" aria-hidden="true" /> {this.props.User.them.name}</div>
        </div>
      )
    }

    if (this.props.Party == 'you') {
      return (
        <div><i id="user_icon" className="fa fa-user" aria-hidden="true" /> {this.props.User.you.name}</div>
      );
    }

    if (this.props.Party == 'them') {
      return (
        <div><i id="user_icon" className="fa fa-user" aria-hidden="true" /> {this.props.User.them.name}</div>
      );
    }
  }
})


var InfobarTag = React.createClass({

  render() {
    const { learners, tagType } = this.props;

    let colorCode;
    learners.map(learner => {
      if (learner.name.toLowerCase() === tagType.label.toLowerCase())
      {
        colorCode=learner.color_code;
      }
    })
    const tagStyle = { background:colorCode }

    if (tagType.party == null) {
      var userAddedTag = classNames({
        'tag':true ,
        'member_tag': tagType.type == 'M'
      });
      var tagIcon;
      if (tagType.type == 'K') {
        tagIcon = (
          <i className="fa fa-bookmark" />
        );
      } else if (tagType.type == 'S') {
        tagIcon = (
          <i className="fa fa-lightbulb" />
        );
      }

      return (
        <div className={userAddedTag} style={tagStyle}>
          {tagIcon} {tagType.label}
        </div>
      );
    }

    var partyTagClasses = classNames('tag', 'party_tag');
    var memberTagClases = classNames('tag', 'party_member');

    return (
      <div className="party_tag_wrapper">
        <div className={partyTagClasses} style={tagStyle} >{tagType.label} </div>
        <div className={memberTagClases}>

          <PartyUser
            Party={tagType.party}
            User={this.props.bothSides}
          />

        </div>
      </div>
    );
  }
});


var Infobar = React.createClass({

  render() {
    if (this.props.tags == undefined || this.props.tags.length < 1) {
      return (
        <div className="infobar infobar-hidden" />
      )
    }

    return (
        <div className="infobar">
          <div className="wrapper">
            {
              this.props.tags.map((tag, i) =>
                <InfobarTag
                  learners={this.props.learners}
                  key={i}
                  tagType={tag}
                  bothSides={this.props.partyMembers}
                />
            )}
          </div>
        </div>
    );
  }
});

module.exports = Infobar;
