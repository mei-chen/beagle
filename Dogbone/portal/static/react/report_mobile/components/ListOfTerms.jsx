import _ from 'lodash';
var React = require('react');
var Reflux = require('reflux');
var $ = require('jquery');
var assign = require('object-assign');
var classNames = require('classnames');
var PureRenderMixin = React.addons.PureRenderMixin;

var log = require('utils/logging');
var Actions = require('report/actions').ReportActions;
var LikeTools = require('report/components/LikeTools');
var UserStore = require('common/stores/UserStore');
var classNames = require('classnames');
var NoDataContextV = require('report/components/NoData').NoDataContextV;
var BeaglePropTypes = require('utils/BeaglePropTypes');
var RevisionControls = require('report/components/RevisionControls');
var replaceLineBreak = require('utils/replaceLineBreak');
var { ReportActions } = require('report/actions');
var EditorBox = require('./EditorBox');
var { KeywordsStore } = require('../../account/stores');

require('./styles/ListOfTerms.scss');


var ClauseForm = React.createClass({

  getInitialState() {
    return {
      commentText: this.props.sentence.comment
    };
  },

  commentChange(evt) {
    var commentText = evt.target.value;
    this.setState({ commentText: commentText });
  },

  saveComment() {
    var id = this.props.sentence.idx;
    var commentText = this.state.commentText || '';
    Actions.editComment(id, commentText);
  },

  onAcceptChange() {
    var idx = this.props.sentence.idx;
    ReportActions.acceptChange(idx);
    this.props.disableEditMode();
  },

  onRejectChange() {
    var idx = this.props.sentence.idx;
    ReportActions.rejectChange(idx);
    this.props.disableEditMode();
  },

  dummyFunction() {
    log.error("Submit Received");
  },

  render() {
    var sentence = this.props.sentence;
    var user = UserStore.getUser();
    var hasUnapprovedRevision = !!sentence.latestRevision;
    var username = user.username;
    var hasOpinions = !!sentence.likes;
    var hasLikes = hasOpinions && sentence.likes.likes.length > 0;
    var hasDislikes = hasOpinions && sentence.likes.dislikes.length > 0;
    var userDoesLike = hasLikes && _.contains(sentence.likes.likes, username);
    var userDoesDislike = hasDislikes && _.contains(sentence.likes.dislikes, username);

    var checkClasses = classNames(
      'check',
      userDoesLike ? null : 'inactive'
    );

    var issueClasses = classNames(
      'issue',
      userDoesDislike ? null : 'inactive'
    );

    return (
      <div className="clause-controls">
        <LikeTools
          sentence={sentence}
          username={username}
        />
        <RevisionControls
          pending={false}
          deletePending={false}
          unapproved={hasUnapprovedRevision}
          acceptChange={this.onAcceptChange}
          rejectChange={this.onRejectChange}
          submitRevision={this.dummyFunction}
        />
      </div>
    );
  }

});


var Clause = React.createClass({

  mixins: [PureRenderMixin],

  propTypes: {
    sentence: React.PropTypes.object.isRequired
  },

  getInitialState() {
    return {
      language: 'en',
      editMode: false,
    };
  },

  getSourceText() {
    var sentence = this.props.sentence;
    return !!sentence ? replaceLineBreak(sentence.form) : '';
  },

  disableEditMode() {
    this.setState({ editMode : false });
  },

  enableEditMode() {
    this.setState({ editMode : true});
  },

  generateEditBox() {
    return (
      <EditorBox
        isInList
        sentence={this.props.sentence}
        disableEditMode={this.disableEditMode}
      />
    );
  },

  clauseClick() {
    this.enableEditMode();
  },

  render() {
    var sentence = this.props.sentence;
    var lang = this.state.language;

    var refStyle = {
      backgroundColor: '#bcf0d2'
    };

    var displayTextNode;

    var text = sentence.form;
    var refs = _.sortBy(sentence.external_refs, 'offset');

    var strings = [];
    var index = 0;
    refs.forEach(ref => {
      var thisStartIndex = ref.offset;
      strings.push({
        text: text.slice(index, thisStartIndex),
        ref: false
      });
      strings.push({
        text: ref.form,
        ref: true
      });
      index = ref.offset + ref.length;
    });
    strings.push({
      text: text.slice(index),
      ref: false
    });
    displayTextNode = (
      <span>
        {strings.map((string, idx) => {
          return (
            <span key={idx} style={string.ref ? refStyle : null}>
              {replaceLineBreak(string.text)}
            </span>
          );
        })}
      </span>
    );

    if (this.state.editMode) {
      return this.generateEditBox();
    } else {
      return (
        <li className="clause-item">
          <a className="clause-focus-link" onClick={this.clauseClick}>
            {displayTextNode}
          </a>
          <div className="clause-all-controls">
            <ClauseForm sentence={sentence}
              selectedLanguage={this.state.language}
            />
          </div>
        </li>
      );
    }
  }

});


