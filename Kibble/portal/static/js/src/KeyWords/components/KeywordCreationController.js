import React from 'react';
import { Map } from 'immutable';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import DebounceInput from 'react-debounce-input';
import { ButtonToolbar, Button, ListGroup, ListGroupItem, Grid, Col, Row } from 'react-bootstrap';
import KeywordListPanel from 'KeyWords/components/KeywordListPanel';
import RecommendationList from 'KeyWords/components/RecommendationList';
import SimModelSelect from 'KeyWords/components/SimModelSelect';
import {
    setCurrentWord,
    markRecommendation,
    markSynonym,
    markManual,
    setModalOpen,
    selectSimModel,
    selectKeywordList,
    addNewKeyword
} from 'KeyWords/redux/actions';
import { getSimModels } from 'base/redux/modules/simmodel';
import { getKeywordLists } from 'base/redux/modules/keywordlists';
import { makeRecommendations } from 'base/redux/modules/recommendations';
import { getSynonyms } from 'base/redux/modules/synonyms';

import { MODULE_NAME } from 'KeyWords/constants';

class KeywordCreationComponent extends React.Component { // eslint-disable-line react/no-multi-comp
  constructor(props) {
    super(props);
    this.input = ev => this.props.setCurrentWord(ev.target.value);
    this.handleInputChange = this.handleInputChange.bind(this);
    this.addManualKeyword = this.addManualKeyword.bind(this);
    this.searchForSynonyms = this.searchForSynonyms.bind(this);
    this.filterChosen = this.filterChosen.bind(this);
    this.state = {
      manualKeyword: '',
      synonymsKeyword: ''
    }
  }

  componentWillMount() {
      this.props.getSimModels();
  }

  filterChosen(keywords) {
    return keywords.filter(keyword => keyword.status === 'success')
  }

  handleInputChange(e) {
    this.setState({ [e.target.name]: e.target.value });
  }

  addManualKeyword() {
    const { manualKeyword } = this.state;
    if(manualKeyword) {
      this.props.addNewKeyword(this.state.manualKeyword);
      this.setState({ manualKeyword: '' })
    }
  }

  searchForSynonyms() {
    const { synonymsKeyword } = this.state;
    if(synonymsKeyword) {
      this.props.getSynonyms(synonymsKeyword);
      this.setState({ synonymsKeyword: '' });
    }
  }

  render() {
    const isListCreationDisabled = (
      !this.filterChosen(this.props.recommendations).size &&
      !this.filterChosen(this.props.synonyms).size &&
      !this.filterChosen(this.props.manualkeywords).size
    )
    return (
      <Grid>
        <Col xs={12} md={12} sm={12}>
          <Row className="formSelectStyle">
            <div className="row-title">Create Keywords list </div>
            <Row className="no-margin-row">
              <Col xs={6} md={6} sm={6}>
                <RecommendationList
                  keywords={this.props.recommendations}
                  label="Recommendations"
                  noKeyWords="No recommendations yet"
                  markKeyword={this.props.markRecommendation}
                />
              </Col>
              <Col xs={6} md={6} sm={6}>
                <h4>Generate recommendations</h4>
                <DebounceInput
                  type="text"
                  className="search-projects"
                  name="search-projects"
                  placeholder="Type target word like: example, example|noun"
                  minLength={2}
                  debounceTimeout={100}
                  onChange={this.input}
                />
                <SimModelSelect
                  simmodels={this.props.simmodels}
                  onChange={this.props.selectSimModel}
                  selectedSimModel={this.props.selectedSimModel}
                  makeRecommendations={this.props.makeRecommendations}
                  currentWord={this.props.currentWord}
                />
              </Col>
            </Row>
            <Row className="no-margin-row">
              <Col xs={6} md={6} sm={6}>
                <RecommendationList
                  keywords={this.props.synonyms}
                  label="Synonyms"
                  noKeyWords="No synonyms found"
                  markKeyword={this.props.markSynonym}
                />
              </Col>
              <Col xs={6} md={6} sm={6}>
                <h4>Generate synonyms for</h4>
                <div className="input-wrapper">
                  <input
                    value={this.state.synonymsKeyword}
                    name="synonymsKeyword"
                    className="add-keyword-input"
                    placeholder="Type a word..."
                    onChange={this.handleInputChange}
                    onKeyDown={e => e.keyCode === 13 && this.searchForSynonyms()}/>
                  <Button className="add-button" onClick = {this.searchForSynonyms}>Generate</Button>
                </div>
              </Col>
            </Row>
            <Row className="no-margin-row">
              <Col xs={6} md={6} sm={6}>
                <RecommendationList
                  keywords={this.props.manualkeywords}
                  label="Manual added keywords"
                  noKeyWords="No manual keywords added"
                  markKeyword={this.props.markManual}
                />
              </Col>
              <Col xs={6} md={6} sm={6}>
                <h4>Add manual key words</h4>
                <div className="input-wrapper">
                  <input
                    value={this.state.manualKeyword}
                    name="manualKeyword"
                    className="add-keyword-input"
                    placeholder="Add a keyword..."
                    onChange={this.handleInputChange}
                    onKeyDown={e => e.keyCode === 13 && this.addManualKeyword()}/>
                  <Button className="add-button" onClick = {this.addManualKeyword}>Add</Button>
                </div>
              </Col>
            </Row>
            <Row className="no-margin-row">
              <div className="submit-list-wrapper">
                <ButtonToolbar>
                 <Button
                    onClick={() => this.props.setModalOpen('create', true)}
                    disabled={isListCreationDisabled}
                  >
                    Create New Keyword list
                  </Button>
                </ButtonToolbar>
              </div>
            </Row>
          </Row>
        </Col>
      </Grid>
    );
  }
};

const mapDispatchToProps = dispatch => bindActionCreators({
  markRecommendation,
  markSynonym,
  markManual,
  makeRecommendations,
  getSynonyms,
  setModalOpen,
  setCurrentWord,
  getSimModels,
  selectSimModel,
  selectKeywordList,
  addNewKeyword
}, dispatch);

const mapStateToProps = state => ({
  recommendations: state[ MODULE_NAME ].get('recommendations'),
  manualkeywords: state[ MODULE_NAME ].get('manualkeywords'),
  synonyms: state[ MODULE_NAME ].get('synonyms'),
  recommendationMarks: state[ MODULE_NAME ].get('recommendationMarks'),
  currentWord: state[ MODULE_NAME ].get('currentWord'),
  keywordlists: state[ MODULE_NAME ].get('keywordlists'),
  selectedKeywordList: state[ MODULE_NAME ].get('selectedKeywordList'),
  simmodels: state[ MODULE_NAME ].get('simmodels'),
  selectedSimModel: state[ MODULE_NAME ].get('selectedSimModel'),
});

export default connect(mapStateToProps, mapDispatchToProps)(KeywordCreationComponent);
