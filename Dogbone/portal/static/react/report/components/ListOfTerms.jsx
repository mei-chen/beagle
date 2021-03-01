import _ from 'lodash';
import React from 'react';
import { connect } from 'react-redux';
import $ from 'jquery';
import assign from 'object-assign';
import classNames from 'classnames';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import uuidV4 from 'uuid/v4';

import log from 'utils/logging';
import LikeTools from './LikeTools';
import { NoDataContextV } from './NoData';
import RevisionControls from './RevisionControls';
import replaceLineBreak from 'utils/replaceLineBreak';
import {
  submitComment,
  acceptChange,
  rejectChange
} from 'report/redux/modules/report';
import ILVL_MARKER from 'utils/INDENTLEVEL_MARKER';
import insertIndents from 'utils/insertIndents';

require('./styles/ListOfTerms.scss');


const TRANSLATE_API = 'https://www.googleapis.com/language/translate/v2';
const TRANSLATE_KEY = 'AIzaSyAb_m3H2ckI6r69wqbUtGjJhkBpjEzBY3o';

// this component was previously used for sentence translation
// translation methods are still in Clause component

// const Translate = React.createClass({

//   onChange(evt) {
//     const languageKey = evt.target.value;
//     this.props.onChange(languageKey);
//   },

//   render() {
//     var languages = ['en', 'ro', 'fr', 'es', 'it', 'de', 'ru', 'zh-CN', 'ja', 'ga'];
//     return (
//       <div className="translation">
//         <select className="translation"
//           defaultValue={this.props.selected}
//           onChange={this.onChange}>
//           {languages.map((lang, idx) => <option key={idx}>{lang}</option>)}
//         </select>
//       </div>
//     );
//   }


// });


