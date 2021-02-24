import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { Grid, Col, Button, ButtonToolbar } from 'react-bootstrap';
import  validate from 'uuid-validate';
import ModalForm from 'base/components/ModalForm';
import KeywordListCreateForm from 'KeyWords/components/CreateForm';
import KeywordListEditForm from 'KeyWords/components/EditForm';
import KeywordCreationController from 'KeyWords/components/KeywordCreationController';
import KeywordSearchController from 'KeyWords/components/KeywordSearchController';
import PreviewKeywordsPopup from 'KeyWords/components/PreviewKeywordsPopup';
import {
    getKeywordLists,
    patchKeywordList,
    deleteKeywordList,
    postKeywordList
} from 'base/redux/modules/keywordlists';
import {
    deselectKeywordList,
    setModalOpen,
    purge,
} from 'KeyWords/redux/actions';

import { MODULE_NAME } from 'KeyWords/constants';

import "../scss/ContentComponent.scss"

class ContentComponent extends React.Component {
  constructor(props) {
    super(props);
    this.editKeywordListSubmit = this.editKeywordListSubmit.bind(this);
    this.deleteKeywordListSubmit = this.deleteKeywordListSubmit.bind(this);
    this.getSuccessKeywords = this.getSuccessKeywords.bind(this);
    this.prepareKeywords = this.prepareKeywords.bind(this);
  }

  editKeywordListSubmit(formData) {
    const { patchKeywordList, selectedKeywordList, setModalOpen, deselectKeywordList } = this.props;
    let data = { name: formData.name };
    data.keywords = [];
    formData.keywords.every(uuid => data.keywords.push(validate(uuid) ? { uuid: uuid } : { content: uuid }));
    return patchKeywordList(
      selectedKeywordList.get('resource_uri'), data,
      [() => setModalOpen('edit', false), () => deselectKeywordList()]
    );
  }

  deleteKeywordListSubmit() {
    const { deleteKeywordList, selectedKeywordList, setModalOpen, deselectKeywordList } = this.props;
    deleteKeywordList(
      selectedKeywordList.get('resource_uri'),
      [() => setModalOpen('delete', false), () => deselectKeywordList()]
    );
  }

  getSuccessKeywords(keywords) {
    return keywords.filter(keyword => keyword.status === 'success').map(keyword => ({ content: keyword.text })).toJS();
  }

  prepareKeywords(recommendations, synonyms, manualkeywords) {
    return this.getSuccessKeywords(recommendations)
      .concat( this.getSuccessKeywords(synonyms) )
      .concat( this.getSuccessKeywords(manualkeywords) );
  }

  componentWillMount() {
    this.props.getKeywordLists();
  }

  render() {
    const {
        isModalOpen,
        setModalOpen,
        postKeywordList,
        purge,
        selectedKeywordList,
        recommendations,
        synonyms,
        manualkeywords,
        selectedReport,
        currentWord
    } = this.props;

    return (
        <div>
          <Grid>
            <Col xs={12} md={12}>
              <KeywordCreationController />
              <KeywordSearchController />
            </Col>
          </Grid>
          <PreviewKeywordsPopup
            isOpen={isModalOpen.get('preview')}
            report={selectedReport}
            onClose={() => setModalOpen('preview', false)}
            title="Report Preview"
          />
          <ModalForm
            isOpen={isModalOpen.get('create')}
            onClose={() => setModalOpen('create', false)}
            title="Create new Keyword list"
          >
            <KeywordListCreateForm
              submit_label='Create'
              name=''
              content=''
              onSubmit={data => postKeywordList(data, currentWord, this.prepareKeywords(recommendations, synonyms, manualkeywords), [() => purge(), () => setModalOpen('create', false)])}
            />
          </ModalForm>

          <ModalForm
            isOpen={isModalOpen.get('edit')}
            onClose={() => setModalOpen('edit', false)}
            title={`Edit Keyword list ${selectedKeywordList.get('name')}`}
          >
            <KeywordListEditForm
              submit_label='Edit'
              onSubmit={this.editKeywordListSubmit}
            />
          </ModalForm>

          <ModalForm
            isOpen={isModalOpen.get('delete')}
            onClose={() => setModalOpen('delete', false)}
            title="Are You Sure?"
          >
            <div className="text-center">
              <p>
                <strong>Do you want delete `{selectedKeywordList.get('name')}`?</strong>
              </p>
              <ButtonToolbar style={{display: 'inline-block'}}>
                <Button
                  bsStyle="danger"
                  onClick={this.deleteKeywordListSubmit}
                >
                  Yes
                </Button>
                <Button onClick={() => setModalOpen('delete', false)}>No</Button>
              </ButtonToolbar>
            </div>
          </ModalForm>

        </div>
    );
  }
}

const mapDispatchToProps = dispatch => bindActionCreators({
  postKeywordList,
  patchKeywordList,
  deleteKeywordList,
  setModalOpen,
  deselectKeywordList,
  getKeywordLists,
  purge
}, dispatch);

const mapStateToProps = state => ({
  recommendations: state[ MODULE_NAME ].get('recommendations'),
  synonyms: state[ MODULE_NAME ].get('synonyms'),
  manualkeywords: state[ MODULE_NAME ].get('manualkeywords'),
  currentWord: state[ MODULE_NAME ].get('currentWord'),
  selectedReport: state[ MODULE_NAME ].get('selectedReport'),
  selectedKeywordList: state[ MODULE_NAME ].get('selectedKeywordList'),
  isModalOpen: state[ MODULE_NAME ].get('isModalOpen')
});

export default connect(mapStateToProps, mapDispatchToProps)(ContentComponent);