var ClauseSubsection = React.createClass({

  propTypes: {
    title: React.PropTypes.string.isRequired,
    sentences: React.PropTypes.array.isRequired,
    isReferences: React.PropTypes.bool.isRequired,
    subsectionCollapsed: React.PropTypes.bool,
  },

  getDefaultProps() {
    return {
      subsectionCollapsed: false,
    };
  },

  getInitialState() {
    return {
      collapsed: this.props.subsectionCollapsed ? true : false,
    }
  },

  toggleCollapsed() {
    this.setState({
      collapsed: !this.state.collapsed
    });
  },

  render() {
    var collapsed = this.state.collapsed;

    var iconClassnames = classNames(
      'fa',
      'collapse-icon',
      collapsed ? 'fa-caret-right' : 'fa-caret-down'
    );

    let clauses = this.props.sentences.map(sentence => {
      return (
        <Clause
          key={sentence.idx}
          sentence={sentence}
          reference={this.props.isReferences}
          introJsObject={this.props.introJsObject}
        />
      );
    });

    var subsection_header;
    if (this.props.title != 'Neither') {
      subsection_header = (
        <h5 className="subpanel-heading"
          onClick={this.toggleCollapsed}>
          <i className={iconClassnames} />
          {this.props.title}
          <span className="clauses-count">
            {this.props.sentences.length}
          </span>
        </h5>
      );
    }

    var listClasses = classNames(
      (subsection_header && collapsed) ? 'collapsed' : null
    );

    return (
      <div className="beagle-listofterms-subsection">
        {subsection_header}
        <ul className={listClasses}>{clauses}</ul>
      </div>
    );
  }

});


var ClauseList = React.createClass({

  propTypes: {
    type: React.PropTypes.oneOf([
      'liabilities', 'responsibilities', 'terminations', 'references', 'keyword', 'custom'
    ]).isRequired,
    groupedSentences: React.PropTypes.object.isRequired,
    eventKey: React.PropTypes.string.isRequired,
    parties: React.PropTypes.object.isRequired,
  },

  render() {
    var { type, parties, groupedSentences, ...props } = this.props;
    var isReferences = type === 'references';
    var isKeyword = type === 'keyword';
    var isCustom = type === 'custom';

    var sectionYou, sectionThem, sectionBoth, sectionNone;
    if (groupedSentences.you && groupedSentences.you.length > 0) {
      sectionYou = (
        <ClauseSubsection
          title={parties.you.name}
          sentences={groupedSentences.you}
          isReferences={isReferences}
          {...props}
        />
      );
    }
    if (groupedSentences.them && groupedSentences.them.length > 0) {
      sectionThem = (
        <ClauseSubsection
          title={parties.them.name}
          sentences={groupedSentences.them}
          isReferences={isReferences}
          {...props}
        />
      );
    }
    if (groupedSentences.both && groupedSentences.both.length > 0) {
      sectionBoth = (
        <ClauseSubsection
          title="Both"
          sentences={groupedSentences.both}
          isReferences={isReferences}
          {...props}
        />
      );
    }
    if (groupedSentences.none && groupedSentences.none.length > 0) {
      // External References are entirely belonging to 'neither' party
      sectionNone = (
        <ClauseSubsection
          title="Neither"
          sentences={groupedSentences.none}
          isReferences={isReferences}
          {...props}
        />
      );
    }

    if (sectionThem || sectionYou || sectionBoth || sectionNone) {
      return (
        <div classNames="beagle-clauselist">
          {sectionYou}
          {sectionThem}
          {sectionBoth}
          {sectionNone}
        </div>
      );
    } else {
      return (
        <div classNames="beagle-clauselist">
          <NoDataContextV />
        </div>
      );
    }
  }

});