const ClauseFormComponent = React.createClass({

  getInitialState() {
    return {
      commentText: this.props.sentence.comment
    };
  },

  commentChange(evt) {
    const commentText = evt.target.value;
    this.setState({ commentText: commentText });
  },

  saveComment() {
    const { sentence, dispatch } = this.props;
    const idx = sentence.idx;
    const commentText = this.state.commentText || '';
    if (commentText) {
      dispatch(submitComment(idx, commentText));
    }
  },

  onAcceptChange() {
    const { sentence, dispatch } = this.props;
    const idx = sentence.idx;
    dispatch(acceptChange(idx));
  },

  onRejectChange() {
    const { sentence, dispatch } = this.props;
    const idx = sentence.idx;
    dispatch(rejectChange(idx));
  },

  dummyFunction() {
    log.error('Submit Received');
  },

  render() {
    const { user, sentence } = this.props;
    const hasUnapprovedRevision = !!sentence.latestRevision;
    const username = user.get('username');

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

const mapClauseFormComponentStateToProps = (state) => {
  return {
    user: state.user
  }
};

const ClauseForm = connect(mapClauseFormComponentStateToProps)(ClauseFormComponent)


const Clause = React.createClass({

  propTypes: {
    sentence: React.PropTypes.object.isRequired
  },

  // this state structure was used when Tranlate component was enabled
  // getInitialState() {
    // return {
    //   language: 'en',
    //   translations: {
    //     en: this.props.sentence.form
    //   }
    // };
  // },

  hasTranslation(lang) {
    let { translations } = this.state;
    return translations.hasOwnProperty(lang);
  },

  getTextNode() {
    const text = replaceLineBreak(this.props.sentence.form || '');
    const ilvlRegExp = new RegExp(ILVL_MARKER);
    const split = text.split(ilvlRegExp);
    let spans = [];

    if (split.length === 1) {
      spans.push(<span key={uuidV4()}>{insertIndents(text)}</span>);
    } else {
      split.forEach((txt, idx) => {
        if (idx % 2 == 0) {
          spans.push(<span key={uuidV4()}>{insertIndents(txt)}</span>);
          spans.push(<br key={`${idx}.br`}/>);
        }
      });
    }
    return spans;
  },

  getSourceText() {
    var sentence = this.props.sentence;
    return sentence ? replaceLineBreak(sentence.form) : '';
  },

  addTranslation(lang, translatedText) {
    let newTranslations = assign(this.state.translations, {
      [lang]: translatedText
    });
    // use `forceUpdate` to force a re-render
    // PureRenderMixin doesn't re-render when a translation is added
    this.setState({ translations: newTranslations }, this.forceUpdate);
  },

  changeLanguage(languageKey) {
    this.setState({ language: languageKey });

    if (!this.hasTranslation(languageKey)) {
      let sourceLang = 'en';
      let targetLang = languageKey;
      let sourceText = this.getSourceText();
      $.ajax({
        url: TRANSLATE_API,
        data: {
          q: sourceText,
          key: TRANSLATE_KEY,
          source: sourceLang,
          target: targetLang,
          format: 'text'
        },
        dataType: 'jsonp',
        success: (response) => {
          // this looks complicated, but we just get the text from the response
          let translatedText = response.data.translations[0].translatedText;
          this.addTranslation(targetLang, translatedText);
        }
      });
    }
  },

  clauseClick() {
    this.props.focusSentence(this.props.sentence.idx);
    //if the wizard is running, a click should advance the user to the next step
    if (this.props.introJsObject) {
      this.props.introJsObject.nextStep();
    }
  },

  render() {
    var sentence = this.props.sentence;

    var refStyle = {
      backgroundColor: '#bcf0d2'
    };

    var displayTextNode;
    // external refs
    if (this.props.reference) {
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
    // other sentences
    } else {
      displayTextNode = this.getTextNode();
    }

    return (
      <li className="clause-item">
        <a className="clause-focus-link" onClick={this.clauseClick}>
          {displayTextNode}
        </a>
        <div className="clause-all-controls">
          <ClauseForm
            sentence={sentence}
          />
        </div>
      </li>
    );
  }

});


const ClauseSubsection = React.createClass({

  propTypes: {
    title: React.PropTypes.string.isRequired,
    sentences: React.PropTypes.array.isRequired,
    isReferences: React.PropTypes.bool.isRequired,
    focusSentence: React.PropTypes.func.isRequired,
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
    const collapsed = this.state.collapsed;

    const iconClassnames = classNames(
      'fa',
      'collapse-icon',
      collapsed ? 'fa-angle-right' : 'fa-angle-down'
    );

    let clauses = this.props.sentences.map(sentence => {
      return (
        <Clause
          key={sentence.idx}
          sentence={sentence}
          reference={this.props.isReferences}
          focusSentence={this.props.focusSentence}
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


const ClauseList = React.createClass({

  propTypes: {
    type: React.PropTypes.oneOf([
      'Liabilities', 'Responsibilities', 'Terminations', 'references', 'keyword', 'custom'
    ]).isRequired,
    groupedSentences: React.PropTypes.object.isRequired,
    eventKey: React.PropTypes.string.isRequired,
    parties: React.PropTypes.object.isRequired,
    focusSentence: React.PropTypes.func.isRequired,
  },

  render() {
    const { type, parties, groupedSentences, ...props } = this.props;
    const isReferences = type === 'references';

    let sectionYou, sectionThem, sectionBoth, sectionNone;
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
        <div className="beagle-clauselist">
          {sectionYou}
          {sectionThem}
          {sectionBoth}
          {sectionNone}
        </div>
      );
    } else {
      return (
        <div className="beagle-clauselist">
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
    case 'Responsibilities': mapped = 'RESPONSIBILITY'; break;
    case 'Liabilities': mapped = 'LIABILITY'; break;
    case 'Terminations': mapped = 'TERMINATION'; break;
    case 'keyword': mapped = this.props.eventKey; break;
    }
    return mapped;
  },

  render() {
    let { isActive, header, className, type, sentences, colorCode, ...props } = this.props;
    const isReferences = type === 'references';
    const isKeyword = type === 'keyword';
    const isCustom = type === 'custom';

    let icon;
    let totalCount = 0;
    const groupedSentences = {
      you: [], them: [], both: [], none: []
    };

    if (isReferences) {
      let pred = s => (s.external_refs || []).length > 0;
      groupedSentences.none = sentences.filter(pred);
      totalCount += groupedSentences.none.length;
    } else if (isCustom) {
      // This ugly line selects clauses with at least one annotation/keyword
      // that is not RLT and neither NDA related tag
      let pred = s => (_.filter(s.annotations, function(ann) {return ann.type != 'A' && ann.label != 'Return-Destroy-Information' && ann.label != 'Definition-on-Confidential-Information' && ann.label != 'Term-of-NDA' && ann.label != 'Term-of-Confidentiality'}).length > 0);
      groupedSentences.none = sentences.filter(pred);
      totalCount = groupedSentences.none.length;
    } else if (isKeyword) {
      let label = this.mapLabel(type);
      let pred = s => _.find(s.annotations, { label: label });
      groupedSentences.none = sentences.filter(pred);
      totalCount = groupedSentences.none.length;
      icon=(
        <OverlayTrigger placement="top" overlay={<Tooltip id={uuidV4()}>Keyword</Tooltip>}>
          <span className="tag-type">
            <i className="fa fa-bookmark" aria-hidden="true" />
          </span>
        </OverlayTrigger>
      );
      if (this.props.learner) {
        icon=(
          <OverlayTrigger placement="top" overlay={<Tooltip id={uuidV4()}>Learner</Tooltip>}>
            <span className="tag-type">
              <i className="fa fa-lightbulb" aria-hidden="true" />
            </span>
          </OverlayTrigger>
        );
      }
    } else {
      let label = this.mapLabel(type);
      let pred = s => _.find(s.annotations, { label: label });
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
      !isActive ? 'fa-angle-right' : 'fa-angle-down',
      (totalCount == 0) ? 'void-panel' : null
    );

    var clauseList = (
      <ClauseList {...props} type={type} groupedSentences={groupedSentences} />
    );
    if (totalCount == 0 && this.props.isNew) {
      totalCount = (
        <i className="fa fa-asterisk" />
      );
      clauseList = (
        <div className="beagle-clauselist">
          <NoDataContextV info="Re-analyze to include this keyword" />
        </div>
      );
    }
    return (
      <div className={panelClasses}>
        <h4 className="header" onClick={this.toggleCollapsed}>
          <i className={iconClasses} style={{ backgroundColor: colorCode ? colorCode : null }} />
          {icon}
          <span className="tag-name" title={header}>
            {header}
          </span>
          <span className="clauses-count">
            {totalCount}
          </span>
        </h4>
        {clauseList}
      </div>
    );
  }

});


const ListOfTerms = React.createClass({

  propTypes: {
    report: React.PropTypes.object.isRequired,
    openSection: React.PropTypes.string,
    focusSentence: React.PropTypes.func.isRequired,
    changeOpenSection: React.PropTypes.func.isRequired,
    subsectionCollapsed: React.PropTypes.bool,
  },

  sectionActiveMap: {
    'Responsibilities': false,
    'Liabilities':      false,
    'Terminations':     false,
    'references':       false,
    'custom':           false,
  },

  handleSelect(selectedKey) {
    var label = selectedKey;
    this.props.changeOpenSection(label);
  },

  render() {
    const {
      report,
      keywords,
      learners,
      isInitialized,
      className,
      openSection,
      ...props
    } = this.props;

    if (!isInitialized) {
      return null;
    }


    const analysis = report.get('analysis').toJS();
    const parties = analysis.parties;
    const keywords_state = report.get('keywords_state').toJS().map(k => k[0]);

    const SAM = this.sectionActiveMap;
    const sentences = analysis.sentences.filter(s => {
      return s.form !== '' &&
        ((s.annotations && s.annotations.length > 0) ||
         (s.external_refs && s.external_refs.length > 0));
    });

    // Init with all active keywords
    const custSubsect = keywords.filter(kobj => kobj.active)
      .map(kobj => kobj.keyword);

    var learnersSubsect=[];
    // Also update SAM
    keywords.map(kobj => { SAM[kobj.keyword] = false });
    sentences.filter(s => {
      return s.form !== '' &&
        (s.annotations && s.annotations.length > 0 &&
          (s.annotations.filter(a => {
            if (a.type != 'A' && a.type !='K' && a.label != 'Return-Destroy-Information' &&
                                 a.label != 'Definition-on-Confidential-Information' &&
                                 a.label != 'Term-of-NDA' &&
                                 a.label != 'Term-of-Confidentiality') {
              if (learnersSubsect.indexOf(a.label) === -1) {
                learnersSubsect.push(a.label);
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
    let customSubSectionsKywd = custSubsect.map((keyword, idx) => {
      return (<Panel className="kywd"
                key={'custsub' + idx + uuidV4()}
                type="keyword"
                header={keyword}
                isNew={(keywords_state.indexOf(keyword) <= -1)}
                eventKey={keyword}
                isActive={SAM[keyword]}
                {...genericProps}
              />);
    });

    let customSubSectionsLearn = learnersSubsect.map((keyword, idx) => {
      const foundLearner = learners.find(learner => learner.name === keyword);

      return (<Panel className="kywd"
                key={'custsub' + idx + uuidV4()}
                type="keyword"
                learner={true}
                colorCode={foundLearner ? foundLearner.color_code : ''}
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
          type="Responsibilities"
          header="Responsibilities"
          isNew={false}
          eventKey="Responsibilities"
          isActive={SAM.Responsibilities}
          {...genericProps}
        />
        <Panel className="liab"
          key="liab"
          type="Liabilities"
          header="Liabilities"
          isNew={false}
          eventKey="Liabilities"
          isActive={SAM.Liabilities}
          {...genericProps}
        />
        <Panel className="term"
          key="term"
          type="Terminations"
          header="Terminations"
          isNew={false}
          eventKey="Terminations"
          isActive={SAM.Terminations}
          {...genericProps}
        />
        <Panel className="refs"
          type="references"
          header="External References"
          isNew={false}
          eventKey="references"
          isActive={SAM.references}
          {...genericProps}
        />
        <Panel className="cust"
          key="cust"
          type="custom"
          header="Custom"
          isNew={false}
          eventKey="custom"
          isActive={SAM.custom}
          {...genericProps}
        />
        {customSubSectionsKywd}
        {customSubSectionsLearn}
      </div>
    );
  }

});

const mapListOfTermsStateToProps = (state) => {
  return {
    report: state.report,
    isInitialized: state.report.get('isInitialized'),
    keywords: state.keyword.get('keywords').toJS(),
    learners: state.learner.get('learners').toJS()
  }
};

export default connect(mapListOfTermsStateToProps)(ListOfTerms)