var Panel = React.createClass({

  propTypes: {
    header: React.PropTypes.string.isRequired,
    eventKey: React.PropTypes.string.isRequired,
  },

  toggleCollapsed() {
    this.props.changeActiveKey(this.props.eventKey);
  },

  mapLabel(label) {
    var mapped;
    switch (label) {
      case 'responsibilities': mapped = 'RESPONSIBILITY'; break;
      case 'liabilities':      mapped = 'LIABILITY'; break;
      case 'terminations':     mapped = 'TERMINATION'; break;
      case 'keyword':          mapped = this.props.eventKey; break;
    }
    return mapped;
  },

  render() {
    var { isActive, header, className, type, sentences, ...props } = this.props;
    var isReferences = type === 'references';
    var isKeyword = type === 'keyword';
    var isCustom = type === 'custom';

    var totalCount = 0;
    var groupedSentences = {
      you: [], them: [], both: [], none: []
    };

    if (isReferences) {
      let pred = s => (s.external_refs || []).length > 0;
      groupedSentences.none = sentences.filter(pred);
      totalCount += groupedSentences.none.length;

    } else if (isCustom) {
      // This ugly line selects clauses with at least one annotation that
      // is not RLT and neither NDA related tag
      let pred = s => (_.filter(s.annotations, function(ann) {return ann.type != 'K' && ann.type != 'A' && ann.label != 'Return-Destroy-Information' && ann.label != 'Definition-on-Confidential-Information' && ann.label != 'Term-of-NDA' && ann.label != 'Term-of-Confidentiality'}).length > 0);
      groupedSentences.none = sentences.filter(pred);
      totalCount = groupedSentences.none.length;

    } else if (isKeyword) {
      let label = this.mapLabel(type);
      let pred = s => _.findWhere(s.annotations, { label: label });
      groupedSentences.none = sentences.filter(pred);
      totalCount = groupedSentences.none.length;

    } else {
      let label = this.mapLabel(type);
      let pred = s => _.findWhere(s.annotations, { label: label });
      sentences = sentences.filter(pred);
      totalCount = sentences.length;
      sentences.forEach(sentence => {
        let annotations = sentence.annotations || [];
        annotations = annotations.filter(a => a.label === label);
        annotations.forEach(annotation => {
          let party = annotation.party;
          groupedSentences[party].push(sentence);
        });
      });
    }

    var panelClasses = classNames(
      'beagle-panel',
      className,
      !isActive ? 'collapsed' : null
    );

    var iconClasses = classNames(
      'cv-dropdown-btn', 'fa',
      !isActive ? 'fa-caret-right' : 'fa-caret-down',
      (totalCount == 0) ? 'void-panel' : null
    );

    var clauseList = (
      <ClauseList {...props} type={type} groupedSentences={groupedSentences} />
    );
    if (totalCount == 0 && this.props.isNew) {
      totalCount = (
        <i className="fa fa-asterisk"></i>
      );
      clauseList = (
        <div classNames="beagle-clauselist">
          <NoDataContextV info="Re-analyze to include this keyword" />
        </div>
      );
    }

    return (
      <div className={panelClasses}>
        <h4 className="header" onClick={this.toggleCollapsed}>
          <i className={iconClasses} />
          {header}
          <span className="clauses-count">
            {totalCount}
          </span>
        </h4>
        {clauseList}
      </div>
    );
  }

});


var ListOfTerms = React.createClass({

  mixins: [Reflux.connect(KeywordsStore, 'keywords')],

  propTypes: {
    analysis: React.PropTypes.object.isRequired,
    openSection: React.PropTypes.string,
    changeOpenSection: React.PropTypes.func.isRequired,
    subsectionCollapsed: React.PropTypes.bool,
  },

  sectionActiveMap: {
    'responsibilities': false,
    'liabilities':      false,
    'terminations':     false,
    'references':       false,
    'custom':           false,
  },

  handleSelect(selectedKey) {
    var label = selectedKey;
    this.props.changeOpenSection(label);
  },

  render() {
    let { analysis, className, openSection, ...props } = this.props;
    if (!analysis || !analysis.analysis) {
      return null;
    }

    var parties = analysis.analysis.parties;
    var keywords_state = (analysis.keywords_state) ? analysis.keywords_state.map(k => k[0]) : [];

    var SAM = this.sectionActiveMap;

    var sentences = analysis.analysis.sentences.filter(s => {
      return s.form !== '' &&
        ((s.annotations && s.annotations.length > 0) ||
         (s.external_refs && s.external_refs.length > 0));
    });

    // Init with all active keywords
    var custSubsect = this.state.keywords.filter(kobj => kobj.active)
                                         .map(kobj => kobj.keyword);
    // Also update SAM
    this.state.keywords.map(kobj => { SAM[kobj.keyword] = false });
    sentences.filter(s => {
      return s.form !== '' &&
        (s.annotations && s.annotations.length > 0 &&
          (s.annotations.filter(a => {
            if (a.type != 'A' && a.label != 'Return-Destroy-Information' &&
                                 a.label != 'Definition-on-Confidential-Information' &&
                                 a.label != 'Term-of-NDA' &&
                                 a.label != 'Term-of-Confidentiality') {
              if(custSubsect.indexOf(a.label) === -1) {
                custSubsect.push(a.label);
              }
              SAM[a.label] = false;
              return true;
            } else {
              return false;
            }
          }).length > 0)
        );
    });

    var accordionClassNames = classNames(
      'beagle-list-of-terms',
      'beagle-panel-group',
      className
    );

    for (var section in SAM) {
      if (section == openSection) {
        SAM[section] = true;
      } else {
        SAM[section] = false;
      }
    }

    let genericProps = assign({}, props, {
      parties: parties,
      sentences: sentences,
      changeActiveKey: this.handleSelect,
    });

    let customSubSections = custSubsect.map((keyword, idx) => {
      return (<Panel className="kywd"
                key={"custsub" + idx}
                type='keyword'
                header={keyword}
                isNew={(keywords_state.indexOf(keyword) <= -1)}
                eventKey={keyword}
                isActive={SAM[keyword]}
                {...genericProps}
              />);
    });

    return (
      <div className={accordionClassNames}>
        <Panel className="resp"
          key="resp"
          type='responsibilities'
          header="Responsibilities"
          eventKey="responsibilities"
          isActive={SAM.responsibilities}
          {...genericProps}
        />
        <Panel className="liab"
          key="liab"
          type='liabilities'
          header="Liabilities"
          isNew={false}
          eventKey="liabilities"
          isActive={SAM.liabilities}
          {...genericProps}
        />
        <Panel className="term"
          key="term"
          type='terminations'
          header="Terminations"
          isNew={false}
          eventKey="terminations"
          isActive={SAM.terminations}
          {...genericProps}
        />
        <Panel className="refs"
          type='references'
          header="External References"
          isNew={false}
          eventKey="references"
          isActive={SAM.references}
          {...genericProps}
        />
        <Panel className="cust"
          key="cust"
          type='custom'
          header="Custom"
          isNew={false}
          eventKey="custom"
          isActive={SAM.custom}
          {...genericProps}
        />
        {customSubSections}
      </div>
    );
  }

});


module.exports = ListOfTerms;
